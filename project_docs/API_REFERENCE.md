# XRPL MCP Server API Reference

Complete API documentation for the XRPL MCP Server and React Agent Client.

## Overview

The XRPL MCP Server provides two main interfaces:
1. **MCP Protocol Interface** - Direct tool access via MCP clients
2. **WebSocket/REST API** - HTTP and WebSocket access for web applications

## MCP Protocol Interface

### Connection Details

**Protocol**: Model Context Protocol (MCP)
**Transport**: Server-Sent Events (SSE) / stdio
**URL**: `http://localhost:8000/sse`

### Available Tools

The system exposes 156 XRPL tools across 5 categories:

#### Transaction Tools (61)
Create XRPL transaction objects with proper validation.

**Naming Pattern**: `create_transaction_{transaction_type}`

Examples:
- `create_transaction_payment` - Payment transactions
- `create_transaction_trustset` - Trust line creation
- `create_transaction_offercreate` - Order book offers
- `create_transaction_nftokenmint` - NFT minting
- `create_transaction_ammcreate` - AMM pool creation

**Common Parameters**:
- `account` (required) - Source account address
- `fee` (optional) - Transaction fee in drops
- `flags` (optional) - Transaction flags
- `memos` (optional) - Array of memo objects
- `sequence` (optional) - Account sequence number

#### Request Tools (52)
Create XRPL request objects for querying network data.

**Naming Pattern**: `create_request_{request_type}`

Examples:
- `create_request_accountinfo` - Account information
- `create_request_accountlines` - Trust lines
- `create_request_ledger` - Ledger data
- `create_request_tx` - Transaction lookup

**Common Parameters**:
- `account` (often required) - Target account address  
- `ledger_index` (optional) - Ledger version ("validated", "current", or number)
- `limit` (optional) - Maximum results to return

#### Amount Tools (2)
Create properly formatted amount objects.

- `create_amount_issuedcurrencyamount` - Non-XRP currency amounts
- `create_amount_mptamount` - Multi-Purpose Token amounts

#### Currency Tools (3) 
Create currency specification objects.

- `create_currency_xrp` - XRP currency
- `create_currency_issuedcurrency` - Issued currencies  
- `create_currency_mptcurrency` - Multi-Purpose Token currencies

#### Utility Tools (38)
Various XRPL utility functions for addresses, encoding, parsing, etc.

Examples:
- `encode_classic_address` - Address encoding
- `decode_classic_address` - Address decoding
- `get_balance_changes` - Transaction parsing
- `xrp_to_drops` - XRP conversion

### Tool Response Format

All tools return validated XRPL objects:

```json
{
  "Account": "rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH",
  "TransactionType": "Payment", 
  "Amount": "1000000",
  "Destination": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
  "SigningPubKey": ""
}
```

### Error Handling

Validation errors return detailed information:

```json
{
  "success": false,
  "error": "Missing required fields: [destination]",
  "model_class": "Payment",
  "required_fields": ["account", "destination", "amount"],
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

## WebSocket API

### Connection

**URL**: `ws://localhost:8080/chat`
**Protocol**: WebSocket
**Format**: JSON messages

### Message Format

#### Client to Server
```json
{
  "message": "Your request in natural language or specific instruction"
}
```

#### Server to Client

**System Messages**:
```json
{
  "type": "system",
  "message": "Connected to XRPL AI Agent! Available tools: 156",
  "tools_count": 156
}
```

**User Acknowledgment**:
```json
{
  "type": "user_message_received", 
  "message": "Create a payment transaction..."
}
```

**Processing Indicator**:
```json
{
  "type": "typing",
  "message": "Agent is thinking..."
}
```

**Agent Response**:
```json
{
  "type": "agent_response",
  "message": "Here is your transaction:\n```json\n{...}\n```",
  "metadata": {
    "model": "gemini-2.0-flash",
    "tokens": 1234
  }
}
```

**Error Messages**:
```json
{
  "type": "error",
  "message": "Error processing request: Invalid account address"
}
```

### Natural Language Examples

The AI agent can understand various request formats:

```javascript
// Simple payment
ws.send(JSON.stringify({
  message: "Send 10 XRP from rAccount1 to rAccount2"
}));

// Complex transaction
ws.send(JSON.stringify({
  message: "Create a trust line for USDC issued by Bitstamp with a limit of 10000 for account rMyAccount"
}));

// Data requests  
ws.send(JSON.stringify({
  message: "Get account information for rAccountAddress"
}));

// NFT operations
ws.send(JSON.stringify({
  message: "Mint an NFT with taxon 1 and 2% transfer fee"
}));
```

## REST API

### Health Check

**GET** `http://localhost:8080/`

