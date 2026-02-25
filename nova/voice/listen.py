"""Microphone recording with silence detection and Whisper transcription."""

from __future__ import annotations

import io
import time
import wave
from dataclasses import dataclass
from typing import Optional

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ListenConfig:
    silence_seconds: float = 1.5
    max_seconds: float = 12.0
    threshold: int = 450
    sample_rate: int = 16000
    chunk_size: int = 1024


class VoiceListener:
    """Capture speech audio and transcribe via Whisper API."""

    def __init__(self, config: Optional[ListenConfig] = None) -> None:
        self.config = config or ListenConfig()

    def record_until_silence(self) -> bytes:
        try:
            import audioop
            import pyaudio
        except ImportError:
            logger.warning("PyAudio unavailable; returning empty audio")
            return b""

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )

        frames: list[bytes] = []
        silence_for = 0.0
        start = time.time()

        try:
            while True:
                chunk = stream.read(self.config.chunk_size, exception_on_overflow=False)
                frames.append(chunk)
                rms = audioop.rms(chunk, 2)
                if rms < self.config.threshold:
                    silence_for += self.config.chunk_size / self.config.sample_rate
                else:
                    silence_for = 0.0

                elapsed = time.time() - start
                if silence_for >= self.config.silence_seconds or elapsed >= self.config.max_seconds:
                    break
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(b"".join(frames))

        return wav_buffer.getvalue()

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        settings = get_settings()
        if not settings.whisper_api_key:
            logger.warning("WHISPER_API_KEY missing; returning empty transcript")
            return ""

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.whisper_api_key)
            file_data = io.BytesIO(audio_bytes)
            file_data.name = "audio.wav"
            transcript = client.audio.transcriptions.create(model=settings.whisper_model, file=file_data)
            return transcript.text.strip()
        except Exception:  # noqa: BLE001
            logger.exception("Whisper transcription failed")
            return ""
