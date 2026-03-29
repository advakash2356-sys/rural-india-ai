# Rural India AI - Cloud Deployment & Compliance Guide

## 🚀 PHASE 1: CLOUD DEPLOYMENT PREPARATION

This guide walks through preparing Rural India AI for public beta launch on Render or Railway with mandatory legal compliance guardrails.

---

## Overview of New Files

### Deployment Files
- **`requirements.txt`** - Production dependencies with environment management
- **`Procfile`** - Heroku/Render-compatible startup configuration
- **`render.yaml`** - Render-specific configuration with auto-scaling
- **`.env.example`** - Template for environment variables (secrets management)
- **`.gitignore`** - Prevents committing secrets, databases, and logs

### Compliance Files
- **`index.html`** - Beta UI with mandatory clickwrap consent modal
- **`api_server.py`** - Updated with environment config and legal disclaimers

---

## 🔐 PHASE 2: SECRETS MANAGEMENT

### Step 1: Create `.env` File Locally (NEVER COMMIT)

```bash
cp .env.example .env
# Edit .env with your actual secrets
```

### Step 2: Update `api_server.py` to Use Environment Variables

The updated `api_server.py` now includes:

```python
from dotenv import load_dotenv
import os

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
BETA_MODE = os.getenv("BETA_MODE", "True").lower() == "true"
REQUIRE_CONSENT = os.getenv("REQUIRE_CONSENT", "True").lower() == "true"
```

### Step 3: Set Environment Variables on Cloud Platform

#### For Render:
1. Go to your Render dashboard
2. Create a Web Service from GitHub
3. In **Environment** settings, add:
   - `PORT` = 8000
   - `ENVIRONMENT` = production
   - `DEBUG` = False
   - `BETA_MODE` = True
   - `REQUIRE_CONSENT` = True
   - `SECRET_KEY` = (generate a secure key)
   - `MQTT_BROKER` = (your MQTT server)
   - etc.

#### For Railway:
1. Create a new project
2. Connect your GitHub repo
3. Go to **Variables** → Add each env var
4. Railway will auto-set `PORT`

---

## 📋 PHASE 3: LEGAL COMPLIANCE IMPLEMENTATION

### Mandatory UI Elements Implemented

#### 1. Clickwrap Consent Modal
**File:** `index.html`

When users visit `/ui`:
- They see a **BLOCKING modal** that prevents interaction with the app
- They MUST read the 5-point Beta Agreement
- They MUST check "I agree" checkbox
- They must click "Enter Beta Platform" button
- Consent is saved to `localStorage` (permission given at specific timestamp)

**The 5 Required Disclosures:**
1. **Experimental System (As-Is)** - No warranties
2. **Not Professional Advice** - Healthcare & Agriculture agents are informational only
3. **Limitation of Liability** - No liability for damages
4. **Data & Privacy** - All interactions monitored and logged
5. **Governing Law** - Indian jurisdiction, New Delhi courts

#### 2. Persistent Beta Warning Banner
Every page shows: `⚠️ BETA VERSION: AI responses may be inaccurate. Do not use for medical emergencies.`

### Backend Disclaimer Enforcement
**File:** `api_server.py` (lines ~383-405)

```python
@app.post("/api/v4/agents/query")
async def agent_query(request: QueryRequest):
    result = await agent_orchestrator.route_query(request.query, {})
    
    # Add mandatory disclaimers
    domain = result.get("domain", "").lower()
    response_text = result.get("response", "")
    
    if domain == "healthcare":
        response_text += "\n\n🛑 DISCLAIMER: I am an AI, not a doctor. Please consult a local medical professional before making health decisions."
    elif domain == "agriculture":
        response_text += "\n\n🛑 DISCLAIMER: This is automated guidance. Verify with a local agricultural expert or KVK."
    
    result["response"] = response_text
    return result
```

---

## 🌍 PHASE 4: CLOUD DEPLOYMENT STEPS

### Option A: Deploy to Render

**1. Push to GitHub:**
```bash
git add .
git commit -m "Cloud deployment: compliance and env config"
git push origin main
```

**2. On Render Dashboard:**
- Click "New +" → "Web Service"
- Connect your GitHub repo
- Configure:
  - **Name:** rural-india-ai-beta
  - **Environment:** Python
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `uvicorn api_server:app --host 0.0.0.0 --port $PORT --workers 2`
  - **Plan:** Standard (or higher for more traffic)

**3. Set Environment Variables in Render:**
```
ENVIRONMENT=production
DEBUG=False
BETA_MODE=True
REQUIRE_CONSENT=True
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECRET_KEY=<generate-random-key>
MQTT_BROKER=<your-mqtt-server>
```

**4. Deploy:**
- Click "Create Web Service"
- Render builds and deploys automatically

**Access your app:**
- API: `https://rural-india-ai-beta-xxxxx.onrender.com`
- UI with Consent Modal: `https://rural-india-ai-beta-xxxxx.onrender.com/ui`
- API Docs: `https://rural-india-ai-beta-xxxxx.onrender.com/docs`

---

### Option B: Deploy to Railway

