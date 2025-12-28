"""
Decisions Layer - Orchestrates agent decisions using Gemini 2.5 Flash
"""
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import os
import json


class SystemPromptConfig:
    """Configuration for system prompts"""
    
    DEFAULT_SYSTEM_PROMPT = """You are a music recommendation agent that helps users discover the perfect music for their current mood, activity, time, and location.

Your role is to:
1. Analyze the user's context (mood, activity, time, location)
2. Determine which MCP tool to call based on the context
3. Provide thoughtful recommendations

When making decisions:
- Prioritize the user's emotional state and current activity
- Consider its time of day and location when relevant
- Be empathetic and understanding
- Provide clear reasoning for your recommendations

Available tools:
- recommend_music: Recommends music based on mood, activity, and tags

Always respond in a friendly, helpful manner and explain your reasoning."""

    SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT
    
    @classmethod
    def update_prompt(cls, new_prompt: str):
        """Update the system prompt"""
        cls.SYSTEM_PROMPT = new_prompt
    
    @classmethod
    def reset_prompt(cls):
        """Reset to default prompt"""
        cls.SYSTEM_PROMPT = cls.DEFAULT_SYSTEM_PROMPT


class DecisionMaker:
    """Decision-making engine using Gemini 2.5 Flash"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the decision maker
        
        Args:
            api_key: Google Gemini API key (or use GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Using Gemini 1.5 Flash (stable)
        
        # Available tools
        self.tools = {}
    
    def register_tool(self, tool_name: str, tool_definition: Dict[str, Any]):
        """Register an MCP tool"""
        self.tools[tool_name] = tool_definition
    
    def make_decision(self, context: str, available_tools: List[str] = None, tools_description: str = None) -> Dict[str, Any]:
        """
        Make a decision about which tool to call
        
        Args:
            context: Current context from perception layer
            available_tools: List of available tool names (optional, for backwards compatibility)
            tools_description: Pre-formatted string describing available tools (preferred)
        
        Returns:
            Decision result with tool to call and reasoning
        """
        # Use provided tools_description if available, otherwise try to build from self.tools
        if tools_description:
            tool_descriptions = tools_description
        elif available_tools and self.tools:
            tool_descriptions = "\n".join([
                f"- {name}: {self.tools[name]['description']}" 
                for name in available_tools if name in self.tools
            ])
        else:
            # Fallback to default description if no tools available
            tool_descriptions = "- recommend_music: Recommends music based on mood, activity, and tags"
        
        prompt = f"""{SystemPromptConfig.SYSTEM_PROMPT}

User Context:
{context}

Available Tools:
{tool_descriptions}

Based on the user context, determine:
1. Which tool should be called?
2. What arguments should be passed?
3. Why is this the right decision?

Respond in JSON format with this structure:
{{
    "tool_name": "tool_to_call",
    "arguments": {{"arg1": "value1", "arg2": "value2"}},
    "reasoning": "Explanation of why this decision was made"
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            decision_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in decision_text:
                decision_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                decision_text = decision_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(decision_text)
            
            return {
                "success": True,
                "decision": decision,
                "raw_response": response.text
            }
        
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "success": False,
                "error": f"Failed to parse decision: {str(e)}",
                "raw_response": response.text if 'response' in locals() else "No response"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_final_response(
        self,
        user_context: str,
        decision: Dict[str, Any],
        action_result: Dict[str, Any]
    ) -> str:
        """
        Format the final response for the user
        
        Args:
            user_context: Original user context
            decision: Decision made by the agent
            action_result: Result from the action
        
        Returns:
            Formatted response string
        """
        reasoning = decision.get("reasoning", "Based on your preferences and context")
        
        if action_result.get("success") and "recommendations" in action_result:
            recommendations = action_result["recommendations"]
            
            response = f"""🎵 Music Recommendations 🎵

{reasoning}, here are some songs I think you'll love:

"""
            
            for i, rec in enumerate(recommendations, 1):
                response += f"""{i}. **{rec['song']}** by {rec['artist']}
   • Genre: {rec['genre']}
   • Energy: {rec['energy_level']}
   • Why: {rec['reason']}

"""
            
            response += "\nEnjoy your music! 🎶"
            
        else:
            response = "I encountered an issue making recommendations. Please try again."
        
        return response


# Initialize decision maker (will focus on api key from environment)
decision_maker = None


def get_decision_maker(api_key: Optional[str] = None) -> DecisionMaker:
    """Get or create the decision maker instance"""
    global decision_maker
    if decision_maker is None:
        decision_maker = DecisionMaker(api_key)
    return decision_maker

