#!/bin/bash

# Deploy Rural India AI to MacBook (local or remote)
# Usage: ./deploy_to_macbook.sh [optional_target_path]

TARGET_PATH="${1:-.}"
APP_NAME="Rural India AI"

echo "🚀 Deploying $APP_NAME to MacBook"
echo "=========================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python 3.9+ if not present
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python 3.9+..."
    brew install python3
fi

# Verify Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION installed"

# Create target directory if remote
if [[ "$TARGET_PATH" != "." ]]; then
    mkdir -p "$TARGET_PATH"
fi

# Navigate to target
cd "$TARGET_PATH"

# Copy application files
echo "📁 Setting up application directory..."
if [[ "$TARGET_PATH" != "." ]]; then
    cp -r "$(dirname "$0")"/* . 2>/dev/null || true
fi

# Create virtual environment
echo "🌱 Creating Python virtual environment..."
python3 -m venv venv || python -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install optional audio dependencies (gracefully handle failures on M1/M2)
echo "🔊 Installing audio libraries..."
pip install librosa soundfile scipy 2>/dev/null || {
    echo "⚠️  Some audio libraries optional - system can run without them"
}

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/metrics data/backups logs

# Generate initial config if needed
if [ ! -f "config.json" ]; then
    echo "⚙️ Generating configuration..."
    cat > config.json << 'EOF'
{
    "app_name": "Rural India AI",
    "environment": "development",
    "api_host": "127.0.0.1",
    "api_port": 8000,
    "debug": true,
    "languages": ["en", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu"],
    "data_path": "./data",
    "logs_path": "./logs",
    "max_workers": 4
}
EOF
    echo "✓ Config generated at config.json"
fi

# Make scripts executable
chmod +x *.sh cli.py 2>/dev/null || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate environment: source venv/bin/activate"
echo "   2. Start API server:    python3 api_server.py"
echo "   3. Open dashboard:      open dashboard.html"
echo "   4. Use CLI tool:        python3 cli.py query 'Your question'"
echo ""
echo "API will be available at: http://127.0.0.1:8000"
echo "Dashboard at:            dashboard.html"
echo ""
