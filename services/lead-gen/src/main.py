"""Lead Generation Service — FastAPI application entry point.

Part of the Horizons Secure AI infrastructure. Provides:
- Web scraping pipeline for local electronics repair leads
- Contact capture forms for inbound leads
- LLM-powered lead scoring via Ollama
- CRM management with PostgreSQL
- Automated follow-up sequences via Celery
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.api.forms import router as forms_router
from src.api.routes import router as api_router
from src.db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Lead Gen service for %s", settings.business_name)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Lead Gen service")


app = FastAPI(
    title=f"{settings.business_name} — Lead Generation",
    description="Automated lead generation and CRM for electronics repair",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(forms_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lead-gen", "business": settings.business_name}
