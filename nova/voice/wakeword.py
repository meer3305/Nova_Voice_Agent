"""Wake word listener using Porcupine in a background thread."""

from __future__ import annotations

import struct
import threading
from queue import Queue
from typing import Optional

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class WakeWordListener:
    """Always-on wake-word listener that pushes events onto a queue."""

    def __init__(self, event_queue: Queue[str]) -> None:
        self.event_queue = event_queue
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True, name="wakeword-thread")
        self._thread.start()
        logger.info("Wake word listener started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        settings = get_settings()
        try:
            import pvporcupine
            import pyaudio
        except ImportError:
            logger.warning("Porcupine/PyAudio unavailable; wake word listener disabled")
            return

        if not settings.porcupine_access_key:
            logger.warning("PORCUPINE_ACCESS_KEY missing; wake word listener disabled")
            return

        porcupine = pvporcupine.create(
            access_key=settings.porcupine_access_key,
            keyword_paths=[settings.porcupine_keyword_path] if settings.porcupine_keyword_path else None,
            keywords=None if settings.porcupine_keyword_path else ["porcupine"],
        )
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        try:
            while not self._stop.is_set():
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm_unpacked)
                if keyword_index >= 0:
                    logger.info("Wake word detected")
                    self.event_queue.put("wake_word_detected")
        finally:
            stream.close()
            pa.terminate()
            porcupine.delete()
