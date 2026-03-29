"""Craigslist scraper for electronics repair leads.

Scrapes the 'electronics' and 'wanted' sections for posts mentioning
broken devices, screen repairs, water damage, etc.
"""

import logging
import re

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedLead

logger = logging.getLogger(__name__)

REPAIR_KEYWORDS = [
    "broken screen",
    "cracked screen",
    "water damage",
    "won't turn on",
    "not charging",
    "need repair",
    "fix my",
    "broken phone",
    "broken laptop",
    "broken tablet",
    "screen replacement",
    "battery replacement",
    "repair needed",
    "damaged",
    "shattered",
]


class CraigslistScraper(BaseScraper):
    """Scrapes Craigslist for electronics repair leads."""

    def __init__(self, city: str = "sfbay"):
        self.city = city
        self.base_url = f"https://{city}.craigslist.org"

    def source_name(self) -> str:
        return "craigslist"

    async def scrape(self, location: str, radius_miles: int) -> list[ScrapedLead]:
        leads: list[ScrapedLead] = []
        search_sections = ["ela", "wan"]  # electronics, wanted

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for section in search_sections:
                for keyword in ["broken phone", "repair needed", "fix my"]:
                    try:
                        url = (
                            f"{self.base_url}/search/{section}"
                            f"?query={keyword}&searchNearby=1"
                            f"&nearbyArea={radius_miles}"
                        )
                        resp = await client.get(url)
                        if resp.status_code != 200:
                            logger.warning(
                                "Craigslist returned %d for %s", resp.status_code, url
                            )
                            continue

                        parsed = self._parse_listings(resp.text, section)
                        leads.extend(parsed)
                    except httpx.HTTPError as e:
                        logger.error("Craigslist scrape error: %s", e)

        logger.info("Craigslist: found %d raw leads", len(leads))
        return self._deduplicate(leads)

    def _parse_listings(self, html: str, section: str) -> list[ScrapedLead]:
        soup = BeautifulSoup(html, "lxml")
        results: list[ScrapedLead] = []

        for item in soup.select("li.result-row, li.cl-static-search-result"):
            title_el = item.select_one("a.result-title, a.titlestring")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            if not any(kw in title.lower() for kw in REPAIR_KEYWORDS):
                if section != "wan":
                    continue

            device_type = self._extract_device_type(title)

            results.append(
                ScrapedLead(
                    source="craigslist",
                    device_type=device_type,
                    issue_description=title,
                    source_url=href if href.startswith("http") else f"{self.base_url}{href}",
                    raw_text=title,
                )
            )

        return results

    @staticmethod
    def _extract_device_type(text: str) -> str | None:
        patterns = {
            "iPhone": r"iphone\s*\d*\s*\w*",
            "Samsung": r"samsung\s+\w+\s*\w*",
            "iPad": r"ipad\s*\w*",
            "MacBook": r"macbook\s*\w*",
            "Laptop": r"laptop",
            "Phone": r"phone",
            "Tablet": r"tablet",
            "Console": r"(ps[45]|xbox|nintendo|switch)",
        }
        for device, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return device
        return None

    @staticmethod
    def _deduplicate(leads: list[ScrapedLead]) -> list[ScrapedLead]:
        seen_urls: set[str] = set()
        unique: list[ScrapedLead] = []
        for lead in leads:
            if lead.source_url and lead.source_url not in seen_urls:
                seen_urls.add(lead.source_url)
                unique.append(lead)
        return unique
