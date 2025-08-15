"""XRPL MCP Server main entry point."""

from xrpl.server.config import mcp

if __name__ == "__main__":
    # Import modules that contain MCP tools to register them
    import xrpl.asyncio.account.main
    import xrpl.asyncio.ledger.main
    import xrpl.asyncio.transaction.main
    import xrpl.asyncio.wallet.wallet_generation
    import xrpl.core.addresscodec.main
    import xrpl.core.binarycodec.main
    import xrpl.core.keypairs.main

    # Import all model tools
    import xrpl.server.models.enhanced_main
    import xrpl.utils.get_nftoken_id
    import xrpl.utils.get_xchain_claim_id
    import xrpl.utils.parse_nftoken_id
    import xrpl.utils.str_conversions
    import xrpl.utils.time_conversions
    import xrpl.utils.txn_parser.get_balance_changes
    import xrpl.utils.txn_parser.get_final_balances
    import xrpl.utils.txn_parser.get_order_book_changes
    import xrpl.utils.xrp_conversions
    
    # Check if running in stdio mode for Claude Code
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run("stdio")
    else:
        mcp.run("sse")