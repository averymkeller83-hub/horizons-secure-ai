"""Tests for the lead scoring module."""

import pytest

from src.scrapers.base import ScrapedLead
from src.scoring.lead_scorer import LeadScorer


class TestLeadScorerFallback:
    """Test the rule-based fallback scorer (no Ollama required)."""

    def setup_method(self):
        self.scorer = LeadScorer()

    def test_fallback_with_device_and_contact(self):
        lead = ScrapedLead(
            source="craigslist",
            name="John",
            email="john@example.com",
            device_type="iPhone",
            issue_description="Cracked screen, need fix ASAP",
            raw_text="Cracked iPhone screen need fix ASAP",
        )
        result = self.scorer._fallback_score(lead)
        assert result["score"] >= 0.65
        assert "Device identified" in result["reasoning"]
        assert "Contact info" in result["reasoning"]

    def test_fallback_minimal_lead(self):
        lead = ScrapedLead(
            source="google_maps",
            raw_text="some random post",
        )
        result = self.scorer._fallback_score(lead)
        assert result["score"] == 0.3
        assert result["urgency"] == "medium"

    def test_fallback_urgency_detection(self):
        lead = ScrapedLead(
            source="craigslist",
            issue_description="BROKEN phone need repair urgent",
            raw_text="broken phone urgent",
        )
        result = self.scorer._fallback_score(lead)
        assert result["score"] > 0.3
        assert "Urgency detected" in result["reasoning"]


class TestParseResponse:
    def test_valid_json(self):
        response = '{"score": 0.85, "reasoning": "Good lead", "device_type": "iPhone", "urgency": "high"}'
        result = LeadScorer._parse_response(response)
        assert result["score"] == 0.85
        assert result["reasoning"] == "Good lead"
        assert result["urgency"] == "high"

    def test_json_with_markdown_fences(self):
        response = '```json\n{"score": 0.7, "reasoning": "OK", "device_type": null, "urgency": "medium"}\n```'
        result = LeadScorer._parse_response(response)
        assert result["score"] == 0.7

    def test_invalid_json(self):
        result = LeadScorer._parse_response("This is not JSON at all")
        assert result["score"] == 0.3
        assert "default score" in result["reasoning"]

    def test_score_clamped(self):
        result = LeadScorer._parse_response('{"score": 5.0, "reasoning": "over"}')
        assert result["score"] == 1.0
        result = LeadScorer._parse_response('{"score": -1.0, "reasoning": "under"}')
        assert result["score"] == 0.0
