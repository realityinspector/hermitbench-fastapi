"""
Entry point for the HermitBench FastAPI application.
"""
import os
import uvicorn
import logging
from app.factory import create_app
from app.config import AppSettings
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()

# Check for OpenRouter API Key
api_key = os.getenv("OPENROUTER_API_KEY", "")
if not api_key:
    logging.warning("OPENROUTER_API_KEY not found in environment variables or Replit Secrets.")
    logging.warning("Note: Make sure to set it using Replit Secrets to use the API functionality.")

# Create app settings with environment variables
port = int(os.getenv("PORT", "5000"))  # Default to port 5000 for Replit
settings = AppSettings(
    openrouter_api_key=api_key,
    host=os.getenv("HOST", "0.0.0.0"),
    port=port
)

# Create the application
app = create_app(settings)

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True  # Enable hot reloading for development
    )
