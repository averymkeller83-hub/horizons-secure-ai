"""Horizons Secure AI — API Gateway

Central API layer managing communication between services and the local LLM.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import health, llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"Starting Horizons API on {settings.api_host}:{settings.api_port}")
    print(f"Ollama endpoint: {settings.ollama_base_url}")
    print(f"Default model: {settings.ollama_model}")
    yield
    print("Shutting down Horizons API")


app = FastAPI(
    title="Horizons Secure AI",
    description="API gateway for Horizons Electronics Repair AI infrastructure",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(llm.router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level,
    )
