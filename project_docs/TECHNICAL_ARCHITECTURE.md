# XRPL MCP Server - Technical Architecture Documentation

## 🏗️ System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
│     (Web Browsers, Mobile Apps, Desktop Tools, etc.)       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
                      │ Port 8080
┌─────────────────────▼───────────────────────────────────────┐
│                React Agent Client                           │
│  ┌─────────────────┬──────────────────┬─────────────────┐   │
│  │   FastAPI       │   LangChain      │   Google        │   │
│  │   WebSocket     │   React Agent    │   Gemini        │   │
│  │   Server        │                  │   2.0 Flash     │   │
│  └─────────────────┴──────────────────┴─────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
                      │ SSE/HTTP Port 8000
┌─────────────────────▼───────────────────────────────────────┐
│                 XRPL MCP Server                             │
│  ┌─────────────────┬──────────────────┬─────────────────┐   │
│  │    FastMCP      │   Enhanced       │   Dynamic       │   │
│  │    Protocol     │   Models         │   Tool          │   │
│  │    Handler      │   Generator      │   Registration  │   │
│  └─────────────────┴──────────────────┴─────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ Direct Python Calls
┌─────────────────────▼───────────────────────────────────────┐
│                    xrpl-py Library                         │
│  ┌─────────────────┬──────────────────┬─────────────────┐   │
│  │  Transaction    │    Request       │   Utility       │   │
│  │  Models         │    Models        │   Functions     │   │
│  │  (61 types)     │    (52 types)    │   (38 funcs)    │   │
│  └─────────────────┴──────────────────┴─────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                 XRPL Network                                │
│            (Testnet/Mainnet)                                │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Component Deep Dive

### 1. React Agent Client (`client/client.py`)

**Framework Stack:**
- **FastAPI**: HTTP server and WebSocket handling
- **LangChain**: AI agent orchestration framework
- **Google Gemini**: Large language model for natural language processing
- **langchain-mcp-adapters**: MCP protocol client integration

**Key Responsibilities:**
- WebSocket server for real-time communication
- Natural language processing and intent recognition
- Tool selection and parameter extraction
- Response formatting and error handling
- Conversation state management

**Critical Code Sections:**
```python
# System prompt (lines 23-219) - Contains all tool documentation
system_prompt = """You are a XRPL AI AGENT with access to..."""

# Agent initialization (lines 264-300)
async def initialize_agent():
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    agent = create_react_agent(model, tools, prompt=system_prompt)

# WebSocket handler (lines 342-430)
@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
```

### 2. XRPL MCP Server (`xrpl/server/`)

**Framework:** FastMCP (Model Context Protocol implementation)

**Core Components:**

#### A. Main Entry Point (`main.py`)
```python
# Tool registration through imports
import xrpl.server.models.enhanced_main  # Registers all model tools
import xrpl.asyncio.account.main         # Account utilities
import xrpl.core.addresscodec.main       # Address encoding
# ... additional imports

mcp.run("sse")  # Start SSE server
```

#### B. Configuration (`config.py`)
```python
# Global instances shared across modules
xrpl_client = AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234/")
mcp = FastMCP("XRPL-MCP-Server")
```

#### C. Enhanced Models (`models/enhanced_main.py`) - **CRITICAL COMPONENT**

**Purpose:** Dynamically converts all xrpl-py BaseModel classes into MCP tools

**Key Functions:**

1. **Model Discovery:**
```python
def get_model_classes(module: ModuleType) -> Dict[str, Type[BaseModel]]:
    # Scans modules for BaseModel subclasses
    # Excludes interfaces, flags, and private classes
```

2. **Tool Generation:**
```python
def create_dynamic_model_tool(model_class: Type[BaseModel], category: str):
    # Creates MCP tool with proper parameter signature
    # Generates comprehensive documentation
    # Implements parameter conversion and validation
```

3. **Parameter Conversion:**
```python
def convert_field_value(field_name: str, value: object) -> object:
    # XRPL-specific type conversions
    # Currency code handling (3-char vs hex)
    # Amount field preservation (strings for XRP)
    # Boolean, numeric, and hex conversions
```

