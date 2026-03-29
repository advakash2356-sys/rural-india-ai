# FastAPI + Google Sheets Logger Integration Guide

## Quick Reference

Add these components to your `api_server.py` to enable Google Sheets session logging.

---

## 1. Imports & Initialization

Add these imports at the top of `api_server.py`:

```python
from fastapi import BackgroundTasks
from google_sheets_logger import GoogleSheetLogger
import os
import logging

logger = logging.getLogger(__name__)
```

After creating your FastAPI app, initialize the logger:

```python
app = FastAPI()

# Initialize Google Sheets logger
GOOGLE_SHEET_WEBHOOK_URL = os.getenv('GOOGLE_SHEET_WEBHOOK_URL')
if GOOGLE_SHEET_WEBHOOK_URL:
    sheet_logger = GoogleSheetLogger(webhook_url=GOOGLE_SHEET_WEBHOOK_URL)
    logger.info(f"✅ Google Sheets logger initialized with webhook: {GOOGLE_SHEET_WEBHOOK_URL[:50]}...")
else:
    sheet_logger = None
    logger.warning("⚠️  GOOGLE_SHEET_WEBHOOK_URL not set. Session logging disabled.")
```

---

## 2. Login Endpoint Integration

### Option A: If you have a dedicated login endpoint

```python
@app.post('/api/v4/login')
async def google_login(request: dict, background_tasks: BackgroundTasks):
    """
    Google OAuth2 login endpoint.
    Accepts a Google JWT token and logs session to Google Sheets.
    """
    try:
        token = request.get('token')
        
        # Verify token using existing function
        token_data = verify_google_token(token)
        
        # Extract user info
        user_email = token_data.get('email')
        user_name = token_data.get('name', user_email.split('@')[0])
        
        # Log to Google Sheets (non-blocking)
        if sheet_logger:
            background_tasks.add_task(
                sheet_logger.log_login,
                user_email=user_email,
                user_name=user_name
            )
            logger.info(f"📊 Google Sheets login logged for {user_email}")
        
        return {
            'status': 'authenticated',
            'email': user_email,
            'name': user_name,
            'token': token
        }
    
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
```

### Option B: If login is handled in your main query endpoint

Find where you verify the token in your existing endpoint:

```python
@app.post('/api/v4/agents/query')
async def agent_query(request: Request, background_tasks: BackgroundTasks):
    """
    Main agent query endpoint.
    Extracts user info from Authorization header and logs Google Sheets on first request.
    """
    try:
        # Verify token (existing code)
        token_data = verify_google_token_with_rate_limit(request)
        
        # Extract user info from token
        user_email = token_data.get('email')
        user_name = token_data.get('name', user_email.split('@')[0])
        
        # Log to Google Sheets (non-blocking)
        # This triggers on FIRST request from user per session
        if sheet_logger:
            background_tasks.add_task(
                sheet_logger.log_login,
                user_email=user_email,
                user_name=user_name
            )
            logger.info(f"📊 Session started for {user_email}")
        
        # ... rest of your endpoint code ...
        
    except Exception as e:
        logger.error(f"❌ Query error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
```

---

## 3. Logout Endpoint

Add a dedicated logout endpoint if you don't have one:

```python
@app.post('/api/v4/agents/logout')
async def logout(request: Request, background_tasks: BackgroundTasks):
    """
    Logout endpoint.
    Logs session end to Google Sheets and clears auth state.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail='Missing authorization token')
        
        token = auth_header.replace('Bearer ', '')
        
        # Verify token to get user email
        # Use your existing JWT verification function
        token_data = verify_google_token(token)  # or however you decode JWT
        user_email = token_data.get('email')
        
        # Log logout to Google Sheets (non-blocking)
        if sheet_logger:
            background_tasks.add_task(
                sheet_logger.log_logout,
                user_email=user_email
            )
            logger.info(f"📊 Session ended for {user_email}")
        
        return {
            'status': 'logged_out',
            'email': user_email,
            'message': 'Session logged and closed'
        }
    
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        # Return success even if logging fails (don't block user logout)
        return {
            'status': 'logged_out',
            'message': 'Logged out (sheet logging may have failed)'
        }
```

---

## 4. Helper Function: Get User Info from Token

If you're decoding JWT in multiple places, create a helper:

