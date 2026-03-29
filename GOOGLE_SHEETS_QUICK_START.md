# Google Sheets Session Logging - Implementation Checklist

## 📋 Quick Start (15 minutes)

Follow this checklist in order. Each item takes ~2 minutes.

---

## Phase 1: Google Sheets & Apps Script Setup (5 minutes)

- [ ] **1.1** Create new Google Sheet: https://sheets.google.com → "+ Create new spreadsheet" → Name: "Rural India AI - Session Logs"

- [ ] **1.2** Open Apps Script: Extensions → Apps Script

- [ ] **1.3** Find and open: `Code.gs` (in this project folder)

- [ ] **1.4** Copy entire contents of `Code.gs`

- [ ] **1.5** Paste into Apps Script editor (replace default code)

- [ ] **1.6** Save: Ctrl+S (or Cmd+S on Mac)

- [ ] **1.7** Initialize sheet:
  - Dropdown: Select `initializeSheet`
  - Click Run (▶️)
  - Authorize when asked
  - Check logs: "✅ Sheet initialized"

**⏱️ Result:** Sheet has headers: Serial | Name | Email | Login Time | Logout Time | Total Minutes

---

## Phase 2: Deploy Apps Script as Webhook (5 minutes)

- [ ] **2.1** In Apps Script editor: Deploy → New Deployment

- [ ] **2.2** Select type: Web app

- [ ] **2.3** Configure:
  - Execute as: [Your email]
  - Who has access: Anyone

- [ ] **2.4** Click Deploy

- [ ] **2.5** Copy deployment URL:
  ```
  https://script.google.com/macros/d/{SCRIPT_ID}/userweb?state=done
  ```

- [ ] **2.6** Test in Apps Script:
  - Dropdown: Select `testWebhook`
  - Click Run
  - Check logs for: "✅ Test completed successfully!"

- [ ] **2.7** Go to Google Sheet and verify test row exists:
  - "Session Logs" tab
  - Serial: 2, Name: Test User, Email: test@example.com
  - Login Time: [timestamp], Logout Time: [timestamp], Total Minutes: 0 or 1

- [ ] **2.8** Clean up test data:
  - In Apps Script: Select `cleanupTestData`
  - Click Run
  - Refresh Google Sheet (F5)
  - Test row should be gone

**⏱️ Result:** Webhook URL copied and tested successfully

---

## Phase 3: Configure FastAPI Backend (3 minutes)

- [ ] **3.1** Update `.env` file:
  ```
  GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/d/{YOUR_SCRIPT_ID}/userweb?state=done
  ```
  Replace `{YOUR_SCRIPT_ID}` with actual ID from Phase 2, Step 2.5

- [ ] **3.2** Add to `requirements.txt`:
  ```
  httpx==0.24.0
  ```

- [ ] **3.3** Verify `google_sheets_logger.py` exists in project root

**⏱️ Result:** Dependencies installed and webhook URL configured

---

## Phase 4: Integrate Logger into api_server.py (3 minutes)

Follow these steps to wire the logger into your FastAPI app:

### Step 4.1: Add Imports
At the top of `api_server.py`, add:
```python
from fastapi import BackgroundTasks
from google_sheets_logger import GoogleSheetLogger
import os
```

### Step 4.2: Initialize Logger
After `app = FastAPI()`, add:
```python
GOOGLE_SHEET_WEBHOOK_URL = os.getenv('GOOGLE_SHEET_WEBHOOK_URL')
sheet_logger = GoogleSheetLogger(webhook_url=GOOGLE_SHEET_WEBHOOK_URL) if GOOGLE_SHEET_WEBHOOK_URL else None
```

### Step 4.3: Add Login Logging
Find your authentication endpoint (or create one) and add:
```python
@app.post('/api/v4/login')
async def google_login(request: dict, background_tasks: BackgroundTasks):
    token = request.get('token')
    token_data = verify_google_token(token)
    
    user_email = token_data.get('email')
    user_name = token_data.get('name', user_email.split('@')[0])
    
    # Log to Google Sheets (non-blocking)
    if sheet_logger:
        background_tasks.add_task(
            sheet_logger.log_login,
            user_email=user_email,
            user_name=user_name
        )
    
    return {
        'status': 'authenticated',
        'email': user_email,
        'name': user_name,
        'token': token
    }
```

### Step 4.4: Add Logout Logging
Add a logout endpoint:
```python
@app.post('/api/v4/agents/logout')
async def logout(request: Request, background_tasks: BackgroundTasks):
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    token_data = verify_google_token(token)
    user_email = token_data.get('email')
    
    if sheet_logger:
        background_tasks.add_task(
            sheet_logger.log_logout,
            user_email=user_email
        )
    
    return {'status': 'logged_out', 'email': user_email}
```

- [ ] **4.1** Added imports to `api_server.py`
- [ ] **4.2** Initialized GoogleSheetLogger after FastAPI app creation
- [ ] **4.3** Added `log_login` call in authentication endpoint
- [ ] **4.4** Added logout endpoint with `log_logout` call
- [ ] **4.5** Verified imports: `BackgroundTasks`, `GoogleSheetLogger`, `os`

**⏱️ Result:** Logger integrated into FastAPI endpoints

---

## Phase 5: Deploy to Render (5 minutes)

- [ ] **5.1** Commit code to Git:
  ```bash
  git add -A
  git commit -m "Feature: Add Google Sheets session logging"
  git push origin main
  ```

