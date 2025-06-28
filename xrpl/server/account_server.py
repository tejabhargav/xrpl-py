"""XRPL Account MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import account-related modules
    import xrpl.asyncio.account.main
    
    print("Starting Account MCP Server on port 8001...")
    mcp.run("sse", port=8001) 