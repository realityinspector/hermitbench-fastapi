"""
Utility for loading prompts from JSON files.
"""
import json
import os
import logging
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

def load_prompt(file_path: str, prompt_key: Optional[str] = None, 
             fallback_text: Optional[str] = None) -> str:
    """
    Load a prompt from a JSON file with robust error handling.
    
    Args:
        file_path: Path to the JSON file containing the prompt
        prompt_key: Key for the specific prompt to load from the JSON file
                    If None, the first value in the JSON object will be returned
        fallback_text: Optional fallback text to return if the prompt cannot be loaded
    
    Returns:
        The loaded prompt as a string, or the fallback text if provided and the prompt cannot be loaded
    
    Raises:
        FileNotFoundError: If the specified file does not exist and no fallback is provided
        KeyError: If the specified prompt key does not exist and no fallback is provided
        json.JSONDecodeError: If the file contains invalid JSON and no fallback is provided
    """
    try:
        # Get the absolute path relative to the prompts directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, file_path)
        
        # Attempt to read raw file content first
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
                
            # Handle empty files
            if not file_content:
                logger.warning(f"Empty prompt file: {file_path}")
                if fallback_text is not None:
                    logger.info(f"Using fallback text for {file_path}")
                    return fallback_text
                raise ValueError("Empty prompt file")
            
            # Try to parse JSON
            prompts = json.loads(file_content)
            
            if prompt_key:
                if prompt_key not in prompts:
                    logger.warning(f"Prompt key '{prompt_key}' not found in {file_path}")
                    if fallback_text is not None:
                        logger.info(f"Using fallback text for missing key '{prompt_key}' in {file_path}")
                        return fallback_text
                    raise KeyError(f"Prompt key '{prompt_key}' not found in {file_path}")
                return prompts[prompt_key]
            else:
                # If no key is specified, return the first value
                return next(iter(prompts.values()))
                
        except json.JSONDecodeError as e:
            # Try to fix common JSON formatting issues
            logger.warning(f"Invalid JSON in {file_path}. Attempting to fix...")
            
            # Get fresh content since we're in the exception handler
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
            except Exception as inner_e:
                logger.error(f"Failed to re-read file in error handler: {str(inner_e)}")
                if fallback_text is not None:
                    return fallback_text
                raise ValueError(f"Internal error processing {file_path}")
                
            # Try adding missing braces or fixing common issues
            if not file_content.strip().startswith('{'):
                file_content = '{' + file_content
            if not file_content.strip().endswith('}'):
                file_content = file_content + '}'
                
            # Remove comments that might cause parsing issues
            file_content = '\n'.join([line for line in file_content.split('\n') 
                                    if not line.strip().startswith('//')])
            
            # Replace JavaScript-style comments in JSON strings
            import re
            file_content = re.sub(r'//.*', '', file_content)
            
            try:
                # Try parsing the fixed JSON
                prompts = json.loads(file_content)
                logger.info(f"Successfully fixed JSON formatting in {file_path}")
                
                if prompt_key:
                    if prompt_key not in prompts:
                        if fallback_text is not None:
                            return fallback_text
                        raise KeyError(f"Prompt key '{prompt_key}' not found in fixed JSON")
                    return prompts[prompt_key]
                else:
                    return next(iter(prompts.values()))
            except Exception:
                # If we still can't parse it and have a fallback, use that
                if fallback_text is not None:
                    logger.info(f"Using fallback text for {file_path} after failed JSON repair")
                    return fallback_text
                # Otherwise, re-raise the original error
                logger.error(f"Failed to fix JSON in {file_path}: {str(e)}")
                raise
                
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        if fallback_text is not None:
            logger.info(f"Using fallback text for missing file {file_path}")
            return fallback_text
        raise
    except Exception as e:
        logger.error(f"Error loading prompt from {file_path}: {str(e)}")
        if fallback_text is not None:
            logger.info(f"Using fallback text due to error: {str(e)}")
            return fallback_text
        raise

def load_all_prompts(file_path: str, fallback_dict: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Load all prompts from a JSON file with robust error handling.
    
    Args:
        file_path: Path to the JSON file containing the prompts
        fallback_dict: Optional fallback dictionary to return if the prompts cannot be loaded
    
    Returns:
        Dictionary of prompt keys to prompt values, or the fallback dictionary if provided
        and the prompts cannot be loaded
    
    Raises:
        FileNotFoundError: If the specified file does not exist and no fallback is provided
        json.JSONDecodeError: If the file contains invalid JSON and no fallback is provided
    """
    try:
        # Get the absolute path relative to the prompts directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, file_path)
        
        try:
            # Read raw file content first
            with open(full_path, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
            
            # Handle empty files
            if not file_content:
                logger.warning(f"Empty prompt file: {file_path}")
                if fallback_dict is not None:
                    logger.info(f"Using fallback dictionary for {file_path}")
                    return fallback_dict
                raise ValueError("Empty prompt file")
            
            # Try to parse JSON
            try:
                return json.loads(file_content)
            except json.JSONDecodeError as e:
                # Try to fix common JSON formatting issues
                logger.warning(f"Invalid JSON in {file_path}. Attempting to fix...")
                
                # Re-read the file to ensure we have the content
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                except Exception as inner_e:
                    logger.error(f"Failed to re-read file in error handler: {str(inner_e)}")
                    if fallback_dict is not None:
                        return fallback_dict
                    raise ValueError(f"Internal error processing {file_path}")
                
                # Try adding missing braces or fixing common issues
                if not file_content.strip().startswith('{'):
                    file_content = '{' + file_content
                if not file_content.strip().endswith('}'):
                    file_content = file_content + '}'
                    
                # Remove comments that might cause parsing issues
                file_content = '\n'.join([line for line in file_content.split('\n') 
                                        if not line.strip().startswith('//')])
                
                # Replace JavaScript-style comments in JSON strings
                import re
                file_content = re.sub(r'//.*', '', file_content)
                
                try:
                    # Try parsing the fixed JSON
                    prompts = json.loads(file_content)
                    logger.info(f"Successfully fixed JSON formatting in {file_path}")
                    return prompts
                except Exception:
                    # If we still can't parse it and have a fallback, use that
                    if fallback_dict is not None:
                        logger.info(f"Using fallback dictionary for {file_path} after failed JSON repair")
                        return fallback_dict
                    # Otherwise, re-raise the original error
                    logger.error(f"Failed to fix JSON in {file_path}: {str(e)}")
                    raise
        
        except Exception as e:
            if fallback_dict is not None:
                logger.info(f"Using fallback dictionary due to error: {str(e)}")
                return fallback_dict
            raise
            
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        if fallback_dict is not None:
            logger.info(f"Using fallback dictionary for missing file {file_path}")
            return fallback_dict
        raise
    except Exception as e:
        logger.error(f"Error loading prompts from {file_path}: {str(e)}")
        if fallback_dict is not None:
            logger.info(f"Using fallback dictionary due to error: {str(e)}")
            return fallback_dict
        raise