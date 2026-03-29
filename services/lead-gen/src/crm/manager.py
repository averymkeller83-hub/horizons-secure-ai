"""CRM integration manager for lead lifecycle management.

Handles creating, updating, and querying leads in the PostgreSQL database.
Designed to be extended with external CRM integrations (HubSpot, etc.)
via adapter pattern.
"""

import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FollowUp, Lead, LeadSource, LeadStatus
from src.scrapers.base import ScrapedLead

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "craigslist": LeadSource.CRAIGSLIST,
    "facebook": LeadSource.FACEBOOK,
    "google_maps": LeadSource.GOOGLE_MAPS,
    "web_form": LeadSource.WEB_FORM,
    "manual": LeadSource.MANUAL,
}


class CRMManager:
    """Manages leads in the local CRM (PostgreSQL)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lead(self, scraped: ScrapedLead, score_data: dict | None = None) -> Lead:
        """Create a new lead from scraped data and optional scoring."""
        lead = Lead(
            source=SOURCE_MAP.get(scraped.source, LeadSource.MANUAL),
            name=scraped.name,
            email=scraped.email,
            phone=scraped.phone,
            address=scraped.address,
            device_type=scraped.device_type or (score_data or {}).get("device_type"),
            issue_description=scraped.issue_description,
            source_url=scraped.source_url,
            raw_text=scraped.raw_text,
        )

        if score_data:
            lead.score = score_data["score"]
            lead.score_reasoning = score_data["reasoning"]
            lead.status = LeadStatus.SCORED

        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)
        logger.info("Created lead #%d (score=%.2f)", lead.id, lead.score or 0)
        return lead

    async def create_lead_from_form(
        self,
        name: str,
        email: str | None,
        phone: str | None,
        device_type: str | None,
        issue_description: str,
    ) -> Lead:
        """Create a lead from a contact capture form submission."""
        lead = Lead(
            source=LeadSource.WEB_FORM,
            status=LeadStatus.NEW,
            name=name,
            email=email,
            phone=phone,
            device_type=device_type,
            issue_description=issue_description,
            raw_text=f"Form submission from {name}: {issue_description}",
        )
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)
        logger.info("Created form lead #%d from %s", lead.id, name)
        return lead

    async def update_status(self, lead_id: int, status: LeadStatus) -> Lead | None:
        """Update a lead's status."""
        stmt = (
            update(Lead)
            .where(Lead.id == lead_id)
            .values(status=status)
            .returning(Lead)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        row = result.scalar_one_or_none()
        if row:
            logger.info("Lead #%d status -> %s", lead_id, status.value)
        return row

    async def approve_lead(self, lead_id: int) -> Lead | None:
        """Approve a lead for outreach."""
        return await self.update_status(lead_id, LeadStatus.APPROVED)

    async def reject_lead(self, lead_id: int) -> Lead | None:
        """Reject a lead."""
        return await self.update_status(lead_id, LeadStatus.REJECTED)

    async def get_lead(self, lead_id: int) -> Lead | None:
        """Fetch a single lead by ID."""
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def list_leads(
        self,
        status: LeadStatus | None = None,
        source: LeadSource | None = None,
        min_score: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lead]:
        """List leads with optional filtering."""
        stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Lead.status == status)
        if source:
            stmt = stmt.where(Lead.source == source)
        if min_score is not None:
            stmt = stmt.where(Lead.score >= min_score)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_leads_for_followup(self) -> list[Lead]:
        """Get approved leads that haven't been contacted yet."""
        stmt = select(Lead).where(
            Lead.status == LeadStatus.APPROVED,
            Lead.last_contacted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def record_followup(
        self, lead_id: int, message: str, channel: str, attempt: int
    ) -> FollowUp:
        """Record that a follow-up was sent."""
        followup = FollowUp(
            lead_id=lead_id,
            attempt_number=attempt,
            message=message,
            channel=channel,
        )
        self.db.add(followup)

        await self.db.execute(
            update(Lead)
            .where(Lead.id == lead_id)
            .values(
                status=LeadStatus.CONTACTED,
                last_contacted_at=datetime.utcnow(),
            )
        )
        await self.db.commit()
        await self.db.refresh(followup)
        return followup

    async def check_duplicate(self, source_url: str | None, email: str | None) -> bool:
        """Check if a lead already exists by source URL or email."""
        if source_url:
            result = await self.db.execute(
                select(Lead).where(Lead.source_url == source_url)
            )
            if result.scalar_one_or_none():
                return True
        if email:
            result = await self.db.execute(
                select(Lead).where(Lead.email == email)
            )
            if result.scalar_one_or_none():
                return True
        return False

    async def get_stats(self) -> dict:
        """Get lead pipeline statistics."""
        all_leads = await self.db.execute(select(Lead))
        leads = list(all_leads.scalars().all())

        by_status = {}
        by_source = {}
        for lead in leads:
            by_status[lead.status.value] = by_status.get(lead.status.value, 0) + 1
            by_source[lead.source.value] = by_source.get(lead.source.value, 0) + 1

        scores = [l.score for l in leads if l.score is not None]
        return {
            "total": len(leads),
            "by_status": by_status,
            "by_source": by_source,
            "avg_score": sum(scores) / len(scores) if scores else 0,
        }
