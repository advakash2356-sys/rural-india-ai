# 🚀 Personal Server Deployment Guide

## Quick Start for MacBook & Linux Servers

Your Rural India AI system is ready for deployment on your personal infrastructure.

---

## 📦 Option 1: Deploy to MacBook (Development/Testing)

```bash
cd rural-india-ai
chmod +x deploy_to_macbook.sh
./deploy_to_macbook.sh

# Then activate and run
source venv/bin/activate
python3 api_server.py
```

**Time**: ~3 minutes  
**Requirements**: Homebrew (auto-installed)  
**Result**: API running at http://127.0.0.1:8000

---

## 📦 Option 2: Deploy to Linux Server

### Local Linux System
```bash
cd rural-india-ai
chmod +x deploy_to_linux.sh
sudo ./deploy_to_linux.sh localhost /opt/rural-india-ai

# Service runs automatically
sudo systemctl status rural-india-ai
```

### Remote Linux Server (VPS/Dedicated)
```bash
cd rural-india-ai
chmod +x deploy_to_linux.sh
./deploy_to_linux.sh user@your-server.com /opt/rural-india-ai

# SSH and verify
ssh user@your-server.com
sudo systemctl status rural-india-ai
```

**Time**: ~5 minutes  
**Requirements**: Ubuntu 20.04+ or Debian 10+  
**Result**: API running at http://your-server.com:8000

---

## 📦 Option 3: Docker Deployment (Any Platform)

```bash
# Build
docker build -t rural-india-ai:latest .

# Run
docker run -p 8000:8000 -v $(pwd)/data:/app/data rural-india-ai:latest

# Or use compose
docker-compose up -d
```

**Time**: ~2 minutes  
**Requirements**: Docker installed  
**Result**: API running at http://localhost:8000

---

## ✅ After Deployment

### Test the System
```bash
# API health check
curl http://your-server:8000/api/v1/health

# Run complete demo
python3 complete_demo.py

# Use CLI tool
python3 cli.py query "Your question" --language=hi
```

### Access Dashboard
- Open `dashboard.html` in your browser
- Shows real-time metrics, query interface, analytics

### System Status
```bash
# MacBook
source venv/bin/activate
python3 cli.py health

# Linux (systemd)
sudo systemctl status rural-india-ai
journalctl -u rural-india-ai -f
```

---

## 🔧 Configuration

All systems share same config:
- **API Port**: 8000 (configurable)
- **Data Path**: ./data/
- **Log Path**: ./logs/
- **Languages**: 9 Indic languages + English
- **Startup Time**: ~2 seconds
- **Memory**: 150-200MB base, 400MB peak

---

## 📡 Networking

### MacBook (Local)
```
Accessible from: localhost:8000, 127.0.0.1:8000
```

### Linux Server (Local Network)
```
Find IP: hostname -I
Other machines: http://<server-ip>:8000
```

### Linux Server (Public/Internet)
```
Configure firewall: sudo ufw allow 8000
Access from anywhere: http://your-domain.com:8000
Recommend: Use reverse proxy (nginx) + SSL certificate
```

---

## 🛠️ Common Tasks

### Change API Port
```bash
# Edit config.json or environment variable
export API_PORT=8001
python3 api_server.py
```

### Enable SSL/HTTPS
```bash
# Option 1: Use nginx reverse proxy
# Option 2: Configure uvicorn with SSL
# See DEPLOYMENT_MACBOOK_LINUX.md for details
```

### Backup Data
```bash
./backup.sh
# Auto-daily backup configured on Linux systemd
```

### View Logs
```bash
# MacBook
tail -f logs/api.log

# Linux (systemd)
journalctl -u rural-india-ai -f
```

### Update Code
```bash
# Pull latest
git pull origin main

# Restart service
systemctl restart rural-india-ai  # Linux
# Or kill and restart: Ctrl+C then python3 api_server.py
```

---

## 📊 What You Get

✅ **All 6 Phases Operational**
- Edge Infrastructure (hardware monitoring, model management)
- Voice Processing (9 languages, STT/TTS)
- Vector Database (semantic search, RAG)
- Domain Agents (agriculture, healthcare, education)
- Safety Guardrails (content filtering, bias detection)
- Observability (metrics, analytics, dashboards)

✅ **REST API** (28+ endpoints)

✅ **Web Dashboard** (real-time metrics, query interface)

✅ **CLI Tool** (command-line access)

✅ **Production Ready** (error handling, logging, systemd service)

---

## 🚀 Next Steps

1. **Choose deployment method** (MacBook, Linux, or Docker)
2. **Run deployment script** (3-5 minutes)
3. **Test system** (verify all 6 phases operational)
4. **Configure networking** (expose to other machines if needed)
5. **Enable auto-restart** (systemd on Linux, LaunchAgent on Mac)
6. **Monitor logs** (ensure healthy operation)

---

## 📝 Full Documentation

See [DEPLOYMENT_MACBOOK_LINUX.md](DEPLOYMENT_MACBOOK_LINUX.md) for:
- Detailed setup instructions
- Configuration options
- Monitoring & logging
- Performance tuning
- Troubleshooting
- Scaling options

---

**System Status**: All 6 phases complete and verified ✅  
**Ready for**: Production deployment ✅  
**Support**: See deployment guide for troubleshooting  
