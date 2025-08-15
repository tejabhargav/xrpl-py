# XRPL MCP Server - Development Guide

## 🎯 Developer Onboarding

### For New Developers Joining the Project

This guide provides everything needed to understand, modify, and extend the XRPL MCP Server project.

## 🧠 Core Concepts Understanding

### What is MCP (Model Context Protocol)?
- **Standard**: Protocol for exposing tools/functions to AI systems
- **Purpose**: Allows AI agents to call specific functions with proper parameters
- **Implementation**: FastMCP framework provides the server infrastructure
- **Benefits**: Standardized way for AI to interact with external systems

### What is a React Agent?
- **Framework**: LangChain's agent that can use tools
- **Behavior**: Thinks, acts, observes in cycles until task completion
- **Tool Use**: Can call multiple tools in sequence to accomplish complex tasks
- **Integration**: Connects to MCP servers to access available tools

### XRPL Integration Strategy
- **Abstraction**: Every xrpl-py operation becomes an MCP tool
- **Dynamic Generation**: Tools created automatically from model classes
- **Validation**: Each tool validates parameters according to XRPL specifications
- **AI Interface**: Natural language requests converted to tool calls

## 🔍 Critical Code Understanding

### 1. Tool Generation (`xrpl/server/models/enhanced_main.py`)

**This is the most important file in the project**

```python
def create_dynamic_model_tool(model_class: Type[BaseModel], category: str):
    """
    Creates MCP tool from XRPL model class
    - Extracts field information from dataclass
    - Generates function signature dynamically  
    - Implements parameter conversion logic
    - Registers with MCP framework
    """
```

**Key Understanding Points:**
- **Dynamic Creation**: Tools aren't hand-written, they're generated from xrpl-py models
- **Parameter Extraction**: Uses `__dataclass_fields__` to get field information
- **Type Conversion**: Special logic for XRPL requirements (amounts, currencies, etc.)
- **Validation**: Comprehensive error handling with helpful messages

### 2. Parameter Conversion Logic

**Most Critical Function:**
```python
def convert_field_value(field_name: str, value: object) -> object:
    # Currency conversion (>3 chars → hex)
    if field_name == "currency" and isinstance(value, str):
        if len(value) > 3:
            hex_currency = value.encode('utf-8').hex().upper()
            return hex_currency.ljust(40, '0')
    
    # Amount preservation (keep as strings for XRP)
    if field_name in ["amount", "balance", "limit", "fee", ...]:
        if isinstance(value, str) and value.isdigit():
            return value  # Keep as string for XRP drops
```

**Why This Matters:**
- **XRPL Compliance**: XRPL has specific requirements for data formats
- **Currency Codes**: Must be 3 chars OR 40-char hex strings
- **XRP Amounts**: Must be strings representing drops, not numbers
- **Field Names**: Must be PascalCase, not snake_case

### 3. React Agent System Prompt

**Location:** `client/client.py` lines 23-219

**Critical Sections:**
```python
system_prompt = """
CRITICAL INSTRUCTIONS:
1. NEVER create or provide transaction JSON manually - ALWAYS use the appropriate MCP tools
2. When a user requests any transaction, request, or data, you MUST execute the corresponding tool
3. ALL transaction objects, account information, ledger data, and network responses MUST come directly from tool execution results
"""
```

**Understanding:**
- **Tool-First Approach**: Agent must use tools, not generate JSON manually
- **Complete Documentation**: Contains descriptions of all 156 tools
- **Format Specifications**: Detailed XRPL format requirements
- **Error Prevention**: Instructions to avoid common mistakes

## 🛠️ Development Workflow

### Setting Up Development Environment

1. **Prerequisites Check:**
```bash
python3 --version  # Must be 3.10+
poetry --version   # Must be installed
echo $GOOGLE_API_KEY  # Must be set
```

2. **Quick Start:**
```bash
./run.sh  # One-click setup and run
```

3. **Manual Start:**
```bash
./scripts/dev.sh setup   # Initial setup
./scripts/dev.sh start   # Start servers
./scripts/dev.sh test    # Verify everything works
```

### Development Commands

