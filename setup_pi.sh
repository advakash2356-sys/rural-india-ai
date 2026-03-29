#!/bin/bash

# Raspberry Pi 5 Setup Script
# Run this on a fresh Raspberry Pi OS installation

echo "⚙️ Rural India AI - Raspberry Pi 5 Setup"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dev tools
echo "🐍 Installing Python dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev

# Install audio libraries
echo "🔊 Installing audio libraries..."
sudo apt-get install -y \
    alsa-utils \
    alsa-base \
    libmpg123-0 \
    sox

# Enable I2C and SPI for sensors
echo "🔌 Enabling I2C and SPI..."
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt > /dev/null
echo "dtparam=spi=on" | sudo tee -a /boot/config.txt > /dev/null

# Create app directory
echo "📁 Creating Rural India AI directory..."
mkdir -p ~/rural-india-ai
cd ~/rural-india-ai

# Setup Python virtual environment
echo "🌱 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create data directories
echo "📂 Creating data directories..."
mkdir -p data/models
mkdir -p data/vector_db
mkdir -p data/metrics
mkdir -p data/logs

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/rural-india-ai.service > /dev/null << 'EOF'
[Unit]
Description=Rural India AI Edge Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rural-india-ai
Environment="PATH=/home/pi/rural-india-ai/venv/bin"
ExecStart=/home/pi/rural-india-ai/venv/bin/python3 -u /home/pi/rural-india-ai/api_server.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Setup log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/rural-india-ai > /dev/null << 'EOF'
/home/pi/rural-india-ai/data/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 pi pi
}
EOF

# Create cron backup task
echo "💾 Setting up automated backups..."
crontab -l 2>/dev/null | grep -v rural-india-ai | crontab - 2>/dev/null
(crontab -l 2>/dev/null; echo "0 3 * * * /home/pi/rural-india-ai/backup.sh") | crontab -

# Optimize system for edge computing
echo "⚡ Optimizing system..."
echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "net.core.default_qdisc = fq" | sudo tee -a /etc/sysctl.conf > /dev/null
echo "net.ipv4.tcp_congestion_control = bbr" | sudo tee -a /etc/sysctl.conf > /dev/null
sudo sysctl -p > /dev/null

# Enable service
echo "🔌 Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable rural-india-ai

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Start service: sudo systemctl start rural-india-ai"
echo "2. View logs: sudo journalctl -u rural-india-ai -f"
echo "3. Access API: http://localhost:8000"
echo "4. API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Commands:"
echo "  - Start:   sudo systemctl start rural-india-ai"
echo "  - Stop:    sudo systemctl stop rural-india-ai"
echo "  - Status:  sudo systemctl status rural-india-ai"
echo "  - Logs:    sudo journalctl -u rural-india-ai -f"
