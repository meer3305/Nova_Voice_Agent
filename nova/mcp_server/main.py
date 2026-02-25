"""FastAPI MCP-style modular tool server for Nova."""

from __future__ import annotations

from typing import Any, Dict, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nova.mcp_server.calendar_tool import CalendarTool
from nova.mcp_server.gmail_tool import GmailTool
from nova.mcp_server.linkedin_tool import LinkedInTool
from nova.mcp_server.order_tool import OrderTool
from nova.mcp_server.sentiment_tool import SentimentTool
from nova.mcp_server.sms_tool import SMSTool
from nova.utils.logger import get_logger

logger = get_logger(__name__)
app = FastAPI(title="Nova MCP Tool Server", version="1.0.0")

TOOLS = {
    "gmail": GmailTool(),
    "calendar": CalendarTool(),
    "sms": SMSTool(),
    "sentiment": SentimentTool(),
    "order": OrderTool(),
    "linkedin": LinkedInTool(),
}


class ToolRequest(BaseModel):
    tool: Literal["gmail", "calendar", "sms", "sentiment", "order", "linkedin"]
    action: str
    args: Dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/tools/execute")
def execute_tool(req: ToolRequest) -> Dict[str, Any]:
    logger.info("Tool request: %s.%s", req.tool, req.action)
    tool_obj = TOOLS.get(req.tool)
    if tool_obj is None:
        raise HTTPException(status_code=400, detail=f"Unknown tool {req.tool}")
    
    method = getattr(tool_obj, req.action, None)
    if method is None:
        raise HTTPException(status_code=400, detail=f"Unknown action {req.action} for tool {req.tool}")

    try:
        result = method(**req.args)
        return {"ok": True, "result": result}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Tool execution failure")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

