"""FastAPI routes for Nova REST API."""

from __future__ import annotations

import base64
import json
import tempfile
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import ValidationError

from nova.agent.graph import build_graph
from nova.agent.state import AgentState
from nova.api.schemas import (
    ConfirmRequest,
    HistoryResponse,
    HistoryItem,
    ProcessRequest,
    ProcessResponse,
    StatusResponse,
    TranscriptionResponse,
)
from nova.config import get_settings
from nova.memory.db import MemoryDB
from nova.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nova", tags=["nova"])

# Global state for ongoing sessions
_sessions: Dict[str, Dict[str, Any]] = {}
_memory_db = MemoryDB()
_graph = build_graph()


def _get_or_create_session(user_id: str) -> Dict[str, Any]:
    """Get or create a user session."""
    if user_id not in _sessions:
        _sessions[user_id] = {
            "state": AgentState(user_input=""),
            "created_at": datetime.now(),
            "confirmation_pending": False,
        }
    return _sessions[user_id]


def _transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using local Whisper."""
    try:
        from faster_whisper import WhisperModel
        
        model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # Write temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            segments, _ = model.transcribe(tmp_path, beam_size=5)
            text = "".join([segment.text for segment in segments])
            return text.strip()
        finally:
            import os
            os.unlink(tmp_path)
    except ImportError:
        logger.warning("faster_whisper not installed, using fallback")
        return "[Whisper not available - please install faster-whisper]"
    except Exception as exc:
        logger.exception("Transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(exc)}")


def _get_memory_context(user_id: str) -> Dict[str, Any]:
    """Retrieve memory context for user."""
    context = {}
    
    try:
        contacts = _memory_db.get_category("frequent_contacts", limit=5)
        if contacts:
            context["frequent_contacts"] = [
                {c.key: c.value} for c in contacts
            ]
    except Exception as exc:
        logger.warning("Failed to load contacts: %s", exc)
    
    try:
        preferences = _memory_db.get_memory("preferences", "food_preferences")
        if preferences:
            context["food_preferences"] = preferences.value
    except Exception as exc:
        logger.warning("Failed to load food preferences: %s", exc)
    
    try:
        tone = _memory_db.get_memory("preferences", "tone_preference")
        if tone:
            context["tone_preference"] = tone.value
    except Exception as exc:
        logger.warning("Failed to load tone preference: %s", exc)
    
    return context


@router.post("/process", response_model=ProcessResponse)
async def process_input(req: ProcessRequest) -> ProcessResponse:
    """
    Process user input (text or audio) and orchestrate agent execution.
    
    - If input_type is "audio", decodes base64 and transcribes
    - Loads user memory context
    - Runs LangGraph agent
    - Returns execution plan and next steps
    """
    try:
        logger.info(f"Processing request for user {req.user_id}, type={req.input_type}")
        
        # Get or create session
        session = _get_or_create_session(req.user_id)
        
        # Transcribe if audio
        user_text = req.content
        if req.input_type == "audio":
            try:
                audio_bytes = base64.b64decode(req.content)
                logger.info(f"Transcribing {len(audio_bytes)} bytes of audio")
                user_text = _transcribe_audio(audio_bytes)
                logger.info(f"Transcribed: {user_text}")
            except Exception as exc:
                logger.exception("Audio processing failed")
                raise HTTPException(status_code=400, detail=f"Audio processing failed: {str(exc)}")
        
        # Get memory context
        memory_context = _get_memory_context(req.user_id)
        
        # Merge with provided context
        if req.context:
            memory_context.update(req.context)
        
        # Create initial state
        state = AgentState(
            user_input=user_text,
            memory_context=memory_context,
        )
        
        # Run agent
        logger.info(f"Running agent for user {req.user_id}")
        try:
            final_state = _graph.invoke(state)
        except Exception as exc:
            logger.exception("Agent execution failed")
            raise HTTPException(
                status_code=500,
                detail=f"Agent execution failed: {str(exc)}"
            )
        
        # Save to session
        session["state"] = final_state
        session["last_updated"] = datetime.now()
        
        # Check if confirmation required
        if final_state.requires_confirmation and final_state.confirmation_granted is None:
            session["confirmation_pending"] = True
            
            # Log action
            try:
                _memory_db.log_action(
                    user_input=user_text,
                    intent=final_state.plan.intent if final_state.plan else "unknown",
                    result_summary="Pending confirmation",
                    user_id=req.user_id
                )
            except Exception as exc:
                logger.warning("Failed to log action: %s", exc)
            
            proposed_action = {
                "intent": final_state.plan.intent if final_state.plan else "unknown",
                "risk_level": final_state.plan.risk_level if final_state.plan else "unknown",
                "description": final_state.final_response or "Confirmation required for this action"
            }
            
            return ProcessResponse(
                status="confirmation_required",
                message=final_state.final_response or "This action requires your confirmation",
                proposed_action=proposed_action,
                requires_user_approval=True
            )
        
        # Log successful action
        try:
            _memory_db.log_action(
                user_input=user_text,
                intent=final_state.plan.intent if final_state.plan else "unknown",
                result_summary=final_state.final_response or "Completed",
                user_id=req.user_id
            )
        except Exception as exc:
            logger.warning("Failed to log action: %s", exc)
        
        # Build response
        actions_taken = [f"Step {r['step']}: {r['tool']}" for r in final_state.results]
        
        return ProcessResponse(
            status="success",
            message=final_state.final_response or "Completed successfully",
            actions_taken=actions_taken,
            next_steps=["Continue with next task if needed"],
            results=[
                {
                    "step": r["step"],
                    "tool": r["tool"],
                    "result": r.get("result"),
                    "error": r.get("error"),
                    "execution_ms": r.get("execution_ms"),
                }
                for r in final_state.results
            ],
        )
    
    except ValidationError as exc:
        logger.exception("Request validation failed")
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in process endpoint")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")


@router.post("/confirm")
async def confirm_action(req: ConfirmRequest) -> ProcessResponse:
    """
    Confirm or cancel a pending risky action.
    
    If confirmed, resumes agent execution from where it paused.
    If canceled, returns cancellation message.
    """
    try:
        logger.info(f"Confirmation request for user {req.user_id}: confirm={req.confirm}")
        
        session = _sessions.get(req.user_id)
        if not session or not session.get("confirmation_pending"):
            raise HTTPException(status_code=400, detail="No pending confirmation for this user")
        
        state = session["state"]
        
        if not req.confirm:
            # User denied
            state.confirmation_granted = False
            session["confirmation_pending"] = False
            
            return ProcessResponse(
                status="success",
                message="Action cancelled as requested",
                actions_taken=["Cancelled pending action"],
            )
        
        # User confirmed
        state.confirmation_granted = True
        session["confirmation_pending"] = False
        
        # Resume execution
        try:
            final_state = _graph.invoke(state)
        except Exception as exc:
            logger.exception("Execution after confirmation failed")
            raise HTTPException(
                status_code=500,
                detail=f"Execution failed: {str(exc)}"
            )
        
        session["state"] = final_state
        session["last_updated"] = datetime.now()
        
        # Log
        try:
            _memory_db.log_action(
                user_input=state.user_input,
                intent=state.plan.intent if state.plan else "unknown",
                result_summary=final_state.final_response or "Completed",
                user_id=req.user_id
            )
        except Exception as exc:
            logger.warning("Failed to log action: %s", exc)
        
        actions_taken = [f"Step {r['step']}: {r['tool']}" for r in final_state.results]
        
        return ProcessResponse(
            status="success",
            message=final_state.final_response or "Completed successfully",
            actions_taken=actions_taken,
            next_steps=[],
            results=[
                {
                    "step": r["step"],
                    "tool": r["tool"],
                    "result": r.get("result"),
                    "error": r.get("error"),
                    "execution_ms": r.get("execution_ms"),
                }
                for r in final_state.results
            ],
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in confirm endpoint")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")


@router.get("/history/{user_id}", response_model=HistoryResponse)
async def get_history(user_id: str, limit: int = 50) -> HistoryResponse:
    """
    Retrieve action history for a user.
    """
    try:
        logger.info(f"Retrieving history for user {user_id}, limit={limit}")
        
        actions = _memory_db.get_actions(user_id=user_id, limit=limit)
        
        items = [
            HistoryItem(
                id=a.get("id", 0),
                user_input=a.get("user_input", ""),
                intent=a.get("intent"),
                result_summary=a.get("result_summary"),
                created_at=a.get("created_at", ""),
            )
            for a in actions
        ]
        
        return HistoryResponse(
            status="success",
            user_id=user_id,
            total_items=len(items),
            items=items,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve history")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(exc)}")


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """
    Get system status and health.
    """
    try:
        services = {
            "agent": "ok",
            "memory": "ok",
            "mcp_server": "unknown",
        }
        
        # Check MCP server
        try:
            import requests
            settings = get_settings()
            resp = requests.get(f"{settings.tool_server_url}/health", timeout=2)
            if resp.status_code == 200:
                services["mcp_server"] = "ok"
        except Exception:
            pass
        
        return StatusResponse(
            status="ok",
            timestamp=datetime.now().isoformat(),
            services=services,
            version="1.0.0",
        )
    except Exception as exc:
        logger.exception("Status check failed")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(exc)}")


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)) -> TranscriptionResponse:
    """
    Transcribe audio file using Whisper.
    """
    try:
        logger.info(f"Transcribing file: {file.filename}")
        
        # Read file
        audio_data = await file.read()
        
        start_time = time.time()
        text = _transcribe_audio(audio_data)
        duration = (time.time() - start_time) * 1000
        
        return TranscriptionResponse(
            status="success",
            text=text,
            confidence=None,
            duration_ms=round(duration, 2),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(exc)}")
