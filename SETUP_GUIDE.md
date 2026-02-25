# Nova Setup Guide

## Quick Start (5 minutes)

### Installation

```bash
# 1. Clone/navigate to project
cd Nova_Voice_Agent

# 2. Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers (for automation features)
playwright install chromium

# 5. Create .env file
cp .env.example .env  # or create manually
```

### .env Configuration - Minimal Setup

Create `.env` file in project root:

```env
# Required for LLM
GROQ_API_KEY=sk_your_key_here

# Logging (optional)
LOG_LEVEL=INFO

# Database (optional - will use default)
SQLITE_PATH=nova.db
```

Get Groq API key (free):
1. Go to https://console.groq.com
2. Sign up (free tier)
3. Copy API key
4. Paste into `.env`

### Run API Server

```bash
# Terminal 1 - Run the API server
python run_api_server.py

# Server will start at http://localhost:8001
# Documentation at http://localhost:8001/docs
```

### Test the API

Open another terminal:

```bash
# Test text input
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_type": "text",
    "content": "What is the sentiment of this great day?"
  }'

# Test system status
curl http://localhost:8001/nova/status
```

Expected response:
```json
{
  "status": "success",
  "message": "Completed intent sentiment_analysis...",
  "actions_taken": ["Step 0: sentiment.analyze_text"],
  "results": [...]
}
```

---

## Full Setup (with Email & Calendar)

### 1. Google OAuth Setup

For Gmail and Calendar integration:

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project (name: "Nova")
3. Enable APIs:
   - Gmail API
   - Google Calendar API
4. Create OAuth 2.0 Desktop Application:
   - Go to "Credentials"
   - "Create Credentials" → "OAuth Client ID"
   - Application type: "Desktop Application"
   - Download JSON file

#### Step 2: Get Refresh Token

Run once to authorize:

```python
from Google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Use the downloaded JSON file
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/calendar']
)

creds = flow.run_local_server(port=0)
print("Refresh token:", creds.refresh_token)
```

#### Step 3: Update .env

```env
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
```

### 2. SMS Setup (Twilio)

For SMS sending:

1. Sign up at https://www.twilio.com
2. Get Account SID and Auth Token
3. Add phone number or verify recipient numbers
4. Update `.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1234567890
```

### 3. Playwright Browser Automation

For LinkedIn and Order automation:

```bash
# Install browsers
playwright install chromium

# Test installation
python -c "
import asyncio
from nova.automation.playwright_engine import PlaywrightEngine

async def test():
    engine = PlaywrightEngine(headless=True)
    await engine.init()
    print('Playwright OK')
    await engine.close()

asyncio.run(test())
"
```

### Complete .env Example

```env
# Core
LOG_LEVEL=INFO
APP_NAME=Nova

# LLM (Required)
GROQ_API_KEY=sk_xxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant

# Gmail (Optional)
GMAIL_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxxxxxxxxxx
GMAIL_REFRESH_TOKEN=xxxxxxxxxxxx

# Calendar (Optional - uses same OAuth as Gmail)
# Uses GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN

# SMS (Optional)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1234567890

# Database
SQLITE_PATH=nova.db

# Server
TOOL_SERVER_URL=http://127.0.0.1:8000

# Voice (only needed for voice mode)
LOG_LEVEL=INFO
```

---

## Running Different Modes

### API-Only Mode (for website integration)

```bash
# Just the REST API server
python run_api_server.py

# Access at http://localhost:8001
# Docs at http://localhost:8001/docs
```

### Voice-Only Mode (standalone assistant)

```bash
# Just voice interaction
python quick_start.py
```

Requires:
- Microphone
- Speaker
- Porcupine wake word API key (optional)
- ElevenLabs TTS API key (optional)

### Dual Mode (API + Voice)

```bash
# Terminal 1
python run_api_server.py

# Terminal 2 (different terminal)
python quick_start.py
```

Both systems share the same memory and tool infrastructure.

---

## Testing Endpoints

### Using curl

```bash
# Test sentiment analysis
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "input_type": "text",
    "content": "I am very happy with this great service!"
  }'

# Get system status
curl http://localhost:8001/nova/status

# Get user history
curl http://localhost:8001/nova/history/test?limit=10
```

### Using Python

```python
import requests
import json

# Initialize API
BASE_URL = "http://localhost:8001"

# Process text input
response = requests.post(
    f"{BASE_URL}/nova/process",
    json={
        "user_id": "user1",
        "input_type": "text",
        "content": "Create calendar event tomorrow at 10 AM"
    }
)

result = response.json()
print(json.dumps(result, indent=2))

# If confirmation required
if result['status'] == 'confirmation_required':
    confirm_response = requests.post(
        f"{BASE_URL}/nova/confirm",
        json={
            "user_id": "user1",
            "confirm": True
        }
    )
    print(json.dumps(confirm_response.json(), indent=2))
```

### Using JavaScript (Frontend Example)

```javascript
async function callNova(userId, content) {
  const response = await fetch('http://localhost:8001/nova/process', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      input_type: 'text',
      content: content
    })
  });

  const data = await response.json();
  
  if (data.status === 'confirmation_required') {
    const confirmed = confirm(data.message);
    
    if (confirmed) {
      const confirmResponse = await fetch(
        'http://localhost:8001/nova/confirm',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            confirm: true
          })
        }
      );
      
      return await confirmResponse.json();
    }
  }
  
  return data;
}

// Use it
callNova('user123', 'Send email to alice@example.com')
  .then(result => console.log(result));
```

