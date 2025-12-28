"""
Perception Layer - Handles user inputs and environmental data
"""
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import google.generativeai as genai


class UserInput(BaseModel):
    """Structured representation of user input"""
    mood: str = Field(..., description="User's current mood")
    activity: str = Field(..., description="User's current activity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current time")
    location: Optional[Dict[str, Any]] = Field(default=None, description="User's location data")


class PerceptionManager:
    """Manages perception and input processing"""
    
    def __init__(self):
        self.current_input: Optional[UserInput] = None
    
    def perceive_user_input(
        self,
        mood: str,
        activity: str,
        timestamp: Optional[datetime] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> UserInput:
        """
        Process and structure user inputs
        
        Args:
            mood: User's current mood
            activity: User's current activity
            timestamp: Current timestamp (defaults to now)
            location: Location data with lat, lon, city, etc.
        
        Returns:
            Structured UserInput object
        """
        self.current_input = UserInput(
            mood=mood,
            activity=activity,
            timestamp=timestamp or datetime.now(),
            location=location
        )
        
        return self.current_input
    
    def format_input_for_agent(self) -> str:
        """
        Format the perceived input for the decision-making agent
        
        Returns:
            Formatted string with all context
        """
        if not self.current_input:
            return ""
        
        context = f"""
User Context:
- Mood: {self.current_input.mood}
- Activity: {self.current_input.activity}
- Time: {self.current_input.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if self.current_input.location:
            location_str = self.current_input.location.get('city', 'Unknown')
            if self.current_input.location.get('lat') and self.current_input.location.get('lon'):
                context += f"- Location: {location_str} ({self.current_input.location['lat']}, {self.current_input.location['lon']})\n"
            else:
                context += f"- Location: {location_str}\n"
        
        return context.strip()
    
    def get_semantic_tags(self) -> list[str]:
        """
        Extract semantic tags from the perceived input
        Useful for memory storage and retrieval
        
        Returns:
            List of tags
        """
        if not self.current_input:
            return []
        
        tags = []
        
        # Mood-based tags
        mood = self.current_input.mood.lower()
        if any(word in mood for word in ['happy', 'excited', 'joyful', 'energetic']):
            tags.append('positive-energy')
        elif any(word in mood for word in ['sad', 'melancholy', 'depressed', 'down']):
            tags.append('melancholic')
        elif any(word in mood for word in ['calm', 'peaceful', 'relaxed', 'zen']):
            tags.append('calm')
        elif any(word in mood for word in ['angry', 'frustrated', 'aggressive']):
            tags.append('intense')
        
        # Activity-based tags
        activity = self.current_input.activity.lower()
        if any(word in activity for word in ['work', 'study', 'focus', 'coding']):
            tags.append('focus')
        elif any(word in activity for word in ['exercise', 'workout', 'gym', 'running']):
            tags.append('exercise')
        elif any(word in activity for word in ['relax', 'meditate', 'chill', 'rest']):
            tags.append('relaxation')
        elif any(word in activity for word in ['party', 'celebrate', 'social']):
            tags.append('social')
        elif any(word in activity for word in ['commute', 'travel', 'driving']):
            tags.append('travel')
        
        # Time-based tags
        hour = self.current_input.timestamp.hour
        if 5 <= hour < 12:
            tags.append('morning')
        elif 12 <= hour < 17:
            tags.append('afternoon')
        elif 17 <= hour < 21:
            tags.append('evening')
        else:
            tags.append('night')
        
        return tags


# Initialize perception manager
perception_manager = PerceptionManager()

def perceive_with_gemini(
    mood: str,
    activity: str,
    tags: Optional[List[str]] = None,
    location: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash to produce a structured perception of user inputs.
    Returns a dict with normalized fields and semantic tags.
    """
    genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    now_iso = datetime.now().isoformat()
    prompt = f"""
You are a perception module. Normalize inputs and infer semantic tags.
Return ONLY valid JSON, no extra text.

Inputs:
- mood: {mood}
- activity: {activity}
- tags: {tags or []}
- location: {location or {}}
- timestamp: {now_iso}

Requirements:
- Normalize mood and activity to short phrases.
- Provide 5-10 semantic tags (lowercase, hyphenated).
- Include a concise time_context (e.g., "weekday morning", "late night").
- If location has lat/lon, keep them; if text present, echo it as provided_text.
- Provide a compact summary string.

JSON schema:
{{
  "mood_normalized": "string",
  "activity_normalized": "string",
  "semantic_tags": ["string", "..."],
  "time_context": "string",
  "location": {{
     "lat": "number|null",
     "lon": "number|null",
     "provided_text": "string|null"
  }},
  "summary": "string"
}}
"""



    print(f"\n\nCurrent prompt: \n==================\n {prompt} \n==================\n")
    resp = model.generate_content(prompt)
    text = (resp.text or "").strip()

    # Extract JSON if wrapped in code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(text)
    except Exception:
        # Minimal safe fallback
        data = {
            "mood_normalized": mood.strip().lower(),
            "activity_normalized": activity.strip().lower(),
            "semantic_tags": (tags or [])[:10],
            "time_context": "unknown",
            "location": {
                "lat": (location or {}).get("lat") if location else None,
                "lon": (location or {}).get("lon") if location else None,
                "provided_text": (location or {}).get("text") if location else None,
            },
            "summary": f"mood={mood}; activity={activity}; tags={(tags or [])}"
        }

    # Ensure required keys exist
    data.setdefault("semantic_tags", [])
    data.setdefault("location", {})
    data["location"].setdefault("lat", (location or {}).get("lat") if location else None)
    data["location"].setdefault("lon", (location or {}).get("lon") if location else None)
    data["location"].setdefault("provided_text", (location or {}).get("text") if location else None)

    return data

