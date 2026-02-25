"""Quick starter for Nova: boots MCP tool server and runtime in one command."""

from __future__ import annotations

import threading
import time

import uvicorn

from nova.main import NovaRuntime
from nova.utils.logger import get_logger

logger = get_logger(__name__)


def run_tool_server() -> None:
    """Run the FastAPI MCP tool server."""

    config = uvicorn.Config(
        "nova.mcp_server.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )
    server = uvicorn.Server(config)
    server.run()


def main() -> None:
    logger.info("Starting Nova quick launcher")

    tool_server_thread = threading.Thread(
        target=run_tool_server,
        daemon=True,
        name="mcp-tool-server-thread",
    )
    tool_server_thread.start()

    # Small delay so the tool server starts before agent requests are made.
    time.sleep(1.0)

    runtime = NovaRuntime()
    runtime.start()


if __name__ == "__main__":
    main()
