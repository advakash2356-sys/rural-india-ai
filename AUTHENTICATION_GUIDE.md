# GOOGLE OAUTH2 AUTHENTICATION INTEGRATION GUIDE

## Overview
This guide shows how to integrate Google OAuth2 authentication into your FastAPI backend (`api_server.py`). The authentication system includes:

- **JWT Verification**: Validates Google OAuth2 tokens
- **Audit Logging**: Records every authenticated interaction
- **Rate Limiting**: Prevents spam (60 requests/minute per user)
- **User Context**: Extracts email, name, and picture from tokens

## Prerequisites

### 1. Install Dependencies
```bash
pip install google-auth==2.27.0 google-auth-httplib2==0.2.0
```

OR update requirements.txt (already done):
```
google-auth==2.27.0
google-auth-httplib2==0.2.0
```

### 2. Get Your Google Client ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new OAuth 2.0 Web Application
3. Configure authorized origins: `https://rural-india-ai.onrender.com` and `http://localhost:8000`
4. Copy your **Client ID**

### 3. Set Environment Variable

Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID_HERE
```

## Integration Steps

### Step 1: Import Authentication Module

At the top of your `api_server.py`:

```python
from auth import (
    verify_google_token,
    verify_google_token_with_rate_limit,
    AuditLogger
)
```

### Step 2: Apply Authentication to Routes

#### Simple Authentication (No Rate Limiting)

```python
from fastapi import Depends
from typing import Dict

@app.post("/api/v4/agents/query")
async def query_agents(
    query: str,
    user: Dict = Depends(verify_google_token)
):
    """
    Query an AI agent with text input
    
    Only authenticated users can access this endpoint
    """
    
    email = user.get('email')
    name = user.get('name')
    
    # Your existing logic
    agent_response = agent_orchestrator.route_query(query)
    
    # Log interaction
    AuditLogger.log_interaction(
        user_email=email,
        endpoint="/api/v4/agents/query",
        query=query,
        method="POST",
        status_code=200
    )
    
    # Add healthcare/agriculture disclaimers as needed
    if 'health' in query.lower():
        agent_response += "\n\n🛑 DISCLAIMER: I am an AI assistant, not a doctor..."
    
    return {
        "response": agent_response,
        "user": {
            "email": email,
            "name": name
        }
    }
```

#### With Rate Limiting (Recommended)

```python
@app.post("/api/v2/voice")
async def process_voice(
    file: UploadFile = File(...),
    user: Dict = Depends(verify_google_token_with_rate_limit)
):
    """
    Process voice input from authenticated users
    
    Includes rate limiting: 60 requests/minute per user
    """
    
    email = user.get('email')
    
    # Read audio file
    audio_content = await file.read()
    
    # Process with Whisper (your existing code)
    transcription = whisper_model.transcribe(audio_content)
    
    # Route to appropriate agent
    agent_response = agent_orchestrator.route_query(transcription)
    
    # Log interaction
    AuditLogger.log_interaction(
        user_email=email,
        endpoint="/api/v2/voice",
        query=transcription,
        method="POST",
        status_code=200
    )
    
    return {
        "transcription": transcription,
        "response": agent_response,
        "remaining_requests_this_minute": user.get('rate_limit_remaining')
    }
```

### Step 3: Update All Protected Routes

Apply the dependency to these key endpoints:

```python
# Phase 2: Voice Processing
@app.post("/api/v2/voice")
async def voice_endpoint(user: Dict = Depends(verify_google_token_with_rate_limit)):
    pass

@app.post("/api/v2/query")
async def voice_query(user: Dict = Depends(verify_google_token)):
    pass

# Phase 3: Vector Database
@app.post("/api/v3/search")
async def vector_search(query: str, user: Dict = Depends(verify_google_token)):
    pass

# Phase 4: Domain Agents (MOST IMPORTANT)
@app.post("/api/v4/agents/query")
async def query_agents(query: str, user: Dict = Depends(verify_google_token_with_rate_limit)):
    pass

@app.get("/api/v4/agents")
async def list_agents(user: Dict = Depends(verify_google_token)):
    pass

# Phase 5: Safety Checks
@app.post("/api/v5/safety/check")
async def safety_check(text: str, user: Dict = Depends(verify_google_token)):
    pass