```python
def extract_user_info_from_token(token: str) -> dict:
    """
    Extract email and name from JWT token.
    Returns dict with 'email' and 'name' keys.
    """
    try:
        # Decode JWT (adjust based on your JWT verification function)
        token_data = verify_google_token(token)
        
        return {
            'email': token_data.get('email'),
            'name': token_data.get('name', token_data.get('email', 'Unknown').split('@')[0])
        }
    except Exception as e:
        logger.error(f"❌ Error extracting user info: {e}")
        return {'email': 'unknown', 'name': 'unknown'}
```

Then use it in endpoints:

```python
user_info = extract_user_info_from_token(token)
background_tasks.add_task(sheet_logger.log_login, **user_info)
```

---

## 5. Graceful Degradation (Optional)

If the Google Sheets webhook fails or isn't configured, the system should still work:

```python
async def safe_log_to_sheets(background_tasks: BackgroundTasks, 
                             action: str, 
                             user_email: str, 
                             user_name: str = None):
    """
    Safely log to Google Sheets.
    If webhook not configured or fails, doesn't block user.
    """
    if not sheet_logger:
        logger.debug("Google Sheets logger not configured, skipping")
        return
    
    try:
        if action == 'login':
            background_tasks.add_task(
                sheet_logger.log_login,
                user_email=user_email,
                user_name=user_name or user_email.split('@')[0]
            )
        elif action == 'logout':
            background_tasks.add_task(
                sheet_logger.log_logout,
                user_email=user_email
            )
    except Exception as e:
        logger.warning(f"⚠️  Failed to queue Google Sheets task: {e}")
        # Don't raise - let user continue even if logging fails
```

Usage:

```python
await safe_log_to_sheets(background_tasks, 'login', user_email, user_name)
```

---

## 6. Testing the Integration

### Manual Test in Python

```python
# In Python shell or script
import asyncio
from google_sheets_logger import GoogleSheetLogger

async def test():
    logger = GoogleSheetLogger(
        webhook_url='https://script.google.com/macros/d/YOUR_SCRIPT_ID/userweb?state=done'
    )
    
    # Test login
    result = await logger.log_login('test@example.com', 'Test User')
    print(f"Login result: {result}")
    
    # Test logout
    result = await logger.log_logout('test@example.com')
    print(f"Logout result: {result}")

asyncio.run(test())
```

### Integration Test with FastAPI TestClient

```python
from fastapi.testclient import TestClient
import json

client = TestClient(app)

def test_google_sheets_integration():
    # Test login
    response = client.post(
        '/api/v4/login',
        headers={'Content-Type': 'application/json'},
        json={'token': 'valid_jwt_token'}
    )
    assert response.status_code == 200
    
    # Wait a moment for background task
    import time
    time.sleep(1)
    
    # Check Google Sheet for new row
    # (This would require reading the sheet, which needs sheets API)
```

### Curl Test

```bash
# Test logout endpoint
curl -X POST https://rural-india-ai.onrender.com/api/v4/agents/logout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
# {"status":"logged_out","email":"user@example.com","message":"Session logged and closed"}
```

---

## 7. Error Handling & Logging

The logger handles errors gracefully:

```python
# In google_sheets_logger.py, errors are caught and logged:
# - Network timeouts: Retries 3 times automatically
# - Invalid webhook URL: Logs warning, continues
# - Malformed payloads: Logs error, continues
# - Google Apps Script errors: Returns error response

# Check error logs in:
# - Render: render.com → Service → Logs
# - Google Apps Script: Code.gs → View → Execution Log
```

Example log output:

```
📩 Received LOGIN request for user@example.com
Sending payload to Google Sheets... (attempt 1/3)
✅ Google Sheets response: 200
✅ Login logged: user@example.com (Serial: 2)

📩 Received LOGOUT request for user@example.com
Final attempt (3/3) succeeded after retry
✅ Logout logged: user@example.com (Row: 2, Duration: 15 min)
```

---

## 8. Configuration Checklist

Before deploying, verify:

