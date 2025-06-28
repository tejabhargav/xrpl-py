"""XRPL Codec MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import codec-related modules
    import xrpl.core.addresscodec.main
    import xrpl.core.binarycodec.main
    import xrpl.core.keypairs.main
    
    print("Starting Codec MCP Server on port 8005...")
    mcp.run("sse", port=8005) 