from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://horizons:horizons@localhost:5432/horizons_leads"
    database_url_sync: str = "postgresql://horizons:horizons@localhost:5432/horizons_leads"

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Scraping
    scrape_interval_minutes: int = 60
    scrape_location: str = "local"
    scrape_radius_miles: int = 25

    # Lead Scoring
    min_lead_score: float = 0.4
    auto_approve_threshold: float = 0.8

    # Outreach
    followup_delay_hours: int = 24
    max_followup_attempts: int = 3

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_key: str = "changeme-generate-a-real-key"

    # Business Info
    business_name: str = "Horizons Electronics Repair"
    business_phone: str = ""
    business_email: str = ""
    business_address: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
