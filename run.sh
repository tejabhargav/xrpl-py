#!/bin/bash

# XRPL MCP Server - One-Click Setup and Run Script
# This script sets up and runs the complete XRPL MCP Server with AI Agent

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down servers..."
    if [[ ! -z "$MCP_PID" ]]; then
        kill $MCP_PID 2>/dev/null || true
        print_status "MCP Server stopped"
    fi
    if [[ ! -z "$AGENT_PID" ]]; then
        kill $AGENT_PID 2>/dev/null || true
        print_status "Agent Client stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "🚀 Starting XRPL MCP Server Setup..."

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | grep -o '[0-9]\+\.[0-9]\+' | head -1)
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    print_error "Python 3.10+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected ✓"

# Check for Poetry
if ! command_exists poetry; then
    print_error "Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    if ! command_exists poetry; then
        print_error "Failed to install Poetry. Please install manually: https://python-poetry.org/docs/"
        exit 1
    fi
fi

print_success "Poetry detected ✓"

# Install dependencies
print_status "Installing dependencies with Poetry..."
poetry install --no-dev

print_success "Dependencies installed ✓"

# Check for Google API Key
if [[ -z "$GOOGLE_API_KEY" ]]; then
    if [[ -f ".env" ]]; then
        source .env
    fi
    
    if [[ -z "$GOOGLE_API_KEY" ]] || [[ "$GOOGLE_API_KEY" == "your_google_api_key_here" ]] || [[ "$GOOGLE_API_KEY" == "test_key_for_development" ]]; then
        print_warning "Google API Key not found or using test key."
        print_status "Please enter your Google API Key for Gemini (required for AI agent):"
        read -r GOOGLE_API_KEY
        
        if [[ -z "$GOOGLE_API_KEY" ]]; then
            print_warning "No API key provided. AI agent will have limited functionality."
            GOOGLE_API_KEY="test_key_for_development"
        fi
        
        # Update .env file
        echo "GOOGLE_API_KEY=$GOOGLE_API_KEY" > .env
        print_success "API key saved to .env file ✓"
    fi
fi

export GOOGLE_API_KEY

# Create log directory
mkdir -p logs

print_success "Setup complete! Starting servers..."

# Start MCP Server
print_status "Starting XRPL MCP Server on port 8000..."
poetry run python -m xrpl.server.main > logs/mcp_server.log 2>&1 &
MCP_PID=$!

# Wait for MCP server to start
sleep 3

if ! kill -0 $MCP_PID 2>/dev/null; then
    print_error "MCP Server failed to start. Check logs/mcp_server.log for details."
    exit 1
fi

print_success "MCP Server started (PID: $MCP_PID) ✓"

# Start Agent Client
print_status "Starting React Agent Client on port 8080..."
cd client && poetry run python client.py > ../logs/agent_client.log 2>&1 &
AGENT_PID=$!
cd ..

# Wait for Agent client to start
sleep 5

if ! kill -0 $AGENT_PID 2>/dev/null; then
    print_error "Agent Client failed to start. Check logs/agent_client.log for details."
    cleanup
    exit 1
fi

print_success "React Agent Client started (PID: $AGENT_PID) ✓"

# Check if servers are responding
print_status "Verifying server health..."

MCP_HEALTH=$(curl -s http://localhost:8080/ 2>/dev/null | grep -o '"tools_count":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [[ "$MCP_HEALTH" -gt "0" ]]; then
    print_success "Servers are healthy! Tools loaded: $MCP_HEALTH ✓"
else
    print_error "Server health check failed. Check logs for issues."
    cleanup
    exit 1
fi

# Print status and URLs
echo ""
echo "🎉 XRPL MCP Server is now running!"
echo ""
echo "📊 Server Status:"
echo "  • MCP Server:     http://localhost:8000"
echo "  • Agent API:      http://localhost:8080"
echo "  • WebSocket Chat: ws://localhost:8080/chat"
echo "  • Tools Available: $MCP_HEALTH"
echo ""
echo "🧪 Test the system:"
echo "  • Browser Test:   open test_websocket_client.html"
echo "  • Direct Test:    poetry run python test_mcp_tools.py"
echo "  • Currency Test:  poetry run python test_currency_agent.py"
echo ""
echo "📚 Documentation:"
echo "  • README:         README.md"
echo "  • Project Status: CONTEXT.md"
echo "  • Logs:           logs/"
echo ""
print_status "Press Ctrl+C to stop all servers"

# Keep script running and show logs
while true; do
    sleep 10
    
    # Check if processes are still running
    if ! kill -0 $MCP_PID 2>/dev/null; then
        print_error "MCP Server has stopped unexpectedly!"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $AGENT_PID 2>/dev/null; then
        print_error "Agent Client has stopped unexpectedly!"
        cleanup
        exit 1
    fi
    
    # Optional: Show recent log entries
    if [[ "$1" == "--verbose" ]]; then
        echo "--- Recent MCP Server Log ---"
        tail -n 5 logs/mcp_server.log 2>/dev/null || echo "No MCP logs yet"
        echo "--- Recent Agent Client Log ---"
        tail -n 5 logs/agent_client.log 2>/dev/null || echo "No Agent logs yet"
        echo ""
    fi
done