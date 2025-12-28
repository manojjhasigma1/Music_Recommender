# Music Recommendation Agent 🎵

An intelligent agentic CLI application that recommends music based on your current mood, activity, location, and time of day. Built with Python and Google's Gemini AI.

## Features

- 🎯 **Context-Aware Recommendations**: Considers mood, activity, time, and location
- 🧠 **Agentic Architecture**: Modular design with perception, memory, decision, and action layers
- 🔧 **MCP Tools**: Each action is an MCP (Model Context Protocol) tool
- 🤖 **Gemini AI Orchestration**: Uses Gemini 2.5 Flash for intelligent decision making and perception
- 💾 **Memory System**: Stores interactions and learns from context
- ⚙️ **Configurable System Prompt**: Easily modify agent behavior
- 📊 **Detailed Logging**: Clear step-by-step output showing the agent's decision-making process

## Architecture

The application follows a layered agentic architecture:

```
┌─────────────────────────────────────────┐
│         CLI Interface (main.py)          │
│    - Collects user input                 │
│    - Coordinates agent layers            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    1. Memory Layer (memory.py)          │
│    - Stores user inputs                 │
│    - Maintains conversation context     │
│    - Tracks importance scores           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    2. Perception Layer (perception.py)  │
│    - Processes user inputs              │
│    - Structures context with Gemini     │
│    - Extracts semantic information      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    3. Decision Layer (decisions.py)     │
│    - Gemini 2.5 Flash orchestration    │
│    - Chooses which MCP tools to call    │
│    - Configurable system prompt         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    4. Action Layer (actions.py)         │
│    - MCP Tool: recommend_music          │
│    - Uses Gemini to match music         │
│    - Returns recommendations            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Final Recommendations            │
│    - Formatted output with details      │
│    - YouTube search links               │
└─────────────────────────────────────────┘
```

## Installation

1. **Clone or download this repository**

2. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file or export the following variable:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
   
   Get your API key from: https://aistudio.google.com/apikey

## Usage

### Running the Application

1. **Start the CLI application**:
   ```bash
   uv run python main.py
   ```

2. **Follow the interactive prompts**:
   - Enter your current city & country
   - Enter your mood (e.g., happy, calm, energetic)
   - Enter your activity (e.g., working, exercising, relaxing)
   - Enter any tags (comma or space separated, optional)

3. **Get recommendations**: The agent will process your inputs and provide personalized music recommendations!

### Example Usage

**Input:**
```
Enter your current city & country: New York, USA
Enter your mood: happy and energetic
Enter your activity: exercising at the gym
Enter any tags (comma or space separated, optional): workout, cardio
```

**Output:**
The agent will:
1. Store your inputs to memory
2. Process context with Gemini perception
3. Make a decision about which tool to call
4. Execute the recommendation tool
5. Display formatted recommendations with song details and YouTube links

### Example Output

```
Final Music Recommendations:

Song: Eye of the Tiger
Artist: Survivor
Genre: Rock
Energy Level: high
Reason: Perfect high-energy workout anthem that matches your energetic mood

Link to YouTube: https://www.youtube.com/results?search_query=Eye+of+the+Tiger+Survivor

Enjoy your music! 🎶
```

## Configuration

### System Prompt

Modify the agent's behavior by updating the system prompt in `decisions.py`:

```python
from decisions import SystemPromptConfig

SystemPromptConfig.update_prompt("Your custom prompt here")
```

The default prompt guides the agent to:
- Analyze user context (mood, activity, time, location)
- Determine which MCP tool to call
- Provide thoughtful recommendations with clear reasoning

## Project Structure

```
agentic-app/
├── main.py              # Main CLI application and orchestration
├── perception.py        # Perception layer with Gemini integration
├── decisions.py         # Decision layer with Gemini 2.5 Flash
├── actions.py           # Action layer with MCP tools
├── memory.py            # Memory layer for conversation context
├── pyproject.toml       # Dependencies
└── README.md           # This file
```

## How It Works

1. **User Input**: CLI collects mood, activity, location, and optional tags
2. **Memory**: System stores the inputs for conversation context
3. **Perception**: Gemini AI processes and structures the context
4. **Decision**: Gemini AI analyzes context and decides which tool to use
5. **Action**: MCP tool uses Gemini to generate personalized music recommendations
6. **Response**: Formatted recommendations are displayed with song details and YouTube links

## MCP Tools

### recommend_music

Recommends music based on mood, activity, location, and context.

**Parameters**:
- `mood` (string): User's current mood
- `activity` (string): User's current activity
- `location` (string, optional): User's current location
- `tags` (array, optional): Semantic tags

**Returns**:
- List of 3 music recommendations with song, artist, genre, energy_level, and reasoning

The tool uses Gemini 2.5 Flash to generate personalized recommendations that match the user's context.

## Extending the System

### Adding New Tools

1. Create tool definition in `actions.py`:
```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> dict:
    """Tool description"""
    # Tool implementation
    return result
```

2. The decision layer will automatically discover and use the new tool

3. Update decision logic in `decisions.py` if needed

### Customizing Music Recommendations

The `recommend_music` tool uses Gemini AI to generate recommendations dynamically. You can customize the prompt in `actions.py` to change how recommendations are generated.

## Troubleshooting

### "GEMINI_API_KEY environment variable must be set"

The app requires the Gemini API key to function. Set it using:

```bash
export GEMINI_API_KEY="your_key_here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your_key_here
```

### JSON parsing errors

If you see JSON parsing warnings, the agent will fall back to default recommendations. This usually indicates an issue with the Gemini API response format.

### No recommendations received

Check that:
1. Your GEMINI_API_KEY is set correctly
2. You have an internet connection
3. The mood and activity fields are not empty

## License

MIT License - feel free to use and modify as needed!

## Contributing

Contributions are welcome! Feel free to:
- Add more sophisticated music recommendation logic
- Implement new MCP tools
- Enhance the memory system
- Improve error handling and user experience

## Acknowledgments

- Built with Python, Pydantic, and Google Gemini AI
- Uses MCP (Model Context Protocol) for tool definitions
- Inspired by agentic AI architectures
- Powered by Gemini 2.5 Flash for intelligent decision-making
