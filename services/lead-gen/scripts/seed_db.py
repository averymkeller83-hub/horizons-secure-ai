"""Seed the database with sample leads for development/testing."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from src.db.database import Base
from src.db.models import Lead, LeadSource, LeadStatus

SAMPLE_LEADS = [
    {
        "source": LeadSource.CRAIGSLIST,
        "status": LeadStatus.SCORED,
        "name": "Mike Johnson",
        "email": "mike.j@example.com",
        "phone": "555-0101",
        "device_type": "iPhone",
        "issue_description": "Cracked iPhone 14 screen, still turns on",
        "score": 0.85,
        "score_reasoning": "Common repair, contact info provided, clear issue",
    },
    {
        "source": LeadSource.FACEBOOK,
        "status": LeadStatus.APPROVED,
        "name": "Sarah Lee",
        "phone": "555-0102",
        "device_type": "MacBook",
        "issue_description": "MacBook Pro won't charge, tried multiple cables",
        "score": 0.78,
        "score_reasoning": "Repair-feasible issue, phone provided",
    },
    {
        "source": LeadSource.WEB_FORM,
        "status": LeadStatus.NEW,
        "name": "Alex Chen",
        "email": "alex.chen@example.com",
        "device_type": "Samsung Phone",
        "issue_description": "Samsung Galaxy S24 screen is shattered, need ASAP fix",
        "score": 0.92,
        "score_reasoning": "High urgency, common device, email provided",
    },
    {
        "source": LeadSource.GOOGLE_MAPS,
        "status": LeadStatus.SCORED,
        "name": None,
        "device_type": "Laptop",
        "issue_description": "Laptop running slow, might need repair or cleanup",
        "score": 0.45,
        "score_reasoning": "Vague issue, no contact info, could be software not hardware",
    },
    {
        "source": LeadSource.CRAIGSLIST,
        "status": LeadStatus.CONTACTED,
        "name": "Taylor Smith",
        "email": "taylor@example.com",
        "phone": "555-0105",
        "device_type": "Console",
        "issue_description": "PS5 disc drive stopped working completely",
        "score": 0.72,
        "score_reasoning": "Repairable issue, full contact info",
    },
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        for data in SAMPLE_LEADS:
            lead = Lead(**data)
            db.add(lead)
        await db.commit()
        print(f"Seeded {len(SAMPLE_LEADS)} sample leads")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
