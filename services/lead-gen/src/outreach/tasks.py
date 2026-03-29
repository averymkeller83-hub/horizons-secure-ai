"""Celery tasks for background lead processing.

Handles periodic scraping, lead scoring, and follow-up scheduling.
"""

import asyncio
import logging

from celery import Celery
from celery.schedules import crontab

from config.settings import settings

logger = logging.getLogger(__name__)

app = Celery("lead_gen", broker=settings.redis_url)

app.conf.beat_schedule = {
    "scrape-all-sources": {
        "task": "src.outreach.tasks.run_scrape_pipeline",
        "schedule": crontab(minute=f"*/{settings.scrape_interval_minutes}"),
    },
    "process-followups": {
        "task": "src.outreach.tasks.process_followups",
        "schedule": crontab(hour="9-17", minute="0"),  # hourly during business hours
    },
}


def _run_async(coro):
    """Run async code in Celery sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="src.outreach.tasks.run_scrape_pipeline")
def run_scrape_pipeline():
    """Scrape all sources, score leads, and store in CRM."""
    _run_async(_scrape_pipeline())


async def _scrape_pipeline():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.crm.manager import CRMManager
    from src.scoring.lead_scorer import LeadScorer
    from src.scrapers.craigslist import CraigslistScraper
    from src.scrapers.google_maps import GoogleMapsScraper

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    scrapers = [
        CraigslistScraper(),
        GoogleMapsScraper(),
    ]
    scorer = LeadScorer()

    async with session_factory() as db:
        crm = CRMManager(db)

        for scraper in scrapers:
            try:
                leads = await scraper.scrape(
                    settings.scrape_location, settings.scrape_radius_miles
                )
                logger.info("%s returned %d leads", scraper.source_name(), len(leads))

                for lead_data in leads:
                    is_dup = await crm.check_duplicate(lead_data.source_url, lead_data.email)
                    if is_dup:
                        continue

                    score_result = await scorer.score(lead_data)
                    if score_result["score"] < settings.min_lead_score:
                        continue

                    lead = await crm.create_lead(lead_data, score_result)

                    if score_result["score"] >= settings.auto_approve_threshold:
                        await crm.approve_lead(lead.id)
                        logger.info("Auto-approved lead #%d (score=%.2f)", lead.id, lead.score)
            except Exception as e:
                logger.error("Scraper %s failed: %s", scraper.source_name(), e)

    await engine.dispose()


@app.task(name="src.outreach.tasks.process_followups")
def process_followups():
    """Send follow-ups to approved leads."""
    _run_async(_process_followups())


async def _process_followups():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.crm.manager import CRMManager
    from src.outreach.followup import FollowUpManager

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    followup_mgr = FollowUpManager()

    async with session_factory() as db:
        crm = CRMManager(db)
        leads = await crm.get_leads_for_followup()

        for lead in leads:
            if not followup_mgr.should_followup(len(lead.followups)):
                continue

            attempt = len(lead.followups) + 1
            message = await followup_mgr.generate_message(
                name=lead.name,
                device_type=lead.device_type,
                issue_description=lead.issue_description,
                source=lead.source.value,
                attempt_number=attempt,
            )

            # In production, this would send via email/SMS.
            # For now, record the generated message.
            await crm.record_followup(lead.id, message, "email", attempt)
            logger.info("Follow-up #%d sent for lead #%d", attempt, lead.id)

    await engine.dispose()
