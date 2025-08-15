#!/usr/bin/env python3
"""Test script to verify MCP tools are working correctly."""

import asyncio
import json
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_tools():
    """Test the MCP server tools."""
    
    # Configure the MCP server connection
    server_config = {
        "xrpl": {
            "url": "http://localhost:8000/sse", 
            "transport": "sse", 
            "timeout": 6000, 
            "sse_read_timeout": 6000
        },
    }
    
    print("🔌 Connecting to XRPL MCP Server...")
    
    try:
        # Connect to MCP server
        client = MultiServerMCPClient(server_config)
        
        # Get all available tools
        print("🔍 Loading MCP tools...")
        tools = await client.get_tools()
        
        print(f"✅ Successfully loaded {len(tools)} tools!")
        print("\n📋 Available tools:")
        
        # Group tools by category
        categories = {}
        for tool in tools:
            name = tool.name
            if name.startswith("create_transaction_"):
                category = "Transaction"
                model_name = name.replace("create_transaction_", "")
            elif name.startswith("create_request_"):
                category = "Request"
                model_name = name.replace("create_request_", "")
            elif name.startswith("create_amount_"):
                category = "Amount"
                model_name = name.replace("create_amount_", "")
            elif name.startswith("create_currency_"):
                category = "Currency"
                model_name = name.replace("create_currency_", "")
            else:
                category = "Other"
                model_name = name
                
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "name": name,
                "model": model_name,
                "description": getattr(tool, 'description', 'No description')
            })
        
        for category, tool_list in categories.items():
            print(f"\n  {category} Tools ({len(tool_list)}):")
            for tool_info in tool_list[:5]:  # Show first 5 of each category
                print(f"    - {tool_info['name']}")
            if len(tool_list) > 5:
                print(f"    ... and {len(tool_list) - 5} more")
        
        # Test a simple transaction tool
        print(f"\n🧪 Testing Payment transaction tool...")
        payment_tool = None
        for tool in tools:
            if tool.name == "create_transaction_payment":
                payment_tool = tool
                break
        
        if payment_tool:
            print(f"✅ Found Payment tool: {payment_tool.name}")
            
            # Test with basic parameters
            try:
                result = await payment_tool.ainvoke({
                    "account": "rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH",
                    "destination": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", 
                    "amount": "1000000"
                })
                
                print("✅ Payment tool executed successfully!")
                print("📄 Result:")
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2))
                else:
                    print(str(result))
                    
            except Exception as e:
                print(f"❌ Payment tool failed: {e}")
                print(f"   Tool signature: {payment_tool}")
        else:
            print("❌ Payment tool not found!")
            
        # Test an amount tool
        print(f"\n🧪 Testing XRP amount tool...")
        xrp_tool = None
        for tool in tools:
            if tool.name == "create_currency_xrp":
                xrp_tool = tool
                break
                
        if xrp_tool:
            try:
                result = await xrp_tool.ainvoke({})
                print("✅ XRP currency tool executed successfully!")
                print("📄 Result:")
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2))
                else:
                    print(str(result))
            except Exception as e:
                print(f"❌ XRP tool failed: {e}")
        
        # Test account info request
        print(f"\n🧪 Testing AccountInfo request tool...")
        account_info_tool = None
        for tool in tools:
            if tool.name == "create_request_accountinfo":
                account_info_tool = tool
                break
                
        if account_info_tool:
            try:
                result = await account_info_tool.ainvoke({
                    "account": "rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH"
                })
                print("✅ AccountInfo tool executed successfully!")
                print("📄 Result:")
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2))
                else:
                    print(str(result))
            except Exception as e:
                print(f"❌ AccountInfo tool failed: {e}")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        return

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())