4. **Nested Processing:**
```python
def convert_nested_currencies(obj):
    # Recursively processes complex objects
    # Handles arrays and nested dictionaries
    # Applies currency conversion at any depth
```

## 🔄 Data Flow Architecture

### 1. Natural Language Request Processing

```
User Input → WebSocket → Agent Client → LangChain → Gemini Model
                                                        │
                                                        ▼
Response ← WebSocket ← Agent Client ← Tool Result ← MCP Tool Call
```

**Detailed Flow:**
1. User sends natural language message via WebSocket
2. Agent Client receives and logs the message
3. LangChain React Agent processes the request
4. Gemini model analyzes intent and selects appropriate tools
5. MCP tool calls are made to XRPL MCP Server
6. XRPL operations are executed and validated
7. Results are returned through the chain back to user

### 2. Direct Tool Call Processing

```
MCP Client → MCP Protocol → XRPL MCP Server → xrpl-py → XRPL Network
                                                │
                                                ▼
MCP Client ← Validated Result ← Parameter Conversion ← Raw Result
```

### 3. Parameter Transformation Pipeline

```
Raw Input → Field Type Detection → XRPL Conversion → Validation → Model Creation
```

**Conversion Rules:**
- **Currency Fields**: Auto-detect and hex-encode if >3 characters
- **Amount Fields**: Preserve as strings for XRP drops
- **Field Names**: Convert snake_case to PascalCase
- **Nested Objects**: Recursive processing for complex structures
- **Arrays**: Process each element individually

## 🧮 Tool Registration System

### Dynamic Registration Process

1. **Module Scanning:**
   - Imports all xrpl model modules
   - Scans for BaseModel subclasses
   - Categorizes by module type (transactions, requests, etc.)

2. **Tool Creation:**
   - Extracts field information from dataclass metadata
   - Generates function signatures dynamically
   - Creates parameter documentation
   - Implements validation logic

3. **MCP Registration:**
   - Registers tools with FastMCP framework
   - Creates proper MCP tool schemas
   - Handles tool discovery and execution

### Tool Naming Convention

```python
# Pattern: create_{category}_{model_name}
"Payment" → "create_transaction_payment"
"AccountInfo" → "create_request_accountinfo"
"IssuedCurrencyAmount" → "create_amount_issuedcurrencyamount"
```

### Tool Categories and Counts

| Category | Count | Module Source | Purpose |
|----------|-------|---------------|---------|
| Transactions | 61 | `xrpl.models.transactions` | XRPL transaction creation |
| Requests | 52 | `xrpl.models.requests` | Network query objects |
| Amounts | 2 | `xrpl.models.amounts` | Currency amount objects |
| Currencies | 3 | `xrpl.models.currencies` | Currency specification |
| Utilities | 38 | Various `xrpl.*` modules | Helper functions |

## 🔐 Parameter Validation System

### Validation Pipeline

1. **Required Field Check:**
   - Identifies missing required parameters
   - Returns detailed error with field schemas

2. **Type Conversion:**
   - Applies XRPL-specific conversions
   - Handles special cases (amounts, currencies, etc.)

3. **Enum Validation:**
   - Validates enum values against allowed options
   - Provides helpful error messages with valid choices

4. **Model Creation:**
   - Instantiates xrpl-py model with converted parameters
   - Catches and reports model validation errors

### Error Response Format

```json
{
  "success": false,
  "error": "Missing required fields: [destination]",
  "model_class": "Payment",
  "required_fields": ["account", "destination", "amount"],
  "optional_fields": ["fee", "flags", "memos"],
  "provided_fields": ["account", "amount"],
  "field_schemas": {
    "destination": {
      "required": true,
      "type": "str",
      "description": "The destination account address"
    }
  }
}
```

## 🌐 Network Integration

### XRPL Network Configuration

**Default Setup:**
- **Network**: XRPL Testnet
- **URL**: `https://s.altnet.rippletest.net:51234/`
- **Client**: AsyncJsonRpcClient (for async operations)

