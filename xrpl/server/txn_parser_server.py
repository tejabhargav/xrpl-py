"""XRPL Transaction Parser MCP Server."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import transaction parser modules
    import xrpl.utils.txn_parser.get_balance_changes
    import xrpl.utils.txn_parser.get_final_balances
    import xrpl.utils.txn_parser.get_order_book_changes
    
    print("Starting Transaction Parser MCP Server on port 8008...")
    mcp.run("sse", port=8008) 