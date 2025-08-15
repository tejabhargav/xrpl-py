#!/usr/bin/env python3
"""Test the React Agent via WebSocket."""

import asyncio
import json
import websockets

async def test_agent_websocket():
    """Test the agent via WebSocket interface."""
    
    uri = "ws://localhost:8080/chat"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to XRPL AI Agent WebSocket")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            print("📨 Welcome:", json.loads(welcome))
            
            test_queries = [
                "Create a payment transaction from rhARfQZ2xqQYnm65VYFoXYgHrcsjr3a7ta to rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe for 10 XRP",
                "Get account information for rhARfQZ2xqQYnm65VYFoXYgHrcsjr3a7ta",
                "Create a trust line for USD from rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq with limit 5000",
                "Create an NFT mint transaction with taxon 1 and transfer fee 2%"
            ]
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n🧪 Test {i}: {query}")
                
                # Send query
                await websocket.send(json.dumps({"message": query}))
                
                # Receive responses until we get the agent response
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    print(f"  📨 {data['type']}: {data.get('message', '')[:100]}...")
                    
                    if data['type'] == 'agent_response':
                        print(f"  ✅ Agent completed task {i}")
                        break
                    elif data['type'] == 'error':
                        print(f"  ❌ Error in task {i}")
                        break
                        
                # Wait a moment between tests
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_websocket())