**Mainnet Configuration:**
```python
# Change in xrpl/server/config.py
xrpl_client = AsyncJsonRpcClient("https://s1.ripple.com:51234/")
```

### Network Operations

1. **Account Queries**: Balance, lines, objects, transactions
2. **Ledger Operations**: Current state, historical data, validation
3. **Transaction Submission**: Sign, validate, submit, monitor
4. **Server Information**: Network status, fees, definitions

## 🔧 Performance Architecture

### Optimization Strategies

1. **Async Processing:**
   - All network operations use async/await
   - Non-blocking I/O for concurrent requests
   - WebSocket connections maintained efficiently

2. **Caching Opportunities:**
   - Tool schemas (static after startup)
   - Account information (short-term caching)
   - Ledger data (immutable historical data)

3. **Resource Management:**
   - Connection pooling for XRPL network
   - Memory-efficient tool registration
   - Garbage collection for conversation history

### Scalability Considerations

**Current Bottlenecks:**
- Google API rate limits (60 requests/minute)
- Single-threaded MCP tool execution
- In-memory conversation storage

**Scaling Solutions:**
- Multiple API keys for rate limit distribution
- Queue-based async tool execution
- Redis for distributed conversation state
- Load balancing for multiple agent instances

## 🛡️ Security Architecture

### Current Security Model

1. **Development Mode:**
   - No authentication required
   - CORS allows all origins
   - Full access to all tools

2. **API Key Protection:**
   - Google API key secured in environment
   - Not exposed in responses or logs

### Production Security Recommendations

1. **Authentication:**
```python
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    # Implement key validation
```

2. **Rate Limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
```

3. **Input Sanitization:**
   - XRPL address validation
   - Parameter type checking
   - SQL injection prevention (if database added)

## 📊 Monitoring and Observability

### Current Logging

**Log Locations:**
- MCP Server: `logs/mcp_server.log`
- Agent Client: `logs/agent_client.log`

**Log Contents:**
- Tool registration events
- Request processing
- Error conditions
- Performance metrics

### Monitoring Recommendations

1. **Metrics Collection:**
   - Tool execution times
   - Error rates by tool type
   - WebSocket connection counts
   - Memory and CPU usage

2. **Health Checks:**
   - Server availability endpoints
   - Tool registration verification
   - XRPL network connectivity

3. **Alerting:**
   - High error rates
   - Service unavailability
   - Resource exhaustion

## 🔄 Development Workflow

### Local Development Setup

1. **Environment Preparation:**
```bash
poetry install              # Install dependencies
export GOOGLE_API_KEY="..."  # Set API key
```

2. **Server Startup:**
```bash
# Terminal 1: MCP Server
poetry run python -m xrpl.server.main

# Terminal 2: Agent Client  
cd client && poetry run python client.py
```

3. **Testing:**
```bash
poetry run python test_mcp_tools.py      # Direct tool testing
poetry run python test_currency_agent.py # Currency conversion
```

### Code Modification Guidelines

1. **Adding New Tools:**
   - Tools are auto-generated from xrpl-py models
   - No manual registration required
   - Test with `./scripts/dev.sh health`

2. **Modifying Parameter Conversion:**
   - Edit `convert_field_value()` in `enhanced_main.py`
   - Test thoroughly with currency conversion
   - Verify all amount fields still work

3. **Changing Agent Behavior:**
   - Modify system prompt in `client.py`
   - Test natural language understanding
   - Verify tool selection accuracy

### Debugging Workflow

1. **Check Server Status:**
```bash
./scripts/dev.sh health  # Verify 156 tools loaded
curl http://localhost:8080/tools | jq '.tools | length'
```

2. **Review Logs:**
```bash
./scripts/dev.sh logs    # Recent log entries
tail -f logs/mcp_server.log  # Real-time monitoring
```

3. **Test Specific Components:**
```bash
./scripts/dev.sh test-tools     # MCP tools only
./scripts/dev.sh test-currency  # Currency conversion
```

---

This technical architecture documentation provides the complete implementation details needed to understand, maintain, and extend the XRPL MCP Server system.

*Last Updated: August 15, 2025*