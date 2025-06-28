"""XRPL Wallet MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import wallet-related modules
    import xrpl.asyncio.wallet.wallet_generation
    
    print("Starting Wallet MCP Server on port 8004...")
    mcp.run("sse", port=8004) 