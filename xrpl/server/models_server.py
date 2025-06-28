"""XRPL Models MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import model-related modules
    import xrpl.server.models.enhanced_main
    
    print("Starting Models MCP Server on port 8006...")
    mcp.run("sse", port=8006) 