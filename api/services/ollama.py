"""Ollama client service — wraps the Ollama REST API."""

import httpx

from config import settings


class OllamaService:
    """Client for the local Ollama LLM instance."""

    def __init__(self, base_url: str | None = None, default_model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.default_model = default_model or settings.ollama_model

    async def list_models(self) -> list[str]:
        """Return names of all locally available models."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
    ) -> dict:
        """Single-shot text generation."""
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {
                "model": data.get("model", payload["model"]),
                "response": data.get("response", ""),
                "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
            }

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        system: str | None = None,
    ) -> dict:
        """Multi-turn chat completion."""
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(messages)

        payload = {
            "model": model or self.default_model,
            "messages": chat_messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            msg = data.get("message", {})
            return {
                "model": data.get("model", payload["model"]),
                "message": {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                },
                "total_duration_ms": data.get("total_duration", 0) / 1_000_000,
            }
