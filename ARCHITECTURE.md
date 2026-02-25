# Nova Architecture

## System Overview

Nova is a modular AI assistant backend designed for integration into websites. It provides two primary interfaces:

1. **REST API** (`nova/api/`) - For frontend web integration
2. **Voice Assistant** (`nova/main.py`) - For standalone voice-based operation

Both share the same underlying agent orchestration and tool ecosystem.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React/JS)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                    HTTP (REST API)
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  nova/api/routes.py (FastAPI)                    │
│  ┌─────────────┬──────────────┬─────────┬──────────────────┐    │
│  │ /process    │ /confirm     │ /status │ /history/{uid}   │    │
│  └──────┬──────┴──────┬───────┴────┬────┴──────────────────┘    │
└─────────┼──────────────┼────────────┼──────────────────────────┘
          │              │            │
          ▼              ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent Engine                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Planner → Router → Executor → Responder               │   │
│  │  (create_plan) (conditional) (execute_steps) (format)  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬──────────┬──────────────┬──────────────────────────────┘
          │          │              │
          ▼          ▼              ▼
    Machine Learning    Tool Execution   Memory System
    (Groq LLM)         (MCP Server)      (SQLite)
         │                  │                 │
    ┌────▼──────────┐  ┌────▼────────────┐  ▼
    │• Reasoning    │  │• Gmail          │  Persistent
    │• Planning     │  │• Calendar       │  Storage:
    │• Tone         │  │• SMS            │  • Contacts
    │  Adjustment   │  │• Sentiment      │  • Preferences
    │• Risk Assess  │  │• Order (Auto)   │  • History
    │               │  │• LinkedIn (Auto)│  • Patterns
    └────────────────┘  └─────────────────┘
```

---

## Core Components

### 1. API Layer (`nova/api/`)

**Files:**
- `app.py` - FastAPI application factory
- `routes.py` - API endpoints
- `schemas.py` - Request/response data models

**Responsibilities:**
- Accept text/audio input from frontend
- Manage user sessions and confirmation flows
- Coordinate with agent and memory systems
- Return structured JSON responses

**Key Endpoints:**
- `POST /nova/process` - Main request handler
- `POST /nova/confirm` - Risk action confirmation
- `GET /nova/history/{user_id}` - User action history
- `GET /nova/status` - System health check
- `POST /nova/transcribe` - Audio-to-text (Whisper)

---

### 2. Agent Orchestration (`nova/agent/`)

**LangGraph State Machine:**

```
START
  ↓
[Plan] ← User input + memory context
  ↓
[Router: needs_confirmation?]
  ├─ Yes → [Confirm] → [Router: confirmation_granted?]
  │        ├─ Yes → [Execute]
  │        └─ No  → [Respond] → END
  └─ No  → [Execute]
            ↓
          [Router: has_more_steps?]
            ├─ Yes → [Execute] (loop)
            └─ No  → [Respond] → END
```

**Files:**
- `state.py` - Agent state definition
- `graph.py` - LangGraph workflow definition
- `planner.py` - Create structured execution plan
- `router.py` - Conditional routing logic
- `executor.py` - Execute individual steps
- `responder.py` - Generate final response

**State Structure:**
```python
@dataclass
class AgentState:
    user_input: str              # Original user request
    plan: Optional[Plan]          # Structured plan with steps
    current_step: int             # Current execution position
    results: List[Dict]           # Step execution results
    memory_context: Dict          # User memory & preferences
    requires_confirmation: bool   # Risk level threshold
    confirmation_granted: Optional[bool]  # User approval status
    final_response: str           # Human-readable output
    error: Optional[str]          # Error message if failed
```

---

### 3. Tool Execution (`nova/mcp_server/`)

**MCP Server Pattern:**
Each tool is a standalone executor with a consistent interface:

```
┌─────────────────────────────────┐
│ FastAPI MCP Server (port 8000)  │
├─────────────────────────────────┤
│ POST /tools/execute             │
│ {                               │
│   "tool": "gmail",              │
│   "action": "send_email",       │
│   "args": {...}                 │
│ }                               │
└────────┬────────────────────────┘
         │
    ┌────▼────────────────┐
    │ Tool Router         │
    └────┬─────┬──────┬──────┬──────┬─────────┘
         │     │      │      │      │
    ┌────▼──┐┌──▼──┐┌─▼───┐┌──▼──┐┌─▼────────┐
    │ Gmail ││SMS  ││Sent││Order││LinkedIn │
    │ Tool  ││Tool ││Tool││Tool ││ Tool    │
    └───────┘└─────┘└────┘└─────┘└─────────┘
