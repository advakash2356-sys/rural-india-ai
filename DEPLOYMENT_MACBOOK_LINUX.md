# Deployment Guide - MacBook & Linux Server

## Rural India AI - Complete System Deployment

All 6 phases + REST API + Web Dashboard + CLI Tools

---

## 🎯 Deployment Targets

- **MacBook** (local development & testing)
- **Linux Server** (Ubuntu/Debian - VPS, self-hosted, or local)
- **Docker** (any platform)

---

## ⚡ Quick Start (Local MacBook)

### 1. One-Line Setup
```bash
chmod +x deploy_to_macbook.sh
./deploy_to_macbook.sh
source venv/bin/activate
python3 api_server.py
```

### 2. Access the System
- **API**: http://127.0.0.1:8000
- **Dashboard**: Open `dashboard.html` in browser
- **CLI**: `python3 cli.py query "Your question"`

---

## 🖥️ MacBook Deployment

### Prerequisites
- macOS 10.15 or later
- Homebrew (auto-installed if missing)
- 2GB free disk space
- 4GB RAM recommended

### Full Setup Steps

```bash
# 1. Clone or download the project
cd path/to/rural-india-ai

# 2. Run deployment script
chmod +x deploy_to_macbook.sh
./deploy_to_macbook.sh

# 3. Activate environment
source venv/bin/activate

# 4. Verify installation
python3 -c "import edge_node; print('✅ Edge node imported successfully')"

# 5. Start the API server
python3 api_server.py

# 6. In another terminal, test the system
python3 cli.py health

# 7. Open dashboard
open dashboard.html
```

### Manual Installation (if script fails)

```bash
# Install Python 3.9+
brew install python3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/metrics data/backups logs

# Start API
python3 api_server.py
```

### Running as Background Service (macOS)

Create `~/Library/LaunchAgents/com.ruralaiai.service.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ruralaiai.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python3</string>
        <string>/path/to/api_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/rural-ai.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/rural-ai-error.log</string>
    <key>WorkingDirectory</key>
    <string>/path/to/app</string>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.ruralaiai.service.plist
launchctl status com.ruralaiai.service
```

---

## 🐧 Linux Server Deployment

### Prerequisites
- Ubuntu 20.04+ or Debian 10+
- SSH access to server
- 2GB free disk space
- 4GB RAM recommended
- Python 3.9+

### Local Linux System

```bash
# 1. Make script executable
chmod +x deploy_to_linux.sh

# 2. Deploy to local system
sudo ./deploy_to_linux.sh localhost /opt/rural-india-ai

# 3. Enable and start service
sudo systemctl enable rural-india-ai
sudo systemctl start rural-india-ai

# 4. Check status
sudo systemctl status rural-india-ai

# 5. View logs
journalctl -u rural-india-ai -f
```

### Remote Linux Server

```bash
# 1. From your MacBook/local machine
chmod +x deploy_to_linux.sh

# 2. Deploy to remote server (via rsync + SSH)
./deploy_to_linux.sh user@your-server.com /opt/rural-india-ai

# 3. SSH into server and enable service
ssh user@your-server.com
sudo systemctl enable rural-india-ai
sudo systemctl start rural-india-ai

# 4. Check status
sudo systemctl status rural-india-ai

# 5. Verify API is running
curl http://your-server.com:8000/api/v1/health
```

### Manual Setup on Linux

```bash
# 1. SSH to server
ssh user@your-server.com

# 2. Install dependencies
sudo apt-get update
sudo apt-get install -y python3.9 python3-pip python3-venv \
    python3-dev build-essential git curl wget

# 3. Create app directory
sudo mkdir -p /opt/rural-india-ai
sudo chown -R $USER:$USER /opt/rural-india-ai
cd /opt/rural-india-ai

# 4. Copy your project files
# (via scp, git clone, or rsync)

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# 7. Run API server
python3 api_server.py &
```

### Systemd Service Management

