#!/bin/bash

# XRPL MCP Server - Development Helper Scripts
# Usage: ./scripts/dev.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_usage() {
    echo "XRPL MCP Server Development Commands"
    echo ""
    echo "Usage: ./scripts/dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup         - Initial project setup"
    echo "  start         - Start both servers"
    echo "  stop          - Stop all servers"
    echo "  restart       - Restart all servers"
    echo "  test          - Run all tests"
    echo "  test-tools    - Test MCP tools directly"
    echo "  test-ws       - Test WebSocket interface"
    echo "  test-currency - Test currency conversion"
    echo "  health        - Check server health"
    echo "  logs          - Show recent logs"
    echo "  clean         - Clean up processes and logs"
    echo "  install       - Install/update dependencies"
    echo "  lint          - Run code linting"
    echo "  format        - Format code"
    echo ""
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Command functions
cmd_setup() {
    print_status "Setting up development environment..."
    cd "$PROJECT_DIR"
    
    if ! command -v poetry >/dev/null 2>&1; then
        print_status "Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
    fi
    
    poetry install
    
    if [[ ! -f ".env" ]] || [[ ! -s ".env" ]]; then
        print_status "Creating .env file..."
        echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
        print_warning "Please update .env with your Google API key"
    fi
    
    mkdir -p logs
    print_success "Development environment ready!"
}

cmd_start() {
    print_status "Starting XRPL MCP Server..."
    cd "$PROJECT_DIR"
    
    # Source environment
    if [[ -f ".env" ]]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Start MCP server
    print_status "Starting MCP Server..."
    poetry run python -m xrpl.server.main > logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > logs/mcp_server.pid
    
    sleep 3
    
    # Start Agent client
    print_status "Starting Agent Client..."
    cd client
    poetry run python client.py > ../logs/agent_client.log 2>&1 &
    AGENT_PID=$!
    echo $AGENT_PID > ../logs/agent_client.pid
    cd ..
    
    sleep 5
    
    # Health check
    if cmd_health; then
        print_success "Servers started successfully!"
        echo "MCP Server PID: $MCP_PID"
        echo "Agent Client PID: $AGENT_PID"
    else
        print_error "Server startup failed!"
        cmd_stop
        exit 1
    fi
}

cmd_stop() {
    print_status "Stopping servers..."
    cd "$PROJECT_DIR"
    
    if [[ -f "logs/mcp_server.pid" ]]; then
        PID=$(cat logs/mcp_server.pid)
        kill $PID 2>/dev/null || true
        rm -f logs/mcp_server.pid
        print_status "MCP Server stopped"
    fi
    
    if [[ -f "logs/agent_client.pid" ]]; then
        PID=$(cat logs/agent_client.pid)
        kill $PID 2>/dev/null || true
        rm -f logs/agent_client.pid
        print_status "Agent Client stopped"
    fi
    
    # Kill any remaining processes
    pkill -f "xrpl.server.main" 2>/dev/null || true
    pkill -f "client.py" 2>/dev/null || true
    
    print_success "All servers stopped"
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_test() {
    print_status "Running comprehensive tests..."
    cd "$PROJECT_DIR"
    
    if ! cmd_health; then
        print_error "Servers not running. Starting them first..."
        cmd_start
    fi
    
    print_status "Testing MCP tools..."
    poetry run python test_mcp_tools.py
    
    print_status "Testing WebSocket interface..."
    poetry run python test_websocket_client.py
    
    print_status "Testing currency conversion..."
    poetry run python test_currency_agent.py
    
    print_success "All tests completed!"
}

cmd_test_tools() {
    print_status "Testing MCP tools directly..."
    cd "$PROJECT_DIR"
    poetry run python test_mcp_tools.py
}

cmd_test_ws() {
    print_status "Testing WebSocket interface..."
    cd "$PROJECT_DIR"
    poetry run python test_websocket_client.py
}

cmd_test_currency() {
    print_status "Testing currency conversion..."
    cd "$PROJECT_DIR"
    poetry run python test_currency_agent.py
}

cmd_health() {
    cd "$PROJECT_DIR"
    
    # Check MCP server
    if ! curl -s http://localhost:8080/ >/dev/null 2>&1; then
        print_error "Agent Client (8080) not responding"
        return 1
    fi
    
    # Check tool count
    TOOL_COUNT=$(curl -s http://localhost:8080/ 2>/dev/null | grep -o '"tools_count":[0-9]*' | grep -o '[0-9]*' || echo "0")
    
    if [[ "$TOOL_COUNT" -gt "150" ]]; then
        print_success "Servers healthy! Tools: $TOOL_COUNT"
        return 0
    else
        print_error "Server unhealthy. Tools: $TOOL_COUNT"
        return 1
    fi
}

cmd_logs() {
    cd "$PROJECT_DIR"
    
    echo "=== Recent MCP Server Logs ==="
    tail -n 20 logs/mcp_server.log 2>/dev/null || echo "No MCP server logs"
    
    echo ""
    echo "=== Recent Agent Client Logs ==="
    tail -n 20 logs/agent_client.log 2>/dev/null || echo "No agent client logs"
    
    echo ""
    echo "=== Process Status ==="
    if [[ -f "logs/mcp_server.pid" ]]; then
        PID=$(cat logs/mcp_server.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "MCP Server running (PID: $PID)"
        else
            echo "MCP Server not running (stale PID)"
        fi
    else
        echo "MCP Server not running"
    fi
    
    if [[ -f "logs/agent_client.pid" ]]; then
        PID=$(cat logs/agent_client.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "Agent Client running (PID: $PID)"
        else
            echo "Agent Client not running (stale PID)"
        fi
    else
        echo "Agent Client not running"
    fi
}

cmd_clean() {
    print_status "Cleaning up..."
    cd "$PROJECT_DIR"
    
    cmd_stop
    
    # Clean logs
    rm -f logs/*.log
    rm -f logs/*.pid
    
    # Clean Python cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "Cleanup complete"
}

cmd_install() {
    print_status "Installing/updating dependencies..."
    cd "$PROJECT_DIR"
    poetry install
    print_success "Dependencies updated"
}

cmd_lint() {
    print_status "Running linters..."
    cd "$PROJECT_DIR"
    poetry run flake8 xrpl client --count --show-source --statistics
    print_success "Linting complete"
}

cmd_format() {
    print_status "Formatting code..."
    cd "$PROJECT_DIR"
    poetry run black xrpl client
    poetry run isort xrpl client
    print_success "Code formatted"
}

# Main command dispatcher
case "$1" in
    setup)      cmd_setup ;;
    start)      cmd_start ;;
    stop)       cmd_stop ;;
    restart)    cmd_restart ;;
    test)       cmd_test ;;
    test-tools) cmd_test_tools ;;
    test-ws)    cmd_test_ws ;;
    test-currency) cmd_test_currency ;;
    health)     cmd_health ;;
    logs)       cmd_logs ;;
    clean)      cmd_clean ;;
    install)    cmd_install ;;
    lint)       cmd_lint ;;
    format)     cmd_format ;;
    *)          print_usage ;;
esac