```

**Available Tools:**

| Tool | Actions | Auth | Note |
|------|---------|------|------|
| Gmail | send_email, draft_email, read_unread_important | OAuth | Google API |
| Calendar | create_event, upcoming_events, delete_event | OAuth | Google API |
| SMS | send_sms | API Key | Twilio |
| Sentiment | analyze_text | LLM | Groq or rule-based |
| Order | place_order, prepare_order_sync | Playwright | Semi-automated checkout |
| LinkedIn | prepare_post_sync | Playwright | Semi-automated post |

**Tool Pattern:**
- All tools inherit from a base interface
- Async tools support Playwright browser automation
- Sync wrappers for FastAPI endpoints
- Fallback to simulated responses if credentials missing

---

### 4. Browser Automation (`nova/automation/`)

**PlaywrightEngine:**

For sensitive actions like LinkedIn posting or online ordering, Nova uses Playwright to:

1. **Open the website** in headless browser
2. **Fill in forms** with AI-generated content
3. **Navigate through workflows** (login, search, add to cart)
4. **Stop before completion** (before publish/payment)
5. **Return status** to user for final approval

**Why Semi-Automated?**
- Avoids accidental publication without user review
- Solves CAPTCHA and 2FA with manual user intervention
- Provides transparency for high-risk actions
- Complies with platform TOS by preventing automated final submission

---

### 5. Memory System (`nova/memory/`)

**SQLite Backend:**

```
SCHEMA:
┌─────────────┐     ┌──────────────┐
│  memories   │     │   actions    │
├─────────────┤     ├──────────────┤
│ id (PK)     │     │ id (PK)      │
│ category    │     │ user_id      │
│ key         │     │ user_input   │
│ value (JSON)│     │ intent       │
│ updated_at  │     │ result_sum   │
└─────────────┘     │ created_at   │
                    └──────────────┘
```

**Memory Categories:**
- `frequent_contacts` - Email/phone patterns
- `preferences.food_preferences` - Food choices
- `preferences.tone_preference` - Communication style
- `time_patterns` - Usage by time of day
- `actions` - Complete action history per user

**Memory Usage:**
1. **Planner** uses memory context to refine plans
2. **Tools** read preferences for personalization
3. **Logger** records all actions for future context
4. **Router** influences confirmation thresholds

---

### 6. Speech Processing (`nova/voice/`)

Only in voice-based mode; REST API users provide:
- Text directly or
- Base64-encoded audio for transcription

**Transcription Path:**
```
Audio Input (Frontend)
    ↓
Base64 Encode
    ↓
POST /nova/transcribe
    ↓
Whisper (CPU) ← faster-whisper library
    ↓
Transcribed Text
    ↓
POST /nova/process (with text)
```

**TTS Response:**
Optional - Nova returns response text. Frontend handles conversion to speech using Web Speech API or external TTS.

---

## Data Flow

### Typical Request Flow

```
1. User Input
   ├─ Frontend sends: POST /nova/process
   ├─ Body: { user_id, input_type, content }
   │
2. Entry Point (routes.py)
   ├─ Transcribe audio if needed (Whisper)
   ├─ Load user memory context
   ├─ Create AgentState
   │
3. Agent Execution
   ├─ Planner (routes.py → graph.invoke)
   │  └─ Groq LLM creates structured plan
   │
   ├─ Router: Check risk level
   │  ├─ High risk? → Confirm node
   │  └─ Return confirmation_required status
   │
   ├─ Wait for confirmation (POST /nova/confirm)
   │
   ├─ Executor (for each step):
   │  ├─ Call MCP tool server
   │  ├─ GET /tools/execute
   │  ├─ Tool executes (Gmail, Calendar, etc.)
   │  ├─ Result stored in state
   │
   ├─ Router: More steps?
   │  ├─ Yes → Executor again
   │  └─ No → Responder
   │
   ├─ Responder
   │  └─ Format response text
   │
4. Memory Update
   ├─ Log action to SQLite
   ├─ Update preferences
   │
5. Return Response
   └─ JSON with status, message, results
```

---

## Request/Response Examples

### Simple Text Request
```
→ POST /nova/process
{
  "user_id": "alice",
  "input_type": "text",
  "content": "Send email to bob@work.com saying I'm running late"
}

