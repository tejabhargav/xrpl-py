"""XRPL Utils MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import utility modules
    import xrpl.utils.get_nftoken_id
    import xrpl.utils.get_xchain_claim_id
    import xrpl.utils.parse_nftoken_id
    import xrpl.utils.str_conversions
    import xrpl.utils.time_conversions
    
    print("Starting Utils MCP Server on port 8007...")
    mcp.run("sse", port=8007) 