"""
Flask API server for the music recommendation agent.
This server exposes REST endpoints that can be called from the Node.js frontend.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import json
from datetime import datetime
from collections import deque
from threading import Lock
from memory import memory, MemoryType
from perception import PerceptionManager, UserInput, perceive_with_gemini
from decisions import get_decision_maker

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for Node.js frontend

# In-memory log storage (circular buffer, max 1000 entries)
logs = deque(maxlen=1000)
log_lock = Lock()

def add_log(level: str, message: str, data: dict = None):
    """Add a log entry with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = {
        "timestamp": timestamp,
        "level": level,  # INFO, WARNING, ERROR, SUCCESS
        "message": message,
        "data": data or {}
    }
    with log_lock:
        logs.append(log_entry)
    # Also print to console
    print(f"[{timestamp}] [{level}] {message}")

def get_logs(limit: int = 100):
    """Get recent logs"""
    with log_lock:
        return list(logs)[-limit:]

# Access your API key and initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    from google import genai
    client = genai.Client(api_key=api_key)
else:
    client = None

def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "api_key_set": api_key is not None})

@app.route('/recommend', methods=['POST'])
def recommend():
    """Main recommendation endpoint"""
    try:
        add_log("INFO", "🎵 New recommendation request received")
        data = request.json
        mood = data.get('mood', '').strip()
        activity = data.get('activity', '').strip()
        current_loc = data.get('location', '').strip()
        tags_raw = data.get('tags', '').strip()
        
        add_log("INFO", f"📝 User Input - Mood: {mood}, Activity: {activity}, Location: {current_loc}, Tags: {tags_raw}")
        
        if not mood or not activity:
            add_log("ERROR", "❌ Validation failed: Mood and activity are required")
            return jsonify({"error": "Mood and activity are required."}), 400
        
        # Parse tags
        tags = []
        if tags_raw:
            tags = [t.strip() for t in (tags_raw.split(",") if "," in tags_raw else tags_raw.split()) if t.strip()]
        
        add_log("INFO", "💾 Storing inputs in memory...")
        # Store in memory
        mem_id = memory.add_memory(
            content=f"Mood: {mood}; Activity: {activity}; Tags: {', '.join(tags) if tags else ''}",
            memory_type=MemoryType.CONVERSATION,
            importance=2.0,
            tags=tags or [],
            metadata={"source": "web"}
        )
        add_log("SUCCESS", f"✅ Stored to short-term memory: {mem_id}")
        
        # Build perception
        add_log("INFO", "🧠 Building perception layer...")
        pm = PerceptionManager()
        user_input = pm.perceive_user_input(
            mood=mood,
            activity=activity,
            location={"tags": tags} if tags else None
        )
        
        # Gemini perception
        add_log("INFO", "🤖 Calling Gemini Perception Layer...")
        gem_perception = perceive_with_gemini(
            mood=mood,
            activity=activity,
            tags=tags,
            location={"text": current_loc} if current_loc else None
        )
        add_log("SUCCESS", f"✅ Gemini perception completed: {json.dumps(gem_perception, indent=2)}")
        
        # Get MCP tools
        add_log("INFO", "🔧 Getting MCP tools list...")
        server_params = StdioServerParameters(
            command="python",
            args=["actions.py"]
        )
        
        async def get_tools_list():
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return tools_result.tools
        
        tools = run_async(get_tools_list())
        add_log("SUCCESS", f"✅ Found {len(tools)} available tools")
        
        # Create tools description string
        tools_description_list = []
        for i, tool in enumerate(tools):
            try:
                params = tool.inputSchema
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                
                if 'properties' in params:
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ', '.join(param_details)
                else:
                    params_str = 'no parameters'
                
                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description_list.append(tool_desc)
            except Exception as e:
                add_log("WARNING", f"⚠️ Error processing tool {i}: {e}")
                tools_description_list.append(f"{i+1}. Error processing tool")
        
        tools_description = "\n".join(tools_description_list)
        available_tool_names = [getattr(tool, 'name', f'tool_{i}') for i, tool in enumerate(tools)]
        add_log("INFO", f"📋 Available tools: {', '.join(available_tool_names)}")
        
        # Make decision
        add_log("INFO", "🎯 Calling Decision Maker...")
        decision_maker = get_decision_maker()
        decision = decision_maker.make_decision(
            user_input.model_dump_json(), 
            available_tools=available_tool_names,
            tools_description=tools_description
        )
        
        tool_name = decision["decision"]["tool_name"]
        arguments = decision["decision"]["arguments"]
        reasoning = decision["decision"]["reasoning"]
        add_log("SUCCESS", f"✅ Decision made: Tool={tool_name}, Reasoning={reasoning}")
        
        # Call the tool
        add_log("INFO", f"⚙️ Calling tool: {tool_name} with arguments: {json.dumps(arguments)}")
        async def call_tool_with_session():
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    content = result.content
                    if content and len(content) > 0:
                        payload = content[0].text if hasattr(content[0], 'text') else str(content[0])
                    else:
                        payload = "[]"
                    return payload
        
        payload = run_async(call_tool_with_session())
        add_log("SUCCESS", f"✅ Tool execution completed")
        
        # Parse the JSON string if it's a string
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except json.JSONDecodeError:
            add_log("WARNING", f"⚠️ Failed to parse payload as JSON: {payload}")
            payload = []
        except Exception as e:
            add_log("WARNING", f"⚠️ Error parsing payload: {e}")
            payload = []
        
        # Handle case where payload might be a dict instead of a list
        if isinstance(payload, dict):
            payload = [payload]
        
        if payload and len(payload) > 0:
            add_log("SUCCESS", f"🎶 Received {len(payload)} recommendation(s)")
            if isinstance(payload[0], dict):
                song = payload[0].get('song', 'Unknown')
                artist = payload[0].get('artist', 'Unknown')
                add_log("INFO", f"🎵 Top recommendation: {song} by {artist}")
        else:
            add_log("WARNING", "⚠️ No recommendations received")
        
        add_log("SUCCESS", "✅ Recommendation request completed successfully")
        
        return jsonify({
            "success": True,
            "recommendations": payload,
            "reasoning": reasoning,
            "memory_id": mem_id,
            "perception": gem_perception
        })
        
    except Exception as e:
        add_log("ERROR", f"❌ Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/memory/recent', methods=['GET'])
def get_recent_memories():
    """Get recent conversation memories"""
    try:
        limit = request.args.get('limit', 5, type=int)
        mems = memory.get_memories(memory_type=MemoryType.CONVERSATION, limit=limit)
        return jsonify({"memories": [m.model_dump() for m in mems]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs_endpoint():
    """Get recent logs for display in frontend"""
    try:
        limit = request.args.get('limit', 100, type=int)
        log_entries = get_logs(limit=limit)
        return jsonify({"logs": log_entries, "count": len(log_entries)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all logs"""
    try:
        with log_lock:
            logs.clear()
        add_log("INFO", "🗑️ Logs cleared")
        return jsonify({"success": True, "message": "Logs cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    PORT = 5001  # Changed from 5000 to avoid conflict with AirPlay Receiver on macOS
    print(f"Starting Flask API server on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)