- [ ] `google_sheets_logger.py` is in project root
- [ ] `Code.gs` is deployed to Google Apps Script as Web App
- [ ] Webhook URL is correct format: `https://script.google.com/macros/d/{ID}/userweb?state=done`
- [ ] `.env` contains: `GOOGLE_SHEET_WEBHOOK_URL=...`
- [ ] `requirements.txt` contains: `httpx==0.24.0`
- [ ] `api_server.py` imports GoogleSheetLogger
- [ ] Sheet logger is initialized in app startup
- [ ] Login endpoint calls `sheet_logger.log_login()`
- [ ] Logout endpoint calls `sheet_logger.log_logout()`
- [ ] BackgroundTasks is imported from FastAPI
- [ ] Environment variable is set on Render
- [ ] Code is pushed to GitHub and deployed

---

## 9. Common Issues & Solutions

**Issue: `ModuleNotFoundError: No module named 'google_sheets_logger'`**
- Solution: Ensure `google_sheets_logger.py` is in the same directory as `api_server.py`
- Or add to sys.path: `import sys; sys.path.insert(0, '/path/to/project')`

**Issue: `AttributeError: 'NoneType' object has no attribute 'log_login'`**
- Solution: sheet_logger is None because GOOGLE_SHEET_WEBHOOK_URL not set
- Check .env file has correct line
- Verify env var is set on Render

**Issue: Rows appear but Name/Email are empty**
- Solution: User info not extracted correctly from token
- Debug: Add print statements to see token_data contents
- Verify your JWT decoder returns 'name' and 'email' fields

**Issue: Logout time shows but Duration is empty**
- Solution: Time format mismatch between login and logout
- Check Code.gs formatTimestamp() is consistent
- Both times must parse to Date objects correctly

---

## 10. Production Checklist

Before going live with beta testers:

- [ ] Test with real Google account login
- [ ] Verify login row appears in Google Sheet within 5 seconds
- [ ] Verify logout row completes with session duration
- [ ] Test 3-retry logic by temporarily blocking webhook
- [ ] Monitor for errors in Render logs during real usage
- [ ] Check Google App Script execution logs for failures
- [ ] Verify no tokens are logged to Google Sheets (security)
- [ ] Monitor sheet for spam/bot entries (implement caps if needed)
- [ ] Have backup deployment URL if webhook goes down

---

## Code Examples by Endpoint Type

### REST API Style

```python
@app.post('/api/auth/login')
async def login(credentials: dict, background_tasks: BackgroundTasks):
    user = authenticate_user(credentials)
    if sheet_logger:
        background_tasks.add_task(
            sheet_logger.log_login,
            user_email=user['email'],
            user_name=user['name']
        )
    return user
```

### FastAPI Dependency Injection

```python
from fastapi import Depends, Request

async def get_current_user(request: Request) -> dict:
    """Dependency to get current user from Authorization header."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    token_data = verify_google_token(token)
    return token_data

@app.get('/api/user/profile')
async def profile(current_user: dict = Depends(get_current_user),
                  background_tasks: BackgroundTasks):
    if sheet_logger and not hasattr(profile, '_logged_in'):
        background_tasks.add_task(
            sheet_logger.log_login,
            user_email=current_user['email'],
            user_name=current_user.get('name')
        )
        profile._logged_in = True
    return current_user
```

### WebSocket Support (if applicable)

```python
@app.websocket('/ws/chat')
async def websocket_endpoint(websocket: WebSocketConnection, background_tasks: BackgroundTasks):
    await websocket.accept()
    
    # Get user from connection query params or headers
    user_email = websocket.query_params.get('user_email')
    user_name = websocket.query_params.get('user_name')
    
    # Log start of WebSocket session
    if sheet_logger:
        background_tasks.add_task(
            sheet_logger.log_login,
            user_email=user_email,
            user_name=user_name
        )
    
    try:
        while True:
            data = await websocket.receive_text()
            # Process WebSocket messages
    finally:
        # Log session end
        if sheet_logger:
            background_tasks.add_task(
                sheet_logger.log_logout,
                user_email=user_email
            )
```

---

## Monitoring & Analytics

Once logging is working, you can analyze patterns:

```python
# Example: Get total sessions per day
# In Google Sheets, add pivot table:
# Rows: Login Time (groupby date)
# Values: COUNT of Serial

# Example: Get average session duration
# Formula: =AVERAGE(F2:F) in empty cell

# Example: Get active users right now
# Formula: =COUNTIF(E2:E, "") to count rows with no logout time
```

---

Done! Your FastAPI backend is now logging sessions to Google Sheets. Monitor the "Session Logs" sheet to see real-time user activity.

