"""LLM-powered lead scoring via local Ollama instance.

Analyzes scraped lead data and assigns a relevance score (0.0-1.0) based on:
- Device type and repair feasibility
- Urgency signals in the text
- Geographic proximity
- Contact information completeness
"""

import json
import logging

import httpx

from config.settings import settings
from src.scrapers.base import ScrapedLead

logger = logging.getLogger(__name__)

SCORING_PROMPT = """You are a lead scoring assistant for an electronics repair business called "{business_name}".

Analyze the following lead and return a JSON object with:
- "score": a float from 0.0 to 1.0 (1.0 = highest quality lead)
- "reasoning": a brief explanation of the score
- "device_type": the device type if identifiable, else null
- "urgency": "high", "medium", or "low"

Scoring criteria:
- Higher score for common repair jobs (phones, laptops, tablets, game consoles)
- Higher score if urgency is indicated ("ASAP", "need today", "broken", "emergency")
- Higher score if contact info is available
- Lower score for vague or unrelated posts
- Lower score for devices we typically don't repair (appliances, cars, HVAC)

Lead data:
- Source: {source}
- Text: {raw_text}
- Device: {device_type}
- Issue: {issue_description}
- Name: {name}
- Email: {email}
- Phone: {phone}
- Location: {address}

Respond ONLY with valid JSON, no markdown."""


class LeadScorer:
    """Scores leads using the local Ollama LLM."""

    def __init__(self):
        self.ollama_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.business_name = settings.business_name

    async def score(self, lead: ScrapedLead) -> dict:
        """Score a single lead. Returns dict with score, reasoning, urgency."""
        prompt = SCORING_PROMPT.format(
            business_name=self.business_name,
            source=lead.source,
            raw_text=lead.raw_text[:500],
            device_type=lead.device_type or "unknown",
            issue_description=lead.issue_description or "not specified",
            name=lead.name or "unknown",
            email=lead.email or "not provided",
            phone=lead.phone or "not provided",
            address=lead.address or "not provided",
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return self._parse_response(data.get("response", ""))
        except httpx.HTTPError as e:
            logger.error("Ollama scoring request failed: %s", e)
            return self._fallback_score(lead)
        except Exception as e:
            logger.error("Scoring error: %s", e)
            return self._fallback_score(lead)

    async def score_batch(self, leads: list[ScrapedLead]) -> list[dict]:
        """Score multiple leads sequentially (Ollama handles one at a time)."""
        results = []
        for lead in leads:
            result = await self.score(lead)
            results.append(result)
        return results

    @staticmethod
    def _parse_response(text: str) -> dict:
        """Parse JSON from LLM response, handling common formatting issues."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            parsed = json.loads(cleaned)
            score = float(parsed.get("score", 0.0))
            return {
                "score": max(0.0, min(1.0, score)),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
                "device_type": parsed.get("device_type"),
                "urgency": parsed.get("urgency", "medium"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse LLM scoring response: %s", e)
            return {
                "score": 0.3,
                "reasoning": "Could not parse LLM response — assigned default score",
                "device_type": None,
                "urgency": "medium",
            }

    @staticmethod
    def _fallback_score(lead: ScrapedLead) -> dict:
        """Rule-based fallback when Ollama is unavailable."""
        score = 0.3
        reasons = []

        if lead.device_type:
            score += 0.2
            reasons.append(f"Device identified: {lead.device_type}")

        if lead.email or lead.phone:
            score += 0.2
            reasons.append("Contact info available")

        if lead.issue_description:
            urgency_words = ["asap", "urgent", "emergency", "today", "broken", "cracked"]
            if any(w in (lead.issue_description or "").lower() for w in urgency_words):
                score += 0.15
                reasons.append("Urgency detected")

        return {
            "score": min(1.0, score),
            "reasoning": "Fallback scoring: " + "; ".join(reasons) if reasons else "No signals",
            "device_type": lead.device_type,
            "urgency": "medium",
        }
