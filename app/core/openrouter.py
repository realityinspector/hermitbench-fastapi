"""
Client for interacting with the OpenRouter API.
"""
import httpx
import backoff
import logging
from typing import Dict, List, Any, Optional
import json

# Configure logger
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    Client for making requests to the OpenRouter API.
    """
    
    def __init__(self, api_key: str, api_base: str = "https://openrouter.ai/api/v1"):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            api_base: Base URL for the OpenRouter API
        """
        self.api_key = api_key
        self.api_base = api_base
        
        # Default headers for all requests
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hermitbench.fastapi",  # Required by OpenRouter
        }
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        max_time=30
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Make a request to the OpenRouter API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data for POST requests
            timeout: Request timeout in seconds
            
        Returns:
            JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from OpenRouter.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = await self._make_request("GET", "/models")
            models = response.get("data", [])
            
            # Add pricing information where available
            for model in models:
                if "pricing" in model and "prompt" in model["pricing"]:
                    model["price_per_token"] = model["pricing"]["prompt"]
                else:
                    model["price_per_token"] = "Unknown"
            
            return models
        except Exception as e:
            logger.error(f"Error fetching models from OpenRouter: {str(e)}")
            raise
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion from a model.
        
        Args:
            model: Name of the model to use
            messages: List of message dictionaries with role and content
            temperature: Temperature for generation
            top_p: Top-p value for generation
            max_tokens: Maximum tokens to generate (None for model default)
            
        Returns:
            Chat completion response
        """
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        try:
            return await self._make_request("POST", "/chat/completions", data)
        except Exception as e:
            logger.error(f"Error getting chat completion from {model}: {str(e)}")
            raise
