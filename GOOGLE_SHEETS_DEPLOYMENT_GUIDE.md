# Google Sheets Session Logging - Complete Deployment Guide

## Overview

This guide walks you through setting up Google Sheets as your session tracking backend. The system will:
- ✅ Log every user login (name, email, timestamp)
- ✅ Log every user logout (with session duration auto-calculated)
- ✅ Use Google Sheets instead of a database (lightweight for beta)
- ✅ Non-blocking logging (doesn't impact user experience)
- ✅ 3-retry resilience (handles temporary network issues)

**Total Setup Time: ~10 minutes**

---

## Part 1: Create Google Sheet & Deploy Apps Script

### Step 1.1: Create a New Google Sheet

1. Go to https://sheets.google.com
2. Click the **"+ Create new spreadsheet"** button
3. Name it: `Rural India AI - Session Logs`
4. Press Enter and the sheet opens

**Your new URL will be:** `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

### Step 1.2: Open Apps Script Editor

1. In the Google Sheet, click **Extensions** (top menu)
2. Select **Apps Script**
3. A new tab opens with the Apps Script editor
4. You'll see a blank `Code.gs` file with a `myFunction()` stub

### Step 1.3: Add the Google Apps Script Code

1. Delete all the default code in `Code.gs`
2. Open this file: `Code.gs` (located in your project)
3. **Copy the entire contents** (starting from `/**` comment)
4. Paste into the Apps Script editor
5. Press **Ctrl+S** (or Cmd+S on Mac) to save
6. You'll see a dialog asking to rename the project → Name it `Rural India AI Logger` → OK

**Now your Code.gs is uploaded to Google Apps Script.**

### Step 1.4: Initialize the Sheet

The first time, you need to add headers and format the columns.

1. In the Apps Script editor, at the top:
   - Find the dropdown that says `myFunction` (or the first function name)
   - Click it, and select **`initializeSheet`**
2. Click the blue **Play** button (▶️ Run)
3. A popup appears asking permissions → Click **Review Permissions**
4. Select your Google account
5. Click **Allow** (it needs permission to modify the sheet)
6. The script runs. Check the **Execution log** (View → Execution log) to see:
   ```
   ✅ Sheet initialized with headers
   ```

**Check your Google Sheet:** You should now see the "Session Logs" tab with columns:
| Serial | Name | Email | Login Time | Logout Time | Total Minutes |

---

## Part 2: Deploy Apps Script as Web App & Get Webhook URL

### Step 2.1: Deploy as Web App

1. In the Apps Script editor, click **Deploy** (top-right button)
2. Select **New deployment** (or "Manage deployments" if this is an update)
3. A dialog opens. For **Select type**, click the dropdown and choose **Web app**
4. Configure as follows:
   - **Execute as:** `[your Google account email]`
   - **Who has access:** `Anyone` (allows FastAPI to send requests)
   - Click **Deploy**

5. A dialog shows your deployment URL:
   ```
   https://script.google.com/macros/d/{SCRIPT_ID}/userweb?state=done
   ```
   **Copy this entire URL.** This is your webhook URL.

### Step 2.2: Test the Webhook

Before integrating, let's verify it works.

1. Back in Apps Script, in the dropdown select **`testWebhook`**
2. Click **Run** (▶️ button)
3. Authorize if needed
4. Check Execution log (View → Execution log) for:
   ```
   ✅ Testing Google Apps Script setup...
   ✅ Sheet "Session Logs" exists
   ✅ Headers found in row 1
   ✅ Login row appended
   ✅ Logout time and duration calculated
   ✅ Test completed successfully!
   ```

5. **Go to your Google Sheet** and look at the "Session Logs" tab
   - You should see 1 row with:
     - Serial: 2
     - Name: Test User
     - Email: test@example.com
     - Login Time: [current date/time]
     - Logout Time: [current date/time]
     - Total Minutes: 0 or 1

   If you see this, **the webhook is working!** ✅

### Step 2.3: Clean Up Test Data

1. Back in Apps Script, select **`cleanupTestData`** from dropdown
2. Click **Run**
3. Go back to Google Sheet and refresh (F5)
4. The test row should be gone

---

## Part 3: Configure FastAPI Backend

### Step 3.1: Update Environment Variables

1. Open your `.env` file in the project root
2. Add this line:
   ```
   GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/d/{YOUR_SCRIPT_ID}/userweb?state=done
   ```
   Replace `{YOUR_SCRIPT_ID}` with the actual script ID from Part 2, Step 2.1

3. Save the file

**Example .env:**
```
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/d/1a2b3c4d5e6f7g8h9i0j/userweb?state=done
```

### Step 3.2: Add httpx to requirements.txt

The `google_sheets_logger.py` uses `httpx` for async HTTP requests.

1. Open `requirements.txt`
2. Add this line (in alphabetical order or at the end):
   ```
   httpx==0.24.0
   ```
3. Save

### Step 3.3: Integrate Logger into api_server.py

Open your `api_server.py` and add the logger integration. Here are the steps:

**A) Add imports at the top:**

```python
from fastapi import BackgroundTasks
from google_sheets_logger import GoogleSheetLogger
import os
```

**B) Initialize logger:**

```python
# Add after creating FastAPI app
app = FastAPI()

# Initialize Google Sheets logger
GOOGLE_SHEET_WEBHOOK_URL = os.getenv('GOOGLE_SHEET_WEBHOOK_URL')
sheet_logger = GoogleSheetLogger(webhook_url=GOOGLE_SHEET_WEBHOOK_URL) if GOOGLE_SHEET_WEBHOOK_URL else None
```

**C) Update your Google OAuth2 login endpoint:**

Find your endpoint that handles OAuth2 verification (where you verify the token). It probably looks like:

```python
@app.post('/api/v4/login')
async def google_login(request: dict, background_tasks: BackgroundTasks):
    # ... existing verification code ...
    
    # After successful token verification, log to Google Sheets
    user_email = token_data.get('email')
    user_name = token_data.get('name')
    
    if sheet_logger:
        background_tasks.add_task(
            sheet_logger.log_login,
            user_email=user_email,
            user_name=user_name
        )
    
    # ... existing return statement ...
```

**D) Update your logout endpoint:**

Add or update your logout endpoint:

```python
@app.post('/api/v4/logout')
async def logout(request: Request, background_tasks: BackgroundTasks):
    # Get user email from Authorization header
    auth_header = request.headers.get('Authorization', '')
    
    # Extract token and decode (similar to verify_google_token)
    try:
        token = auth_header.replace('Bearer ', '')
        user_email = decode_jwt_from_token(token)['email']  # Use your existing decode func
        
        if sheet_logger:
            background_tasks.add_task(
                sheet_logger.log_logout,
                user_email=user_email
            )
    except:
        pass  # Gracefully fail if can't extract email
    
    return {'status': 'logged_out'}
```

---

## Part 4: Deploy to Render

### Step 4.1: Push Code to GitHub

```bash
# In your local project directory
git add -A
git commit -m "Feature: Add Google Sheets session logging integration"
git push origin main
```

### Step 4.2: Update Environment Variable on Render

1. Go to https://dashboard.render.com
2. Select your **Rural India AI** service
3. Click **Environment** (left sidebar)
4. Click **Add Environment Variable**
5. Add:
   - **Key:** `GOOGLE_SHEET_WEBHOOK_URL`
   - **Value:** `https://script.google.com/macros/d/{YOUR_SCRIPT_ID}/userweb?state=done`
6. Click **Save Changes**
7. Render auto-deploys your service (~2-5 minutes)

### Step 4.3: Verify Deployment

Once Render finishes deploying:
1. Go to https://rural-india-ai.onrender.com/ui
2. Log in with your Google account
3. Go back to your Google Sheet (in another tab)
4. Refresh the "Session Logs" sheet
5. You should see a new row:
   - Serial: 2 (or next number)
   - Name: [Your name from Google account]
   - Email: [Your email]
   - Login Time: [current time]
   - Logout Time: [empty]
   - Total Minutes: [empty]

### Step 4.4: Test Logout

1. In the Rural India AI UI, click the **Logout** button
2. Go back to Google Sheet and refresh
3. The same row should now show:
   - Logout Time: [logout time]
   - Total Minutes: [duration in minutes]

**If you see this, Google Sheets logging is working!** ✅

---

## Part 5: Testing & Troubleshooting

### Quick Test Checklist

- [ ] Google Sheet created with "Session Logs" tab
- [ ] Apps Script code deployed as Web App
- [ ] Webhook URL copied and saved
- [ ] Test data appeared in Google Sheet during testWebhook
- [ ] Test data cleaned up
- [ ] Webhook URL added to `.env`
- [ ] httpx added to `requirements.txt`
- [ ] Logger integration added to `api_server.py`
- [ ] Code pushed to GitHub
- [ ] Environment variable set on Render
- [ ] Render deployment completed
- [ ] Real login appeared in Google Sheet
- [ ] Real logout appeared with duration calculated

### Troubleshooting

**Q: The webhook URL doesn't seem to work (403 error in logs)**
- Ensure you clicked "Anyone" when deploying (not "Me only")
- Try redeploying: Deploy → New Deployment → same configuration

**Q: Rows appear with empty Name/Email**
- Your FastAPI endpoint might not be extracting the user name/email correctly
- Check that `token_data.get('name')` and `token_data.get('email')` are actually returning values
- Add `print()` debugging to see what's in the token

**Q: Logout Time appears but Total Minutes is blank**
- The timestamp format might not be recognized
- Check both Login Time and Logout Time formats are identical
- Manually recalculate: Open the cell and press Enter

**Q: No rows appearing at all**
- Check Render logs: `render.com → Service Logs`
- Look for errors from `google_sheets_logger.py`
- Verify `GOOGLE_SHEET_WEBHOOK_URL` environment variable is set (not empty/None)
- Test the webhook URL directly in browser (should show an error, but not 404)

**Q: Getting "ModuleNotFoundError: No module named 'httpx'"**
- httpx wasn't added to requirements.txt or dependency error in build
- Add to requirements.txt and git push
- Render will auto-rebuild

### Enable Debug Logging

To see detailed logs from the logger, add to your `api_server.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Then check Render logs for detailed GoogleSheetLogger output.

---

## Architecture Summary

```
User Browser
    ↓ (OAuth2 Login)
FastAPI Backend (api_server.py)
    ↓ (add_task: sheet_logger.log_login())
BackgroundTask (non-blocking)
    ↓ (async HTTP POST)
Google Apps Script Web App (Code.gs)
    ↓ (doPost receives JSON)
Google Sheet (Session Logs tab)
    ↓ (appends row with name, email, login time)
User sees login ✅
```

**Benefits:**
- ✅ Non-blocking (login completes instantly)
- ✅ No database to manage
- ✅ 3-retry resilience (handles network blips)
- ✅ Automatic session duration calculation
- ✅ Real-time visibility (check Google Sheet anytime)
- ✅ Cost-effective (Google Sheets is free)

---

## Next Steps

Once you verify the Google Sheets logging is working:

1. **Monitor session data** - Open Google Sheet anytime to see active users
2. **Set up alerts** (optional) - Add Google Sheets formulas to alert on unusual patterns
3. **Export reports** (optional) - Create pivot tables from session data
4. **Onboard beta testers** - Share the Rural India AI link with beta users
5. **Collect feedback** - Watch session duration and usage patterns

---

## Reference Files

- **Backend Logger:** `google_sheets_logger.py` (async HTTP client, retry logic)
- **Apps Script:** `Code.gs` (webhook handler, duration calculation)
- **Integration Example:** This file (deployment steps, best practices)
- **API Documentation:** See `AUTHENTICATION_GUIDE.md` for endpoint reference

---

## Questions?

If something doesn't work:
1. Check the Execution Log in Apps Script (View → Execution log)
2. Check the Render Service Logs (render.com → Logs)
3. Verify environment variables are set correctly
4. Run `testWebhook` again in Apps Script to verify setup

All integration code is production-ready. No further customization needed unless you want to modify the fields being logged.

