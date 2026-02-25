# Nova Voice Assistant

Nova is a modular, production-oriented voice AI assistant designed for backend integration. It supports:

- Wake-word activation (`Hey Nova` via Porcupine custom keyword path)
- Continuous background listening pipeline
- Whisper STT + ElevenLabs TTS voice loop
- LangGraph state-machine orchestration
- MCP-style modular tool server (FastAPI)
- Persistent SQLite memory
- Proactive scheduled checks (APScheduler)
- Risk confirmation for sensitive actions
- Windows-friendly threaded runtime design

---

## Architecture

### Primary interaction pipeline

`Mic -> Wake Word -> Record (silence detection) -> STT -> LangGraph Agent -> MCP Tools -> TTS -> Speaker`

### Proactive pipeline

`Background Scheduler -> Agent -> Notification decision -> TTS`

### Concurrency model

- **Thread 1**: Wake-word listener
- **Thread 2**: APScheduler background jobs
- **Thread 3**: Agent processing loop

---

## Project structure

```text
nova/
├── agent/
│   ├── graph.py
│   ├── planner.py
│   ├── executor.py
│   ├── router.py
│   ├── responder.py
│   └── state.py
├── mcp_server/
│   ├── main.py
│   ├── gmail_tool.py
│   ├── calendar_tool.py
│   ├── sms_tool.py
│   ├── sentiment_tool.py
│   └── order_tool.py
├── memory/
│   └── db.py
├── scheduler/
│   └── jobs.py
├── voice/
│   ├── wakeword.py
│   ├── listen.py
│   └── speak.py
├── utils/
│   └── logger.py
├── config.py
└── main.py
```

---

## Prerequisites

- Python 3.10+
- PortAudio-compatible audio stack (for `pyaudio`)
- Optional API credentials for full integrations

Suggested packages (install per your environment):

- `fastapi`
- `uvicorn`
- `requests`
- `langgraph`
- `apscheduler`
- `python-dotenv`
- `pydantic`
- `groq`
- `openai`
- `pvporcupine`
- `pyaudio`
- `playsound`

> Note: Nova includes safe fallbacks when keys/dependencies are missing, but voice/tool features are limited until configured.

---

## Environment variables (`.env`)

Create a `.env` file in the repository root:

```env
# Core
LOG_LEVEL=INFO
TOOL_SERVER_URL=http://127.0.0.1:8000
SQLITE_PATH=nova.db
SCHEDULER_INTERVAL_MINUTES=5

# Groq planner
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant

# Wake word
PORCUPINE_ACCESS_KEY=
# Path to your custom "Hey Nova" .ppn keyword file
PORCUPINE_KEYWORD_PATH=

# STT (Whisper)
WHISPER_API_KEY=
WHISPER_MODEL=whisper-1

# TTS (ElevenLabs)
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL

# SMS (optional Twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# Gmail placeholders (adapter-ready)
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
```

---

## Quick start

### Option A (recommended): one command launcher

This starts:
1. MCP tool server on `127.0.0.1:8000`
2. Nova runtime loop

```bash
python quick_start.py
```

### Option B: run components separately

Terminal 1 (tool server):

```bash
uvicorn nova.mcp_server.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 (assistant runtime):

```bash
python main.py
```

---

## Behavior notes

- On startup, Nova announces readiness.
- Wake-word detection triggers recording mode.
- Recording auto-stops after sustained silence.
- Sensitive actions require verbal confirmation (`yes/no`).
- Proactive checks run every 5 minutes (configurable) and may trigger spoken alerts.
- Action summaries and memory are persisted in SQLite.

---

## Safety and validation

Nova includes:

- Tool allowlisting in planner
- Unknown tool rejection
- Retry handling for tool execution failures
- Prompt-injection-resistant planning prompt guidance
- Concise voice responses (max 3 sentences)
- Centralized logging (`logs/nova.log`)

---

## Logs and persistence

- Logs: `logs/nova.log`
- SQLite DB (default): `nova.db`

---

## Current integration status

The codebase is API-ready and modular. Some external services are intentionally adapter/stub-oriented until credentials and provider-specific wiring are completed.
