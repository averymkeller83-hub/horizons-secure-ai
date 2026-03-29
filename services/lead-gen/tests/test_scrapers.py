"""Tests for scraper components."""

import pytest

from src.scrapers.base import ScrapedLead
from src.scrapers.craigslist import CraigslistScraper


class TestCraigslistScraper:
    def setup_method(self):
        self.scraper = CraigslistScraper(city="sfbay")

    def test_source_name(self):
        assert self.scraper.source_name() == "craigslist"

    def test_extract_device_type_iphone(self):
        assert self.scraper._extract_device_type("Broken iPhone 14 Pro") == "iPhone"

    def test_extract_device_type_samsung(self):
        assert self.scraper._extract_device_type("Samsung Galaxy cracked") == "Samsung"

    def test_extract_device_type_laptop(self):
        assert self.scraper._extract_device_type("My laptop won't turn on") == "Laptop"

    def test_extract_device_type_console(self):
        assert self.scraper._extract_device_type("PS5 not working") == "Console"

    def test_extract_device_type_unknown(self):
        assert self.scraper._extract_device_type("Need help with my toaster") is None

    def test_deduplicate(self):
        leads = [
            ScrapedLead(source="craigslist", source_url="http://example.com/1", raw_text="a"),
            ScrapedLead(source="craigslist", source_url="http://example.com/1", raw_text="b"),
            ScrapedLead(source="craigslist", source_url="http://example.com/2", raw_text="c"),
        ]
        result = CraigslistScraper._deduplicate(leads)
        assert len(result) == 2
