"""LLM proxy endpoints — send prompts to the local Ollama instance."""

from fastapi import APIRouter, HTTPException

from models.schemas import (
    ChatRequest,
    ChatResponse,
    GenerateRequest,
    GenerateResponse,
    ModelListResponse,
)
from services.ollama import OllamaService

router = APIRouter(tags=["LLM"])

ollama = OllamaService()


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """List all models available in the local Ollama instance."""
    models = await ollama.list_models()
    return ModelListResponse(models=models)


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Send a single prompt to the LLM and get a completion."""
    try:
        result = await ollama.generate(
            prompt=request.prompt,
            model=request.model,
            system=request.system,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a multi-turn conversation to the LLM."""
    try:
        result = await ollama.chat(
            messages=[m.model_dump() for m in request.messages],
            model=request.model,
            system=request.system,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")
