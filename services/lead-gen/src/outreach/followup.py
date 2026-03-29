"""Automated follow-up sequence manager.

Generates personalized outreach messages via Ollama and manages
the follow-up cadence for approved leads. Supports human-in-the-loop
approval before sending.
"""

import logging

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

OUTREACH_PROMPT = """You are writing a friendly, professional outreach message for {business_name},
an electronics repair shop.

A potential customer posted about needing help with their device. Write a short,
helpful message reaching out to offer repair services.

Details about the lead:
- Name: {name}
- Device: {device_type}
- Issue: {issue_description}
- Source: {source}
- This is follow-up attempt #{attempt_number}

Rules:
- Keep it under 100 words
- Be friendly and helpful, not salesy
- Mention the specific device/issue if known
- Include a call to action (visit, call, or reply)
- If attempt > 1, acknowledge previous message without being pushy
- Never include pricing unless asked

Write ONLY the message body, no subject line or signature."""


class FollowUpManager:
    """Generates and manages follow-up outreach messages."""

    def __init__(self):
        self.ollama_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.business_name = settings.business_name
        self.max_attempts = settings.max_followup_attempts

    async def generate_message(
        self,
        name: str | None,
        device_type: str | None,
        issue_description: str | None,
        source: str,
        attempt_number: int,
    ) -> str:
        """Generate a personalized outreach message via Ollama."""
        prompt = OUTREACH_PROMPT.format(
            business_name=self.business_name,
            name=name or "there",
            device_type=device_type or "device",
            issue_description=issue_description or "electronics issue",
            source=source,
            attempt_number=attempt_number,
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                message = data.get("response", "").strip()
                if message:
                    return message
        except Exception as e:
            logger.error("Ollama outreach generation failed: %s", e)

        return self._fallback_message(name, device_type, attempt_number)

    def _fallback_message(
        self, name: str | None, device_type: str | None, attempt: int
    ) -> str:
        """Template-based fallback when Ollama is unavailable."""
        greeting = f"Hi {name}" if name else "Hi there"
        device = device_type or "device"

        if attempt == 1:
            return (
                f"{greeting},\n\n"
                f"I noticed you might need help with your {device}. "
                f"At {self.business_name}, we specialize in fast, affordable "
                f"electronics repairs with a satisfaction guarantee.\n\n"
                f"Would you like a free diagnostic? Feel free to reply here "
                f"or give us a call.\n\n"
                f"Best,\n{self.business_name}"
            )
        elif attempt == 2:
            return (
                f"{greeting},\n\n"
                f"Just following up about your {device}. We'd love to help "
                f"get it working again. We offer same-day service for most "
                f"common repairs.\n\n"
                f"Let us know if you have any questions!\n\n"
                f"Best,\n{self.business_name}"
            )
        else:
            return (
                f"{greeting},\n\n"
                f"Last note from us — if you still need your {device} looked "
                f"at, our door is always open. No pressure at all.\n\n"
                f"Wishing you the best,\n{self.business_name}"
            )

    def should_followup(self, attempt_count: int) -> bool:
        """Check if another follow-up should be sent."""
        return attempt_count < self.max_attempts
