#!/bin/bash

# RURAL INDIA AI - DEPLOYMENT VERIFICATION SCRIPT
# Verifies system readiness for MacBook or Linux server deployment

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  RURAL INDIA AI - PERSONAL SERVER DEPLOYMENT VERIFICATION    ║"
echo "║                                                              ║"
echo "║  Target: MacBook or Linux Server (NOT Raspberry Pi)         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "🐍 Python Environment:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "   ✓ Python $PYTHON_VERSION available"
else
    echo "   ✗ Python3 not found - install via 'brew install python3' (macOS) or apt-get (Linux)"
fi
echo ""

# Check deployment files
echo "📁 Deployment Files:"
declare -a files=(
    "deploy_to_macbook.sh"
    "deploy_to_linux.sh"
    "docker-compose.yml"
    "PERSONAL_SERVER_DEPLOYMENT.md"
    "DEPLOYMENT_MACBOOK_LINUX.md"
    "ARCHITECTURE_PERSONAL_SERVERS.md"
    "README_PERSONAL_DEPLOYMENT.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (missing)"
    fi
done
echo ""

# Check core system files
echo "🔧 Core System Files:"
declare -a core_files=(
    "edge_node"
    "api_server.py"
    "cli.py"
    "dashboard.html"
    "requirements.txt"
)

for file in "${core_files[@]}"; do
    if [ -e "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (missing)"
    fi
done
echo ""

# Check execution permissions
echo "🔐 Execution Permissions:"
if [ -x "deploy_to_macbook.sh" ]; then
    echo "   ✓ deploy_to_macbook.sh is executable"
else
    echo "   ℹ deploy_to_macbook.sh needs: chmod +x deploy_to_macbook.sh"
fi

if [ -x "deploy_to_linux.sh" ]; then
    echo "   ✓ deploy_to_linux.sh is executable"
else
    echo "   ℹ deploy_to_linux.sh needs: chmod +x deploy_to_linux.sh"
fi
echo ""

# Check system requirements
echo "💻 System Requirements:"
case "$(uname)" in
    Darwin)
        echo "   ✓ macOS detected (ready for MacBook deployment)"
        ;;
    Linux)
        echo "   ✓ Linux detected (ready for Linux server deployment)"
        ;;
    *)
        echo "   ℹ Unknown OS - check DEPLOYMENT_MACBOOK_LINUX.md"
        ;;
esac
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT OPTIONS                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "1️⃣  MacBook Deployment (Development/Testing)"
echo "    Command: ./deploy_to_macbook.sh"
echo "    Time: ~3 minutes"
echo "    Result: API at http://127.0.0.1:8000"
echo ""
echo "2️⃣  Linux Server Deployment (Production)"
echo "    Command: ./deploy_to_linux.sh [user@host] [path]"
echo "    Time: ~5 minutes"
echo "    Result: auto-start via systemd"
echo ""
echo "3️⃣  Docker Deployment (All Platforms)"
echo "    Command: docker-compose up -d"
echo "    Time: ~2 minutes"
echo "    Result: API at http://localhost:8000"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📚 Documentation:"
echo "   • README_PERSONAL_DEPLOYMENT.md (START HERE)"
echo "   • PERSONAL_SERVER_DEPLOYMENT.md (Quick reference)"
echo "   • DEPLOYMENT_MACBOOK_LINUX.md (Comprehensive guide)"
echo "   • ARCHITECTURE_PERSONAL_SERVERS.md (Architecture & design)"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Ready to Deploy!"
echo ""
echo "Next steps:"
echo "   1. Choose deployment method (MacBook/Linux/Docker)"
echo "   2. Run deployment script"
echo "   3. Verify: python3 complete_demo.py"
echo "   4. Access: http://localhost:8000"
echo ""
echo "════════════════════════════════════════════════════════════════"
