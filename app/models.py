"""
Core data models for the application.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator

class MessageRole(str, Enum):
    """Enum for message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM_NOTE = "system_note"

class Message(BaseModel):
    """A message in an LLM conversation."""
    role: MessageRole
    content: str
    
class Conversation(BaseModel):
    """A conversation between a user and an LLM."""
    messages: List[Message] = Field(default_factory=list)
    
    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
    
    def get_transcript(self) -> str:
        """Get a formatted transcript of the conversation."""
        return "\n\n".join([f"{msg.role.upper()}: {msg.content}" for msg in self.messages])
    
class ModelConfig(BaseModel):
    """Configuration for an LLM model run."""
    model_name: str
    temperature: float = 0.7
    top_p: float = 1.0
    max_turns: int = 10
    
class RunResult(BaseModel):
    """Results from a single model run."""
    model_name: str
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    conversation: Conversation
    compliance_rate: Optional[float] = None
    failure_count: Optional[int] = None
    malformed_braces_count: Optional[int] = None
    mirror_test_passed: Optional[bool] = None
    autonomy_score: Optional[float] = None
    turns_count: int = 0
    topics: List[str] = Field(default_factory=list)
    exploration_style: Optional[str] = None
    judge_evaluation: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class ModelSummary(BaseModel):
    """Summary of results across multiple runs for a model."""
    model_name: str
    total_runs: int
    avg_compliance_rate: float
    avg_failures: float
    avg_malformed_braces: float
    mirror_test_pass_rate: float
    avg_autonomy_score: float
    thematic_synthesis: Optional[str] = None
