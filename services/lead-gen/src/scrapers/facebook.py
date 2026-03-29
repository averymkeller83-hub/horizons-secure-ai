"""Facebook Marketplace / community group scraper for repair leads.

Uses headless browsing via Playwright to access public marketplace
listings and community posts about broken electronics.
"""

import logging

from src.scrapers.base import BaseScraper, ScrapedLead

logger = logging.getLogger(__name__)

REPAIR_QUERIES = [
    "broken phone for sale",
    "cracked screen",
    "fix electronics",
    "broken laptop",
    "need phone repair",
]


class FacebookScraper(BaseScraper):
    """Scrapes public Facebook Marketplace listings for repair leads.

    NOTE: This scraper requires Playwright to be installed and configured.
    Facebook's structure changes frequently — this is a best-effort scraper
    that targets public marketplace listings only. No login required for
    public listings.
    """

    def source_name(self) -> str:
        return "facebook"

    async def scrape(self, location: str, radius_miles: int) -> list[ScrapedLead]:
        leads: list[ScrapedLead] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed — skipping Facebook scraper")
            return leads

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()

                for query in REPAIR_QUERIES:
                    try:
                        url = (
                            f"https://www.facebook.com/marketplace/search"
                            f"?query={query}&exact=false"
                        )
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(3000)

                        listings = await page.query_selector_all(
                            "[data-testid='marketplace_feed_item'], "
                            "div[class*='x1lliihq'] a[href*='/marketplace/item/']"
                        )

                        for listing in listings[:10]:
                            text = await listing.inner_text()
                            href = await listing.get_attribute("href") or ""
                            if not text.strip():
                                continue

                            leads.append(
                                ScrapedLead(
                                    source="facebook",
                                    issue_description=text.strip()[:500],
                                    source_url=(
                                        href
                                        if href.startswith("http")
                                        else f"https://facebook.com{href}"
                                    ),
                                    raw_text=text.strip()[:1000],
                                )
                            )
                    except Exception as e:
                        logger.warning("Facebook query '%s' failed: %s", query, e)

                await browser.close()
        except Exception as e:
            logger.error("Facebook scraper error: %s", e)

        logger.info("Facebook: found %d raw leads", len(leads))
        return leads
