"""
Entry point for the HermitBench FastAPI application.
"""
import os
import uvicorn
import logging
from app.factory import create_app
from app.config import AppSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create app settings with environment variables
settings = AppSettings(
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000"))
)

# Create the application
app = create_app(settings)

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
