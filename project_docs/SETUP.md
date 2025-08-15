# XRPL MCP Server Setup Guide

This guide provides detailed instructions for setting up and running the XRPL MCP Server project.

## Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **Poetry**: Latest version for dependency management
- **OS**: macOS, Linux, or Windows with WSL
- **Memory**: 2GB+ RAM recommended
- **Network**: Internet connection for XRPL testnet/mainnet

### API Requirements
- **Google API Key**: Required for AI agent functionality (Gemini 2.0 Flash)
  - Get your API key from: https://aistudio.google.com/app/apikey
  - The key is used for natural language processing in the React Agent

## Installation Methods

### Method 1: One-Click Setup (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone <your-repo-url>
cd xrpl-py

# Run the one-click setup script
chmod +x run.sh
./run.sh
```

The script will:
1. Check system prerequisites 
2. Install Poetry if needed
3. Install all dependencies
4. Prompt for Google API key
5. Start both MCP server and Agent client
6. Verify everything is working

### Method 2: Manual Setup

For developers who prefer step-by-step control:

```bash
# 1. Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Clone and enter project directory
git clone <your-repo-url>
cd xrpl-py

# 3. Install dependencies
poetry install

# 4. Set environment variables
export GOOGLE_API_KEY="your_actual_api_key_here"
# OR create .env file
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env

# 5. Start MCP Server (Terminal 1)
poetry run python -m xrpl.server.main

# 6. Start React Agent Client (Terminal 2 - new window)
cd client
poetry run python client.py
```

### Method 3: Claude Code Integration

For direct integration with Claude Code:

```bash
# 1. Complete Method 1 or 2 setup first
# 2. The project already includes .mcp.json configuration
# 3. Restart Claude Code to load XRPL tools automatically
```

## Configuration Options

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional - Network Configuration  
XRPL_NETWORK=https://s.altnet.rippletest.net:51234/  # Testnet (default)
# XRPL_NETWORK=https://s1.ripple.com:51234/  # Mainnet

# Optional - Port Configuration
MCP_SERVER_PORT=8000    # Default MCP server port
AGENT_SERVER_PORT=8080  # Default agent WebSocket port

# Optional - Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

### Network Configuration

#### Using Testnet (Default)
The system uses XRPL testnet by default, which is perfect for development:
- Free test XRP from faucets
- Safe environment for testing
- Same functionality as mainnet

#### Switching to Mainnet
To use mainnet for production:

```python
# Edit xrpl/server/config.py
xrpl_client = AsyncJsonRpcClient("https://s1.ripple.com:51234/")
```

### MCP Server Configuration

The MCP server can run in different modes:

```python
# For Claude Code integration (stdio)
python -m xrpl.server.main stdio

# For HTTP/SSE integration (default)
python -m xrpl.server.main
```

## Verification & Testing

### Quick Health Check

```bash
# Check if servers are running
curl http://localhost:8080/
# Expected: {"message": "XRPL AI Agent API is running", "tools_count": 156}

curl http://localhost:8080/tools
# Expected: List of 156 available XRPL tools
```

### Comprehensive Testing

```bash
# Test MCP tools directly
poetry run python test_mcp_tools.py

# Test WebSocket interface
poetry run python test_websocket_client.py

# Test currency conversion
poetry run python test_currency_agent.py

# Open browser test interface
open test_websocket_client.html
```

### Tool Verification

Verify all 156 tools are loaded:
- 61 Transaction types (Payment, TrustSet, OfferCreate, NFT ops, etc.)
- 52 Request types (AccountInfo, Ledger queries, etc.)
- 2 Amount types (IssuedCurrency, MPT)
- 3 Currency types (XRP, IssuedCurrency, MPT)
- 38 Utility functions (Address codec, parsers, etc.)

## Usage Examples

### WebSocket API Testing

Connect to `ws://localhost:8080/chat` and send:

```json
{
  "message": "Create a payment sending 10 XRP from rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH to rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
}
```

### Direct Tool Usage

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_tools():
    server_config = {
        "xrpl": {
            "url": "http://localhost:8000/sse",
            "transport": "sse"
        }
    }
    
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    
    # Find payment tool
    payment_tool = next(t for t in tools if t.name == "create_transaction_payment")
    
    # Create payment
    result = await payment_tool.ainvoke({
        "account": "rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH",
        "destination": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
        "amount": "1000000"  # 1 XRP in drops
    })
    
    print("Payment result:", result)

asyncio.run(test_tools())
```

## Troubleshooting

### Common Issues

#### 1. MCP Server Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check Poetry installation
poetry --version

# Check logs
tail -f logs/mcp_server.log
```

#### 2. Agent Client Connection Issues

```bash
# Verify MCP server is running first
curl http://localhost:8000/health

# Check Google API key
echo $GOOGLE_API_KEY

# Check logs
tail -f logs/agent_client.log
```

#### 3. Tools Not Loading

```bash
# Verify tool count
curl http://localhost:8080/tools | jq '.tools | length'
# Should return: 156

# Check MCP server registration
grep "Found.*models" logs/mcp_server.log
```

#### 4. WebSocket Connection Problems

```bash
# Test WebSocket connectivity
wscat -c ws://localhost:8080/chat

# Check CORS settings in client/client.py
# Verify port 8080 is not in use by other services
lsof -i :8080
```

### Performance Optimization

#### For High-Load Environments

```python
# Edit client/client.py - increase connection limits
server_config = {
    "xrpl": {
        "url": "http://localhost:8000/sse",
        "transport": "sse",
        "timeout": 10000,  # Increase timeout
        "sse_read_timeout": 10000
    }
}
```

#### For Development

```bash
# Run with verbose logging
./run.sh --verbose

# Enable debug mode
export LOG_LEVEL=DEBUG
```

### Log Locations

- **MCP Server**: `logs/mcp_server.log`
- **Agent Client**: `logs/agent_client.log`  
- **System Output**: Console output from run.sh

### Getting Help

1. **Check logs** first - most issues show up there
2. **Verify prerequisites** - Python 3.10+, Poetry, API key
3. **Test step by step** - MCP server first, then agent client
4. **Check network connectivity** - XRPL testnet access required
5. **Review configuration** - Environment variables and network settings

## Advanced Configuration

### Custom XRPL Network

```python
# Create custom network config in xrpl/server/config.py
xrpl_client = AsyncJsonRpcClient("https://your-custom-xrpl-node:51234/")
```

### Multiple Agent Instances

```python
# Modify client/client.py to run on different ports
uvicorn.run(app, host="0.0.0.0", port=8081)  # Second instance
```

### Production Deployment

```bash
# Use production WSGI server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker client.client:app

# Set up reverse proxy (nginx)
# Configure SSL certificates  
# Set up monitoring and logging
```

---

For additional support, check the [main README](README.md) and [project context](CONTEXT.md).