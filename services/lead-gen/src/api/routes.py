"""API routes for the Lead Generation service."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.schemas import (
    ContactFormRequest,
    LeadListResponse,
    LeadResponse,
    MessageResponse,
    ScrapeRequest,
    StatsResponse,
    StatusUpdateRequest,
)
from src.crm.manager import CRMManager
from src.db.database import get_db
from src.db.models import LeadSource, LeadStatus
from src.outreach.followup import FollowUpManager
from src.scoring.lead_scorer import LeadScorer
from src.scrapers.base import ScrapedLead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["leads"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str | None = Security(api_key_header)):
    if not key or key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key


# --- Contact Capture Form ---


@router.post("/leads/capture", response_model=LeadResponse)
async def capture_lead(
    form: ContactFormRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint: capture a lead from a contact form.

    No API key required — this is the public-facing form endpoint.
    """
    crm = CRMManager(db)

    if form.email:
        is_dup = await crm.check_duplicate(None, form.email)
        if is_dup:
            raise HTTPException(status_code=409, detail="A request with this email already exists")

    lead = await crm.create_lead_from_form(
        name=form.name,
        email=form.email,
        phone=form.phone,
        device_type=form.device_type,
        issue_description=form.issue_description,
    )

    # Score the form submission
    scorer = LeadScorer()
    scraped = ScrapedLead(
        source="web_form",
        name=form.name,
        email=form.email,
        phone=form.phone,
        device_type=form.device_type,
        issue_description=form.issue_description,
        raw_text=f"{form.name}: {form.issue_description}",
    )
    score_data = await scorer.score(scraped)

    from sqlalchemy import update as sql_update

    from src.db.models import Lead

    await db.execute(
        sql_update(Lead)
        .where(Lead.id == lead.id)
        .values(
            score=score_data["score"],
            score_reasoning=score_data["reasoning"],
            device_type=score_data.get("device_type") or lead.device_type,
            status=LeadStatus.SCORED,
        )
    )
    await db.commit()
    await db.refresh(lead)

    return lead


# --- Lead Management (API key required) ---


@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    status: str | None = None,
    source: str | None = None,
    min_score: float | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List leads with optional filters."""
    crm = CRMManager(db)
    status_enum = LeadStatus(status) if status else None
    source_enum = LeadSource(source) if source else None
    leads = await crm.list_leads(status_enum, source_enum, min_score, limit, offset)
    return LeadListResponse(leads=leads, total=len(leads))


@router.get("/leads/stats", response_model=StatsResponse)
async def lead_stats(
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get lead pipeline statistics."""
    crm = CRMManager(db)
    return await crm.get_stats()


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single lead by ID."""
    crm = CRMManager(db)
    lead = await crm.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/leads/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: int,
    body: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update a lead's status (approve, reject, etc.)."""
    crm = CRMManager(db)
    lead = await crm.update_status(lead_id, LeadStatus(body.status))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/leads/{lead_id}/followup", response_model=MessageResponse)
async def trigger_followup(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Manually trigger a follow-up message for a lead."""
    crm = CRMManager(db)
    lead = await crm.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    fm = FollowUpManager()
    attempt = len(lead.followups) + 1

    if not fm.should_followup(len(lead.followups)):
        raise HTTPException(status_code=400, detail="Max follow-up attempts reached")

    message = await fm.generate_message(
        name=lead.name,
        device_type=lead.device_type,
        issue_description=lead.issue_description,
        source=lead.source.value,
        attempt_number=attempt,
    )

    await crm.record_followup(lead.id, message, "email", attempt)
    return MessageResponse(message=message, lead_id=lead.id)


# --- Scraping ---


@router.post("/scrape", response_model=MessageResponse)
async def trigger_scrape(
    body: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Manually trigger a scrape run."""
    from src.scrapers.craigslist import CraigslistScraper
    from src.scrapers.google_maps import GoogleMapsScraper

    scraper_map = {
        "craigslist": CraigslistScraper(),
        "google_maps": GoogleMapsScraper(),
    }
    scorer = LeadScorer()
    crm = CRMManager(db)
    location = body.location or settings.scrape_location
    radius = body.radius_miles or settings.scrape_radius_miles

    total_created = 0
    for source_name in body.sources:
        scraper = scraper_map.get(source_name)
        if not scraper:
            continue

        leads = await scraper.scrape(location, radius)
        for lead_data in leads:
            is_dup = await crm.check_duplicate(lead_data.source_url, lead_data.email)
            if is_dup:
                continue

            score_result = await scorer.score(lead_data)
            if score_result["score"] >= settings.min_lead_score:
                lead = await crm.create_lead(lead_data, score_result)
                if score_result["score"] >= settings.auto_approve_threshold:
                    await crm.approve_lead(lead.id)
                total_created += 1

    return MessageResponse(message=f"Scrape complete: {total_created} new leads created")
