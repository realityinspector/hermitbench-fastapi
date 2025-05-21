"""
Configuration settings for the application.
"""
from typing import Optional, Dict, Any, List
import os
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppSettings(BaseSettings):
    """Application configuration settings."""
    # OpenRouter API settings
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_api_base: str = "https://openrouter.ai/api/v1"
    
    # Default LLM settings
    default_temperature: float = 0.7
    default_top_p: float = 1.0
    default_max_turns: int = 10
    default_num_runs_per_model: int = 1
    default_task_delay_ms: int = 3000
    
    # Judge model settings
    judge_model_name: str = "anthropic/claude-2.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    @validator("openrouter_api_key")
    def validate_api_key(cls, v: str) -> str:
        """Validate that an API key is provided."""
        if not v:
            # Warning only, don't prevent startup, will be checked at runtime
            print("WARNING: No OpenRouter API key provided. Set OPENROUTER_API_KEY environment variable.")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
