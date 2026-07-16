import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastmcp import Client
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Load environment variables
load_dotenv()

from config import SERVERS

# Initialize client placeholder
client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    print("Starting up FastMCP Client...")
    client = Client(SERVERS)
    try:
        async with client:
            app.state.client = client
            print("FastMCP Client connected successfully!")
            yield
    except Exception as e:
        print(f"Error during FastMCP Client execution: {e}")
        # Allow the server to startup even if client fails, so user can see errors in UI
        app.state.client = None
        yield
    finally:
        print("Shutting down FastMCP Client...")

app = FastAPI(title="MCP Host API", lifespan=lifespan)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def get_status(request: Request):
    cli = getattr(request.app.state, "client", None)
    configured_servers = list(SERVERS.get("mcpServers", {}).keys())
    
    if not cli:
        return {
            "status": "error",
            "message": "Client not connected",
            "servers": {s: "offline" for s in configured_servers}
        }
        
    try:
        tools = await cli.list_tools()
        active_prefixes = set()
        for t in tools:
            # Tool names typically start with the server key (e.g. crop_...)
            parts = t.name.split("_")
            if parts:
                active_prefixes.add(parts[0])
        
        server_status = {}
        for s in configured_servers:
            # If server name prefix is in any of the tool names, it's active
            if s in active_prefixes:
                server_status[s] = "online"
            else:
                server_status[s] = "offline"
                
        return {
            "status": "ok",
            "servers": server_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "servers": {s: "offline" for s in configured_servers}
        }

