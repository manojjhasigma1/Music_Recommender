/**
 * Node.js Express server for serving the HTML UI
 * and proxying requests to the Python Flask API server
 */
const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');

const app = express();
const PORT = 3000;
const PYTHON_API_URL = 'http://localhost:5001';  // Changed from 5000 to avoid AirPlay Receiver conflict

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', server: 'nodejs' });
});

// Proxy endpoint to Python API
app.post('/api/recommend', async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/recommend`, req.body);
    res.json(response.data);
  } catch (error) {
    console.error('Error calling Python API:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.response?.data?.error || 'Failed to get recommendations',
      message: error.message
    });
  }
});

// Proxy endpoint for recent memories
app.get('/api/memory/recent', async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/memory/recent`, {
      params: req.query
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error calling Python API:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.response?.data?.error || 'Failed to get memories',
      message: error.message
    });
  }
});

// Proxy endpoint for logs
app.get('/api/logs', async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/logs`, {
      params: req.query
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error calling Python API:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.response?.data?.error || 'Failed to get logs',
      message: error.message
    });
  }
});

// Proxy endpoint to clear logs
app.post('/api/logs/clear', async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/logs/clear`);
    res.json(response.data);
  } catch (error) {
    console.error('Error calling Python API:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.response?.data?.error || 'Failed to clear logs',
      message: error.message
    });
  }
});

// Serve the main HTML page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`\n🎵 Music Recommendation UI Server`);
  console.log(`=====================================`);
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Python API expected at ${PYTHON_API_URL}`);
  console.log(`\nMake sure the Python API server is running!`);
  console.log(`Run: uv run python api_server.py`);
  console.log(`\nNote: Using port 5001 to avoid AirPlay Receiver conflict on macOS\n`);
});

