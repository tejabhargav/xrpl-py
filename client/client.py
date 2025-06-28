import json
import os
from typing import Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print(os.getenv("GOOGLE_API_KEY"))
    exit(1)

# Define system prompt
system_prompt = """You are a XRPL AI AGENT with access to comprehensive XRPL MCP server tools. You have access to the following categories of tools:

**AMOUNTS & CURRENCIES:**
- create_issuedcurrencyamount: Specifies an amount in an issued currency
- create_mptamount: Specifies an MPT amount
- create_issuedcurrency: Specifies an issued currency (without a value)
- create_mptcurrency: Specifies an MPT currency (without a value)
- create_xrp: Specifies XRP as a currency (without a value)

**ACCOUNT OPERATIONS:**
- create_accountchannels: Returns information about an account's Payment Channels
- create_accountcurrencies: Retrieves a list of currencies an account can send/receive
- create_accountinfo: Retrieves information about an account, its activity, and XRP balance
- create_accountlines: Returns information about an account's trust lines
- create_accountnfts: Retrieves all NFTs currently owned by the specified account
- create_accountobjects: Returns the raw ledger format for all objects owned by an account
- create_accountoffers: Retrieves a list of offers made by a given account
- create_accounttx: Retrieves a list of transactions that involved the specified account

**TRANSACTION TYPES:**
- create_payment: Sends value from one account to another
- create_offercreate: Executes a limit order in the decentralized exchange
- create_offercancel: Removes an Offer object from the decentralized exchange
- create_trustset: Creates or modifies a trust line linking two accounts
- create_accountset: Modifies the properties of an account
- create_accountdelete: Deletes an account and sends the remaining XRP to a destination account
- create_escrowcreate: Locks up XRP until a specific time or condition is met
- create_escrowfinish: Delivers XRP from a held payment to the recipient
- create_escrowcancel: Returns escrowed XRP to the sender after the Escrow has expired
- create_paymentchannelcreate: Creates a payment channel and funds it with XRP
- create_paymentchannelclaim: Claims XRP from a payment channel, adjusts channel's expiration, or both
- create_paymentchannelfund: Adds additional XRP to an open payment channel

**NFT OPERATIONS:**
- create_nftokenmint: Creates an NFToken object
- create_nftokenburn: Removes an NFToken object, effectively burning the token
- create_nftokencreateoffer: Creates an offer to buy or sell an NFToken
- create_nftokenacceptoffer: Accepts an offer to buy or sell an NFToken
- create_nftokencanceloffer: Deletes existing NFTokenOffer objects
- create_nftokenmodify: Modifies an NFToken's URI
- create_nftbuyoffers: Retrieves all of buy offers for the specified NFToken
- create_nftselloffers: Retrieves all of sell offers for the specified NFToken
- create_nfthistory: Retrieves a list of transactions that involved the specified NFToken
- create_nftinfo: Retrieves all the information about the NFToken
- create_nftsbyissuer: Retrieves all of the NFTokens issued by an account

**AMM OPERATIONS:**
- create_ammcreate: Creates a new Automated Market Maker (AMM) instance
- create_ammdeposit: Deposits funds into an Automated Market Maker (AMM) instance
- create_ammwithdraw: Withdraws assets from an Automated Market Maker (AMM) instance
- create_ammbid: Bids on an Automated Market Maker's (AMM's) auction slot
- create_ammvote: Vote on the trading fee for an Automated Market Maker (AMM) instance
- create_ammdelete: Deletes an empty Automated Market Maker (AMM) instance
- create_ammclawback: Claws back tokens from a holder who has deposited your issued tokens into an AMM pool
- create_amminfo: Gets information about an Automated Market Maker (AMM) instance

**LEDGER OPERATIONS:**
- create_ledger: Retrieves information about the public ledger
- create_ledgerclosed: Returns the unique identifiers of the most recently closed ledger
- create_ledgercurrent: Returns the unique identifiers of the current in-progress ledger
- create_ledgerdata: Retrieves contents of the specified ledger
- create_ledgerentry: Returns a single ledger object in its raw format

**NETWORK & SERVER OPERATIONS:**
- create_serverinfo: Asks the server for a human-readable version of various information about the rippled server
- create_serverstate: Asks the server for machine-readable information about the rippled server's current state
- create_serverdefinitions: Asks the server for a human-readable version of various information about the rippled server being queried
- create_fee: Reports the current transaction cost requirements
- create_ping: Returns an acknowledgement to test connection status and latency
- create_random: Provides a random number for client-side random number generation

**TRANSACTION PROCESSING:**
- create_sign: Signs a transaction in JSON format and returns a signed binary representation
- create_signandsubmit: Signs and submits a transaction
- create_signfor: Provides one signature for a multi-signed transaction
- create_simulate: Simulates a transaction without submitting it to the network
- create_submit: Applies a transaction and sends it to the network
- create_submitmultisigned: Applies a multi-signed transaction and sends it to the network
- create_submitonly: Submits a signed, serialized transaction as a binary blob

**CRITICAL INSTRUCTIONS:**
1. NEVER create or provide transaction JSON manually - ALWAYS use the appropriate MCP tools
2. When a user requests any transaction, request, or data, you MUST execute the corresponding tool
3. ALL transaction objects, account information, ledger data, and network responses MUST come directly from tool execution results
4. If a user asks for a transaction creation, gather required parameters first, then execute the appropriate create_* tool
5. Return ONLY the exact output from the executed tools - do not modify or create your own JSON structures
6. For any XRPL operation, there is a corresponding tool that must be used
7. If additional information is needed, ask specific questions to gather required parameters for tool execution
8. Your role is to facilitate tool execution, not to generate XRPL data independently

Your goal is to help users interact with the XRPL network by executing the appropriate MCP tools and returning their exact results.

Here Is Extra Information:
---

# XRPL Transaction Types Documentation

This document provides detailed information about all transaction types available in the XRP Ledger, their required and optional parameters, and the flags that can be used with them.

## Common Transaction Fields

All transactions in the XRP Ledger share the following common fields:

| Field | Required | Description |
|-------|----------|-------------|
| `Account` | Yes | The sender's XRPL address |
| `TransactionType` | Yes | The type of transaction (e.g., "Payment", "AccountSet", etc.) |
| `Fee` | No (Auto-fillable) | The amount of XRP to destroy as a transaction cost (specified in drops) |
| `Sequence` | No (Auto-fillable) | The sequence number of the transaction |
| `LastLedgerSequence` | No (Auto-fillable) | The highest ledger index this transaction can appear in |
| `SourceTag` | No | An arbitrary source tag representing a hosted user or specific purpose |
| `Memos` | No | Additional arbitrary information attached to the transaction |
| `Signers` | No | For multi-signed transactions, signing data authorizing the transaction |

## Critical Format Information

### Amount Formats

XRP Ledger transactions can use two types of currency amounts: XRP and issued currencies.

#### XRP Amount Format
XRP is specified as a string representing the amount in drops (1 XRP = 1,000,000 drops).

Example: `"1000000"` (represents 1 XRP)

#### Issued Currency Amount Format
Issued currencies are specified as objects with three fields:```json
{
  "Currency": "USD",
  "Issuer": "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
  "Value": "100"
}
```

- `Currency`: Three-character currency code (or hex code for non-standard currencies)
- `Issuer`: XRPL address of the currency issuer
- `Value`: String representation of the amount

**Important Note**: if currency length is more than 3 the currency should be passed as hex-string . use convert currency tool to convert it. if currency is USD you can pass it directly if currency is USDC you should convert into HEX and pass it.

### Flag Formats

Flags can be specified in three ways:

1.  **Integer format**: A single integer with all the appropriate bits set
    Example: `131072` (represents TF_PARTIAL_PAYMENT)

2.  **Array format**: Array of integers representing individual flags
    Example: `[131072, 65536]` (represents TF_PARTIAL_PAYMENT and TF_NO_RIPPLE_DIRECT)

3.  **Dictionary format**: Object with flag names and boolean values
    Example: `{"TF_PARTIAL_PAYMENT": true, "TF_NO_RIPPLE_DIRECT": false}`

**Important Note**: For AccountSet transactions, the `SetFlag` and `ClearFlag` fields are separate parameters that accept integer values, not part of the `Flags` field.

### Memo Format

Memos are specified as an array of objects:

```json
[
  {
    "Memo": {
      "MemoData": "4861707079204E657720596561722032303234",
      "MemoFormat": "746578742F706C61696E",
      "MemoType": "687474703A2F2F6578616D706C652E636F6D2F6D656D6F2F67656E65726963"
    }
  }
]
```

- `MemoData`: Hex-encoded string containing the content of the memo
- `MemoFormat`: Hex-encoded string indicating the format (usually MIME type)
- `MemoType`: Hex-encoded string indicating the type (usually an RFC 5988 relation)

At least one of these fields must be present in each Memo object.

### Path Format

For cross-currency payments, paths are specified as arrays of arrays of path steps:

```json
[
  [
    {"Account": "rAccount1", "Currency": "USD", "Issuer": "rIssuer1"},
    {"Account": "rAccount2", "Currency": "EUR", "Issuer": "rIssuer2"}
  ],
  [
    {"Account": "rAccount3", "Currency": "GBP", "Issuer": "rIssuer3"},
    {"Account": "rAccount4", "Currency": "EUR", "Issuer": "rIssuer4"}
  ]
]
```

Each path is an array of path steps, and each path step is an object with Account, Currency, and Issuer fields.

"""