---

## Troubleshooting

### Groq API Issues

```
Error: GROQ_API_KEY not found
```

**Solution:** Check `.env` file exists in project root and contains valid key

```bash
# Check if .env is found
python -c "from nova.config import get_settings; print(get_settings().groq_api_key[:10] + '***')"
```

### Whisper Not Available

```
Error: faster_whisper not installed
```

**Solution:** Install audio processing:
```bash
pip install faster-whisper
```

### Playwright Automation Not Working

```
Error: Playwright not installed
```

**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Gmail Connection Issues

```
Error: Failed to initialize Gmail service
```

**Solution:** Verify Google OAuth credentials:
```bash
python -c "
from nova.mcp_server.gmail_tool import GmailTool
tool = GmailTool()
print('Gmail service:', 'OK' if tool.service else 'FAILED')
"
```

### Database Lock

```
Error: database is locked
```

**Solution:** Ensure only one process is accessing `nova.db`:
```bash
# Check if another process is running
ps aux | grep nova

# Remove/reset database if corrupted
rm nova.db
```

---

## Development Setup

### Install Dev Dependencies

```bash
# Additional testing tools
pip install pytest pytest-asyncio black flake8 mypy

# Code formatting
black nova/

# Type checking
mypy nova/

# Linting
flake8 nova/
```

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Specific test file
pytest tests/test_agent.py

# With coverage
pytest --cov=nova
```

### File Structure Quick Reference

```
Nova_Voice_Agent/
├── nova/
│   ├── api/              ← FastAPI REST endpoints
│   │   ├── app.py       ← FastAPI app factory
│   │   ├── routes.py    ← Endpoints implementation
│   │   └── schemas.py   ← Request/response models
│   │
│   ├── agent/           ← LangGraph orchestration
│   │   ├── graph.py     ← Workflow definition
│   │   ├── planner.py   ← Plan generation
│   │   ├── executor.py  ← Step execution
│   │   ├── router.py    ← Routing logic
│   │   ├── responder.py ← Response generation
│   │   └── state.py     ← State definition
│   │
│   ├── mcp_server/      ← Tool implementations
│   │   ├── main.py      ← Tool server
│   │   ├── gmail_tool.py
│   │   ├── calendar_tool.py
│   │   ├── linkedin_tool.py
│   │   ├── order_tool.py
│   │   ├── sentiment_tool.py
│   │   └── sms_tool.py
│   │
│   ├── automation/      ← Browser automation
│   │   └── playwright_engine.py
│   │
│   ├── memory/          ← Persistent memory
│   │   └── db.py
│   │
│   ├── voice/           ← Voice I/O (optional)
│   │   ├── listen.py
│   │   ├── speak.py
│   │   └── wakeword.py
│   │
│   └── utils/
│       └── logger.py
│
├── run_api_server.py         ← Start API server
├── quick_start.py            ← Start voice mode
├── requirements.txt          ← Dependencies
├── .env                       ← Configuration
├── API_DOCUMENTATION.md      ← API reference
├── ARCHITECTURE.md           ← System design
└── SETUP_GUIDE.md           ← This file
```

---

## Monitoring & Debugging

### Enable Debug Logging

Update `.env`:
```env
LOG_LEVEL=DEBUG
```

### Check Logs

```bash
# Windows
Get-Content nova.log -Tail 50

# Mac/Linux
tail -f nova.log
```

### API Monitoring

```bash
# Check server status
curl http://localhost:8001/health

# View API documentation
open http://localhost:8001/docs

# Test endpoint directly
curl http://localhost:8001/nova/status | python -m json.tool
```

### Memory Database Inspection

```bash
# Access SQLite directly
sqlite3 nova.db "SELECT * FROM actions LIMIT 10;"

# View schema
sqlite3 nova.db ".schema"
```

---

## Next Steps

1. **Test Basic Flow**: Send text request via `/nova/process`
2. **Add Credentials**: Set up Google OAuth or Twilio as needed
3. **Try Different Tools**: Test Gmail, Calendar, Sentiment
4. **Integrate with Frontend**: Connect React/Next.js app to API
5. **Set Memory**:  User actions are automatically logged
6. **Monitor Performance**: Check logs and API docs
7. **Customize**: Extend with new tools (see ARCHITECTURE.md)

---

## Getting Help

- **API Reference**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Code Logs**: Check `nova.log` or terminal output
- **Groq Docs**: https://console.groq.com/docs
- **LangGraph**: https://python.langchain.com/docs/langgraph/

---

## Production Checklist

Before deploying to production:

- [ ] Set `LOG_LEVEL=WARNING` in `.env`
- [ ] Use proper secrets management (not .env file)
- [ ] Enable HTTPS (reverse proxy like nginx)
- [ ] Add database backups (SQLite replication)
- [ ] Implement authentication (JWT/OAuth)
- [ ] Add rate limiting
- [ ] Monitor API performance
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure CORS for specific domains
- [ ] Enable database encryption
- [ ] Regular security audits

---

## Contributing

To add features:
1. Create feature branch
2. Follow code style (black formatting)
3. Add tests
4. Update documentation
5. Submit pull request

See [ARCHITECTURE.md](ARCHITECTURE.md) for extension points.
