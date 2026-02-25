"""State definitions for Nova LangGraph agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


RISKY_TOOLS = {
    "gmail.send_email",
    "gmail.draft_email",
    "sms.send_sms",
    "order.place_order",
    "order.prepare_order_sync",
    "linkedin.prepare_post_sync",
}


@dataclass
class PlanStep:
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    intent: str
    risk_level: str
    steps: List[PlanStep]


@dataclass
class AgentState:
    user_input: str
    plan: Optional[Plan] = None
    current_step: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_granted: Optional[bool] = None
    final_response: str = ""
    error: Optional[str] = None


def is_risky_step(step: PlanStep) -> bool:
    return step.tool in RISKY_TOOLS
