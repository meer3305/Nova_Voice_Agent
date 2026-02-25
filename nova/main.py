"""Nova runtime entrypoint: wake word, agent loop, and proactive scheduler."""

from __future__ import annotations

import threading
import time
from queue import Empty, Queue

from nova.agent.graph import build_graph
from nova.agent.state import AgentState
from nova.config import get_settings
from nova.memory.db import MemoryDB
from nova.scheduler.jobs import ProactiveScheduler
from nova.utils.logger import get_logger
from nova.voice.listen import VoiceListener
from nova.voice.speak import Speaker
from nova.voice.wakeword import WakeWordListener

logger = get_logger(__name__)


class NovaRuntime:
    """Coordinates concurrent Nova subsystems."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.events: Queue[str] = Queue()
        self.stop_event = threading.Event()

        self.memory = MemoryDB()
        self.listener = VoiceListener()
        self.speaker = Speaker()
        self.wake_listener = WakeWordListener(self.events)
        self.scheduler = ProactiveScheduler(interval_minutes=self.settings.scheduler_interval_minutes)
        self.graph = build_graph()

        self.agent_thread = threading.Thread(target=self._agent_loop, daemon=True, name="agent-thread")

    def start(self) -> None:
        logger.info("Starting Nova runtime")
        self.speaker.speak("Nova is online. Say Hey Nova when you need me.")

        self.scheduler.start()
        self.wake_listener.start()
        self.agent_thread.start()

        try:
            while not self.stop_event.is_set():
                time.sleep(0.4)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            self.shutdown()

    def shutdown(self) -> None:
        self.stop_event.set()
        self.scheduler.shutdown()
        self.wake_listener.stop()

    def _agent_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                event = self.events.get(timeout=0.5)
            except Empty:
                continue

            if event != "wake_word_detected":
                continue

            self.speaker.speak("Yes, I am listening.")
            audio = self.listener.record_until_silence()
            transcript = self.listener.transcribe(audio)
            logger.info("User command: %s", transcript)

            if not transcript:
                self.speaker.speak("I did not catch that. Please try again.")
                continue

            state = AgentState(user_input=transcript, memory_context=self.memory.build_context())
            initial = self.graph.invoke(state)

            if initial.requires_confirmation and initial.confirmation_granted is None:
                self.speaker.speak(initial.final_response)
                confirm_audio = self.listener.record_until_silence()
                confirm_text = self.listener.transcribe(confirm_audio).lower().strip()
                confirmed = confirm_text in {"yes", "yeah", "confirm", "proceed", "do it"}

                resumed_state = AgentState(
                    user_input=transcript,
                    memory_context=state.memory_context,
                    plan=initial.plan,
                    current_step=0,
                    results=[],
                    requires_confirmation=True,
                    confirmation_granted=confirmed,
                )
                final_state = self.graph.invoke(resumed_state)
            else:
                final_state = initial

            summary = final_state.final_response
            self.speaker.speak(summary)

            if final_state.plan:
                self.memory.log_action(transcript, final_state.plan.intent, summary)


def run() -> None:
    NovaRuntime().start()


if __name__ == "__main__":
    run()
