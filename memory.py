from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import json


class MemoryType(str, Enum):
    """Types of memories the agent can store"""
    CONVERSATION = "conversation"
    OBSERVATION = "observation"
    DECISION = "decision"
    ACTION = "action"
    LEARNING = "learning"
    CONTEXT = "context"


class Memory(BaseModel):
    """Individual memory entry"""
    id: str = Field(..., description="Unique identifier for the memory")
    content: str = Field(..., description="The actual memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the memory was created")
    importance: float = Field(default=1.0, ge=0.0, le=10.0, description="Importance score (0-10)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")



class ShortTermMemory:
    """Short-term memory manager for the agent"""
    
    def __init__(self, max_memories: int = 100, retention_hours: int = 24):
        self.max_memories = max_memories
        self.retention_hours = retention_hours
        self.memories: List[Memory] = []
        self._next_id = 1
    
    def add_memory(
        self, 
        content: str, 
        memory_type: MemoryType,
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new memory to short-term storage"""
        memory_id = f"mem_{self._next_id}"
        self._next_id += 1
        
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.memories.append(memory)
        self._cleanup_old_memories()
        self._enforce_max_memories()
        
        return memory_id
    
    def get_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: Optional[int] = None,
        hours_back: Optional[int] = None
    ) -> List[Memory]:
        """Retrieve memories based on criteria"""
        filtered_memories = self.memories.copy()
        
        # Filter by type
        if memory_type:
            filtered_memories = [m for m in filtered_memories if m.memory_type == memory_type]
        
        # Filter by tags
        if tags:
            filtered_memories = [m for m in filtered_memories if any(tag in m.tags for tag in tags)]
        
        # Filter by importance
        filtered_memories = [m for m in filtered_memories if m.importance >= min_importance]
        
        # Filter by time
        if hours_back:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            filtered_memories = [m for m in filtered_memories if m.timestamp >= cutoff_time]
        
        # Sort by importance and timestamp (most recent first)
        filtered_memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        # Apply limit
        if limit:
            filtered_memories = filtered_memories[:limit]
        
        return filtered_memories
    
    def get_recent_context(self, limit: int = 10) -> List[Memory]:
        """Get recent memories for context"""
        return self.get_memories(limit=limit)
    
    def search_memories(self, query: str, limit: int = 10) -> List[Memory]:
        """Search memories by content"""
        query_lower = query.lower()
        matching_memories = [
            m for m in self.memories 
            if query_lower in m.content.lower()
        ]
        
        # Sort by relevance (importance + recency)
        matching_memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        return matching_memories[:limit]
    
    def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        """Update the importance of a memory"""
        for memory in self.memories:
            if memory.id == memory_id:
                memory.importance = max(0.0, min(10.0, new_importance))
                return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                del self.memories[i]
                return True
        return False
    
    def clear_memories(self, memory_type: Optional[MemoryType] = None):
        """Clear all memories or memories of a specific type"""
        if memory_type:
            self.memories = [m for m in self.memories if m.memory_type != memory_type]
        else:
            self.memories.clear()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        if not self.memories:
            return {"total": 0, "by_type": {}, "avg_importance": 0.0}
        
        by_type = {}
        total_importance = 0.0
        
        for memory in self.memories:
            by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1
            total_importance += memory.importance
        
        return {
            "total": len(self.memories),
            "by_type": by_type,
            "avg_importance": total_importance / len(self.memories),
            "oldest": min(self.memories, key=lambda m: m.timestamp).timestamp,
            "newest": max(self.memories, key=lambda m: m.timestamp).timestamp
        }
    
    def _cleanup_old_memories(self):
        """Remove memories older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        self.memories = [m for m in self.memories if m.timestamp >= cutoff_time]
    
    def _enforce_max_memories(self):
        """Remove least important memories if we exceed max_memories"""
        if len(self.memories) > self.max_memories:
            # Sort by importance (ascending) and timestamp (ascending)
            self.memories.sort(key=lambda m: (m.importance, m.timestamp))
            # Remove the least important/oldest memories
            excess = len(self.memories) - self.max_memories
            self.memories = self.memories[excess:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memories to dictionary for serialization"""
        return {
            "memories": [memory.dict() for memory in self.memories],
            "next_id": self._next_id,
            "max_memories": self.max_memories,
            "retention_hours": self.retention_hours
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load memories from dictionary"""
        self.memories = [Memory(**mem_data) for mem_data in data.get("memories", [])]
        self._next_id = data.get("next_id", 1)
        self.max_memories = data.get("max_memories", 100)
        self.retention_hours = data.get("retention_hours", 24)


# Convenience functions for common operations
def create_conversation_memory(content: str, importance: float = 2.0) -> Memory:
    """Create a conversation memory"""
    return Memory(
        id=f"conv_{datetime.now().timestamp()}",
        content=content,
        memory_type=MemoryType.CONVERSATION,
        importance=importance,
        timestamp=datetime.now()
    )


def create_observation_memory(content: str, importance: float = 1.5) -> Memory:
    """Create an observation memory"""
    return Memory(
        id=f"obs_{datetime.now().timestamp()}",
        content=content,
        memory_type=MemoryType.OBSERVATION,
        importance=importance,
        timestamp=datetime.now()
    )


def create_decision_memory(content: str, importance: float = 3.0) -> Memory:
    """Create a decision memory"""
    return Memory(
        id=f"dec_{datetime.now().timestamp()}",
        content=content,
        memory_type=MemoryType.DECISION,
        importance=importance,
        timestamp=datetime.now()
    )


# Initialize memory manager for the agent
memory = ShortTermMemory(max_memories=50, retention_hours=12)