# FastAPI app
app = FastAPI(title="XRPL AI Agent API", version="1.0.0")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections and their conversation history
active_connections: Dict[WebSocket, List] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, List] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = []

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    def get_messages(self, websocket: WebSocket) -> List:
        return self.active_connections.get(websocket, [])

    def add_message(self, websocket: WebSocket, message):
        if websocket in self.active_connections:
            self.active_connections[websocket].append(message)


manager = ConnectionManager()


async def initialize_agent():
    """Initialize the XRPL agent with MCP tools"""
    # Define the configuration for the MCP server
    server_config = {
        "xrpl": {
            "url": "http://localhost:8000/sse", "transport": "sse", "timeout": 6000, "sse_read_timeout": 6000
        },
    }

    # Initialize the model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        top_p=0.95,
        max_tokens=4000,
        convert_system_message_to_human=False
    )

    # Connect to MCP server
    client = MultiServerMCPClient(server_config)
    
    # Load all tools from the connected MCP servers
    tools = await client.get_tools()
    # Fix schema issues for array parameters
    for tool in tools:
        if hasattr(tool, 'args_schema'):
            schema = tool.args_schema
            if isinstance(schema, dict) and 'properties' in schema:
                for param_name, param_schema in schema['properties'].items():
                    if (isinstance(param_schema, dict) and 
                            param_schema.get("type") == "array" and 
                            "items" not in param_schema):
                        param_schema["items"] = {"type": "string"}

    # Create the React agent with the loaded tools and system prompt
    agent = create_react_agent(model, tools, prompt=system_prompt, debug=True)
    
    return agent, client, tools


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    app.state.agent, app.state.client, app.state.tools = (
        await initialize_agent()
    )
    print(f"Agent initialized with {len(app.state.tools)} tools")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if hasattr(app.state, 'client'):
        await app.state.client.__aexit__(None, None, None)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "XRPL AI Agent API is running", 
        "tools_count": len(app.state.tools)
    }


