"""Run Nova REST API server."""

from __future__ import annotations

import uvicorn

from nova.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Start the Nova REST API server."""
    logger.info("Starting Nova REST API Server")
    logger.info("API will be available at http://0.0.0.0:8001")
    logger.info("Documentation at http://0.0.0.0:8001/docs")
    
    config = uvicorn.Config(
        "nova.api.app:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=False,
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
