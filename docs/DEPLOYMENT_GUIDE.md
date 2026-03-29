# Deployment Guide - Phase 1

## Target Hardware

- **Raspberry Pi 5** (4GB or 8GB RAM)
- **Solar Panel Array** (400W recommended for rural village)
- **LiFePO4 Battery Pack** (100Ah @ 9.6V = 960 Wh)
- **MPPT Charge Controller** (100A for solar regulation)
- **Cellular/WiFi Modem** (4G/3G/2G backup, or WiFi for local)
- **Fanless Aluminum Enclosure** (thermal + dust protection)
- **UPS/Battery Management System**

## Installation Steps

### 1. Prepare Raspberry Pi 5

```bash
# Download Alpine Linux ARM image
wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/aarch64/alpine-3.18.4-aarch64.iso

# Flash to microSD card (use Balena Etcher or dd)
sudo dd if=alpine-3.18.4-aarch64.iso of=/dev/sdb bs=4M status=progress

# Boot and login (default: root, no password)
# Run setup
setup-alpine
# Select: keyboard, hostname, interface, hostname, timezone, NTP, etc.
```

### 2. Install Dependencies

```bash
# Update package list
apk update && apk upgrade

# Install core dependencies
apk add python3 py3-pip py3-psutil py3-asyncio
apk add gcc musl-dev linux-headers openssl-dev
apk add sqlite
```

### 3. Deploy Rural AI Edge Node

```bash
# Create application directory
mkdir -p /opt/rural-ai-edge
cd /opt/rural-ai-edge

# Clone or extract source
git clone https://github.com/your-org/rural-india-ai.git .
# OR: extract tarball

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --no-cache-dir -r requirements.txt

# Create data directories
mkdir -p data/{models,queue,state}

# Download quantized models
# (Download pre-quantized GGUF files to ./models/)
wget https://your-model-repo/sarvam-2b-indic-q4.gguf -O models/

# Configure for your village
cp deployment/example_village_config.json config/edge_config.json
# Edit config/edge_config.json with village details
```

### 4. Hardware Integration

```bash
# Install power monitoring
apk add py3-pid py3-gpio
# Create /opt/rural-ai-edge/config/hardware_config.ini

# Configure solar/battery monitoring via GPIO/ADC
# (Implementation depends on specific hardware)

# Configure cellular modem (e.g., Quectel RG500)
# Install driver + udev rules
```

### 5. Enable Auto-start Service

**Option A: OpenRC (Alpine default)**

```bash
cat > /etc/init.d/rural-ai-edge << 'EOF'
#!/sbin/openrc-run
description="Rural India AI Edge Node"
supervisor="supervise-daemon"
command="/opt/rural-ai-edge/venv/bin/python3"
command_args="/opt/rural-ai-edge/main.py"
command_user="root"
pidfile="/var/run/rural-ai-edge.pid"
respawn_delay=5
depend() {
    need localmount
    after bootmisc networking
}
EOF

chmod +x /etc/init.d/rural-ai-edge
rc-update add rural-ai-edge default
rc-service rural-ai-edge start
```

**Option B: Systemd (if using non-Alpine)**

```bash
cat > /etc/systemd/system/rural-ai-edge.service << 'EOF'
[Unit]
Description=Rural India AI Edge Node
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rural-ai-edge
ExecStart=/opt/rural-ai-edge/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rural-ai-edge
systemctl start rural-ai-edge
```

### 6. Configure MQTT Broker Connection

```json
// config/edge_config.json
{
  "mqtt_broker": "your-cloud-domain.com",
  "mqtt_port": 1883,
  "mqtt_username": "edge_001",
  "mqtt_password": "SECURE_PASSWORD_HERE"
}
```

## Testing & Validation

### 1. Health Check

```bash
curl http://localhost:8000/health
# Should return JSON status
```

### 2. Local Inference Test

```bash
curl -X POST http://localhost:8000/infer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "मेरी गेहूं की फसल में बीमारी है",
    "context": {"crop": "wheat"}
  }'
```

### 3. Queue Test

```bash
curl -X POST http://localhost:8000/queue \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "PM_KISAN_CHECK",
    "data": {"user_id": "test_123"},
    "priority": 1
  }'

# Check queue status
curl http://localhost:8000/queue/status
```

### 4. Monitor Logs

```bash
# Real-time log monitoring
tail -f /var/log/rural-ai-edge.log

# Or via Syslog
rc-service syslog start  # Alpine syslog daemon
```

## Monitoring Dashboard (Optional)

