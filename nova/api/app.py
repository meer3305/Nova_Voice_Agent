"""Nova REST API FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from nova.api.routes import router as nova_router
from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Nova API starting up...")
    yield
    logger.info("Nova API shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Nova AI Assistant API",
        description="REST API for Nova voice/text AI assistant backend service",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update this to specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(nova_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API info."""
        return {
            "name": "Nova AI Assistant API",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "running"
        }
    
    # Health check
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": __import__('datetime').datetime.now().isoformat()}
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Nova AI Assistant API",
            version="1.0.0",
            description="""
# Nova AI Assistant Backend

A modular AI assistant backend service for website integration.

## Features

- **Voice & Text Input**: Accepts both text and base64-encoded audio
- **Local Whisper STT**: Free speech-to-text transcription
- **LLM Planning**: Uses Groq LLM for task orchestration
- **Tool Execution**: Execute tools like Gmail, Calendar, Orders
- **Risk Management**: Confirmation workflow for sensitive actions
- **Persistent Memory**: SQLite-based user memory
- **REST API**: Clean JSON-based endpoints for frontend integration

## Main Endpoints

- `POST /nova/process` - Process user input
- `POST /nova/confirm` - Confirm risky actions
- `GET /nova/history/{user_id}` - Get user action history
- `GET /nova/status` - Get system status
- `POST /nova/transcribe` - Transcribe audio file

## Request Format

```json
{
    "user_id": "user123",
    "input_type": "text|audio",
    "content": "user input or base64 audio",
    "context": {}
}
```

## Response Format

```json
{
    "status": "success|error|confirmation_required",
    "message": "Human readable message",
    "actions_taken": [],
    "next_steps": [],
    "results": []
}
```
            """,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "nova.api.app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
