"""Executor node for calling MCP tool server with retries."""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple

import requests

from nova.agent.state import AgentState
from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


def _split_tool(tool_ref: str) -> Tuple[str, str]:
    tool, action = tool_ref.split(".", maxsplit=1)
    return tool, action


def execute_next_step(state: AgentState) -> AgentState:
    """Execute the next step and append result into state."""

    if not state.plan or state.current_step >= len(state.plan.steps):
        return state

    step = state.plan.steps[state.current_step]
    tool, action = _split_tool(step.tool)
    payload = {"tool": tool, "action": action, "args": step.args}

    settings = get_settings()
    endpoint = f"{settings.tool_server_url}/tools/execute"

    retries = 2
    for attempt in range(retries + 1):
        start = time.perf_counter()
        try:
            resp = requests.post(endpoint, json=payload, timeout=20)
            elapsed = (time.perf_counter() - start) * 1000
            resp.raise_for_status()
            body = resp.json()
            result = body.get("result", {})
            state.results.append(
                {
                    "step": state.current_step,
                    "tool": step.tool,
                    "result": result,
                    "execution_ms": round(elapsed, 2),
                }
            )
            logger.info("Executed %s in %.2fms", step.tool, elapsed)
            state.current_step += 1
            return state
        except requests.RequestException as exc:
            logger.warning("Step %s attempt %s failed: %s", step.tool, attempt + 1, exc)
            if attempt >= retries:
                state.error = f"Execution failed for {step.tool}: {exc}"
                state.current_step += 1
                state.results.append({"step": state.current_step, "tool": step.tool, "error": str(exc)})
                return state

    return state


def confirm_risky_actions(state: AgentState) -> AgentState:
    """Placeholder node for external yes/no capture."""

    # Main runtime sets confirmation_granted after verbal yes/no.
    return state
