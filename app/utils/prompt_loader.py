"""
Utility for loading prompts from JSON files.
"""
import json
import os
import logging
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

def load_prompt(file_path: str, prompt_key: Optional[str] = None) -> str:
    """
    Load a prompt from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the prompt
        prompt_key: Key for the specific prompt to load from the JSON file
                    If None, the first value in the JSON object will be returned
    
    Returns:
        The loaded prompt as a string
    
    Raises:
        FileNotFoundError: If the specified file does not exist
        KeyError: If the specified prompt key does not exist in the JSON file
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        # Get the absolute path relative to the prompts directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        if prompt_key:
            if prompt_key not in prompts:
                raise KeyError(f"Prompt key '{prompt_key}' not found in {file_path}")
            return prompts[prompt_key]
        else:
            # If no key is specified, return the first value
            return next(iter(prompts.values()))
            
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in prompt file {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompt from {file_path}: {str(e)}")
        raise

def load_all_prompts(file_path: str) -> Dict[str, str]:
    """
    Load all prompts from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the prompts
    
    Returns:
        Dictionary of prompt keys to prompt values
    
    Raises:
        FileNotFoundError: If the specified file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        # Get the absolute path relative to the prompts directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in prompt file {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompts from {file_path}: {str(e)}")
        raise