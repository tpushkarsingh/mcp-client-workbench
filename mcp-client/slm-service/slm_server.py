import asyncio
import os
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm_client import LLMClient

# Configuration
REGISTRY_URL = "http://localhost:8002/api/v1/servers"
# Path to the WASM Runtime script relative to this file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_SCRIPT = os.path.join(SCRIPT_DIR, "..", "wasm-runtime", "run.sh")

# Global State
mcp_sessions: Dict[str, ClientSession] = {}
mcp_tools: List[Dict[str, Any]] = []
exit_stack = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_tools, exit_stack
    print("SLM Service Starting...")
    
    # 1. Fetch available tools from Registry
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(REGISTRY_URL)
            servers = resp.json()
        except Exception as e:
            print(f"Failed to fetch from Registry: {e}")
            servers = []

    print(f"Found {len(servers)} servers in Registry.")

    # 2. Connect to each tool via WASM Runtime
    # We maintain persistent connections for the life of the server
    from contextlib import AsyncExitStack
    exit_stack = AsyncExitStack()
    
    for server in servers:
        name = server['name']
        binary_url = server['binaryUrl']
        env = server.get('runtimeConfig', {})
        
        print(f"Connecting to {name} via WASM Runtime...")
        
        # Configure StdIO Transport
        server_params = StdioServerParameters(
            command=RUNTIME_SCRIPT,
            args=["--url", binary_url],
            env={**os.environ, **env} # Pass current env + runtime config
        )
        
        try:
            # Establish connection
            read, write = await exit_stack.enter_async_context(stdio_client(server_params))
            session = await exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            # List tools
            result = await session.list_tools()
            print('All available tools to slm server',result)
            for tool in result.tools:
                # We namespace tools to avoid collisions? Or just aggregate
                # For now, simple aggregation.
                # Note: MCP Tool object needs to be converted dict for our usage
                tool_def = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                mcp_tools.append(tool_def)
                mcp_sessions[tool.name] = session # Map tool name to session
                
            print(f"Connected to {name}. Tools: {[t.name for t in result.tools]}")
            
        except Exception as e:
            print(f"Failed to connect to {name}: {e}")

    print("--------------------------------------------------")
    print(f"SLM Service Startup Complete.")
    print(f"Total Tools Registered: {len(mcp_tools)}")
    print(f"Tool Names: {[t['name'] for t in mcp_tools]}")
    print("--------------------------------------------------")
    yield
    
    # Cleanup
    print("Shutting down...")
    await exit_stack.aclose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = LLMClient()

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]

class CallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

@app.post("/call")
async def call_tool_direct(request: CallRequest):
    print(f"Direct call requested for tool: {request.name} with args: {request.arguments}")
    session = mcp_sessions.get(request.name)
    if not session:
        raise HTTPException(status_code=404, detail=f"Tool {request.name} not found or not connected.")
    
    try:
        # Execute Tool via MCP
        result = await session.call_tool(request.name, arguments=request.arguments)
        return result
    except Exception as e:
        print(f"Direct tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    # System message to guide tool selection
    system_msg = {
        "role": "system", 
        "content": (
            "You are a helpful assistant with access to weather and activity recommendation tools. "
            "IMPORTANT: If the user provides a weather condition and temperature directly, "
            "use 'get_activity_recommendation' immediately. Do NOT call 'get_weather' if you already "
            "have the weather information."
        )
    }
    messages = [system_msg] + request.messages

    # Loop to handle multiple tool call rounds (e.g. fetch weather -> fetch activity)
    max_turns = 5
    for turn in range(max_turns):
        print(f"Turn {turn + 1}/{max_turns}...")
        
        # Ensure inputSchema is dict for the LLM
        current_tools = []
        for t in mcp_tools:
            schema = t["inputSchema"]
            if isinstance(schema, (str, bytes)):
                import json
                try:
                    schema = json.loads(schema)
                except:
                    pass
            current_tools.append({**t, "inputSchema": schema})
            
        response_msg = await llm.chat(messages, current_tools)
        
        if not response_msg.get('tool_calls'):
            print("No tool calls. Returning final response.")
            return response_msg
            
        print(f"Loop: Tool call requested by LLM: {[tc['function']['name'] for tc in response_msg['tool_calls']]}")
        messages.append(response_msg) # Add assistant's tool call message
        
        for tool_call in response_msg['tool_calls']:
            fn = tool_call['function']
            name = fn['name']
            args = fn['arguments']
            
            print(f"Executing tool: {name} with args: {args}")
            
            session = mcp_sessions.get(name)
            if not session:
                messages.append({"role": "tool", "content": f"Error: Tool {name} not found.", "tool_call_id": tool_call.get('id')})
                continue
                
            try:
                result = await session.call_tool(name, arguments=args)
                tool_output = "".join([c.text for c in result.content if c.type == 'text'])
                print(f"Tool Result: {tool_output}")
                
                # Ollama/OpenAI standard requires 'tool_call_id' in the tool role message
                messages.append({
                    "role": "tool",
                    "content": tool_output,
                    "tool_call_id": tool_call.get('id', 'mock_id')
                })
                
            except Exception as e:
                print(f"Tool execution failed: {e}")
                messages.append({
                    "role": "tool",
                    "content": f"Error: {str(e)}",
                    "tool_call_id": tool_call.get('id')
                })

    return {"role": "assistant", "content": "I encountered an error processing too many tool rounds."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