@app.get("/api/tools")
async def get_tools(request: Request):
    cli = getattr(request.app.state, "client", None)
    if not cli:
        raise HTTPException(status_code=503, detail="MCP Client is not connected")
        
    try:
        tools = await cli.list_tools()
        result = []
        for t in tools:
            # Serialize inputSchema
            schema_dict = {}
            if hasattr(t, 'inputSchema') and t.inputSchema:
                schema = t.inputSchema
                if hasattr(schema, 'model_dump'):
                    schema_dict = schema.model_dump()
                elif hasattr(schema, 'dict'):
                    schema_dict = schema.dict()
                else:
                    schema_dict = dict(schema)
            
            # Determine which server this tool belongs to based on name prefix
            server_name = "unknown"
            for s in SERVERS.get("mcpServers", {}).keys():
                if t.name.startswith(f"{s}_"):
                    server_name = s
                    break
                    
            result.append({
                "name": t.name,
                "description": t.description or "No description provided",
                "server": server_name,
                "inputSchema": schema_dict
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tools: {str(e)}")

@app.post("/api/tools/{name}")
async def call_tool(name: str, args: dict, request: Request):
    cli = getattr(request.app.state, "client", None)
    if not cli:
        raise HTTPException(status_code=503, detail="MCP Client is not connected")
        
    try:
        print(f"Calling tool {name} with args: {args}")
        # Convert numeric values in args if they are passed as strings but schema requires int/float
        # React forms might pass strings, so let's clean them up based on the tool's schema
        tools = await cli.list_tools()
        target_tool = next((t for t in tools if t.name == name), None)
        cleaned_args = {}
        
        if target_tool and hasattr(target_tool, 'inputSchema') and target_tool.inputSchema:
            schema = target_tool.inputSchema
            properties = schema.properties if hasattr(schema, 'properties') else schema.get('properties', {})
            for key, val in args.items():
                if key in properties:
                    prop_type = properties[key].get('type') if isinstance(properties[key], dict) else getattr(properties[key], 'type', None)
                    if prop_type == 'integer' and val != "":
                        try:
                            cleaned_args[key] = int(val)
                        except ValueError:
                            cleaned_args[key] = val
                    elif prop_type == 'number' and val != "":
                        try:
                            cleaned_args[key] = float(val)
                        except ValueError:
                            cleaned_args[key] = val
                    elif val == "" and not (properties[key].get('required') or key in (schema.required if hasattr(schema, 'required') else schema.get('required', []))):
                        # Skip optional empty fields
                        continue
                    else:
                        cleaned_args[key] = val
                else:
                    cleaned_args[key] = val
        else:
            cleaned_args = args

        result = await cli.call_tool(name, cleaned_args)
        
        # Format tool result
        output = ""
        if hasattr(result, 'text'):
            output = result.text
        elif hasattr(result, 'content') and result.content:
            text_contents = []
            for item in result.content:
                if hasattr(item, 'text'):
                    text_contents.append(item.text)
                elif isinstance(item, dict) and 'text' in item:
                    text_contents.append(item['text'])
            output = "\n".join(text_contents)
        else:
            output = str(result)
            
        return {"result": output}
    except Exception as e:
        print(f"Error calling tool {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class Message(BaseModel):
    role: str
    content: Optional[str] = ""

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    apiKey: Optional[str] = None

@app.post("/api/chat")
async def chat(request: ChatRequest, req: Request):
    cli = getattr(req.app.state, "client", None)
    if not cli:
        raise HTTPException(status_code=503, detail="MCP Client is not connected")
        
    # Get API key from request, environment, or settings
    api_key = request.apiKey or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400, 
            detail="OpenAI API Key is missing. Please set the OPENAI_API_KEY environment variable or provide it in the Supervisor Settings."
        )
        
    try:
        # Initialize client (detect OpenRouter keys)
        base_url = None
        model_name = "gpt-4o-mini"
        if api_key.startswith("sk-or-v1-"):
            base_url = "https://openrouter.ai/api/v1"
            model_name = "openai/gpt-4o-mini"
            
        openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # 1. Fetch available tools from MCP Client
        mcp_tools = await cli.list_tools()
        
        # 2. Convert MCP tools to OpenAI tool definitions
        openai_tools = []
        for t in mcp_tools:
            # Serialize inputSchema
            schema_dict = {}
            if hasattr(t, 'inputSchema') and t.inputSchema:
                schema = t.inputSchema
                if hasattr(schema, 'model_dump'):
                    schema_dict = schema.model_dump()
                elif hasattr(schema, 'dict'):
                    schema_dict = schema.dict()
                else:
                    schema_dict = dict(schema)
            
            # Map parameters
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "No description provided",
                    "parameters": {
                        "type": "object",
                        "properties": schema_dict.get("properties", {}),
                        "required": schema_dict.get("required", [])
                    }
                }
            })
            
        # 3. Construct system prompt
        system_prompt = (
            "You are a helpful Supervisor Agent that coordinates multiple domain-specific MCP nodes "
            "(crop recommendation, disease diagnostic, weather forecast, and market prices) to answer user questions.\n"
            "You have access to a set of tools representing these models. Based on the user's question, "
            "determine which tools are relevant and call them to gather information. You can call multiple tools "
            "sequentially or in parallel if needed to satisfy the query.\n"
            "After calling the tools and receiving their results, synthesize a final user-friendly response "
            "based on the gathered information. If no tools are required or relevant to the question, "
            "respond directly to the user.\n"
            "Be clear and precise in your parameters when calling tools."
        )
        
        # 4. Construct messages history list
        messages = [{"role": "system", "content": system_prompt}]
        for msg in request.history:
            # Skip empty content messages if not from assistant (assistant can have None content with tool_calls)
            if not msg.content and msg.role != "assistant":
                continue
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": request.message})
        
        steps = []
        max_iterations = 5
        iteration = 0
        
        # Loop for tool execution steps (support multi-turn tool calling)
        while iteration < max_iterations:
            iteration += 1
            
            # Call openai with tools list if we have tools, else without tools
            completion_args = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
            }
            if openai_tools:
                completion_args["tools"] = openai_tools
                completion_args["tool_choice"] = "auto"
                
            response = await openai_client.chat.completions.create(**completion_args)
            response_message = response.choices[0].message
            
            # Append response to messages for history context
            # Convert to dictionary or format suitable for subsequent calls
            assistant_msg = {
                "role": "assistant",
                "content": response_message.content or ""
            }
            if response_message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            
            messages.append(assistant_msg)
            
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args_str = tool_call.function.arguments
                    
                    try:
                        tool_args = json.loads(tool_args_str)
                    except Exception:
                        tool_args = {}
                        
                    # Find tool definition in mcp_tools to handle type conversions
                    target_tool = next((t for t in mcp_tools if t.name == tool_name), None)
                    cleaned_args = {}
                    
                    if target_tool and hasattr(target_tool, 'inputSchema') and target_tool.inputSchema:
                        schema = target_tool.inputSchema
                        properties = schema.properties if hasattr(schema, 'properties') else schema.get('properties', {})
                        for key, val in tool_args.items():
                            if key in properties:
                                prop_type = properties[key].get('type') if isinstance(properties[key], dict) else getattr(properties[key], 'type', None)
                                if prop_type == 'integer' and val != "":
                                    try:
                                        cleaned_args[key] = int(val)
                                    except ValueError:
                                        cleaned_args[key] = val
                                elif prop_type == 'number' and val != "":
                                    try:
                                        cleaned_args[key] = float(val)
                                    except ValueError:
                                        cleaned_args[key] = val
                                elif val == "" and not (properties[key].get('required') or key in (schema.required if hasattr(schema, 'required') else schema.get('required', []))):
                                    continue
                                else:
                                    cleaned_args[key] = val
                            else:
                                cleaned_args[key] = val
                    else:
                        cleaned_args = tool_args
                        
                    print(f"Supervisor calling tool {tool_name} with args {cleaned_args}")
                    
                    # Execute tool call
                    tool_result_str = ""
                    try:
                        tool_result = await cli.call_tool(tool_name, cleaned_args)
                        if hasattr(tool_result, 'text'):
                            tool_result_str = tool_result.text
                        elif hasattr(tool_result, 'content') and tool_result.content:
                            text_contents = []
                            for item in tool_result.content:
                                if hasattr(item, 'text'):
                                    text_contents.append(item.text)
                                elif isinstance(item, dict) and 'text' in item:
                                    text_contents.append(item['text'])
                            tool_result_str = "\n".join(text_contents)
                        else:
                            tool_result_str = str(tool_result)
                    except Exception as tool_error:
                        print(f"Error calling tool {tool_name}: {tool_error}")
                        tool_result_str = f"Error calling tool: {str(tool_error)}"
                        
                    # Save step trace
                    steps.append({
                        "type": "tool_call",
                        "name": tool_name,
                        "args": cleaned_args,
                        "result": tool_result_str
                    })
                    
                    # Append tool response message to history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result_str
                    })
            else:
                # No more tool calls, return final response
                return {
                    "response": response_message.content or "",
                    "steps": steps
                }
                
        # If we exceed max iterations
        return {
            "response": "The supervisor exceeded the maximum number of reasoning steps to find an answer.",
            "steps": steps
        }
        
    except APIError as api_err:
        print(f"OpenAI API Error: {api_err}")
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(api_err)}")
    except Exception as e:
        print(f"Error in supervisor endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Supervisor failed: {str(e)}")

# Serve React frontend built files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "message": "MCP Host API is running. Frontend build folder 'frontend/dist' not found. "
                       "Please build the frontend using 'npm run build' inside the 'frontend' folder."
        }
