from mcp.server.fastmcp import FastMCP

from xrpl.asyncio.clients import AsyncJsonRpcClient

# Create global instances that can be shared across modules
xrpl_client = AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234/")
mcp = FastMCP("XRPL-MCP-Server") 