```bash
# Server management
./scripts/dev.sh start      # Start both servers
./scripts/dev.sh stop       # Stop all servers  
./scripts/dev.sh restart    # Restart everything
./scripts/dev.sh health     # Check status

# Testing
./scripts/dev.sh test       # Run all tests
./scripts/dev.sh test-tools # Test MCP tools only
./scripts/dev.sh test-ws    # Test WebSocket interface
./scripts/dev.sh test-currency  # Test currency conversion

# Debugging
./scripts/dev.sh logs       # View recent logs
./scripts/dev.sh clean      # Clean up processes and logs

# Code quality
./scripts/dev.sh lint       # Run linting
./scripts/dev.sh format     # Format code
```

### Testing Your Changes

**Always run after making changes:**
```bash
./scripts/dev.sh test
```

**Specific test scenarios:**
```bash
# Test tool registration
curl http://localhost:8080/tools | jq '.tools | length'
# Should return: 156

# Test currency conversion
poetry run python test_currency_agent.py
# Should show USDC → hex conversion

# Test natural language
# Connect to ws://localhost:8080/chat
# Send: "Create a payment sending 10 XRP"
```

## 🔧 Common Development Tasks

### Task 1: Adding New Parameter Conversion

**When:** Need to handle new XRPL field types

**Where:** `xrpl/server/models/enhanced_main.py`

**How:**
```python
def convert_field_value(field_name: str, value: object) -> object:
    # Add new conversion logic
    if field_name == "new_field_type":
        return convert_special_format(value)
    
    # Existing logic continues...
```

**Testing:**
- Create test transaction using the new field
- Verify conversion works correctly
- Check that XRPL accepts the format

### Task 2: Modifying Agent Behavior

**When:** Need to change how AI processes requests

**Where:** `client/client.py` system prompt

**How:**
```python
system_prompt = """
# Add new instructions
When user asks for X, you should Y...

# Existing instructions...
"""
```

**Testing:**
- Test with WebSocket interface
- Verify AI follows new instructions
- Check that tool selection is correct

### Task 3: Adding New Network Support

**When:** Need to connect to different XRPL network

**Where:** `xrpl/server/config.py`

**How:**
```python
# Change network URL
xrpl_client = AsyncJsonRpcClient("https://your-custom-node:51234/")
```

**Testing:**
- Verify connection works
- Test account queries
- Confirm transaction validation

### Task 4: Debugging Tool Issues

**Symptoms:** Tools not loading, parameter errors, validation failures

**Debug Steps:**
1. **Check Tool Count:**
```bash
curl http://localhost:8080/tools | jq '.tools | length'
```

2. **Review Tool Registration:**
```bash
grep "Found.*models" logs/mcp_server.log
```

3. **Test Specific Tool:**
```python
# In test_mcp_tools.py
result = await tool.ainvoke({"param": "value"})
print(result)
```

4. **Check Parameter Conversion:**
```python
# Add debug prints in convert_field_value()
print(f"Converting {field_name}={value} → {converted_value}")
```

## 🚨 Common Pitfalls and Solutions

### Issue 1: Parameter Type Errors

**Error:** `"expected Union[IssuedCurrencyAmount, MPTAmount, str]"`

**Cause:** Amount field converted to int instead of kept as string

**Solution:**
```python
# In convert_field_value(), ensure amount fields stay as strings
if field_name in ["amount", "taker_gets", "taker_pays", ...]:
    if isinstance(value, str) and value.isdigit():
        return value  # Don't convert to int!
```

### Issue 2: Currency Not Converting to Hex

**Error:** XRPL rejects currency codes longer than 3 characters

**Cause:** Nested currency conversion not working

**Solution:**
```python
# Ensure convert_nested_currencies() is called
converted_value = convert_nested_currencies(converted_value)
```

### Issue 3: Tools Not Loading

**Error:** Tool count less than 156

**Cause:** Import error or model scanning issue

**Solution:**
1. Check imports in `xrpl/server/main.py`
2. Verify model scanning logic in `get_model_classes()`
3. Look for Python import errors in logs

### Issue 4: Agent Not Understanding Requests

**Error:** AI gives generic responses instead of using tools

**Cause:** System prompt issues or tool descriptions unclear

**Solution:**
1. Review system prompt in `client/client.py`
2. Verify tool descriptions are accurate
3. Test with simpler, more direct requests

## 📊 Performance Optimization

### Monitoring Performance

