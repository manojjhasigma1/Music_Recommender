# Web UI Setup Guide

This guide explains how to run the HTML UI with Node.js server for the Music Recommendation Agent.

## Architecture

The web application consists of two servers:

1. **Python Flask API Server** (port 5001) - Handles the agent logic and recommendations
2. **Node.js Express Server** (port 3000) - Serves the HTML UI and proxies API requests

```
Browser → Node.js Server (3000) → Python API Server (5001) → Agent Logic
```

**Note:** Port 5001 is used instead of 5000 to avoid conflicts with macOS AirPlay Receiver.

## Prerequisites

1. **Python dependencies** (already installed):
   ```bash
   uv sync
   ```

2. **Node.js and npm** - Make sure you have Node.js installed:
   ```bash
   node --version  # Should be v14 or higher
   npm --version
   ```

## Installation Steps

### 1. Install Node.js Dependencies

```bash
npm install
```

This will install:
- `express` - Web server framework
- `cors` - Cross-origin resource sharing
- `axios` - HTTP client for API calls

### 2. Set Up Environment Variables

Make sure you have a `.env` file with your Gemini API key:

```bash
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

### Option 1: Run Both Servers Manually (Recommended for Development)

**Terminal 1 - Start Python API Server:**
```bash
uv run python api_server.py
```

You should see:
```
Starting Flask API server on http://localhost:5001
 * Running on http://0.0.0.0:5001
```

**Terminal 2 - Start Node.js Server:**
```bash
npm start
```

You should see:
```
🎵 Music Recommendation UI Server
=====================================
Server running on http://localhost:3000
Python API expected at http://localhost:5001
```

**Open your browser:**
Navigate to `http://localhost:3000`

### Option 2: Use a Process Manager (Advanced)

You can use tools like `pm2` or `foreman` to run both servers together:

```bash
# Install pm2 globally
npm install -g pm2

# Create ecosystem file (ecosystem.config.js)
# Then run: pm2 start ecosystem.config.js
```

## Usage

1. **Open the web interface** at `http://localhost:3000`
2. **Fill in the form**:
   - Location (optional, or click "Detect My Location")
   - Mood (required) - e.g., "happy", "energetic", "calm"
   - Activity (required) - e.g., "working", "exercising", "relaxing"
   - Tags (optional) - e.g., "workout", "focus", "cardio"
3. **Click "Get Recommendations"**
4. **View your personalized music recommendations** with YouTube links

## Features

- 🎨 **Modern, responsive UI** with gradient design
- 📍 **Automatic location detection** using browser geolocation
- 🎵 **Real-time recommendations** with detailed information
- 📝 **Recent activity history** showing past recommendations
- ⚡ **Fast and responsive** with loading states

## Troubleshooting

### "Failed to get recommendations" Error

**Problem:** The Node.js server can't connect to the Python API.

**Solution:**
1. Make sure the Python API server is running on port 5001
2. Check that port 5001 is not being used by another application
3. Verify the Python server started successfully

### Port Already in Use

**Problem:** Port 3000 or 5001 is already in use.

**Solution:**
- Change the port in `server.js` (line 11) for Node.js server
- Change the port in `api_server.py` (line 188) for Python server
- Make sure both ports match in the configuration
- **Note:** Port 5001 is used to avoid macOS AirPlay Receiver conflict on port 5000

### CORS Errors

**Problem:** Browser shows CORS errors in console.

**Solution:**
- The Python API server has CORS enabled, so this shouldn't happen
- If it does, check that `flask-cors` is installed: `uv sync`

### Location Detection Not Working

**Problem:** "Detect My Location" button doesn't work.

**Solution:**
- Make sure you're using HTTPS or localhost (geolocation requires secure context)
- Check browser permissions for location access
- You can always enter location manually

## File Structure

```
multi-agentic-app/
├── api_server.py          # Python Flask API server
├── server.js              # Node.js Express server
├── package.json           # Node.js dependencies
├── public/               # Frontend files
│   ├── index.html        # Main HTML page
│   ├── styles.css        # Styling
│   └── app.js            # Frontend JavaScript
├── main.py               # Original CLI application
└── ...                   # Other Python files
```

## Development

### Making Changes

- **Frontend changes**: Edit files in `public/` directory, refresh browser
- **Backend changes**: Edit `api_server.py`, restart Python server
- **Node.js changes**: Edit `server.js`, restart Node.js server

### Testing

1. Test the Python API directly:
   ```bash
   curl -X POST http://localhost:5001/recommend \
     -H "Content-Type: application/json" \
     -d '{"mood":"happy","activity":"working"}'
   ```

2. Test the Node.js proxy:
   ```bash
   curl -X POST http://localhost:3000/api/recommend \
     -H "Content-Type: application/json" \
     -d '{"mood":"happy","activity":"working"}'
   ```

## Next Steps

- Add user authentication
- Implement recommendation history
- Add music preview/playback
- Integrate with Spotify/Apple Music APIs
- Add more interactive features

Enjoy your music recommendations! 🎵

