"""
Helper functions for the HermitBench application.
"""
import re
import json
from typing import List, Dict, Any, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

def format_time_ms(ms: int) -> str:
    """
    Format milliseconds as a human-readable time string.
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Formatted time string
    """
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"

def extract_braced_content(text: str) -> List[str]:
    """
    Extract content enclosed in curly braces from text.
    
    Args:
        text: The text to extract braced content from
        
    Returns:
        List of strings found inside curly braces
    """
    pattern = r'{([^{}]*)}'
    matches = re.findall(pattern, text)
    return matches

def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely load JSON from a string, returning a default value on error.
    
    Args:
        text: JSON string to parse
        default: Default value to return on error
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {str(e)}")
        return default

def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length, adding ellipsis if truncated.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def find_json_in_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Find and extract a JSON object from text that might contain other content.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON object or None if not found
    """
    # Try common patterns for JSON in text
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # JSON in code block with language
        r'```\s*([\s\S]*?)\s*```',      # JSON in code block
        r'{[\s\S]*?}',                  # Any JSON object
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Clean up the match if it's not a complete JSON object
                if not match.strip().startswith('{'):
                    continue
                
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    
    return None
