#!/bin/bash

# Deploy Rural India AI to Raspberry Pi 5
# Usage: ./deploy_to_pi.sh <pi_ip> <pi_user>

PI_IP=${1:-"192.168.1.100"}
PI_USER=${2:-"pi"}
PI_HOME="/home/$PI_USER"
PI_APP_DIR="$PI_HOME/rural-india-ai"

echo "🚀 Deploying Rural India AI to Raspberry Pi 5 @ $PI_IP"

# Step 1: Create app directory
echo "📁 Creating app directory..."
ssh $PI_USER@$PI_IP "mkdir -p $PI_APP_DIR"

# Step 2: Transfer code
echo "📤 Uploading code..."
rsync -avz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='data/metrics' \
  . $PI_USER@$PI_IP:$PI_APP_DIR/

# Step 3: Setup environment
echo "⚙️ Setting up Python environment..."
ssh $PI_USER@$PI_IP "cd $PI_APP_DIR && python3 -m venv venv"

# Step 4: Install dependencies
echo "📦 Installing dependencies..."
ssh $PI_USER@$PI_IP "cd $PI_APP_DIR && source venv/bin/activate && pip install -r requirements.txt --no-cache-dir"

# Step 5: Create systemd service
echo "🔧 Installing systemd service..."
ssh $PI_USER@$PI_IP "sudo tee /etc/systemd/system/rural-india-ai.service > /dev/null" << 'EOF'
[Unit]
Description=Rural India AI Edge Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rural-india-ai
Environment="PATH=/home/pi/rural-india-ai/venv/bin"
ExecStart=/home/pi/rural-india-ai/venv/bin/python3 /home/pi/rural-india-ai/api_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Enable and start service
echo "🚀 Starting service..."
ssh $PI_USER@$PI_IP "sudo systemctl daemon-reload && sudo systemctl enable rural-india-ai && sudo systemctl start rural-india-ai"

# Step 7: Verify deployment
echo "✅ Verifying deployment..."
sleep 3
if ssh $PI_USER@$PI_IP "curl -s http://localhost:8000/ > /dev/null"; then
    echo "✓ API server is running"
else
    echo "✗ API server failed to start"
    ssh $PI_USER@$PI_IP "systemctl status rural-india-ai"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "📊 Access API: http://$PI_IP:8000"
echo "📈 View docs: http://$PI_IP:8000/docs"
echo "🔍 Check logs: ssh $PI_USER@$PI_IP 'journalctl -u rural-india-ai -f'"
