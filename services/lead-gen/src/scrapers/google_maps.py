"""Google Maps / local search scraper for identifying potential customers.

Searches for businesses and individuals posting about electronics issues
in the local area — e.g. people asking for recommendations in Google
reviews, or competitor analysis for positioning.
"""

import logging

import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, ScrapedLead

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "electronics repair near me",
    "phone screen repair",
    "broken laptop repair",
    "tablet repair service",
]


class GoogleMapsScraper(BaseScraper):
    """Scrapes Google search results for local electronics repair demand signals.

    Targets organic search results and Google Maps pack listings to find
    people looking for repair services (potential inbound leads) and
    competitor info for outreach positioning.
    """

    def source_name(self) -> str:
        return "google_maps"

    async def scrape(self, location: str, radius_miles: int) -> list[ScrapedLead]:
        leads: list[ScrapedLead] = []

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; HorizonsBot/1.0)"},
        ) as client:
            for query in SEARCH_QUERIES:
                try:
                    full_query = f"{query} {location}"
                    url = f"https://www.google.com/search?q={full_query}&tbm=lcl"
                    resp = await client.get(url)

                    if resp.status_code != 200:
                        logger.warning("Google returned %d for '%s'", resp.status_code, query)
                        continue

                    parsed = self._parse_results(resp.text, query)
                    leads.extend(parsed)
                except httpx.HTTPError as e:
                    logger.error("Google scrape error for '%s': %s", query, e)

        logger.info("Google Maps: found %d raw leads", len(leads))
        return leads

    def _parse_results(self, html: str, query: str) -> list[ScrapedLead]:
        soup = BeautifulSoup(html, "lxml")
        results: list[ScrapedLead] = []

        # Parse local pack results and organic results
        for item in soup.select("div.VkpGBb, div.g"):
            title_el = item.select_one("div.dbg0pd, h3")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            address_el = item.select_one("span.LrzXr, div.s")
            address = address_el.get_text(strip=True) if address_el else None

            link_el = item.select_one("a[href]")
            href = link_el.get("href", "") if link_el else ""

            results.append(
                ScrapedLead(
                    source="google_maps",
                    name=title,
                    address=address,
                    issue_description=f"Search intent: {query}",
                    source_url=href,
                    raw_text=f"{title} - {address or 'no address'}",
                )
            )

        return results
