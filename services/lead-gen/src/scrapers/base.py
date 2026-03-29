"""Base scraper interface for lead generation sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScrapedLead:
    """Raw lead data extracted from a source."""

    source: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    device_type: str | None = None
    issue_description: str | None = None
    source_url: str | None = None
    raw_text: str = ""


class BaseScraper(ABC):
    """Abstract base for all lead scrapers."""

    @abstractmethod
    async def scrape(self, location: str, radius_miles: int) -> list[ScrapedLead]:
        """Scrape leads from the source within the given area."""
        ...

    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier."""
        ...