```bash
# Start service
sudo systemctl start rural-india-ai

# Stop service
sudo systemctl stop rural-india-ai

# Restart service
sudo systemctl restart rural-india-ai

# View real-time logs
journalctl -u rural-india-ai -f

# View last 100 lines
journalctl -u rural-india-ai -n 100

# Enable on boot
sudo systemctl enable rural-india-ai

# Disable on boot
sudo systemctl disable rural-india-ai
```

---

## 🐳 Docker Deployment (All Platforms)

### Build and Run

```bash
# 1. Build image
docker build -t rural-india-ai:latest .

# 2. Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data rural-india-ai:latest

# 3. Access
curl http://localhost:8000/api/v1/health
```

### Using Docker Compose

```bash
# 1. Start all services
docker-compose up -d

# 2. Check logs
docker-compose logs -f

# 3. Stop services
docker-compose down

# 4. View running containers
docker ps
```

### Production Docker Deployment

```bash
# 1. Push to registry
docker tag rural-india-ai:latest your-registry/rural-india-ai:latest
docker push your-registry/rural-india-ai:latest

# 2. Pull on server
docker pull your-registry/rural-india-ai:latest

# 3. Run with volume mounts
docker run -d \
  --name rural-ai \
  -p 8000:8000 \
  -v /var/rural-ai/data:/app/data \
  -v /var/rural-ai/logs:/app/logs \
  --restart always \
  your-registry/rural-india-ai:latest

# 4. View logs
docker logs -f rural-ai
```

---

## 📋 REST API Endpoints

### Health & Status
- `GET /api/v1/health` - System health check
- `GET /api/v1/status` - Detailed system status

### Phase 1: Edge Infrastructure
- `GET /api/v1/phase1/hardware` - Hardware metrics (CPU, memory, temperature)
- `GET /api/v1/phase1/power` - Power status (battery, solar)
- `GET /api/v1/phase1/models` - Loaded models

### Phase 2: Voice Interface
- `POST /api/v1/phase2/transcribe` - Speech-to-text
- `POST /api/v1/phase2/synthesize` - Text-to-speech
- `GET /api/v1/phase2/languages` - Available languages

### Phase 3: Vector Database
- `POST /api/v1/phase3/search` - Semantic search
- `POST /api/v1/phase3/index` - Index documents
- `GET /api/v1/phase3/stats` - Database statistics

### Phase 4: Domain Agents
- `POST /api/v1/phase4/query` - Query domain agents
- `GET /api/v1/phase4/agents` - List active agents
- `POST /api/v1/phase4/route` - Route query to agent

### Phase 5: Safety Guardrails
- `POST /api/v1/phase5/check` - Check for harmful content
- `GET /api/v1/phase5/status` - Safety system status

### Phase 6: Observability
- `GET /api/v1/phase6/analytics` - Usage analytics
- `GET /api/v1/phase6/metrics` - System metrics
- `GET /api/v1/phase6/dashboard` - Dashboard data

---

## 🛠️ CLI Tool Usage

```bash
# Health check
python3 cli.py health

# Query in English
python3 cli.py query "What should I plant in spring?"

# Query in Hindi
python3 cli.py query "मेरी खेती में कीड़े हैं" --language=hi

# Query in Telugu
python3 cli.py query "నా పంటకు సరైన ఎరువు ఏది?" --language=te

# List available languages
python3 cli.py languages

# Search documents
python3 cli.py search "irrigation methods"

# Check safety
python3 cli.py safety-check "User query"

# View analytics
python3 cli.py analytics

# List agents
python3 cli.py agents
```

---

## 🔒 Environment Configuration

Create `.env` file for custom configuration:

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
DATA_PATH=./data
BACKUP_PATH=./data/backups

# Logging
LOG_LEVEL=INFO
LOG_PATH=./logs

# Models
MODEL_PATH=./models
WHISPER_MODEL_SIZE=tiny

# Languages
ENABLED_LANGUAGES=en,hi,te,ta,kn,ml,mr,bn,gu
DEFAULT_LANGUAGE=en
```

Load with:
```bash
export $(cat .env | xargs)
python3 api_server.py
```

---

## 📊 Monitoring & Logs

### MacBook
```bash
# View API logs
tail -f logs/api.log

