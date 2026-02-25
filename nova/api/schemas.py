"""Request and response schemas for Nova REST API."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ProcessRequest(BaseModel):
    """Request to process user input (text or audio)."""

    user_id: str = Field(..., description="Unique user identifier")
    input_type: Literal["text", "audio"] = Field(..., description="Type of input: text or base64 audio")
    content: str = Field(..., description="Either raw text or base64-encoded audio data")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional memory context")


class ConfirmRequest(BaseModel):
    """Request to confirm a risky action."""

    user_id: str = Field(..., description="Unique user identifier")
    confirm: bool = Field(..., description="true to confirm, false to cancel")


class HistoryRequest(BaseModel):
    """Query parameters for action history."""

    user_id: str = Field(..., description="Unique user identifier")
    limit: int = Field(default=50, ge=1, le=500, description="Number of records to retrieve")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class StepResult(BaseModel):
    """Result of an executed step."""

    step: int
    tool: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_ms: Optional[float] = None


class ConfirmationPrompt(BaseModel):
    """Confirmation requirement for risky actions."""

    status: Literal["confirmation_required"]
    message: str
    proposed_action: Dict[str, Any]


class SuccessResponse(BaseModel):
    """Successful execution response."""

    status: Literal["success"]
    message: str
    actions_taken: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    results: List[StepResult] = Field(default_factory=list)
    memory_updated: bool = False


class ErrorResponse(BaseModel):
    """Error response."""

    status: Literal["error"]
    message: str
    error_code: str = "UNKNOWN_ERROR"
    details: Optional[Dict[str, Any]] = None


class ConfirmationResponse(BaseModel):
    """Response indicating confirmation is required."""

    status: Literal["confirmation_required"]
    message: str
    proposed_action: Dict[str, Any]
    requires_user_approval: bool = True


class ProcessResponse(BaseModel):
    """Union of all possible process responses."""

    status: Literal["success", "error", "confirmation_required"]
    message: str
    actions_taken: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    results: Optional[List[StepResult]] = None
    proposed_action: Optional[Dict[str, Any]] = None
    requires_user_approval: Optional[bool] = None


class HistoryItem(BaseModel):
    """Single action history item."""

    id: int
    user_input: str
    intent: Optional[str]
    result_summary: Optional[str]
    created_at: str


class HistoryResponse(BaseModel):
    """Action history response."""

    status: str = "success"
    user_id: str
    total_items: int
    items: List[HistoryItem]


class StatusResponse(BaseModel):
    """System status response."""

    status: str = "ok"
    timestamp: str
    services: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0.0"


class TranscriptionResponse(BaseModel):
    """STT transcription response."""

    status: str = "success"
    text: str
    confidence: Optional[float] = None
    duration_ms: Optional[float] = None


# ============================================================================
# INTERNAL SCHEMAS
# ============================================================================


class ToolAction(BaseModel):
    """Internal tool action representation."""

    tool: str
    action: str
    args: Dict[str, Any] = Field(default_factory=dict)
