"""Routing logic for LangGraph conditional edges."""

from __future__ import annotations

from nova.agent.state import AgentState, is_risky_step


def needs_confirmation(state: AgentState) -> str:
    """Return next node based on risk confirmation requirement."""

    if not state.plan or not state.plan.steps:
        return "respond"

    for step in state.plan.steps:
        if is_risky_step(step):
            state.requires_confirmation = True
            return "confirm"
    return "execute"


def can_execute(state: AgentState) -> str:
    if not state.requires_confirmation:
        return "execute"
    if state.confirmation_granted is True:
        return "execute"
    return "respond"


def has_more_steps(state: AgentState) -> str:
    if not state.plan:
        return "respond"
    return "execute" if state.current_step < len(state.plan.steps) else "respond"
