import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class LeadSource(str, enum.Enum):
    CRAIGSLIST = "craigslist"
    FACEBOOK = "facebook"
    GOOGLE_MAPS = "google_maps"
    WEB_FORM = "web_form"
    MANUAL = "manual"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    SCORED = "scored"
    APPROVED = "approved"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    REJECTED = "rejected"
    STALE = "stale"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[LeadSource] = mapped_column(Enum(LeadSource), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, nullable=False
    )

    # Contact info
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))

    # Lead details
    device_type: Mapped[str | None] = mapped_column(String(255))
    issue_description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    raw_text: Mapped[str | None] = mapped_column(Text)

    # Scoring
    score: Mapped[float | None] = mapped_column(Float)
    score_reasoning: Mapped[str | None] = mapped_column(Text)
    auto_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    followups: Mapped[list["FollowUp"]] = relationship(back_populates="lead")


class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # email, sms
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    responded: Mapped[bool] = mapped_column(Boolean, default=False)

    lead: Mapped["Lead"] = relationship(back_populates="followups")