One-line HTML dashboard for Gram Panchayat leadership:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Rural AI Node - Monitoring</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial; margin: 20px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; }
        .ok { background-color: #90EE90; }
        .warning { background-color: #FFD700; }
        .error { background-color: #FF6B6B; }
    </style>
</head>
<body>
    <h1>Edge Node Status - मेरा गांव AI</h1>
    <div id="status"></div>
    <script>
        fetch('/health')
            .then(r => r.json())
            .then(d => {
                let html = `
                    <div class="metric ok">
                        <b>CPU:</b> ${d.hardware.cpu_percent}%
                    </div>
                    <div class="metric ok">
                        <b>Memory:</b> ${d.hardware.memory_percent}%
                    </div>
                    <div class="metric ok">
                        <b>Temperature:</b> ${d.hardware.temperature_celsius}°C
                    </div>
                    <div class="metric ok">
                        <b>Battery:</b> ${d.power.battery_percent}%
                    </div>
                    <div class="metric ok">
                        <b>Pending Tasks:</b> ${d.queue.pending}
                    </div>
                `;
                document.getElementById('status').innerHTML = html;
            });
    </script>
</body>
</html>
```

## Troubleshooting

### Issue: Edge node won't boot after power loss

**Solution:**
```bash
# Check filesystem integrity
fsck /dev/sda1

# Verify state files not corrupted
sqlite3 data/queue.db "PRAGMA integrity_check;"

# Restore from backup if needed
cp data/state/node_state.json data/state/node_state.json.bak
```

### Issue: High CPU (>80%) constantly

**Solution:**
1. Check running processes: `top -d 1`
2. Profile Python: `python3 -m cProfile -s cumtime main.py`
3. Reduce model size or inference batch size
4. Monitor ambient temperature (may be throttled)

### Issue: MQTT not connecting (offline)

**Solution:**
```bash
# Test connectivity
ping 8.8.8.8  # Check internet
nc -zv mqtt-broker.com 1883  # Check MQTT port

# Monitor queue (should still work locally)
curl http://localhost:8000/queue/status

# Requests will queue locally and sync when connectivity returns
```

### Issue: Battery draining faster than solar charges

**Solution:**
1. Monitor solar panel output: `cat /sys/class/hwmon/*/in0_input` / 1000
2. Check if thermal throttling causing long inference times
3. Reduce sync frequency in config (increase mqtt_sync_interval)
4. Enable low-power mode manually: `edge_node.power_manager.set_power_mode("low_power")`
5. Switch to even smaller model if available

## Performance Tuning

### 1. Model Selection Trade-offs

```
Faster Inference:
- Sarvam 1B (not available yet)
- MobileBERT for intent only
- Quantize to q2_K (loses some accuracy)

Better Accuracy:
- Sarvam 2B (default)
- Llama-3 8B (requires 8GB Pi)
- Quantize to q5 or q6 (uses more memory)
```

### 2. Memory Optimization

```bash
# Check current memory usage
ps aux | grep python3 | awk '{print $6}'

# Limit Python heap if needed
export PYTHONHASHSEED=0
python3 -X dev main.py  # Check for warnings
```

### 3. Network Optimization

```bash
# Reduce MQTT QoS if bandwidth critical (less reliable)
# MQTT_QOS=1 python3 main.py

# Batch telemetry to compress (already done daily)
# Reduce sync frequency if power constrained
```

## Long-term Maintenance

### Weekly Tasks
- [ ] Monitor health dashboard
- [ ] Check battery charge cycles
- [ ] Review temperature logs

### Monthly Tasks
- [ ] Validate queue is syncing properly
- [ ] Check free disk space (rotate old queue backups)
- [ ] Update time via NTP

### Quarterly
- [ ] Download latest models from cloud
- [ ] Check for security updates: `apk update && apk upgrade`
- [ ] Inspect for dust/damage in enclosure

## Scaling to Multiple Villages

For NGOs/governments deploying across multiple villages:

```bash
# 1. Create village-specific config
./scripts/generate_village_config.py \
  --state "Uttar Pradesh" \
  --district "Lucknow" \
  --gp_name "Example Village" \
  --lat 26.8467 --lon 80.9462

# 2. Pre-download models to fleet USB drives
./scripts/download_models.sh ./fleet_models_usb/

# 3. Deploy to each village
# Copy via USB → pip install → customize config

# 4. Register with cloud dashboard
curl -X POST https://cloud.example.com/register \
  -d @config/edge_config.json
```

## Next Steps

Once Phase 1 is stable:
1. Deploy Phase 2 (Voice UI) - WhatsApp integration
2. Add Phase 3 components (Local Vector DB)
3. Integrate with government systems (NREGA, PM-Kisan, etc.)
