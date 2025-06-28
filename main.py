import asyncio
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient


async def main():
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        exit(1)
    
    # # Create configuration for the XRPL MCP server
    config = {
        "mcpServers": {
            "tokenization-module": {"url": "http://localhost:8081/mcp", "transport": "sse", "timeout": 6000, "sse_read_timeout": 6000}
        }
    }
    
    # Create MCPClient from configuration
    client = MCPClient.from_config_file(
        os.path.join(os.path.dirname(__file__), "w3saas_config.json")
    )
    
    # Create Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1,
        verbose=True
    )
    
    # Create agent with the client
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=30,
        auto_initialize=True
    )
    
    try:
        # Welcome message
        print("\nXRPL MCP Client powered by mcp_use and Gemini AI")
        print("Type 'exit' or 'quit' to end the session\n")
        
        # Interactive loop
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() in ['exit', 'quit']:
                print("Exiting client.")
                break
            
            if not query:
                continue
            
            print("\nProcessing...\n")
            
            # Run the query through the agent
            result = await agent.run(query)
            print(f"\nResult:\n{result}")
            
    finally:
        # Ensure we clean up resources properly
        if client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())