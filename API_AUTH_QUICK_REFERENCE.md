# Quick Reference: Apply Authentication to api_server.py

## Step 1: Add Imports (at the top of api_server.py)

```python
from fastapi import Depends, File, UploadFile
from typing import Dict
from auth import (
    verify_google_token,
    verify_google_token_with_rate_limit,
    AuditLogger
)
```

## Step 2: Replace Route Signatures

### Before (Without Authentication):
```python
@app.post("/api/v4/agents/query")
async def query_agents(query: str):
    agent_response = agent_orchestrator.route_query(query)
    return {"response": agent_response}
```

### After (With Authentication):
```python
@app.post("/api/v4/agents/query")
async def query_agents(
    query: str,
    user: Dict = Depends(verify_google_token_with_rate_limit)
):
    """Query AI agents with authentication & rate limiting"""
    
    email = user.get('email')
    
    # Your existing logic
    agent_response = agent_orchestrator.route_query(query)
    
    # Add disclaimer if healthcare query
    if 'health' in query.lower() or 'medical' in query.lower():
        agent_response += "\n\n🛑 DISCLAIMER: I am an AI assistant, not a medical doctor..."
    
    # Log the interaction
    AuditLogger.log_interaction(
        user_email=email,
        endpoint="/api/v4/agents/query",
        query=query,
        method="POST",
        status_code=200
    )
    
    return {
        "response": agent_response,
        "user_email": email
    }
```

## Step 3: Apply to All Key Routes

### Phase 2: Voice Processing
```python
@app.post("/api/v2/voice")
async def process_voice(
    file: UploadFile = File(...),
    user: Dict = Depends(verify_google_token_with_rate_limit)
):
    email = user.get('email')
    audio_content = await file.read()
    
    # Your Whisper transcription code here
    transcription = "..."  # Result from Whisper
    
    # Route to agent
    response = agent_orchestrator.route_query(transcription)
    
    # Log
    AuditLogger.log_interaction(email, "/api/v2/voice", transcription)
    
    return {"transcription": transcription, "response": response}
```

### Phase 3: Vector Search
```python
@app.post("/api/v3/search")
async def search_vectors(
    query: str,
    user: Dict = Depends(verify_google_token)
):
    email = user.get('email')
    
    # Your search logic here
    results = vector_db.search(query)
    
    # Log
    AuditLogger.log_interaction(email, "/api/v3/search", query)
    
    return {"results": results}
```

### Phase 4: Agent List
```python
@app.get("/api/v4/agents")
async def list_agents(user: Dict = Depends(verify_google_token)):
    """Get list of available agents - requires authentication"""
    
    email = user.get('email')
    
    agents = [
        {"name": "Healthcare Agent", "description": "..."},
        {"name": "Agriculture Agent", "description": "..."},
        {"name": "Education Agent", "description": "..."}
    ]
    
    AuditLogger.log_interaction(email, "/api/v4/agents", "list", method="GET")
    
    return {"agents": agents}
```

### Phase 5: Safety Check
```python
@app.post("/api/v5/safety/check")
async def safety_check(
    text: str,
    user: Dict = Depends(verify_google_token)
):
    email = user.get('email')
    
    # Your safety checking logic
    is_safe = safety_module.check_content(text)
    
    AuditLogger.log_interaction(email, "/api/v5/safety/check", text)
    
    return {"is_safe": is_safe}
```

## Step 4: Keep Public Endpoints Public

```python
# Health check - NO authentication required
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "authenticated": False}

# Frontend UI - NO authentication required
@app.get("/ui")
async def serve_ui():
    with open('index.html', 'r') as f:
        return HTMLResponse(f.read())
```

## Step 5: Update Environment Variable

Create/Update `.env`:
```env
GOOGLE_CLIENT_ID=YOUR_ACTUAL_GOOGLE_CLIENT_ID_HERE
MQTT_BROKER=localhost
MQTT_PORT=1883
API_PORT=8000
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Step 6: Update Frontend index.html

Replace `YOUR_GOOGLE_CLIENT_ID_HERE` in this section:

```html
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID_HERE"
     data-callback="handleGoogleSignIn">
</div>
```

With your actual Client ID from Google Cloud Console:

```html
<div id="g_id_onload"
     data-client_id="123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com"
     data-callback="handleGoogleSignIn">
</div>
```

## Complete api_server.py Import Section

```python
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
import os
import json
import logging
from datetime import datetime

# Your existing imports
from agent_orchestrator import AgentOrchestrator
from voice_processor import VoiceProcessor
# ... other imports

# NEW: Authentication imports
from auth import (
    verify_google_token,
    verify_google_token_with_rate_limit,
    AuditLogger
)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Rest of your code...
```

## Testing

```bash
# 1. Sign in to https://rural-india-ai.onrender.com/ui
# 2. Accept Google sign-in
# 3. Check browser DevTools → Network tab
# 4. Every API call should have header:
#    Authorization: Bearer eyJhbGciOiJSUzI1NiIs...

# 5. Check logs at data/logs/auth.log
cat data/logs/auth.log
# Should see:
# [2026-03-29T10:32:45.123456] | User: user@gmail.com | Endpoint: /api/v4/agents/query | ...

# 6. Rate limiting test (make 61+ requests in 60 seconds):
# Request 61: Get 429 Too Many Requests
```

## Deployment to Render

1. Push to GitHub:
```bash
git add .
git commit -m "Add Google OAuth2 authentication"
git push origin main
```

2. Render auto-detects new files (`auth.py`, updated `requirements.txt`)

3. Add environment variable in Render dashboard:
   - Service → Settings → Environment Variables
   - Add: `GOOGLE_CLIENT_ID=your_actual_id`

4. Manual Redeploy (if needed):
   - Go to Render dashboard
   - Click "Deploy Latest Commit"

5. Verify:
   - Check logs for: `🚀 Authentication system initialized`
   - Test login at: https://rural-india-ai.onrender.com/ui

---

That's it! Your system is now secured with Google OAuth2 authentication. 🔐
