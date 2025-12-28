# basic import 
from typing import Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
import math
import sys
import subprocess
import time
import platform
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# instantiate an MCP server client
mcp = FastMCP[Any]("MusicRecommendationTools")

# Music library
MUSIC_LIBRARY = [
    {"song": "Happy", "artist": "Pharrell Williams", "genre": "Pop", "energy": "high", "mood_tags": ["happy", "joyful", "cheerful"], "activity_tags": ["dancing", "exercising", "celebrating"]},
    {"song": "Let It Be", "artist": "The Beatles", "genre": "Rock", "energy": "low", "mood_tags": ["calm", "peaceful", "reflective"], "activity_tags": ["relaxing", "meditating", "working"]},
    {"song": "Eye of the Tiger", "artist": "Survivor", "genre": "Rock", "energy": "high", "mood_tags": ["energetic", "motivated", "powerful"], "activity_tags": ["exercising", "working out", "training"]},
    {"song": "Weightless", "artist": "Marconi Union", "genre": "Ambient", "energy": "very low", "mood_tags": ["calm", "relaxed", "peaceful"], "activity_tags": ["relaxing", "meditating", "working", "studying"]},
    {"song": "Uptown Funk", "artist": "Bruno Mars", "genre": "Funk", "energy": "high", "mood_tags": ["happy", "energetic", "fun"], "activity_tags": ["dancing", "partying", "exercising"]},
    {"song": "Autumn Leaves", "artist": "Eva Cassidy", "genre": "Jazz", "energy": "low", "mood_tags": ["melancholic", "reflective", "peaceful"], "activity_tags": ["relaxing", "reading", "evening"]},
    {"song": "Can't Stop The Feeling", "artist": "Justin Timberlake", "genre": "Pop", "energy": "high", "mood_tags": ["happy", "energetic", "positive"], "activity_tags": ["dancing", "exercising", "driving"]},
    {"song": "Rain", "artist": "Ben Folds Five", "genre": "Alternative", "energy": "medium", "mood_tags": ["melancholic", "peaceful", "reflective"], "activity_tags": ["relaxing", "working", "reading"]},
]

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

# Get current time in ISO format
@mcp.tool()
def get_current_time() -> str:
    """Get the current time in ISO 8601 format"""
    print("CALLED: get_current_time() -> str:")
    current_time = datetime.now().isoformat()
    return current_time

@mcp.tool()
def recommend_music(mood: str, activity: str, location: str = None, tags: list = None) -> list:
    """Recommend music based on mood, activity, location, and tags
    
    Args:
        mood: Current mood (e.g., happy, calm, energetic, melancholic)
        activity: Current activity (e.g., working, exercising, relaxing)
        location: Current location (e.g., home, office, gym, park)
        tags: Optional list of additional context tags
    
    Returns:
        List of music recommendations with song details
    """
    print(f"CALLED: recommend_music(mood: {mood}, activity: {activity}, location: {location})")
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable must be set")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Build context string for the prompt
    location_context = f" at {location}" if location else ""
    tags_context = f" with context: {', '.join(tags)}" if tags else ""
    
    # Create the prompt for Gemini
    prompt = f"""You are a music recommendation expert. Generate 3 personalized music recommendations based on the user's context.

User Context:
- Mood: {mood}
- Activity: {activity}
- Location: {location if location else 'Not specified'}{tags_context}

Requirements:
1. Recommend exactly 3 diverse songs that match the user's mood, activity, and location
2. Consider how location might influence music choice (e.g., gym vs. library, home vs. office)
3. Each recommendation should include:
   - A real, existing song title
   - The actual artist name
   - An appropriate genre
   - An energy level (very low, low, medium, high, very high)
   - A specific reason explaining why this song fits their context

Return ONLY valid JSON in this exact format (no markdown, no code fences, just JSON):
{{
  "recommendations": [
    {{
      "song": "Song Title",
      "artist": "Artist Name",
      "genre": "Genre",
      "energy_level": "low/medium/high/very low/very high",
      "reason": "Brief explanation of why this song fits"
    }},
    {{
      "song": "Song Title",
      "artist": "Artist Name",
      "genre": "Genre",
      "energy_level": "low/medium/high/very low/very high",
      "reason": "Brief explanation of why this song fits"
    }},
    {{
      "song": "Song Title",
      "artist": "Artist Name",
      "genre": "Genre",
      "energy_level": "low/medium/high/very low/very high",
      "reason": "Brief explanation of why this song fits"
    }}
  ]
}}
"""
    
    try:
        # Generate recommendations using Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON if wrapped in code fences (Gemini sometimes wraps JSON in markdown)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse the JSON response
        data = json.loads(response_text)
        recommendations = data.get("recommendations", [])
        
        # Validate that we got recommendations
        if not recommendations:
            raise ValueError("No recommendations returned from model")
        
        # Ensure we have exactly 3 recommendations (or less if model returned fewer)
        return recommendations[:3]
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response text: {response_text}")
        # Fallback to a default recommendation
        return [{
            "song": "Weightless",
            "artist": "Marconi Union",
            "genre": "Ambient",
            "energy_level": "very low",
            "reason": "Universal calming track - default recommendation due to API parsing error"
        }]
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Fallback to a default recommendation
        return [{
            "song": "Weightless",
            "artist": "Marconi Union",
            "genre": "Ambient",
            "energy_level": "very low",
            "reason": f"Default recommendation due to error: {str(e)}"
        }]

if __name__ == "__main__":
    mcp.run()