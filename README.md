# Nova AI Assistant Backend

Nova is a modular, production-ready AI assistant backend designed for website integration and standalone voice operation. It provides intelligent task orchestration, tool execution, and persistent memory.

## ✨ Features

- **Dual Interface**: REST API for web frontend + voice assistant for standalone use
- **Multi-Input**: Text, audio (Whisper STT), or voice input
- **Smart Planning**: Groq LLM-powered task planning and reasoning
- **Tool Ecosystem**: Gmail, Calendar, SMS, LinkedIn, Orders, Sentiment analysis
- **Semi-Automation**: Playwright for browser actions (LinkedIn posts, food orders) with human confirmation
- **Persistent Memory**: SQLite-based user preferences, contact history, and action audit logs
- **Risk Management**: Confirmation workflow for sensitive actions (emails, payments, publishing)
- **LangGraph Orchestration**: State-machine-based workflow with conditional routing
- **MCP Tool Server**: Modular tool architecture for easy extension

## 🚀 Quick Start

### REST API (for website frontend)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 3. Run
python run_api_server.py

# Server at http://localhost:8001
# Docs at http://localhost:8001/docs
```

**Test it:**
```bash
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user1",
    "input_type": "text",
    "content": "What is the sentiment of this excellent day?"
  }'
```

### Voice Assistant (standalone)

```bash
python quick_start.py
# Say "Hey Nova" to activate
```

### Dual Mode

Run both simultaneously:
```bash
# Terminal 1
python run_api_server.py

# Terminal 2
python quick_start.py
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete REST API reference |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Installation and configuration |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and internals |

## 🏗️ Architecture

```
Frontend (React/Web)
        ↓ HTTP
    REST API (FastAPI)
        ↓
    LangGraph Agent
    ├─ Planner (Groq LLM)
    ├─ Router (conditional logic)
    ├─ Executor (tool calls)
    └─ Responder (formatting)
        ↓
    MCP Tool Server
    ├─ Gmail (OAuth)
    ├─ Calendar (OAuth)
    ├─ SMS (Twilio)
    ├─ Orders (Playwright)
    ├─ LinkedIn (Playwright)
    └─ Sentiment (LLM)
        ↓
    Memory System (SQLite)
```

## 📋 REST API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/nova/process` | Process text/audio input |
| `POST` | `/nova/confirm` | Confirm risky actions |
| `GET` | `/nova/history/{user_id}` | Get action history |
| `GET` | `/nova/status` | System health check |
| `POST` | `/nova/transcribe` | Transcribe audio file |
| `GET` | `/docs` | Interactive API documentation |

## 🛠️ Available Tools

| Tool | Actions | Notes |
|------|---------|-------|
| **Gmail** | send_email, draft_email, read_unread_important | Google OAuth |
| **Calendar** | create_event, upcoming_events, delete_event | Google OAuth |
| **SMS** | send_sms | Twilio API |
| **Sentiment** | analyze_text | Groq LLM or rule-based |
| **Order** | place_order, prepare_order_sync | Playwright browser automation |
| **LinkedIn** | prepare_post_sync | Playwright browser automation |

## 💾 Memory System

Nova automatically stores per-user:
- Frequent contacts (emails, phone numbers)
- Food preferences
- Tone preferences (professional, casual, etc.)
- Complete action history
- Usage patterns

This memory influences planning and personalization.

## 🔒 Security

- **Allowlist-based**: Only predefined tools execute
- **Prompt injection prevention**: Tool names validated
- **Risk classification**: Low/medium/high confirmation required
- **Human-in-the-loop**: Risky actions need confirmation
- **Credential management**: Environment variables, OAuth tokens with refresh
- **Audit logging**: All actions logged to SQLite

## 🎯 Request Flow Example

```
1. Frontend sends: POST /nova/process
   {
     "user_id": "alice",
     "input_type": "text",
     "content": "Send email to bob@work.com saying I'm running late"
   }

2. API receives request
   └─ Transcribes audio if needed
   └─ Loads user memory
   └─ Creates agent state

3. Agent executes
   └─ Planner: Groq LLM creates plan
   └─ Router: Detects HIGH risk (email sending)
   └─ Confirm node: Paused, waiting for user approval

4. API returns:
   {
     "status": "confirmation_required",
     "message": "This action needs your approval",
     "proposed_action": {...}
   }

5. Frontend shows dialog, user clicks YES

6. Frontend sends: POST /nova/confirm
   {
     "user_id": "alice",
     "confirm": true
   }

7. Agent resumes & executes
   └─ Executor: Calls gmail.send_email tool
   └─ Tool server processes request
   └─ Result stored in state
   └─ Responder: Formats response

8. API returns:
   {
     "status": "success",
     "message": "Email sent to bob@work.com",
     "actions_taken": ["Step 0: gmail.send_email"]
     "results": [...]
   }
```

