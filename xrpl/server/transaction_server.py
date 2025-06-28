"""XRPL Transaction MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import transaction-related modules
    import xrpl.asyncio.transaction.main
    
    print("Starting Transaction MCP Server on port 8003...")
    mcp.run("sse", port=8003) 