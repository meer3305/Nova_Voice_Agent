"""Background proactive scheduler jobs for Nova."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from nova.agent.graph import build_graph
from nova.agent.state import AgentState
from nova.memory.db import MemoryDB
from nova.utils.logger import get_logger
from nova.voice.speak import Speaker

logger = get_logger(__name__)


class ProactiveScheduler:
    """Runs recurring jobs that trigger proactive AI notifications."""

    def __init__(self, interval_minutes: int = 5) -> None:
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.memory = MemoryDB()
        self.speaker = Speaker()
        self.graph = build_graph()

    def start(self) -> None:
        self.scheduler.add_job(self._check_proactive, "interval", minutes=self.interval_minutes, id="proactive_check")
        self.scheduler.start()
        logger.info("Proactive scheduler started with %s-minute interval", self.interval_minutes)

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

    def _check_proactive(self) -> None:
        logger.info("Running proactive checks")
        synthetic_prompt = (
            "Check upcoming meetings, important unread emails, and missed replies. "
            "If action needed, summarize alert for user."
        )
        state = AgentState(user_input=synthetic_prompt, memory_context=self.memory.build_context(), confirmation_granted=True)
        result = self.graph.invoke(state)
        response = result.final_response if hasattr(result, "final_response") else result.get("final_response", "")
        if response:
            self.speaker.speak(response)