# Phase 6: Analytics/Metrics (can remain public or require auth)
@app.get("/api/v6/dashboard")
async def dashboard(user: Dict = Depends(verify_google_token)):
    pass
```

### Step 4: Keep Public Endpoints Public

Some endpoints can remain public without authentication:

```python
# Health check endpoint (public - for monitoring)
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

# Frontend UI (public)
@app.get("/ui")
async def serve_ui():
    pass
```

## Frontend Integration

The updated `index.html` already includes:

1. **Google Sign-In Button**: Shows login screen until authenticated
2. **JWT Token Storage**: Securely stored in `sessionStorage`
3. **Bearer Token Headers**: Automatically added to all API calls

```javascript
// Frontend automatically adds Authorization header
headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${googleToken}`
}
```

## Audit Log Format

All authenticated interactions are logged to `data/logs/auth.log`:

```
[2026-03-29T10:32:45.123456] | User: user@gmail.com | Endpoint: /api/v4/agents/query | Method: POST | Status: 200 | Query: What is dengue
[2026-03-29T10:33:12.654321] | User: user@gmail.com | Endpoint: /api/v2/voice | Method: POST | Status: 200 | Query: How to grow tomatoes
```

## Error Handling

The authentication system returns standard HTTP status codes:

### 401 Unauthorized
```json
{
    "detail": "Missing Authorization header"
}
```

### 401 Unauthorized (Invalid Token)
```json
{
    "detail": "Invalid token: Token audience mismatch"
}
```

### 429 Too Many Requests (Rate Limited)
```json
{
    "error": "Rate limit exceeded",
    "reset_in_seconds": 45,
    "limit": 60,
    "window": "per minute"
}
```

## Testing Authentication

### Test with cURL

```bash
# Get token from Google (in browser first)
TOKEN="your_google_jwt_here"

# Test authenticated endpoint
curl -X POST "https://rural-india-ai.onrender.com/api/v4/agents/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is fever?"}'

# Should return 200 with response
# Without token would return 401 Unauthorized
```

### Frontend Testing

1. Open https://rural-india-ai.onrender.com/ui
2. Click "Sign in with Google"
3. Sign in with your Google account
4. Should see "Welcome, [Your Name]"
5. Chat interface becomes available
6. All requests include `Authorization: Bearer <token>`

## Security Best Practices

1. **Never expose GOOGLE_CLIENT_ID in frontend**: ✅ Only on index.html (public by design)
2. **Never expose GOOGLE_CLIENT_SECRET**: Only on backend in .env
3. **Validate tokens on backend**: ✅ Done in `verify_google_token()`
4. **Use HTTPS**: ✅ Required for OAuth2
5. **Implement rate limiting**: ✅ Included in `verify_google_token_with_rate_limit()`
6. **Log all interactions**: ✅ All requests logged with user email

## Production Deployment

### On Render.com

1. Go to your Render service settings
2. Add environment variable:
   - Key: `GOOGLE_CLIENT_ID`
   - Value: Your actual Google Client ID
3. Ensure `.env` file is in `.gitignore` (don't commit credentials)
4. Push `api_server.py` with authentication imports
5. Render auto-deploys

### Check Logs

```bash
# In Render dashboard, view logs:
# Should see: "🚀 Authentication system initialized with Google Client ID: xxx..."
# User logins: "🔐 User authenticated: user@gmail.com"
```

## Troubleshooting

### "GOOGLE_CLIENT_ID not set"
- Solution: Add `GOOGLE_CLIENT_ID=your_id` to `.env` file on Render

### "Token audience mismatch"
- Solution: Make sure GOOGLE_CLIENT_ID in `.env` matches your Google Console Client ID

### "Missing Authorization header"
- Solution: Frontend must send: `Authorization: Bearer <token>`

### "Rate limit exceeded"
- Solution: User exceeded 60 requests/minute. Wait or adjust limit in `auth.py`

## Next Steps

1. ✅ Update `api_server.py` with `Depends(verify_google_token)` on protected routes
2. ✅ Update `.env` with your GOOGLE_CLIENT_ID
3. ✅ Update `index.html` with your GOOGLE_CLIENT_ID (replace placeholder)
4. ✅ Push to GitHub for auto-deployment
5. ✅ Test authentication at https://rural-india-ai.onrender.com/ui

---

**Authentication is now protecting your AI system from unauthorized access!** 🔐
