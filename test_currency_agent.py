#!/usr/bin/env python3
"""Test currency conversion via AI agent."""

import asyncio
import json
import websockets

async def test_currency_agent():
    """Test currency conversion through the AI agent."""
    
    uri = "ws://localhost:8080/chat"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to XRPL AI Agent WebSocket")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            print("📨 Welcome:", json.loads(welcome))
            
            test_queries = [
                "Create a payment transaction sending 500 USDC from rhARfQZ2xqQYnm65VYFoXYgHrcsjr3a7ta to rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe, with USDC issued by rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq",
                "Create a trust line for CUSTOMTOKEN issued by rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq with limit 10000 for account rhARfQZ2xqQYnm65VYFoXYgHrcsjr3a7ta",
                "Create an offer trading 1000 USDC for 5000 CUSTOMTOKEN where both are issued by rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n🧪 Test {i}: {query[:50]}...")
                
                # Send query
                await websocket.send(json.dumps({"message": query}))
                
                # Receive responses until we get the agent response
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data['type'] == 'agent_response':
                        print(f"  ✅ Agent response received for test {i}")
                        # Check if the response contains hex currency codes
                        message = data.get('message', '')
                        if '55534443' in message or '435553544F4D544F4B454E' in message:
                            print(f"  🎯 Currency auto-conversion detected!")
                        print(f"  📝 Response preview: {message[:200]}...")
                        break
                    elif data['type'] == 'error':
                        print(f"  ❌ Error in test {i}: {data.get('message', '')}")
                        break
                        
                # Wait between tests
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_currency_agent())