## 🔧 Configuration

### Minimal (.env)
```env
GROQ_API_KEY=sk_your_key
```

### Full (.env)
See [.env.example](.env.example) for complete template

Get credentials:
- **Groq**: https://console.groq.com (free)
- **Gmail/Calendar**: Google Cloud Console OAuth
- **Twilio**: https://www.twilio.com (optional)

## 📦 Project Structure

```
nova/
├── api/              # REST API layer
│   ├── app.py
│   ├── routes.py
│   └── schemas.py
├── agent/            # LangGraph orchestration
│   ├── graph.py
│   ├── planner.py
│   ├── executor.py
│   ├── router.py
│   ├── responder.py
│   └── state.py
├── mcp_server/       # Tool implementations
│   ├── main.py
│   ├── gmail_tool.py
│   ├── calendar_tool.py
│   ├── linkedin_tool.py
│   ├── order_tool.py
│   ├── sentiment_tool.py
│   └── sms_tool.py
├── automation/       # Browser automation
│   └── playwright_engine.py
├── memory/           # Persistent storage
│   └── db.py
├── voice/            # Voice I/O (optional)
│   ├── listen.py
│   ├── speak.py
│   └── wakeword.py
└── utils/
    └── logger.py

run_api_server.py     # Start REST API
quick_start.py        # Start voice mode
```

## 🚦 Risk Levels

- **Low**: Information retrieval (reading emails, checking calendar)
- **Medium**: Calendar creation, scheduling
- **High**: Email sending, SMS, order placement, social media publishing

High-risk actions trigger confirmation workflow.

## 📊 Monitoring

```bash
# Check server status
curl http://localhost:8001/nova/status

# View API documentation
open http://localhost:8001/docs

# Check logs
tail -f nova.log

# View user history
curl http://localhost:8001/nova/history/user123?limit=20
```

## 🧪 Testing

```bash
# Text input
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "input_type": "text",
    "content": "What time is my next meeting?"
  }'

# Audio transcription
curl -F "file=@audio.wav" \
  http://localhost:8001/nova/transcribe

# System status
curl http://localhost:8001/nova/status
```

## 🔌 Extending Nova

**Add a new tool:**

1. Create `nova/mcp_server/my_tool.py`:
```python
class MyTool:
    def my_action(self, param: str) -> Dict[str, Any]:
        return {"status": "success", "result": "..."}
```

2. Register in `nova/mcp_server/main.py`:
```python
TOOLS = {
    "my_tool": MyTool(),
    ...
}
```

3. Add to allowlist in `nova/agent/planner.py`:
```python
ALLOWED_TOOLS.add("my_tool.my_action")
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for more details.

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not found` | Check .env file in project root |
| `Playwright not installed` | `pip install playwright && playwright install chromium` |
| `Gmail not working` | Verify OAuth tokens in .env, see SETUP_GUIDE.md |
| `Database locked` | Ensure only one process accessing nova.db |

## 📝 Environment Variables

```env
# Required
GROQ_API_KEY=sk_...

# Optional (for tools)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...

# Optional (voice mode)
PORCUPINE_ACCESS_KEY=...
ELEVENLABS_API_KEY=...

# Configuration
LOG_LEVEL=INFO
SQLITE_PATH=nova.db
TOOL_SERVER_URL=http://127.0.0.1:8000
```

See [.env.example](.env.example) for complete template.

## 📄 License

This project is provided as-is for backend integration.

## 🤝 Support

- **API Docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Setup Help**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Interactive Docs**: http://localhost:8001/docs (when running)

## 🎓 Key Concepts

- **LangGraph**: State machine for agent workflow
- **MCP Tools**: Modular tool ecosystem
- **Groq LLM**: Free reasoning and planning
- **Playwright**: Semi-automated browser actions
- **Confirmation Flow**: Human-in-the-loop for risky actions
- **Memory System**: Per-user persistent preferences and history

---

**Ready to integrate?** Start with [SETUP_GUIDE.md](SETUP_GUIDE.md) and check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint reference.