- [ ] **5.2** On Render Dashboard: https://dashboard.render.com

- [ ] **5.3** Click your **Rural India AI** service

- [ ] **5.4** Click **Environment** (left sidebar)

- [ ] **5.5** Click **Add Environment Variable**

- [ ] **5.6** Add:
  - Key: `GOOGLE_SHEET_WEBHOOK_URL`
  - Value: `https://script.google.com/macros/d/{YOUR_SCRIPT_ID}/userweb?state=done`

- [ ] **5.7** Click **Save Changes**

- [ ] **5.8** Wait for Render to auto-deploy (~2-5 minutes)

**⏱️ Result:** Backend deployed with Google Sheets webhook URL configured

---

## Phase 6: Test End-to-End (2 minutes)

- [ ] **6.1** Go to: https://rural-india-ai.onrender.com/ui

- [ ] **6.2** Log in with your Google account

- [ ] **6.3** Go to Google Sheet (in separate tab) and refresh

- [ ] **6.4** Check "Session Logs" sheet for new row:
  - Serial: 2 (or next number)
  - Name: [Your full name]
  - Email: [Your email]
  - Login Time: [current time]
  - Logout Time: [empty]
  - Total Minutes: [empty]

- [ ] **6.5** Back to Rural India AI UI, click **Logout**

- [ ] **6.6** Refresh Google Sheet again

- [ ] **6.7** Same row should now show:
  - Logout Time: [logout time]
  - Total Minutes: [duration in minutes]

**✅ SUCCESS!** Google Sheets session logging is working!

---

## 📊 What Happens Now

Every time a user logs in/out on https://rural-india-ai.onrender.com/ui:
- ✅ Login event: New row appears in "Session Logs" sheet with name, email, login time
- ✅ Logout event: Same row updates with logout time and session duration (auto-calculated)
- ✅ Non-blocking: User doesn't wait for logging to complete
- ✅ Resilient: 3 automatic retries if network is unreliable

---

## 🔍 Monitoring

Real-time monitoring in Google Sheets:
```
- View current active sessions: COUNT rows with empty Logout Time
- View total sessions today: COUNT rows with Login Time = TODAY()
- View average session length: AVERAGE(F:F) for Total Minutes column
- Export daily reports: File → Download → As CSV
```

---

## ❌ Troubleshooting Quick Fix

| Problem | Check | Fix |
|---------|-------|-----|
| No rows appearing | Render logs | `GOOGLE_SHEET_WEBHOOK_URL` environment variable set? |
| Empty Name/Email | Token data | Is `token_data.get('name')` returning a value? |
| Logout time missing | Google Sheets | Refresh page (F5) |
| Duration not calculating | Apps Script logs | Check formatTimestamp() function works |
| Webhook 403 error | Apps Script deployment | Did you select "Anyone" for access? |

Details: See `GOOGLE_SHEETS_DEPLOYMENT_GUIDE.md` → Troubleshooting

---

## 📁 Files Created/Modified

**New files:**
- ✅ `Code.gs` - Google Apps Script (paste into Google Sheets)
- ✅ `google_sheets_logger.py` - FastAPI logger class (already created)

**Modified files:**
- ✅ `requirements.txt` - Add `httpx==0.24.0`
- ✅ `api_server.py` - Add imports and integrate logger
- ✅ `.env` - Add `GOOGLE_SHEET_WEBHOOK_URL`

**Documentation:**
- ✅ `GOOGLE_SHEETS_DEPLOYMENT_GUIDE.md` - Full deployment walkthrough
- ✅ `FASTAPI_GOOGLE_SHEETS_INTEGRATION.md` - Code integration examples
- ✅ This checklist

---

## ⏱️ Time Estimate

| Phase | Time | Status |
|-------|------|--------|
| Phase 1: Google Sheets Setup | 5 min | Start here |
| Phase 2: Deploy Apps Script | 5 min | Then this |
| Phase 3: Configure Backend | 3 min | Then this |
| Phase 4: Integrate Logger | 3 min | Then this |
| Phase 5: Deploy to Render | 5 min | Then this |
| Phase 6: Test End-to-End | 2 min | Finally, verify |
| **TOTAL** | **23 min** | Fully operational |

---

## ✅ Final Verification

Once complete, you'll have:
- ✅ Google Sheet with "Session Logs" tab
- ✅ Google Apps Script deployed as Web App
- ✅ FastAPI backend logging sessions
- ✅ Render auto-deploying changes
- ✅ Real-time session tracking in Google Sheets
- ✅ Non-blocking logging (doesn't affect user experience)
- ✅ 3-retry resilience for network issues
- ✅ Automatic session duration calculation

**Your Regional AI system now has production-grade session tracking!**

Ready for beta testing with real users. 🚀

---

## Next Steps

1. **Invite beta testers** to: https://rural-india-ai.onrender.com/ui
2. **Monitor sessions** in Google Sheet
3. **Collect user feedback** based on usage patterns
4. **Iterate** based on session data insights
5. **Scale up** when ready (move to proper database, add analytics)

---

## Support

If stuck on any step:
1. Read the detailed guide: `GOOGLE_SHEETS_DEPLOYMENT_GUIDE.md`
2. Check code examples: `FASTAPI_GOOGLE_SHEETS_INTEGRATION.md`
3. Run test functions in Apps Script to debug
4. Check Render service logs for errors
5. Check Google Apps Script execution logs

All code is production-ready. No customization needed unless modifying tracked fields.

