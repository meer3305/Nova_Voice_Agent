"""Application configuration for Nova voice assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Typed configuration loaded from environment variables."""

    app_name: str = "Nova"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # LLM
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Voice
    porcupine_access_key: Optional[str] = os.getenv("PORCUPINE_ACCESS_KEY")
    porcupine_keyword_path: Optional[str] = os.getenv("PORCUPINE_KEYWORD_PATH")
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    whisper_api_key: Optional[str] = os.getenv("WHISPER_API_KEY")
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-1")

    # External tools
    gmail_client_id: Optional[str] = os.getenv("GMAIL_CLIENT_ID")
    gmail_client_secret: Optional[str] = os.getenv("GMAIL_CLIENT_SECRET")
    gmail_refresh_token: Optional[str] = os.getenv("GMAIL_REFRESH_TOKEN")
    twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from_number: Optional[str] = os.getenv("TWILIO_FROM_NUMBER")

    # Runtime
    tool_server_url: str = os.getenv("TOOL_SERVER_URL", "http://127.0.0.1:8000")
    sqlite_path: str = os.getenv("SQLITE_PATH", "nova.db")
    scheduler_interval_minutes: int = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "5"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return singleton settings instance."""

    return Settings()
