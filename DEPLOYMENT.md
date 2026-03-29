# Deployment & Integration Guide

## Complete Rural India AI System
All 6 phases + REST API + Deployment tools + Web Dashboard

---

## 📋 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python3 api_server.py

# In another terminal, use CLI tool
python3 cli.py query "Meri kheti mein kide hain" --language=hi

# Open dashboard
open dashboard.html
```

### Make scripts executable
```bash
chmod +x setup_pi.sh deploy_to_pi.sh backup.sh cli.py
```

---

## 🚀 Deployment Options

### Option 1: Docker (Recommended)

```bash
# Build image
docker build -t rural-india-ai:latest .

# Run container
docker run -p 8000:8000 -v $(pwd)/data:/app/data rural-india-ai:latest

# Or use docker-compose
docker-compose up -d

# Access
curl http://localhost:8000/api/v1/health
```

### Option 2: Raspberry Pi 5 Direct

```bash
# SSH into Pi
ssh pi@<pi_ip>

# Download the setup script
wget https://your-repo/setup_pi.sh
chmod +x setup_pi.sh

# Run setup (installs dependencies, enables I2C/SPI, creates service)
./setup_pi.sh

# Start service
sudo systemctl start rural-india-ai
sudo systemctl status rural-india-ai
```

### Option 3: Remote Deployment

```bash
# Deploy to Pi from your machine
./deploy_to_pi.sh 192.168.1.100 pi

# Verify
curl http://192.168.1.100:8000/api/v1/health
```

---

## 📡 REST API Endpoints

### Phase 1: Edge Node (v1)
```
GET  /api/v1/health        # System health
GET  /api/v1/status        # Detailed status
GET  /api/v1/hardware      # Hardware metrics
GET  /api/v1/power         # Power status
POST /api/v1/sync          # Trigger request sync
```

### Phase 2: Voice (v2)
```
POST /api/v2/query           # Process text query
POST /api/v2/voice           # Voice interaction
GET  /api/v2/languages       # Supported languages
POST /api/v2/language        # Switch language
```

### Phase 3: Vector DB (v3)
```
POST /api/v3/documents    # Add document
POST /api/v3/search       # Search documents
GET  /api/v3/stats        # DB statistics
```

### Phase 4: Domain Agents (v4)
```
POST /api/v4/agents/query # Query agents
GET  /api/v4/agents       # List agents
```

### Phase 5: Safety (v5)
```
POST /api/v5/safety/check # Check safety
POST /api/v5/trust/score  # Trust score
```

### Phase 6: Observability (v6)
```
GET /api/v6/dashboard    # Dashboard data
GET /api/v6/metrics      # Metrics
GET /api/v6/analytics    # Analytics
GET /api/v6/health       # Component health
GET /api/v6/export/metrics # Export metrics
```

---

## 🖥️ Dashboard & CLI

### Web Dashboard
1. Open `dashboard.html` in browser
2. Select language and ask questions
3. View real-time metrics and health
4. Search documents
5. Monitor agent performance

### CLI Tool
```bash
# Health check
./cli.py health

# System status
./cli.py status

# Hardware metrics
./cli.py hardware

# Ask question
./cli.py query "My crop is affected by pests" --language=en
./cli.py query "मेरी फसल कीटों से प्रभावित है" --language=hi

# List agents
./cli.py agents

# Search
./cli.py search "irrigation methods"

# Check safety
./cli.py safety-check "some text"

# View dashboard
./cli.py dashboard

# Analytics
./cli.py analytics

# Change API URL
./cli.py --api-url=http://192.168.1.100:8000 status
```

---

## 🔧 Configuration

### Environment Variables
```bash
EDGE_MODE=production              # or 'development'
API_HOST=0.0.0.0                 # API bind address
API_PORT=8000                    # API port
MQTT_BROKER=mqtt.example.com     # MQTT broker
MQTT_PORT=1883                   # MQTT port
LOG_LEVEL=INFO                   # Logging level
```

### Hardware Monitoring
- CPU/Memory/Temp thresholds in `edge_node/config/settings.py`
- Power management in `edge_node/hardware/power.py`
- I2C/SPI sensor configuration

### Vector Database
- Embedding dimension: 384 (configurable)
- Persistence: SQLite in `data/vector_db/`
- Search: Cosine similarity

### Domain Agents
- Agriculture: crop advice, irrigation, pest control
- Healthcare: remedies, hygiene, disease prevention
- Education: study tips, subjects, learning resources

### Safety System
- Harmful content filtering
- Bias detection (gender, caste, religion)
- Trust scoring system

---

## 📊 Monitoring

### Metrics Collection
- Inference latency per query
- Request processing time
- Component health status
- Usage analytics by language

### Access Metrics
```bash
# Via API
curl http://localhost:8000/api/v6/metrics

# Via CLI
./cli.py analytics

# Export JSON
curl http://localhost:8000/api/v6/export/metrics > metrics.json

