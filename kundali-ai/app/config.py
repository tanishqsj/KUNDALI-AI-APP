# Placeholder for kundali-ai/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ─── App ──────────────────────────────
    APP_NAME: str = "kundali-ai"
    ENV: str = "local"
    DEBUG: bool = True

    # ─── Database ─────────────────────────
    DATABASE_URL: str

    # ─── Redis ────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # ─── OpenAI ───────────────────────────
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 800
    OPENAI_TIMEOUT: int = 30
    OPENAI_RETRIES: int = 3

    # ─── Local Whisper ────────────────────
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"


    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
