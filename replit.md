# HermitBench API Documentation

## Overview

HermitBench is a tool for running and evaluating autonomous Large Language Model (LLM) interactions. The system enables users to test the autonomous capabilities of various LLMs by having them engage in "hermit-style" conversations where the model is given the freedom to direct its own thought process and interactions. The key innovation is a curly braces mechanism that allows models to control what gets passed between turns.

This FastAPI application provides a RESTful API interface to HermitBench, allowing users to:
- Run single or batch autonomous LLM interactions
- Evaluate model interactions using a judge model
- Analyze and compare different models' autonomous behavior
- Generate reports on interaction results

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## System Architecture

The application follows a clean architecture pattern with clear separation of concerns:

1. **API Layer**: FastAPI routes that handle HTTP requests and responses
2. **Core Services**: Main business logic for running the benchmark and evaluating results
3. **Models**: Data structures that represent the domain objects
4. **Configuration**: System settings and environment variables
5. **Utils**: Helper functions and utilities

The system is built around an asynchronous workflow, leveraging Python's asyncio to handle concurrent LLM requests efficiently.

### Key Architectural Decisions

- **FastAPI Framework**: Chosen for its high performance, automatic OpenAPI documentation, and native async support
- **OpenRouter Integration**: Used as an abstraction layer to access multiple LLM providers through a unified API
- **In-memory Result Storage**: Results are temporarily stored in memory for quick access, with options to export data
- **Asynchronous Processing**: Background tasks handle long-running benchmark operations without blocking API responses
- **Evaluation System**: A judge model evaluates the autonomous behavior of tested models

## Key Components

### 1. OpenRouter Client (`app/core/openrouter.py`)
- Handles API communication with OpenRouter
- Implements retry logic using backoff for robust communication
- Provides methods for model listing and chat completions

### 2. HermitBench Runner (`app/core/hermit_bench.py`)
- Core logic for running autonomous LLM interactions
- Manages conversation flow and turn tracking
- Implements the curly braces protocol for autonomy testing

### 3. Judge Evaluator (`app/core/evaluator.py`)
- Uses a designated judge model to evaluate autonomous interactions
- Calculates metrics like compliance rate, autonomy score, etc.
- Provides standardized evaluation across different models

### 4. API Routes (`app/api/routes.py`)
- Defines RESTful endpoints for interaction with the system
- Handles request validation and response formatting
- Manages background tasks for batch processing

### 5. Data Models (`app/models.py`, `app/api/models.py`)
- Defines Pydantic models for data validation and serialization
- Core domain models (Conversation, Message, RunResult)
- API-specific request and response models

## Data Flow

1. **Model Selection Flow**:
   - Client requests available models from the `/api/models` endpoint
   - System queries OpenRouter API for model list
   - Response includes model details, capabilities, and pricing

2. **Single Interaction Flow**:
   - Client submits a request with model configuration
   - System initializes a conversation with the autonomy prompt
   - LLM responds with a mix of internal thoughts and curly-braced content
   - System extracts braced content and passes only that to next turn
   - Process repeats for specified number of turns
   - Judge model evaluates the full conversation
   - Results returned to client

3. **Batch Processing Flow**:
   - Client submits multiple models for testing
   - System creates background task to handle processing
   - Each model runs in sequence with specified configuration
   - Results stored in memory with a batch ID
   - Client can poll for completion and retrieve results

4. **Reporting Flow**:
   - Client requests report generation
   - System formats results as requested (CSV, detailed scorecard)
   - Returns downloadable report data

## External Dependencies

1. **Core Dependencies**:
   - `fastapi`: Web framework for building APIs
   - `uvicorn`: ASGI server for running the application
   - `httpx`: Async HTTP client for API requests
   - `pydantic`: Data validation and settings management
   - `backoff`: Retry mechanism for API calls

2. **External Services**:
   - **OpenRouter API**: Gateway to access various LLM providers
   - Requires an API key set as `OPENROUTER_API_KEY` environment variable

3. **Testing Dependencies**:
   - `pytest`: Testing framework
   - `pytest-asyncio`: Async test support

## Deployment Strategy

The application is configured to run in a Replit environment with the following setup:

1. **Runtime Environment**:
   - Python 3.11
   - FastAPI application served by Uvicorn
   - Environment variables for configuration

2. **Execution**:
   - Entry point: `main.py` which creates and runs the FastAPI app
   - Server runs on port 5000 with hot reload enabled during development

3. **Configuration**:
   - Environment variables used for API keys and settings
   - Default values provided for non-sensitive configuration

4. **Scaling Considerations**:
   - In-memory storage is used for demo purposes
   - For production, consider implementing a database backend for result storage
   - Rate limiting should be implemented for OpenRouter API consumption

5. **Security Notes**:
   - API key is required for OpenRouter
   - CORS is enabled with permissive settings for development

## Getting Started

1. Set the required environment variable:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

2. The application will start automatically in Replit using the configured workflow.

3. Access the API documentation at `/docs` to explore available endpoints.

## Future Enhancements

1. Add database integration for persistent storage of results
2. Implement user authentication and result ownership
3. Add more sophisticated analysis and visualization tools
4. Support for custom prompts and evaluation criteria
5. Integration with additional LLM providers beyond OpenRouter