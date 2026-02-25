# Nova Quick Reference

## 🚀 Start Here

### 1. Get Your Groq API Key (FREE)
https://console.groq.com → Create account → Copy API key

### 2. Create `.env`
```env
GROQ_API_KEY=sk_your_key_here
```

### 3. Run Nova API
```bash
pip install -r requirements.txt
python run_api_server.py
```

### 4. Test It
```bash
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "input_type": "text",
    "content": "What is the sentiment of this great day?"
  }'
```

---

## 📚 Documentation Map

| Need | Resource |
|------|----------|
| **Getting started** | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| **API reference** | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| **System design** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Implementation details** | [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) |
| **Interactive docs** | http://localhost:8001/docs (when running) |

---

## 🔌 REST API Endpoints

```
POST   /nova/process          Process text/audio
POST   /nova/confirm          Confirm action
GET    /nova/history/{uid}    Get history
GET    /nova/status           Health check
POST   /nova/transcribe       Audio → text
GET    /docs                  Interactive docs
```

---

## 🛠️ Available Tools

```
gmail.send_email              Send email
gmail.draft_email             Draft email
gmail.read_unread_important   Read important emails

calendar.create_event         Create event
calendar.upcoming_events      Get upcoming events
calendar.delete_event         Delete event

sms.send_sms                  Send SMS

sentiment.analyze_text        Analyze sentiment

order.place_order             Place order (API)
order.prepare_order_sync      Semi-auto checkout

linkedin.prepare_post_sync    Semi-auto post
```

---

## 💻 Common Code Examples

### Python
```python
import requests

response = requests.post('http://localhost:8001/nova/process', json={
    'user_id': 'alice',
    'input_type': 'text',
    'content': 'Send email to bob@example.com'
})

result = response.json()
if result['status'] == 'confirmation_required':
    # Show button/dialog to user
    pass
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8001/nova/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'alice',
    input_type: 'text',
    content: 'Create meeting tomorrow at 10 AM'
  })
});

const data = await response.json();
console.log(data);
```

### cURL
```bash
curl -X POST http://localhost:8001/nova/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "input_type": "text",
    "content": "What time is my next meeting?"
  }'
```

---

## ⚙️ Configuration Options

**Minimal (.env):**
```env
GROQ_API_KEY=sk_...
```

**With Gmail/Calendar:**
```env
GROQ_API_KEY=sk_...
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
```

**With SMS:**
```env
GROQ_API_KEY=sk_...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...
```

See [.env.example](.env.example) for all options.

---

## 🔒 Risk Levels

**Low** (no confirmation needed):
- Read emails
- Check calendar
- Analyze sentiment

**Medium** (confirmation recommended):
- Create calendar event

**High** (confirmation required):
- Send email
- Send SMS
- Place order
- Publish to LinkedIn

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GROQ_API_KEY not found` | Check .env file exists in project root |
| `Playwright not installed` | `pip install playwright && playwright install chromium` |
| `Port 8001 already in use` | Change port in `run_api_server.py` or kill existing process |
| `database is locked` | Ensure only one Nova process running |
| `Gmail not working` | Verify OAuth credentials in .env |

---

## 📊 Response Format

### Success
```json
{
  "status": "success",
  "message": "Action completed",
  "actions_taken": ["Step 0: sentiment.analyze_text"],
  "results": [{
    "step": 0,
    "tool": "sentiment.analyze_text",
    "result": {"sentiment": "positive", ...}
  }]
}
```

### Confirmation Required
```json
{
  "status": "confirmation_required",
  "message": "This action needs your approval",
  "proposed_action": {
    "intent": "send_email",
    "risk_level": "high"
  }
}
```

### Error
```json
{
  "status": "error",
  "message": "Failed to process",
  "error_code": "PROCESSING_ERROR"
}
```

---

## 📋 Workflow Example

```
1. Frontend sends:    POST /nova/process
   Body: { user_id, input_type, content }

2. API responds with: status = "confirmation_required"
   Include: proposed_action details

3. User reviews and clicks YES

4. Frontend sends:    POST /nova/confirm
   Body: { user_id, confirm: true }

5. API executes tools and responds:
   status = "success"
   results = [...]

6. Frontend displays results to user
```

---

## 🔗 Links

- **Groq Console**: https://console.groq.com
- **Google Cloud**: https://console.cloud.google.com
- **Twilio**: https://www.twilio.com
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph/
- **Playwright Docs**: https://playwright.dev

---

## 🎯 Common Tasks

### Send Email
```json
{
  "user_id": "alice",
  "input_type": "text",
  "content": "Send email to bob@example.com saying I'll be late"
}
```

### Create Calendar Event
```json
{
  "user_id": "alice",
  "input_type": "text",
  "content": "Schedule meeting with team tomorrow at 10 AM"
}
```

### Check Sentiment
```json
{
  "user_id": "alice",
  "input_type": "text",
  "content": "Analyze the sentiment of this amazing day"
}
```

### Get User History
```
GET http://localhost:8001/nova/history/alice?limit=20
```

### Check Server Status
```
GET http://localhost:8001/nova/status
```

---

## 🔍 Monitoring

```bash
# Check if server is running
curl http://localhost:8001/health

# View API documentation
open http://localhost:8001/docs

# Check user history
curl http://localhost:8001/nova/history/alice

# View logs (if configured)
tail -f nova.log
```

---

## 📝 Logs & Persistence

- **Logs**: Console + optional file
- **Database**: `nova.db` (SQLite)
- **Memory**: Per-user preferences and history
- **Sessions**: In-memory during server uptime

---

## 🚀 Deployment Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set GROQ_API_KEY in .env
- [ ] Run server: `python run_api_server.py`
- [ ] Test endpoint: curl to /nova/status
- [ ] Connect frontend to http://localhost:8001
- [ ] Test full workflow with different inputs
- [ ] Enable additional tools as needed (Gmail, SMS, etc.)
- [ ] Monitor error logs

---

## 🆘 Getting Help

1. **Quick answers**: Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **API questions**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. **Architecture questions**: Read [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Implementation details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
5. **Interactive docs**: Open http://localhost:8001/docs
6. **Logs**: Check console output or nova.log file

---

## ⭐ Pro Tips

- Use `context` parameter in `/nova/process` to provide user-specific info
- Check `/nova/history/{user_id}` to see what Nova remembers about user
- Use `/nova/status` to verify all systems are operational
- Add CORS headers in nginx/reverse-proxy for production
- Enable HTTPS for production deployments
- Implement rate limiting for public APIs
- Keep SQLite database backed up regularly

---

## 📞 Version Info

- **Nova Version**: 1.0.0
- **API Version**: 1.0.0
- **Python**: 3.10+
- **Status**: Production Ready

Last Updated: February 26, 2026
