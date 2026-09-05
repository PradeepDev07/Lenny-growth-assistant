from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to root .env
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_ENV = _ROOT_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "Lenny Growth Assistant"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./growth_assistant.db"

    # LLM Providers
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Default Task-to-Model Mappings (Configurable via UI / API)
    # Google Gemini — free tier
    MODEL_FOR_INTENT_ROUTING: str = "gemini-2.5-flash-lite"
    MODEL_FOR_RETRIEVAL_QA: str = "gemini-2.5-flash"
    MODEL_FOR_ARTIFACT: str = "gemini-2.5-flash"

    # OpenRouter — free models only
    MODEL_FOR_ESSAY: str = "openrouter/free"

    # Local Ollama — completely offline
    MODEL_FOR_OFFLINE: str = "llama3.2:3b"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=(_ROOT_ENV, ".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
