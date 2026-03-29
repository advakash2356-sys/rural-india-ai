#!/bin/bash
# Alpine Linux (for fanless, minimal footprint) deployment script

set -e

echo "Rural India AI Edge Node - Raspberry Pi 5 Deployment"
echo "====================================================="

# Update system
apk update && apk upgrade

# Install Python and build tools
apk add python3 py3-pip py3-psutil py3-asyncio
apk add gcc musl-dev linux-headers

# Create application directory
mkdir -p /opt/rural-ai-edge
cd /opt/rural-ai-edge

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt

# Create data directories
mkdir -p ./data/{models,queue,state}

# Create systemd service
cat > /etc/init.d/rural-ai-edge << 'EOF'
#!/sbin/openrc-run

description="Rural India AI Edge Node Service"
supervisor="supervise-daemon"
command="/usr/bin/python3"
command_args="/opt/rural-ai-edge/main.py"
command_user="root"

pidfile="/var/run/rural-ai-edge.pid"
respawn_delay=5
respawn_max=0

depend() {
    need localmount
    after bootmisc
}

start_pre() {
    mkdir -p /var/run/
}
EOF

chmod +x /etc/init.d/rural-ai-edge

echo "✓ Installation complete"
echo "Start service: rc-service rural-ai-edge start"
echo "View logs: tail -f /var/log/rural-ai-edge.log"
