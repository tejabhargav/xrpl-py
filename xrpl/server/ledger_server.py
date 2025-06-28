"""XRPL Ledger MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import ledger-related modules
    import xrpl.asyncio.ledger.main
    
    print("Starting Ledger MCP Server on port 8002...")
    mcp.run("sse", port=8002) 