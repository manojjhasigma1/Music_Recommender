#!/bin/bash

# Quick start script for the web UI
# This script starts both the Python API server and Node.js server

echo "🎵 Starting Music Recommendation Agent Web UI"
echo "=============================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed"
    exit 1
fi

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    echo ""
fi

# Check if Python API server dependencies are installed
echo "🔍 Checking Python dependencies..."
if ! uv run python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    uv sync
    echo ""
fi

echo "✅ Dependencies ready!"
echo ""
echo "Starting servers..."
echo ""
echo "📝 Note: You'll need to run this script in two separate terminals:"
echo "   Terminal 1: Run 'uv run python api_server.py'"
echo "   Terminal 2: Run 'npm start'"
echo ""
echo "Or use a process manager like pm2 to run both together."
echo ""

# Option to start both (requires background processes)
read -p "Do you want to start both servers now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Python API server in background..."
    uv run python api_server.py &
    PYTHON_PID=$!
    
    sleep 2
    
    echo "Starting Node.js server..."
    npm start &
    NODE_PID=$!
    
    echo ""
    echo "✅ Both servers started!"
    echo "Python API: http://localhost:5000 (PID: $PYTHON_PID)"
    echo "Node.js UI: http://localhost:3000 (PID: $NODE_PID)"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    
    # Wait for user interrupt
    trap "kill $PYTHON_PID $NODE_PID 2>/dev/null; exit" INT TERM
    wait
else
    echo ""
    echo "To start manually:"
    echo "  Terminal 1: uv run python api_server.py"
    echo "  Terminal 2: npm start"
    echo "  Then open: http://localhost:3000"
fi

