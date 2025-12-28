# from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
import argparse
import json
from memory import memory, MemoryType
from perception import PerceptionManager, UserInput, perceive_with_gemini
from decisions import get_decision_maker


# Load environment variables from .env file
load_dotenv()

# app = Flask(__name__)

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 5
last_response = None
iteration = 0
iteration_response = []


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

# Global session for MCP connection
mcp_session = None

async def get_mcp_session():
    """Get or create MCP session"""
    global mcp_session
    if mcp_session is None or mcp_session.closed:
        server_params = StdioServerParameters(
            command="python",
            args=["actions.py"]
        )
        stdio_transport = stdio_client(server_params)
        mcp_session = await stdio_transport.__aenter__()
        session = await ClientSession(mcp_session[0], mcp_session[1]).__aenter__()
        await session.initialize()
        return session
    return mcp_session

def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result

async def run_cli_recommendation(mood: str, activity: str, tags: list | None):
    server_params = StdioServerParameters(command="python", args=["actions.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            arguments = {"mood": mood, "activity": activity}
            if tags:
                arguments["tags"] = tags
            result = await session.call_tool("recommend_music", arguments=arguments)
            content = result.content
            payload = content[0].text if content else "[]"
            try:
                return json.loads(payload) if isinstance(payload, str) else payload
            except Exception:
                return payload

def fetch_recent_conversation_memories(limit: int = 5):
    """Return recent conversation memories as dicts"""
    mems = memory.get_memories(memory_type=MemoryType.CONVERSATION, limit=limit)
    return [m.model_dump() for m in mems]


if __name__ == "__main__":
    try:
        print("Music recommender (interactive)")
        current_loc = input("Enter your current city & country: ").strip()
        mood = input("Enter your mood: ").strip()
        activity = input("Enter your activity: ").strip()
        tags_raw = input("Enter any tags (comma or space separated, optional): ").strip()

        tags = []
        if tags_raw:
            tags = [t.strip() for t in (tags_raw.split(",") if "," in tags_raw else tags_raw.split()) if t.strip()]

        if not mood or not activity:
            raise SystemExit("Mood and activity are required.")

        #calling the memory function to store the values entered by the user
        print("\n***********STORING THE INPUTS IN THE MEMORY**************\n");

        mem_id = memory.add_memory(
            content=f"Mood: {mood}; Activity: {activity}; Tags: {', '.join(tags) if tags else ''}",
            memory_type=MemoryType.CONVERSATION,
            importance=2.0,
            tags=tags or [],
            metadata={"source": "cli"}
        )

        print(f"Stored to short-term memory: {mem_id}")


        # Build detailed perception of the user inputs
        pm = PerceptionManager()

        # Optional: include tags inside location metadata (or pass real lat/lon if you have them)
        user_input = pm.perceive_user_input(
            mood=mood,
            activity=activity,
            location={"tags": tags} if tags else None
        )

        print("\n\n***********CALLING GEMINI PERCEPTION LAYER**************\n");
        # Human-readable context for downstream use (e.g., decision layer)
        gem_perception = perceive_with_gemini(
            mood=mood,
            activity=activity,
            tags=tags,
            location={"text": current_loc} if current_loc else None
        )
        print("Gemini perception output:")
        print(json.dumps(gem_perception, indent=2))

        #Call the decision layer to make the decision
        # Get MCP tools first
        server_params = StdioServerParameters(
            command="python",
            args=["actions.py"]
        )
        
        print("\n\n***********CALLING DECISION MAKER**************\n");
        
        async def get_tools_list():
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return tools_result.tools
        
        tools = run_async(get_tools_list())
        
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
                print(f"Error processing tool {i}: {e}")
                tools_description_list.append(f"{i+1}. Error processing tool")
        
        tools_description = "\n".join(tools_description_list)
        
        # Extract tool names for make_decision
        available_tool_names = [getattr(tool, 'name', f'tool_{i}') for i, tool in enumerate(tools)]

        print("Available tool names:")
        print(available_tool_names)


        decision_maker = get_decision_maker()
        decision = decision_maker.make_decision(
            user_input.model_dump_json(), 
            available_tools=available_tool_names,
            tools_description=tools_description
        )
        # print("Decision:")
        # print(json.dumps(decision, indent=2))

        #Finally call the tool based on the decision
        tool_name = decision["decision"]["tool_name"]
        arguments = decision["decision"]["arguments"]
        reasoning = decision["decision"]["reasoning"]
        print(f"Tool to be called: {tool_name} \nArguments: {arguments} \nReasoning: {reasoning}")
        
        # Create async function to call the tool
        async def call_tool_with_session():
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    content = result.content
                    # Safely extract text from content
                    if content and len(content) > 0:
                        payload = content[0].text if hasattr(content[0], 'text') else str(content[0])
                    else:
                        payload = "[]"
                    return payload
        
        print("\n\n***********CALLING TOOLS BASED ON THE DECISION**************\n");

        payload = run_async(call_tool_with_session())
        # Parse the JSON string if it's a string
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse payload as JSON: {payload}")
            payload = []
        except Exception as e:
            print(f"Warning: Error parsing payload: {e}, payload: {payload}")
            payload = []
        
        # Handle case where payload might be a dict instead of a list
        if isinstance(payload, dict):
            payload = [payload]
        
        # print(f"Final Music Recommendations:\n\n {json.dumps(payload, indent=2)}")
        print("\n\n***********GETTING THE FINAL RECOMMENDATIONS**************\n");
        if not payload or len(payload) == 0:
            print("No recommendations received.")
        else:
            # Ensure we have a valid first item
            if isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
                song = payload[0].get('song', 'Unknown')
                artist = payload[0].get('artist', 'Unknown')
                genre = payload[0].get('genre', 'Unknown')
                energy_level = payload[0].get('energy_level', 'Unknown')
                reason = payload[0].get('reason', 'No reason provided')
                print(f"Final Music Recommendations:\n")
                print(f"\nSong: {song} \nArtist: {artist} \nGenre: {genre} \nEnergy Level: {energy_level} \nReason: {reason}")
                print(f"\nLink to YouTube: https://www.youtube.com/results?search_query={song}+{artist}")
                print("\nEnjoy your music! 🎶")
            else:
                print(f"Unexpected payload format: {payload}")


    except KeyboardInterrupt:
        print("\nCancelled.")

    # asyncio.run(main())