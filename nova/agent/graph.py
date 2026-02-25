"""LangGraph orchestration for Nova's planning and execution loop."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from nova.agent.executor import confirm_risky_actions, execute_next_step
from nova.agent.planner import create_plan
from nova.agent.responder import generate_response
from nova.agent.router import can_execute, has_more_steps, needs_confirmation
from nova.agent.state import AgentState


def build_graph() -> Any:
    """Build and compile the Nova state graph."""

    workflow = StateGraph(AgentState)
    workflow.add_node("plan", create_plan)
    workflow.add_node("confirm", confirm_risky_actions)
    workflow.add_node("execute", execute_next_step)
    workflow.add_node("respond", generate_response)

    workflow.set_entry_point("plan")
    workflow.add_conditional_edges("plan", needs_confirmation, {
        "confirm": "confirm",
        "execute": "execute",
        "respond": "respond",
    })
    workflow.add_conditional_edges("confirm", can_execute, {
        "execute": "execute",
        "respond": "respond",
    })
    workflow.add_conditional_edges("execute", has_more_steps, {
        "execute": "execute",
        "respond": "respond",
    })
    workflow.add_edge("respond", END)

    return workflow.compile()