**1. Create `railway.json`:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api_server:app --host 0.0.0.0 --port $PORT --workers 2"
  }
}
```

**2. Install Railway CLI:**
```bash
npm install -g @railway/cli
```

**3. Deploy:**
```bash
railway login
railway link                    # Link to your project
railway up                      # Deploy changes
```

**4. Set Environment Variables:**
```bash
railway variables set ENVIRONMENT=production
railway variables set DEBUG=False
railway variables set BETA_MODE=True
railway variables set REQUIRE_CONSENT=True
railway variables set ALLOWED_ORIGINS=https://yourdomain.com
railway variables set SECRET_KEY=<generate-key>
railway variables set MQTT_BROKER=<your-mqtt>
```

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

- [ ] **API Health Check**
  ```bash
  curl https://your-domain.com/api/v1/health
  ```
  Should return 200 with system health

- [ ] **Consent Modal**
  Navigate to `https://your-domain.com/ui`
  - Modal appears and blocks content
  - Checkbox required to enable button
  - Consent saved to localStorage

- [ ] **Healthcare Disclaimer**
  ```bash
  curl -X POST https://your-domain.com/api/v4/agents/query \
    -H "Content-Type: application/json" \
    -d '{"query": "I have a fever", "language": "en"}'
  ```
  Response should include: `🛑 DISCLAIMER: I am an AI, not a doctor...`

- [ ] **Agriculture Disclaimer**
  ```bash
  curl -X POST https://your-domain.com/api/v4/agents/query \
    -H "Content-Type: application/json" \
    -d '{"query": "How to grow rice?", "language": "en"}'
  ```
  Response should include: `🛑 DISCLAIMER: This is automated guidance...`

- [ ] **Environment Variables**
  ```bash
  curl https://your-domain.com/api/v1/status | grep ENVIRONMENT
  ```

---

## 🔒 SECURITY BEST PRACTICES

1. **Never commit secrets:**
   ```bash
   # Already configured in .gitignore
   .env
   .env.local
   .env.production
   ```

2. **Use strong `SECRET_KEY`:**
   ```python
   openssl rand -hex 32  # Generate a secure key
   ```

3. **Enable HTTPS:**
   - Render and Railway auto-enable HTTPS
   - All secrets transmitted securely

4. **Rotate credentials regularly:**
   - Change `SECRET_KEY` quarterly
   - Regenerate MQTT passwords
   - Update API keys

5. **Monitor logs:**
   - On Render Dashboard: Logs tab
   - On Railway: Logs view
   - Check for errors and suspicious activity

---

## 📊 MONITORING & LOGS

### Render Logs
```
Render Dashboard → Select Service → Logs tab
```

### Railway Logs
```bash
railway logs -f  # Follow logs in real-time
```

### Key Metrics to Monitor
- **API Response Time:** Should be <500ms
- **Error Rate:** Should be <1%
- **CPU Usage:** Should stay <80%
- **Memory Usage:** Should stay <512MB

---

## 🐛 TROUBLESHOOTING

### Issue: "Port already in use"
**Solution:** The platform auto-sets the `PORT` env var. Use `$PORT` in your command.

```bash
# ✅ Correct
uvicorn api_server:app --host 0.0.0.0 --port $PORT

# ❌ Wrong
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Issue: "ModuleNotFoundError: No module named 'edge_node'"
**Solution:** Ensure `edge_node/` directory structure is correct and `requirements.txt` is up to date.

### Issue: "CORS Error when accessing from frontend"
**Solution:** Update `ALLOWED_ORIGINS` env var:
```
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,http://localhost:3000
```

### Issue: "Consent modal not appearing"
**Solution:** Make sure you're visiting `/ui` endpoint:
```
https://your-domain.com/ui  ✅ Shows modal
https://your-domain.com/    ❌ Shows JSON (API)
```

---

## 📁 File Structure After Deployment

```
rural-india-ai/
├── .env                          # (Local only, NEVER commit)
├── .env.example                  # (Template - safe to commit)
├── .gitignore                    # (Updated for cloud safety)
├── requirements.txt              # (Updated with python-dotenv)
├── Procfile                       # (New - deployment config)
├── render.yaml                    # (New - Render-specific)
├── api_server.py                  # (Updated - env vars + disclaimers)
├── index.html                     # (New - consent modal UI)
├── edge_node/                     # (All 6 phases)
│   ├── core/
│   ├── voice/
│   ├── rag/
│   ├── agents/
│   ├── safety/
│   └── observability/
├── data/
│   ├── queue.db                   # (In .gitignore)
│   └── vector_db.json             # (In .gitignore)
└── logs/                          # (In .gitignore)
```

---

## 🎯 BETA LAUNCH CHECKLIST

- [ ] All 5 legal disclosures in consent modal
- [ ] Consent modal blocks UI until accepted
- [ ] Healthcare responses include medical disclaimer
- [ ] Agriculture responses include agriculture disclaimer
- [ ] Environment variables configured on cloud platform
- [ ] `.env` file in `.gitignore`
- [ ] Database files (*.db, *.json) in `.gitignore`
- [ ] Logs directory in `.gitignore`
- [ ] Deployed to Render or Railway
- [ ] `/ui` endpoint accessible and showing consent modal
- [ ] `/api/v1/health` returning 200
- [ ] `/api/v4/agents/query` returning with disclaimers
- [ ] CORS headers set correctly for your domain
- [ ] Monitoring and logging enabled

---

## 📞 Support

**For deployment issues:**
- Render Support: https://render.com/help
- Railway Support: https://railway.app/support
- GitHub Issues: Link to your repository

**For compliance questions:**
- Consult legal team before launch
- Ensure all disclaimers are clear and visible
- Plan terms of service updates

---

## Version History

- **v1.0.0** (March 29, 2026) - Initial beta release
  - 6 AI phases complete
  - Mandatory consent modal
  - Healthcare & Agriculture disclaimers
  - Cloud deployment ready

---

**Last Updated:** March 29, 2026  
**Status:** Ready for Beta Launch 🚀