**Response**:
```json
{
  "message": "XRPL AI Agent API is running",
  "tools_count": 156
}
```

### Available Tools

**GET** `http://localhost:8080/tools`

**Response**:
```json
{
  "tools": [
    {
      "name": "create_transaction_payment",
      "description": "Create a Payment transaction and return its dictionary representation..."
    },
    ...
  ]
}
```

## Parameter Formats

### Account Addresses
All XRPL addresses use classic format:
```
rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH
```

### Amount Formats

**XRP Amounts** (string in drops):
```json
"1000000"  // 1 XRP = 1,000,000 drops
```

**Issued Currency Amounts** (object):
```json
{
  "currency": "USD",
  "issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq", 
  "value": "100.50"
}
```

### Currency Codes

The system automatically handles currency formats per XRPL requirements:

**Standard Currencies**:
- `"XRP"` - Always use exactly "XRP"
- `"USD"`, `"EUR"`, `"BTC"` - 3-character codes as-is

**Custom Currencies** (auto-converted to hex):
- `"USDC"` → `"5553444300000000000000000000000000000000"`
- `"CUSTOMTOKEN"` → `"435553544F4D544F4B454E000000000000000000"`

### Flag Formats

Flags can be specified in multiple ways:

**Integer format**:
```json
{
  "flags": 131072
}
```

**Array format**:
```json
{
  "flags": [131072, 65536]
}
```

**Dictionary format**:
```json
{
  "flags": {
    "TF_PARTIAL_PAYMENT": true,
    "TF_NO_RIPPLE_DIRECT": false
  }
}
```

### Memo Format

Memos use hex-encoded strings:

```json
{
  "memos": [
    {
      "memo": {
        "memo_data": "48656C6C6F20576F726C64",  // "Hello World" in hex
        "memo_format": "746578742F706C61696E",    // "text/plain" in hex  
        "memo_type": "4D656D6F"                   // "Memo" in hex
      }
    }
  ]
}
```

## Error Codes

### MCP Protocol Errors

**-32602**: Invalid request parameters
**-32603**: Internal error during processing
**-32000**: Tool execution error

### WebSocket/REST Errors

**400**: Bad Request - Invalid message format
**500**: Internal Server Error - Processing failure
**503**: Service Unavailable - MCP server connection issue

### Validation Errors

Common validation errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing required fields" | Required parameters not provided | Check tool schema and provide all required fields |
| "Invalid currency format" | Currency code not XRPL compliant | Use 3-char codes or let system auto-convert to hex |
| "Invalid account address" | Malformed XRPL address | Use valid classic format address |
| "Enum validation failed" | Invalid enum value | Check valid enum values in error message |

## Rate Limits

### Default Limits
- **WebSocket connections**: 10 concurrent per IP
- **MCP tool calls**: 100 per minute per connection
- **Request size**: 1MB maximum message size

### Customization
Modify limits in `client/client.py`:

```python
# Increase connection pool
server_config = {
    "xrpl": {
        "url": "http://localhost:8000/sse",
        "timeout": 30000  # Increase timeout
    }
}
```

## Authentication

### Current Implementation
- **Development mode**: No authentication required
- **API key validation**: Google API key for AI agent functionality

### Production Recommendations
```python
# Add API key authentication
@app.middleware("http")  
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != os.getenv("API_KEY"):
        return JSONResponse(status_code=401, content={"error": "Invalid API key"})
    return await call_next(request)
```

## SDK Examples

### Python SDK
```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def create_payment():
    server_config = {"xrpl": {"url": "http://localhost:8000/sse", "transport": "sse"}}
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    
    payment_tool = next(t for t in tools if t.name == "create_transaction_payment")
    
    result = await payment_tool.ainvoke({
        "account": "rSender123...",
        "destination": "rReceiver456...", 
        "amount": "1000000"
    })
    
    return result
```

### JavaScript SDK
```javascript
class XRPLMCPClient {
  constructor(wsUrl = 'ws://localhost:8080/chat') {
    this.ws = new WebSocket(wsUrl);
    this.messageId = 0;
    this.pendingRequests = new Map();
  }
  
  async sendRequest(message) {
    return new Promise((resolve, reject) => {
      const id = ++this.messageId;
      this.pendingRequests.set(id, { resolve, reject });
      
      this.ws.send(JSON.stringify({ id, message }));
      
      setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error('Request timeout'));
      }, 30000);
    });
  }
  
  async createPayment(account, destination, amount) {
    const message = `Create a payment sending ${amount} drops from ${account} to ${destination}`;
    return await this.sendRequest(message);
  }
}
```

---

For more examples and advanced usage, see the [README](README.md) and [setup guide](SETUP.md).