# Project Summary: Music Recommendation Agent

## Overview
A fully functional agentic web application that provides intelligent music recommendations based on user context (mood, activity, time, location).


### ✅ Agent Layers (Separate Files)
- **perception.py**: Handles user inputs and extracts semantic context
- **memory.py**: Manages conversation history and context storage
- **decisions.py**: Orchestrates decisions using Gemini AI
- **actions.py**: Contains MCP tools for music recommendations

### ✅ MCP Tools
- `recommend_music` tool properly defined with:
  - Tool definition following MCP protocol
  - Input schema for mood, activity, and tags
  - Execution logic with music matching algorithm

### ✅ Gemini Integration
- Integrated Gemini 2.0 Flash model for orchestration
- Configurable system prompt (can be updated via API)
- JSON-based decision making
- Fallback mode when API key not available

### ✅ Web Interface
- Beautiful, modern UI with gradient design
- Simple and intuitive form inputs
- Automatic geolocation detection
- Real-time recommendations display
- Loading states and error handling

### ✅ User Inputs
- Current Mood (text input)
- Current Activity (text input)
- Current Time (auto-detected)
- Location (auto-detected from browser)

## Architecture

```
User Input → Perception → Decision (Gemini) → Action (MCP Tool) → Response
                     ↓                              ↓
                  Memory ←────────────────────────→ Memory
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Flask web server orchestration |
| `perception.py` | Input processing and context extraction |
| `decisions.py` | AI-powered decision making |
| `actions.py` | MCP tools for actions |
| `memory.py` | Conversation memory management |
| `templates/index.html` | Web interface |

## Configuration Points

### 1. System Prompt
Located in `decisions.py` → `SystemPromptConfig`
- Can be updated via API endpoint
- Can be modified in code for experimentation

### 2. Music Database
Located in `actions.py` → `MUSIC_LIBRARY`
- Easy to add new songs
- Tag-based matching system
- Energy level classification

### 3. Memory Settings
Located in `memory.py`
- Maximum memories: 50
- Retention period: 12 hours
- Importance-based filtering

## How to Run

1. **Install dependencies**: `uv sync`
2. **Set API key** (optional): `export GEMINI_API_KEY="your_key"`
3. **Start server**: `uv run python main.py`
4. **Open browser**: `http://localhost:5000`

## API Endpoints

- `POST /recommend` - Get music recommendations
- `GET /config/system-prompt` - Get system prompt
- `POST /config/system-prompt` - Update system prompt
- `GET /memory/stats` - View memory statistics
- `GET /memory/recent` - Get recent memories

## Example Usage

**Input:**
- Mood: "happy and energetic"
- Activity: "exercising at the gym"

**Output:**
- High-energy workout songs
- Matching artists and genres
- Explanation for each recommendation

## Extensibility

The architecture is designed for easy extension:

1. **Add new tools**: Create new MCP tools in `actions.py`
2. **Modify behavior**: Update system prompt in `decisions.py`
3. **Expand database**: Add songs to `MUSIC_LIBRARY`
4. **Customize UI**: Edit `templates/index.html`

## Testing

Run the application and verify:
- ✅ Web interface loads
- ✅ User inputs are processed
- ✅ Location detection works
- ✅ Recommendations are returned
- ✅ Memory system stores interactions
- ✅ System prompt can be configured

## Notes

- The app works in **fallback mode** without API key
- Location detection is **optional**
- Memory is **session-based** (resets on restart)
- Music database is **simulated** (can be connected to real API)



