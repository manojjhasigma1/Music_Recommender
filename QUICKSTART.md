# Quick Start Guide 🚀

Get your Music Recommendation Agent up and running in 3 steps!

## Step 1: Install Dependencies

```bash
uv sync
```

## Step 2: Set Up API Key (Optional but Recommended)

Get your free Google Gemini API key from: https://aistudio.google.com/apikey

Then set it as an environment variable:

```bash
# On macOS/Linux:
export GEMINI_API_KEY="your_api_key_here"

# On Windows:
set GEMINI_API_KEY=your_api_key_here
```

> **Note**: The app will work without the API key in fallback mode, but you'll get better recommendations with it!

## Step 3: Run the Application

```bash
uv run python main.py
```

Then open your browser to: **http://localhost:5000**

## Using the App

1. **Enter your mood**: How are you feeling? (e.g., "happy", "calm", "energetic")
2. **Enter your activity**: What are you doing? (e.g., "working", "exercising", "relaxing")
3. **Get recommendations**: Click the button and enjoy!

## Example Inputs

| Mood | Activity | What You'll Get |
|------|----------|----------------|
| happy | exercising | High-energy workout songs |
| calm | working | Focus music for productivity |
| melancholic | relaxing | Soothing, reflective tunes |
| energetic | party | Upbeat party anthems |

## Troubleshooting

**Problem**: Import errors when running  
**Solution**: Make sure you ran `uv sync` first

**Problem**: Port 5000 already in use  
**Solution**: Change the port in `main.py` (line at the bottom)

**Problem**: Location not detected  
**Solution**: That's fine! Location is optional and doesn't affect recommendations

## Next Steps

- Customize the system prompt (see `README.md`)
- Add your own music to the database (edit `actions.py`)
- Check memory statistics: `curl http://localhost:5000/memory/stats`

Enjoy discovering new music! 🎵

