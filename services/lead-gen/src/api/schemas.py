"""Pydantic request/response schemas for the Lead Gen API."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactFormRequest(BaseModel):
    """Contact capture form submission."""

    name: str = Field(..., min_length=1, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    device_type: str | None = Field(None, max_length=255)
    issue_description: str = Field(..., min_length=5, max_length=2000)


class LeadResponse(BaseModel):
    """Lead data returned by the API."""

    id: int
    source: str
    status: str
    name: str | None
    email: str | None
    phone: str | None
    device_type: str | None
    issue_description: str | None
    score: float | None
    score_reasoning: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_source: dict[str, int]
    avg_score: float


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|contacted|converted|stale)$")


class ScrapeRequest(BaseModel):
    """Manual scrape trigger."""

    sources: list[str] = Field(default=["craigslist", "google_maps"])
    location: str | None = None
    radius_miles: int | None = None


class MessageResponse(BaseModel):
    message: str
    lead_id: int | None = None
