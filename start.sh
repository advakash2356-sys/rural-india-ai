#!/bin/bash

# Quick Start Script for Rural India AI
# Launches all components in one command

echo "🚀 Starting Rural India AI System"
echo "=================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Some dependencies may not have installed (e.g., PyAudio)${NC}"
    echo "   System will function with fallbacks"
fi

# Create data directories
mkdir -p data/models
mkdir -p data/vector_db
mkdir -p data/metrics
mkdir -p data/logs

echo ""
echo -e "${GREEN}✓${NC} All systems ready"
echo ""
echo "🎯 Available commands:"
echo "  1. API Server:  python3 api_server.py"
echo "  2. Dashboard:   open dashboard.html"
echo "  3. CLI Tool:    python3 cli.py --help"
echo "  4. Demo:        python3 complete_demo.py"
echo ""
echo "⏳ Starting API server..."
echo ""

# Start API server
python3 api_server.py
