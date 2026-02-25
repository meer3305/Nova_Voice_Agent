# Nova REST API Documentation

## Overview

Nova is a modular AI assistant backend service designed for website integration. It provides REST API endpoints for frontend applications to submit user requests and receive orchestrated AI responses.

## Base URL

```
http://localhost:8001
```

## API Endpoints

### 1. Process User Input

Process text or audio input from frontend.

**Endpoint:** `POST /nova/process`

**Request Body:**
```json
{
    "user_id": "user123",
    "input_type": "text|audio",
    "content": "user input or base64-encoded audio",
    "context": {
        "optional_memory_context": {}
    }
}
```

**Parameters:**
- `user_id` (string, required): Unique user identifier
- `input_type` (string, required): Either "text" or "audio"
- `content` (string, required):
  - For text: Raw text input
  - For audio: Base64-encoded audio data
- `context` (object, optional): Additional memory context

**Response (Success):**
```json
{
    "status": "success",
    "message": "Completed intent...",
    "actions_taken": [
        "Step 0: gmail.send_email",
        "Step 1: calendar.create_event"
    ],
    "next_steps": ["Continue with next task if needed"],
    "results": [
        {
            "step": 0,
            "tool": "gmail.send_email",
            "result": {
                "status": "sent",
                "to": "user@example.com",
                "message_id": "abc123"
            },
            "error": null,
            "execution_ms": 250.5
        }
    ]
}
```

**Response (Confirmation Required):**
```json
{
    "status": "confirmation_required",
    "message": "This action includes sensitive operations and requires your confirmation.",
    "proposed_action": {
        "intent": "send_email_and_schedule",
        "risk_level": "high",
        "description": "Will send email to manager@company.com"
    },
    "requires_user_approval": true
}
```

**Response (Error):**
```json
{
    "status": "error",
    "message": "Failed to process request",
    "error_code": "PROCESSING_ERROR",
    "details": {
        "reason": "Detailed error information"
    }
}
```

---

### 2. Confirm Action

Confirm or deny a risky action.

**Endpoint:** `POST /nova/confirm`

**Request Body:**
```json
{
    "user_id": "user123",
    "confirm": true
}
```

**Parameters:**
- `user_id` (string, required): Must match the user from `/process`
- `confirm` (boolean, required): `true` to confirm, `false` to cancel

**Response:**
```json
{
    "status": "success",
    "message": "Action confirmed and completed",
    "actions_taken": ["Executed final steps"],
    "next_steps": [],
    "results": [...]
}
```

---

### 3. Get User History

Retrieve action history for a user.

**Endpoint:** `GET /nova/history/{user_id}`

**Query Parameters:**
- `limit` (integer, optional, default: 50, max: 500): Number of records to retrieve

**Response:**
```json
{
    "status": "success",
    "user_id": "user123",
    "total_items": 5,
    "items": [
        {
            "id": 5,
            "user_input": "Send email to manager",
            "intent": "send_email",
            "result_summary": "Email sent successfully",
            "created_at": "2025-02-26T15:30:45.123456"
        },
        {
            "id": 4,
            "user_input": "Schedule meeting for tomorrow",
            "intent": "schedule_meeting",
            "result_summary": "Event created",
            "created_at": "2025-02-26T14:15:22.654321"
        }
    ]
}
```

---

### 4. Get System Status

Check system health and service status.

**Endpoint:** `GET /nova/status`

**Response:**
```json
{
    "status": "ok",
    "timestamp": "2025-02-26T16:00:00.000000",
    "services": {
        "agent": "ok",
        "memory": "ok",
        "mcp_server": "ok"
    },
    "version": "1.0.0"
}
```

---

### 5. Transcribe Audio

Transcribe audio file using local Whisper.

**Endpoint:** `POST /nova/transcribe`

**Request:**
- Content-Type: `multipart/form-data`
- File field: `file` (audio file - WAV, MP3, M4A, etc.)

**Response:**
```json
{
    "status": "success",
    "text": "Transcribed text from audio",
    "confidence": 0.95,
    "duration_ms": 1250.5
}
```

---