**Key Metrics:**
```python
# Tool execution time
start_time = time.time()
result = await tool.ainvoke(params)
execution_time = time.time() - start_time

# Memory usage
import psutil
memory_percent = psutil.virtual_memory().percent

# Active connections
connection_count = len(active_connections)
```

**Optimization Opportunities:**

1. **Caching:**
```python
# Cache tool schemas (don't regenerate every time)
@lru_cache(maxsize=200)
def get_tool_schema(model_class):
    return generate_schema(model_class)
```

2. **Connection Pooling:**
```python
# Reuse XRPL connections
class XRPLConnectionPool:
    def __init__(self, max_connections=10):
        self.pool = []
        self.max_connections = max_connections
```

3. **Async Processing:**
```python
# Process multiple tools concurrently
tasks = [tool1.ainvoke(params1), tool2.ainvoke(params2)]
results = await asyncio.gather(*tasks)
```

## 🔮 Extension Opportunities

### Adding New Features

1. **Real-time XRPL Subscriptions:**
```python
# Subscribe to account changes
@mcp.tool()
async def subscribe_account_changes(account: str):
    # WebSocket subscription to XRPL
    async with websockets.connect(xrpl_ws_url) as ws:
        await ws.send(json.dumps({
            "command": "subscribe",
            "accounts": [account]
        }))
```

2. **Historical Data Analysis:**
```python
@mcp.tool()
async def analyze_account_history(account: str, days: int):
    # Fetch and analyze transaction history
    transactions = await get_account_transactions(account, days)
    return analyze_patterns(transactions)
```

3. **Multi-Network Support:**
```python
@mcp.tool()
async def switch_network(network: str):
    # Dynamically change XRPL network
    global xrpl_client
    xrpl_client = AsyncJsonRpcClient(networks[network])
```

### Integration Opportunities

1. **Database Integration:**
```python
# Store conversation history
class ConversationStore:
    async def save_conversation(self, user_id, messages):
        # Save to PostgreSQL/MongoDB
        
    async def load_conversation(self, user_id):
        # Load previous context
```

2. **Webhook Integration:**
```python
@app.post("/webhook/xrpl")
async def handle_xrpl_event(event: XRPLEvent):
    # Process XRPL network events
    # Notify connected clients
```

3. **Multi-Language Support:**
```javascript
// JavaScript SDK
class XRPLMCPClient {
    constructor(wsUrl) {
        this.ws = new WebSocket(wsUrl);
    }
    
    async createPayment(account, destination, amount) {
        return await this.sendRequest(`Create payment ${amount} from ${account} to ${destination}`);
    }
}
```

## 🎓 Best Practices

### Code Organization

1. **Separation of Concerns:**
   - MCP Server: Tool registration and execution
   - Agent Client: AI processing and WebSocket handling
   - Models: Data validation and conversion

2. **Error Handling:**
```python
try:
    result = await process_request()
    return {"success": True, "data": result}
except ValidationError as e:
    return {"success": False, "error": f"Validation failed: {e}"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"success": False, "error": "Internal server error"}
```

3. **Logging:**
```python
import logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def my_tool(param: str):
    logger.info(f"Executing my_tool with param={param}")
    try:
        result = await execute_logic(param)
        logger.info(f"Tool succeeded with result={result}")
        return result
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        raise
```

### Testing Practices

1. **Unit Tests:**
```python
def test_currency_conversion():
    result = convert_field_value("currency", "USDC")
    expected = "5553444300000000000000000000000000000000"
    assert result == expected
```

2. **Integration Tests:**
```python
async def test_payment_creation():
    tool = get_payment_tool()
    result = await tool.ainvoke({
        "account": "rTest123",
        "destination": "rTest456", 
        "amount": "1000000"
    })
    assert result["TransactionType"] == "Payment"
```

3. **End-to-End Tests:**
```python
async def test_natural_language_payment():
    ws = await connect_websocket()
    await ws.send(json.dumps({
        "message": "Send 10 XRP from rA to rB"
    }))
    response = await ws.recv()
    assert "Payment" in response["message"]
```

---

This development guide provides all the knowledge needed to successfully work with the XRPL MCP Server codebase. Follow these patterns and practices to maintain code quality and system reliability.

*Last Updated: August 15, 2025*