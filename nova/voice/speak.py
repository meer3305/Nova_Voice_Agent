"""Speech synthesis via ElevenLabs with fallback to terminal output."""

from __future__ import annotations

import tempfile
from pathlib import Path

import requests

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class Speaker:
    """Text-to-speech abstraction."""

    def speak(self, text: str) -> None:
        if not text:
            return

        settings = get_settings()
        if not settings.elevenlabs_api_key:
            logger.info("Nova says: %s", text)
            return

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.85},
        }
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = Path(temp_file.name)
            self._play_audio(temp_path)
        except requests.RequestException:
            logger.exception("TTS generation failed")
            logger.info("Nova says: %s", text)

    def _play_audio(self, path: Path) -> None:
        try:
            from playsound import playsound

            playsound(str(path))
        except Exception:  # noqa: BLE001
            logger.info("Generated speech file at %s", path)
