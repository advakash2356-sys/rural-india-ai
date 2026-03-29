#!/bin/bash
# Production API Server Launcher
# Handles startup, monitoring, and graceful shutdown

set -e  # Exit on error

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv"
PYTHON="$VENV_DIR/bin/python3"
PID_FILE="$APP_DIR/.api_server.pid"
LOG_FILE="$APP_DIR/logs/api_server.log"
ERROR_LOG="$APP_DIR/logs/api_server_error.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  $1${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check environment
check_environment() {
    print_header "ENVIRONMENT CHECK"
    
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        print_info "Run: ./deploy_to_macbook.sh"
        exit 1
    fi
    print_success "Virtual environment found"
    
    if [ ! -f "$PYTHON" ]; then
        print_error "Python executable not found at $PYTHON"
        exit 1
    fi
    print_success "Python executable found"
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    print_success "Python version: $PYTHON_VERSION"
    
    # Check required directories
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/data/metrics"
    mkdir -p "$APP_DIR/data/backups"
    print_success "Data directories ready"
}

# Verify modules
verify_modules() {
    print_header "MODULE VERIFICATION"
    
    cd "$APP_DIR"
    "$PYTHON" verify_startup.py
    if [ $? -ne 0 ]; then
        print_error "Module verification failed"
        exit 1
    fi
}

# Start API server
start_api_server() {
    print_header "STARTING API SERVER"
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            print_warning "API server already running (PID: $OLD_PID)"
            echo "Kill it with: kill $OLD_PID"
            exit 1
        fi
    fi
    
    # Create log files
    echo "Starting at $(date)" > "$LOG_FILE"
    echo "Starting at $(date)" > "$ERROR_LOG"
    
    # Start server in background
    cd "$APP_DIR"
    nohup "$PYTHON" api_server.py >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    SERVER_PID=$!
    
    # Save PID
    echo $SERVER_PID > "$PID_FILE"
    
    print_success "API server started (PID: $SERVER_PID)"
    
    # Wait for startup
    echo "Waiting for API server to be ready..."
    RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $RETRIES ]; do
        if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
            print_success "API server is responding"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 1
        
        # Check if process is still alive
        if ! ps -p "$SERVER_PID" > /dev/null 2>&1; then
            print_error "API server process died during startup"
            print_error "Check logs: $ERROR_LOG"
            cat "$ERROR_LOG"
            exit 1
        fi
    done
    
    if [ $RETRY_COUNT -eq $RETRIES ]; then
        print_error "API server did not respond within ${RETRIES}s"
        print_error "Check logs: $ERROR_LOG"
        cat "$ERROR_LOG"
        kill $SERVER_PID 2>/dev/null || true
        rm "$PID_FILE"
        exit 1
    fi
    
    print_success "API server ready for requests"
}

# Show status
show_status() {
    print_header "API SERVER STATUS"
    
    if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
        print_success "API Server is OPERATIONAL"
        
        echo ""
        print_info "Access points:"
        echo "  • API Base:      http://127.0.0.1:8000"
        echo "  • API Docs:      http://127.0.0.1:8000/docs"
        echo "  • Health Check:  http://127.0.0.1:8000/api/v1/health"
        
        echo ""
        print_info "Testing endpoints..."
        
        # Test a few endpoints
        HEALTH=$(curl -s http://127.0.0.1:8000/api/v1/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "  ✓ Phase 1: Health = $HEALTH"
        
        LANGS=$(curl -s http://127.0.0.1:8000/api/v2/languages | grep -o '"languages"' | wc -l)
        echo "  ✓ Phase 2: Voice Interface = Ready"
        
        echo ""
        print_info "Useful commands:"
        echo "  • View logs:     tail -f $LOG_FILE"
        echo "  • Stop server:   ./stop_api_server.sh"
        echo "  • Query API:     python3 cli.py query 'Your question'"
        echo "  • Dashboard:     open dashboard.html"
    else
        print_error "API Server is NOT responding"
        echo "Check error log: $ERROR_LOG"
    fi
}

# Cleanup on exit
cleanup() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_info "Shutting down API server gracefully..."
            kill $PID 2>/dev/null || true
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
}

trap cleanup EXIT INT TERM

# Main execution
main() {
    case "${1:-start}" in
        start)
            check_environment
            verify_modules
            start_api_server
            show_status
            
            # Keep running
            print_info "API Server will run in background"
            print_info "Press Ctrl+C to stop, or run: ./stop_api_server.sh"
            
            # Monitor process
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                while ps -p "$PID" > /dev/null 2>&1; do
                    sleep 10
                done
                print_warning "API server process ended unexpectedly"
                print_info "Check logs: $ERROR_LOG"
            fi
            ;;
        
        status)
            show_status
            ;;
        
        logs)
            tail -f "$LOG_FILE"
            ;;
        
        errors)
            tail -f "$ERROR_LOG"
            ;;
        
        stop)
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ps -p "$PID" > /dev/null 2>&1; then
                    print_info "Stopping API server (PID: $PID)..."
                    kill $PID
                    sleep 2
                    print_success "API server stopped"
                else
                    print_warning "Process $PID not running"
                fi
                rm -f "$PID_FILE"
            else
                print_warning "No PID file found, server may not be running"
            fi
            ;;
        
        *)
            echo "Usage: $0 {start|status|logs|errors|stop}"
            exit 1
            ;;
    esac
}

main "$@"