@app.get("/tools")
async def get_tools():
    """Get available XRPL tools"""
    tools_info = []
    for tool in app.state.tools:
        tools_info.append({
            "name": tool.name,
            "description": getattr(tool, 'description', 
                                   'No description available')
        })
    return {"tools": tools_info}


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat communication"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        welcome_msg = (
            f"Connected to XRPL AI Agent! "
            f"Available tools: {len(app.state.tools)}"
        )
        await manager.send_message({
            "type": "system",
            "message": welcome_msg,
            "tools_count": len(app.state.tools)
        }, websocket)

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            if not user_message:
                continue
                
            # Send acknowledgment
            await manager.send_message({
                "type": "user_message_received",
                "message": user_message
            }, websocket)
            
            try:
                # Get conversation history for this connection
                messages = manager.get_messages(websocket)
                
                # Add user message to history
                human_msg = HumanMessage(content=user_message)
                messages.append(human_msg)
                manager.add_message(websocket, human_msg)
                
                # Send typing indicator
                await manager.send_message({
                    "type": "typing",
                    "message": "Agent is thinking..."
                }, websocket)
                
                # Get agent response
                response = await app.state.agent.ainvoke({"messages": messages})
                
                # Extract AI response
                ai_message = response['messages'][-1]
                
                # Update conversation history
                updated_messages = response['messages']
                manager.active_connections[websocket] = updated_messages
                
                # Prepare metadata
                model_name = ai_message.response_metadata.get(
                    'model_name', 'Unknown'
                )
                tokens = (
                    ai_message.usage_metadata['total_tokens'] 
                    if hasattr(ai_message, 'usage_metadata') 
                    else 'Unknown'
                )
                
                # Send agent response
                await manager.send_message({
                    "type": "agent_response",
                    "message": ai_message.content,
                    "metadata": {
                        "model": model_name,
                        "tokens": tokens
                    }
                }, websocket)
                
            except Exception as e:
                await manager.send_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