# View system logs (if running via plist)
log stream --predicate 'process == "python3"' --level debug
```

### Linux
```bash
# View systemd service logs
journalctl -u rural-india-ai -f

# View system resource usage
top -p $(pgrep -f api_server.py)

# Monitor disk usage
df -h
```

### Docker
```bash
# View container logs
docker logs -f rural-ai

# Access container shell
docker exec -it rural-ai /bin/bash

# Monitor container resources
docker stats rural-ai
```

---

## ⚙️ Performance Tuning

### MacBook

```bash
# Increase file descriptor limit
ulimit -n 4096

# Run with multiple workers
python3 api_server.py --workers 4
```

### Linux with Systemd

Edit `/etc/systemd/system/rural-india-ai.service`:

```ini
Service]
ExecStart=/path/to/venv/bin/python3 -u /path/to/api_server.py
Environment="PYTHONUNBUFFERED=1"
LimitNOFILE=4096
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart rural-india-ai
```

### Docker

```bash
docker run -d \
  --name rural-ai \
  --memory=2g \
  --cpus=2 \
  -p 8000:8000 \
  rural-india-ai:latest
```

---

## 🚨 Troubleshooting

### Python Version Mismatch
```bash
# Ensure Python 3.9+
python3 --version

# Use specific Python version
python3.9 -m venv venv
source venv/bin/activate
```

### Module Import Errors
```bash
# Verify edge_node module
python3 -c "import edge_node; print(edge_node.__path__)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process (macOS/Linux)
kill -9 <PID>

# Or use different port
python3 api_server.py --port 8001
```

### Audio/Voice Issues
```bash
# These are optional - system works without audio
# If needed, install manually:
pip install librosa soundfile scipy

# For macOS M1/M2 if audio fails:
# Use Docker which has pre-configured audio support
```

---

## 📈 Scaling & Optimization

### Single Server to Multiple Servers
1. Set up load balancer (nginx/haproxy)
2. Deploy to multiple Linux servers behind load balancer
3. Use shared database (PostgreSQL) instead of SQLite
4. Configure MQTT broker for inter-node communication

### Add Redis for Caching
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Linux

# Update requirements.txt
echo "redis==4.5.0" >> requirements.txt

# Configure in api_server.py for caching
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] API responds to health check
- [ ] Dashboard loads in browser
- [ ] CLI tool can query system
- [ ] All 6 phases operational
- [ ] Logs are being generated
- [ ] Data directory has proper permissions
- [ ] Service auto-restarts on failure
- [ ] Can handle simultaneous requests

```bash
# Run verification script
python3 complete_demo.py
```

Expected output:
```
✅ Phase 1: Edge Infrastructure | CPU: XX%
✅ Phase 2: Voice Interface | Languages: 9
✅ Phase 3: Vector Database | Status: Ready
✅ Phase 4: Domain Agents | Count: 3
✅ Phase 5: Safety Guardrails | Safety: safe
✅ Phase 6: Observability | Status: Ready

RESULTS: 6/6 tests passed
🎉 ALL SYSTEMS OPERATIONAL - PRODUCTION READY
```

---

## 📚 Additional Resources

- **API Documentation**: `/api/v1/docs` (Swagger UI)
- **Project Structure**: See README.md
- **Configuration**: config.json
- **Models**: models/ directory
- **Data**: data/ directory
- **Logs**: logs/ directory

---

## 🆘 Support

For issues:
1. Check logs: `journalctl -u rural-india-ai -f` or tail logs/
2. Run verification: `python3 complete_demo.py`
3. Check system resources: `top` or `docker stats`
4. Verify Python version: `python3 --version`
5. Reinstall dependencies: `pip install --force-reinstall -r requirements.txt`

---

**Last Updated**: March 2026
**Tested On**: macOS 13+, Ubuntu 20.04+, Debian 11+
**Python**: 3.9+
