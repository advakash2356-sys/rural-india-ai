#!/bin/bash

# Deploy Rural India AI to Linux Server (Ubuntu/Debian)
# Usage: ./deploy_to_linux.sh [remote_user@remote_host] [target_dir]

REMOTE_TARGET="${1:-localhost}"
TARGET_DIR="${2:-/opt/rural-india-ai}"
APP_NAME="Rural India AI"

if [[ "$REMOTE_TARGET" == "localhost" ]]; then
    echo "🚀 Deploying $APP_NAME to local Linux system"
    LOCAL_MODE=true
else
    echo "🚀 Deploying $APP_NAME to $REMOTE_TARGET"
    LOCAL_MODE=false
fi

echo "=========================================="

# Function to run commands locally or remotely
run_cmd() {
    local cmd="$1"
    if [[ "$LOCAL_MODE" == true ]]; then
        eval "$cmd"
    else
        ssh "$REMOTE_TARGET" "$cmd"
    fi
}

# Function to copy files
copy_files() {
    if [[ "$LOCAL_MODE" == true ]]; then
        cp -r . "$TARGET_DIR" 2>/dev/null || true
    else
        echo "📤 Uploading files to $REMOTE_TARGET..."
        rsync -avz \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            --exclude='venv' \
            --exclude='.env' \
            --exclude='data/' \
            . "$REMOTE_TARGET:$TARGET_DIR/"
    fi
}

# Step 1: Update system
echo "📦 Updating system packages..."
run_cmd "sudo apt-get update && sudo apt-get upgrade -y"

# Step 2: Install Python and build tools
echo "🐍 Installing Python and development tools..."
run_cmd "sudo apt-get install -y \
    python3.9 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    libffi-dev \
    libssl-dev"

# Step 3: Install audio libraries (optional)
echo "🔊 Installing audio libraries..."
run_cmd "sudo apt-get install -y \
    sox \
    libsox-dev \
    libsox-fmt-all 2>/dev/null || true" || true

# Step 4: Create target directory
echo "📁 Creating target directory..."
run_cmd "sudo mkdir -p $TARGET_DIR && sudo chown -R $USER:$USER $TARGET_DIR"

# Step 5: Copy files
copy_files

# Step 6: Setup Python environment
echo "🌱 Setting up Python virtual environment..."
run_cmd "cd $TARGET_DIR && python3 -m venv venv"

# Step 7: Install dependencies
echo "📦 Installing Python dependencies..."
run_cmd "cd $TARGET_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Step 8: Create systemd service
echo "🔧 Creating systemd service..."
if [[ "$LOCAL_MODE" == true ]]; then
    sudo tee /etc/systemd/system/rural-india-ai.service > /dev/null << EOF
[Unit]
Description=Rural India AI Edge Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$TARGET_DIR
Environment="PATH=$TARGET_DIR/venv/bin"
ExecStart=$TARGET_DIR/venv/bin/python3 $TARGET_DIR/api_server.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
else
    ssh "$REMOTE_TARGET" "sudo tee /etc/systemd/system/rural-india-ai.service > /dev/null" << EOF
[Unit]
Description=Rural India AI Edge Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(echo $REMOTE_TARGET | cut -d'@' -f1)
WorkingDirectory=$TARGET_DIR
Environment="PATH=$TARGET_DIR/venv/bin"
ExecStart=$TARGET_DIR/venv/bin/python3 $TARGET_DIR/api_server.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
fi

# Step 9: Create data directories
echo "📁 Creating data directories..."
run_cmd "mkdir -p $TARGET_DIR/data/metrics $TARGET_DIR/data/backups $TARGET_DIR/logs"

# Step 10: Enable and start service
echo "🚀 Enabling systemd service..."
run_cmd "sudo systemctl daemon-reload && sudo systemctl enable rural-india-ai"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
if [[ "$LOCAL_MODE" == true ]]; then
    echo "   1. Start service:      sudo systemctl start rural-india-ai"
    echo "   2. Check status:       sudo systemctl status rural-india-ai"
    echo "   3. View logs:          journalctl -u rural-india-ai -f"
    echo "   4. Manual start:       cd $TARGET_DIR && source venv/bin/activate && python3 api_server.py"
else
    echo "   1. SSH to server:      ssh $REMOTE_TARGET"
    echo "   2. Start service:      sudo systemctl start rural-india-ai"
    echo "   3. Check status:       sudo systemctl status rural-india-ai"
    echo "   4. View logs:          journalctl -u rural-india-ai -f"
fi

echo ""
echo "🌐 API will be available at:"
if [[ "$LOCAL_MODE" == true ]]; then
    echo "       http://127.0.0.1:8000"
else
    echo "       http://$REMOTE_TARGET:8000"
fi
echo ""
