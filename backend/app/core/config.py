from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ROOT_ENV), env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "smart_watchlist"

    redis_url: str = "redis://localhost:6380/0"

    chroma_persist_directory: str = "./chroma_data"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    """Current supported Flash-class model per ai.google.dev/gemini-api/docs/models
    (checked live, Sept 2026). gemini-2.0-flash is deprecated/shut down -- do not
    revert to it. Override via GEMINI_MODEL if Google ships a newer one."""

    market_data_provider: str = "yfinance"

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    demo_mode: bool = False

    session_secret: str = "change-me-in-prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
