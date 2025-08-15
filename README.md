# XRPL MCP Server - AI-Powered XRPL Interface

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/jlowin/fastmcp)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](#)

> **🚀 The Complete XRPL-to-MCP Bridge with AI Agent Integration**

Transform the entire XRPL-py library into a production-ready MCP (Model Context Protocol) server with AI-powered natural language interaction. This system exposes all XRPL functionality through 156 standardized tools, making blockchain development accessible through simple tool calls and natural language.

## ✨ Features

- **🔧 156 XRPL Tools**: Complete coverage of transactions, requests, amounts, currencies, and utilities
- **🤖 AI-Powered Interface**: Natural language to blockchain transaction conversion using Google Gemini
- **🌐 WebSocket API**: Real-time communication for frontend applications
- **🔄 Auto Currency Conversion**: Intelligent handling of XRPL currency formats (3-char codes + hex encoding)
- **📡 MCP Protocol**: Standard tool interface compatible with Claude Code and other MCP clients
- **🎯 Production Ready**: Comprehensive validation, error handling, and type conversion

## 🚀 Quick Start

### Option 1: One-Click Setup (Recommended)

```bash
# Clone and run everything with one command
git clone <repo-url>
cd xrpl-py
chmod +x run.sh
./run.sh
```

### Option 2: Manual Setup

```bash
# Install dependencies
poetry install

# Set your Google API key
export GOOGLE_API_KEY="your_google_api_key_here"

# Start MCP server (Terminal 1)
poetry run python -m xrpl.server.main

# Start React Agent client (Terminal 2)
cd client && poetry run python client.py
```

### Option 3: Claude Code Integration

```bash
# The project includes .mcp.json for Claude Code integration
# Simply restart Claude Code to automatically load the XRPL tools
```

## 💡 Usage Examples

### Direct Tool Calls
```python
# Create XRP payment
payment = await create_transaction_payment(
    account="rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH",
    destination="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
    amount="1000000"  # 1 XRP in drops
)

# Create issued currency payment with auto hex conversion
usdc_payment = await create_transaction_payment(
    account="rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH", 
    destination="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
    amount={
        "currency": "USDC",  # Automatically converted to hex
        "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
        "value": "100"
    }
)

# Get account information
account_info = await create_request_accountinfo(
    account="rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH"
)
```

### Natural Language AI Interface
```javascript
// Connect to WebSocket API
const ws = new WebSocket('ws://localhost:8080/chat');

// Send natural language requests
ws.send(JSON.stringify({
    message: "Create a payment sending 500 USDC to rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
}));

ws.send(JSON.stringify({
    message: "Get account information for rhARfQZ2xqQYnm65VYFoXYgHrcsjr3a7ta"
}));
```

## 🏗️ Architecture

### Components
- **MCP Server** (`xrpl/server/`): FastMCP-based server exposing XRPL tools
- **React Agent Client** (`client/`): FastAPI WebSocket server with AI integration  
- **Enhanced Models** (`xrpl/server/models/`): Dynamic tool generation from XRPL models
- **WebSocket Interface**: Real-time communication for frontend applications

### Tool Categories
- **61 Transaction Types**: Payment, TrustSet, OfferCreate, NFT operations, AMM, Escrow, etc.
- **52 Request Types**: AccountInfo, AccountLines, Ledger queries, Server operations
- **Currency & Amount Tools**: XRP, IssuedCurrency, with auto-hex conversion
- **38 Utility Functions**: Address codec, binary codec, keypairs, parsers

## 🔧 Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional
XRPL_NETWORK=https://s.altnet.rippletest.net:51234/  # Default testnet
MCP_SERVER_PORT=8000  # Default MCP server port
AGENT_SERVER_PORT=8080  # Default agent WebSocket port
```

### Network Configuration
The system uses XRPL testnet by default. To use mainnet:

```python
# Edit xrpl/server/config.py
xrpl_client = AsyncJsonRpcClient("https://s1.ripple.com:51234/")
```

## 📊 API Reference

### WebSocket API Endpoints

**Connect**: `ws://localhost:8080/chat`

**Message Format**:
```json
{
  "message": "Your natural language request or specific tool call"
}
```

**Response Types**:
- `system`: Server status messages
- `user_message_received`: Acknowledgment of user input  
- `typing`: Agent processing indicator
- `agent_response`: AI agent response with transaction data
- `error`: Error messages with details

### REST API Endpoints

**Health Check**: `GET http://localhost:8080/`
```json
{
  "message": "XRPL AI Agent API is running",
  "tools_count": 156
}
```

**Available Tools**: `GET http://localhost:8080/tools`
```json
{
  "tools": [
    {
      "name": "create_transaction_payment",
      "description": "Create a Payment transaction..."
    }
  ]
}
```

## 🧪 Testing

```bash
# Run comprehensive tests
poetry run python -m pytest

# Test MCP tools directly  
poetry run python test_mcp_tools.py

# Test WebSocket interface
poetry run python test_websocket_client.py

# Test currency conversion
poetry run python test_currency_agent.py

# Open browser test interface
open test_websocket_client.html
```

## 🔍 Currency Handling

The system automatically handles XRPL currency format requirements:

- **XRP**: Always use `"XRP"`
- **3-character codes**: Use as-is (`"USD"`, `"EUR"`, `"BTC"`)  
- **Longer currencies**: Automatically converted to 40-character hex strings
  - `"USDC"` → `"5553444300000000000000000000000000000000"`
  - `"CUSTOMTOKEN"` → `"435553544F4D544F4B454E000000000000000000"`

## 📚 Documentation

### Getting Started
- **[Setup Guide](SETUP.md)** - Detailed installation and configuration instructions
- **[API Reference](API_REFERENCE.md)** - Complete API documentation with examples
- **[Project Context](CONTEXT.md)** - Project overview, timeline, and current status

### Development
- **[Development Scripts](scripts/dev.sh)** - Helper scripts for common development tasks
- **[Transaction Types](client/transaction_types_documentation.md)** - XRPL transaction reference

### Usage Examples
```bash
# Quick development commands
./scripts/dev.sh setup     # One-time setup
./scripts/dev.sh start     # Start servers
./scripts/dev.sh test      # Run all tests
./scripts/dev.sh health    # Check status
./scripts/dev.sh stop      # Stop servers
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📄 License

This project extends xrpl-py under the ISC License. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Full Documentation](docs/)
- **Community**: [Discord/Telegram links]

---

**🎯 Built for Production | 🤖 AI-Powered | 🔧 Developer-Friendly**

*Transform XRPL development with the power of AI and standardized tooling.*