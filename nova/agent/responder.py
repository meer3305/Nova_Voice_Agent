"""Response generation node with concise voice output constraints."""

from __future__ import annotations

from typing import List

from nova.agent.state import AgentState


MAX_SENTENCES = 3


def _join_sentences(lines: List[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return ". ".join(sentences[:MAX_SENTENCES]) + ("." if sentences else "")


def generate_response(state: AgentState) -> AgentState:
    """Create a short spoken response from execution results."""

    if state.requires_confirmation and state.confirmation_granted is False:
        state.final_response = "Understood. I paused that task because it needs your confirmation."
        return state

    if state.requires_confirmation and state.confirmation_granted is None:
        state.final_response = "This task includes sensitive actions. Please say yes to continue or no to cancel."
        return state

    if state.error:
        state.final_response = _join_sentences(
            [
                "I ran into an execution issue",
                state.error,
                "I can retry or adjust the plan if you want",
            ]
        )
        return state

    if not state.plan:
        state.final_response = "I could not build a safe plan for that request."
        return state

    state.final_response = _join_sentences(
        [
            f"Completed intent {state.plan.intent}",
            f"Executed {len(state.results)} step(s)",
            "Anything else you want me to handle",
        ]
    )
    return state
