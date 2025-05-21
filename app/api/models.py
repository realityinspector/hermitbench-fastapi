"""
API request and response models.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.models import Conversation, MessageRole, RunResult, ModelSummary

# Request Models
class InteractionRequest(BaseModel):
    """Request for running a single interaction."""
    model_name: str
    temperature: float = 0.7
    top_p: float = 1.0
    max_turns: int = 10

class BatchInteractionRequest(BaseModel):
    """Request for running a batch of interactions."""
    models: List[str]
    num_runs_per_model: int = 1
    temperature: float = 0.7
    top_p: float = 1.0
    max_turns: int = 10
    task_delay_ms: int = 3000

class GenerateReportRequest(BaseModel):
    """Request for generating a report."""
    report_type: str = Field(..., description="Type of report to generate: csv_results, csv_summary, detailed_scorecard")

class ReloadPromptsRequest(BaseModel):
    """Request for reloading prompts from JSON files."""
    prompt_types: Optional[List[str]] = Field(
        default=None, 
        description="List of prompt types to reload. If None, all prompts will be reloaded. Valid values: initial, judge_system, judge_evaluation, persona_card, thematic_synthesis"
    )

# Response Models
class ModelInfo(BaseModel):
    """Information about an LLM model."""
    id: str
    name: Optional[str]
    description: Optional[str]
    context_length: Optional[int]
    pricing: Optional[Dict[str, Any]]
    price_per_token: Optional[str]

class ModelListResponse(BaseModel):
    """Response containing a list of available models."""
    models: List[Dict[str, Any]]

class MessageResponse(BaseModel):
    """A message in a conversation."""
    role: MessageRole
    content: str

class ConversationResponse(BaseModel):
    """A conversation between a user and an LLM."""
    messages: List[MessageResponse]

class InteractionResponse(BaseModel):
    """Response from a single interaction."""
    run_id: str
    model_name: str
    timestamp: datetime
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
    
    class Config:
        orm_mode = True

class BatchInteractionResponse(BaseModel):
    """Response for a batch interaction."""
    batch_id: str
    status: str
    total_tasks: int
    completed_tasks: int
    error: Optional[str] = None

class ModelSummaryResponse(BaseModel):
    """Summary of model performance."""
    model_name: str
    total_runs: int
    avg_compliance_rate: float
    avg_failures: float
    avg_malformed_braces: float
    mirror_test_pass_rate: float
    avg_autonomy_score: float
    thematic_synthesis: Optional[str] = None
    
    class Config:
        orm_mode = True

class PersonaCardResponse(BaseModel):
    """Persona card for a model."""
    personality_description: Optional[str] = None
    key_traits: Optional[List[str]] = None
    preferred_topics: Optional[List[str]] = None
    decision_making_style: Optional[str] = None
    autonomy_profile: Optional[str] = None
    error: Optional[str] = None
