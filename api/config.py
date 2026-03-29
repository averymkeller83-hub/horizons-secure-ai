"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "info"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Database
    database_url: str = "postgresql+asyncpg://horizons:horizons_dev_password@localhost:5432/horizons"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