← 200 OK
{
  "status": "confirmation_required",
  "message": "This action includes email sending and needs your approval.",
  "proposed_action": {
    "intent": "send_email",
    "risk_level": "high"
  }
}

→ POST /nova/confirm
{
  "user_id": "alice",
  "confirm": true
}

← 200 OK
{
  "status": "success",
  "message": "Email sent to bob@work.com",
  "actions_taken": ["Step 0: gmail.send_email"],
  "results": [...]
}
```

---

## Security Architecture

### Input Validation
- **Tool Allowlist**: Only predefined tools can execute
- **Parameter Validation**: Pydantic schemas enforce types
- **Prompt Injection Prevention**: Tool names validated against whitelist

### Credential Management
- **Environment Variables**: All API keys stored in `.env`
- **OAuth Tokens**: Cached locally (token.pickle) with auto-refresh
- **No Secrets in Logs**: Credentials sanitized before logging

### Risk Management
- **Risk Level Classification**: low/medium/high
- **Confirmation Workflow**: Human-in-the-loop for risky actions
- **Semi-Automation**: Playwright stops before final submission
- **Action Logging**: All executed actions tracked for audit

---

## Performance Considerations

### Bottlenecks
1. **Groq LLM** - Network latency (~500ms-2s)
2. **Whisper Transcription** - CPU-bound (~5-30s depending on audio length)
3. **Playwright Automation** - Network + browser (~10-30s)
4. **Tool Execution** - Depends on external APIs

### Optimization Strategies
- **Caching**: Memory system caches preferences
- **Parallelization**: Independent tools could run in parallel
- **Timeouts**: All API calls have reasonable timeouts
- **Fallbacks**: Simulated responses when integrations unavailable

---

## Extension Points

### Adding New Tools

1. Create tool class in `nova/mcp_server/new_tool.py`:
```python
class NewTool:
    def action_name(self, param1: str) -> Dict[str, Any]:
        # Implementation
        return {"status": "success", ...}
```

2. Register in `nova/mcp_server/main.py`:
```python
TOOLS = {
    "new_tool": NewTool(),
    ...
}
```

3. Add to planner allowlist (`nova/agent/planner.py`):
```python
ALLOWED_TOOLS.add("new_tool.action_name")
```

4. Mark as risky if needed (`nova/agent/state.py`):
```python
RISKY_TOOLS.add("new_tool.action_name")
```

### Custom Memory Fields

Update `nova/api/routes.py` `_get_memory_context()`:
```python
def _get_memory_context(user_id: str) -> Dict[str, Any]:
    context = {}
    # Add new memory category
    preferences = _memory_db.get_memory("preferences", "custom_preference")
    if preferences:
        context["custom_preference"] = preferences.value
    return context
```

---

## Testing Architecture

### Unit Testing
- Individual tool classes
- State transitions
- Memory operations

### Integration Testing
- Full request/response flow
- Tool execution chains
- Memory persistence

### E2E Testing
- Frontend → API → Agent → Tools → Memory

---

## Deployment & Operations

### Single Process
Run API server:
```bash
python run_api_server.py
```

### Dual Process
Run API (port 8001) + Voice (separate process):
```bash
python run_api_server.py &
python quick_start.py
```

### Monitoring
- Check logs: `tail -f nova.log`
- Health check: `GET /nova/status`
- Memory stats: `GET /nova/history/{user_id}`

---

## Configuration

All configuration through `nova/config.py`:

```python
@dataclass(frozen=True)
class Settings:
    # LLM
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    
    # Tools
    gmail_client_id: str
    gmail_client_secret: str
    gmail_refresh_token: str
    
    # Database
    sqlite_path: str = "nova.db"
    
    # Server
    tool_server_url: str = "http://127.0.0.1:8000"
```

Load from `.env` file via `python-dotenv`.

---

## Future Enhancements

1. **Vector Database** - Semantic memory search
2. **Function Calling** - LLM function calling instead of planner
3. **Multi-Agent Orchestration** - Specialized sub-agents
4. **Knowledge Base** - Document ingestion & RAG
5. **Analytics Dashboard** - Usage patterns & insights
6. **Rate Limiting & Quotas** - Per-user limits
7. **Streaming Responses** - Real-time response streaming
8. **Tool Chaining** - Complex multi-tool workflows