## Available Tools

### Gmail (`gmail`)
- `send_email` - Send email
- `draft_email` - Create email draft
- `read_unread_important` - Read unread important emails

### Calendar (`calendar`)
- `create_event` - Create calendar event
- `upcoming_events` - Get upcoming events
- `delete_event` - Delete calendar event

### SMS (`sms`)
- `send_sms` - Send SMS message

### Sentiment (`sentiment`)
- `analyze_text` - Analyze text sentiment and recommend tone

### Order (`order`)
- `place_order` - Place online food order (API)
- `prepare_order_sync` - Prepare order with browser automation (semi-automated)

### LinkedIn (`linkedin`)
- `prepare_post_sync` - Prepare LinkedIn post (semi-automated, stops before publish)

---

## Input Examples

### Text Example
```json
{
    "user_id": "user123",
    "input_type": "text",
    "content": "Send an email to manager@company.com saying I'll be late to the meeting tomorrow"
}
```

### Audio Example
```json
{
    "user_id": "user123",
    "input_type": "audio",
    "content": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAAA="
}
```

(Audio should be base64-encoded WAV or MP3)

---

## Risk Levels

Nova classifies actions by risk:

- **low**: Information retrieval, read operations, sentiment analysis
- **medium**: Calendar creation, simple automations
- **high**: Email sending, SMS sending, order placement, social media publishing

High-risk actions return `status: "confirmation_required"` and require user approval via `/nova/confirm`.

---

## Error Codes

| Code | Description |
|------|-------------|
| `PROCESSING_ERROR` | Failed to process user request |
| `VALIDATION_ERROR` | Invalid request parameters |
| `TOOL_EXECUTION_ERROR` | Tool execution failed |
| `CONFIRMATION_ERROR` | Confirmation handling failed |
| `MEMORY_ERROR` | Memory database error |
| `UNKNOWN_ERROR` | Unexpected error |

---

## Memory System

Nova maintains persistent per-user memory:

- **Frequent Contacts**: Most-used email addresses and phone numbers
- **Food Preferences**: Saved food choices
- **Tone Preference**: Communication style preference
- **Action History**: Past actions and outcomes
- **Time Patterns**: Usage patterns by time of day

Memory influences planning and response generation.

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Core
LOG_LEVEL=INFO

# LLM
GROQ_API_KEY=sk_xxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant

# Gmail
GMAIL_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxxxxxxxxxxx
GMAIL_REFRESH_TOKEN=xxxxxxxxxxxxx

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1xxxxxxxxxx

# Database
SQLITE_PATH=nova.db

# Tool Server
TOOL_SERVER_URL=http://127.0.0.1:8000
```

---

## Running the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python -m uvicorn nova.api.app:app --host 0.0.0.0 --port 8001

# Or using the standalone script
python run_api_server.py
```

---

## Running the Voice Server

```bash
# Run voice-based Nova (separate process)
python quick_start.py
```

Both servers can run simultaneously on different ports.

---

## Frontend Integration Example

```javascript
// JavaScript fetch example
async function processWithNova(userId, inputText) {
    const response = await fetch('http://localhost:8001/nova/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            input_type: 'text',
            content: inputText
        })
    });
    
    const result = await response.json();
    
    if (result.status === 'confirmation_required') {
        // Show confirmation dialog to user
        const confirmed = await showConfirmDialog(result.proposed_action);
        
        if (confirmed) {
            // Send confirmation
            const confirmResponse = await fetch('http://localhost:8001/nova/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    confirm: true
                })
            });
            
            return await confirmResponse.json();
        }
    }
    
    return result;
}
```

---

## Security Considerations

1. **API Keys**: Store all credentials in environment variables, never in code
2. **Prompt Injection**: Nova validates all tool names against an allowlist
3. **Rate Limiting**: Consider adding rate limiting in production
4. **CORS**: Update CORS settings for production domains
5. **Authentication**: Add OAuth/JWT authentication for production
6. **HTTPS**: Use HTTPS in production

---

## Support

For issues or questions, refer to the main README.md or check logs:

```bash
tail -f nova.log
```
