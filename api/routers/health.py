"""Health check endpoints for all services."""

import httpx
from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Top-level health check for the API gateway."""
    return {"status": "ok", "service": "horizons-api"}


@router.get("/health/ollama")
async def ollama_health():
    """Check Ollama connectivity and list available models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"status": "ok", "models": models}
    except httpx.HTTPError as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/health/all")
async def full_health():
    """Aggregate health status of all backend services."""
    results = {"api": "ok"}

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            results["ollama"] = "ok"
    except Exception:
        results["ollama"] = "error"

    # Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        results["redis"] = "ok"
    except Exception:
        results["redis"] = "error"

    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"status": overall, "services": results}