# Prometheus (if enabled)
curl http://localhost:9090
```

### Logs
```bash
# Systemd logs
sudo journalctl -u rural-india-ai -f

# Application logs
tail -f data/logs/rural-india-ai.log

# Docker logs
docker logs -f rural-india-ai
```

---

## 🔄 Backup & Restore

### Automatic Backups
Backups run daily at 3 AM via cron (set up by `setup_pi.sh`)

```bash
# Manual backup
./backup.sh

# Backups stored in
ls ~/rural-india-ai/backups/
```

### Restore
```bash
cd ~/rural-india-ai

# Extract latest backup
tar -xzf backups/rural-india-ai_backup_LATEST.tar.gz

# Restart service
sudo systemctl restart rural-india-ai
```

---

## 🔗 Integration with External Services

### MQTT Integration
- Edge node connects to MQTT broker
- Store-and-forward for offline scenarios
- QoS 2 guaranteed delivery

### API Integration
```bash
# Example: Call from external service
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How to irrigate my field?", "language": "hi", "use_rag": true}'
```

### Webhook Integration
Setup webhooks in `edge_node/core/orchestrator.py` for event notifications

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process
kill -9 <PID>

# Check logs
python3 api_server.py  # Run directly for debugging
```

### Vector DB errors
```bash
# Reset database
rm -rf data/vector_db/

# Reinitialize
python3 -c "from edge_node.rag.vector_db import VectorDatabase; VectorDatabase()"
```

### Voice service issues
```bash
# Check audio devices
python3 -c "import sounddevice; print(sounddevice.query_devices())"

# Test Whisper
python3 -c "import whisper; whisper.load_model('tiny')"
```

### MQTT connectivity
```bash
# Test MQTT connection
python3 -c "from edge_node.networking.mqtt_client import MQTTClient; 
client = MQTTClient(); 
print('Connected' if client.connect() else 'Failed')"
```

---

## 📈 Performance Optimization

### For Raspberry Pi
1. Use CPU frequency scaling
2. Disable unused services
3. Use lightweight models (Whisper 'tiny')
4. Enable swap for large operations
5. Use vector index caching

### For Edge Deployment
1. Minimize latency: Keep queries under 100ms
2. Optimize memory: Background cleanup every hour
3. Prioritize local processing: Minimize cloud calls
4. Cache embeddings: Reuse computed vectors
5. Batch operations: Group requests for efficiency

---

## 🧪 Testing

### Unit Tests
```bash
python3 -m pytest tests/ -v
```

### Integration Test
```bash
python3 complete_demo.py
```

### Load Testing
```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:8000/api/v1/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/api/v1/health
```

### Voice Testing
```bash
# Record test audio
sox -r 16000 -b 16 -c 1 -e signed-integer | sox - test.wav

# Test STT
python3 -c "from edge_node.voice.speech_to_text import WhisperSTT;
stt = WhisperSTT('tiny')
print(stt.transcribe('test.wav'))"
```

---

## 📚 Architecture

### System Components
```
┌─────────────────────────────────────────┐
│         REST API Server (FastAPI)       │
│              Port 8000                  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────────────────────────────────┐
       │                                            │
       ▼                                            ▼
  ┌─────────────┐                          ┌──────────────┐
  │  Phase 1-6  │                          │  Voice I/O   │
  │ Modules     │                          │  Audio       │
  └─────────────┘                          └──────────────┘
       │
   ┌───┴─────────────┬─────────────┬──────────────┬──────────┐
   │                 │             │              │          │
   ▼                 ▼             ▼              ▼          ▼
┌────────┐    ┌──────────┐   ┌─────────┐   ┌─────────┐  ┌────────┐
│Orchest │    │Hardware  │   │MQTT     │   │Models   │  │RQ      │
│rator  │    │Monitor   │   │Client   │   │Manager  │  │Queue   │
└────────┘    └──────────┘   └─────────┘   └─────────┘  └────────┘
   │
   └─────────────────────────────────────────┐
                                            │
                                 ┌──────────┴──────────┐
                                 │                     │
                                 ▼                     ▼
                         ┌─────────────┐        ┌──────────────┐
                         │SQLite DB    │        │File System   │
                         │Vector DB    │        │Models, Logs  │
                         └─────────────┘        └──────────────┘
```

---

## 📞 Support

For issues, check:
1. Logs: `data/logs/rural-india-ai.log`
2. Health endpoint: `GET /api/v1/health`
3. CLI diagnostics: `./cli.py status`
4. Dashboard: `dashboard.html`

---

## 🎯 Next Steps

1. **Deploy to Raspberry Pi**: Use `deploy_to_pi.sh`
2. **Add Vector Documents**: Use `/api/v3/documents`
3. **Monitor via Dashboard**: Open `dashboard.html`
4. **Configure MQTT**: Update settings for cloud sync
5. **Setup Monitoring**: Enable Prometheus+Grafana
6. **Scale to Multiple Nodes**: Implement node clustering

---

## 📄 License

Rural India AI - Open Source for Rural Development

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Deployment Status**: ✅ Production Ready
