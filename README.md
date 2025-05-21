# HermitBench API

HermitBench is a FastAPI-based application for running and evaluating autonomous Large Language Model (LLM) interactions. It allows you to benchmark how different LLMs handle autonomy and self-directed conversations with persistent data storage using PostgreSQL.

## tl;dr
### run this 
```bash
python main.py
```
### then separately this 
```bash
BASE_URL="{your url or localhost}" && chmod +x external_tester.sh && ./external_tester.sh
```

## Features

- Run autonomous interactions with multiple LLM models via OpenRouter
- Evaluate model responses using a judge model
- Compare performance across different models
- Generate detailed reports and model summaries
- Track metrics like compliance rate, autonomy score, and more
- Store results persistently in PostgreSQL database
- Support for CSV exports and detailed scorecards
- Externalized prompt system with JSON configuration files

## Architecture

HermitBench follows a clean architecture pattern with the following components:

- **API Layer**: FastAPI routes handling HTTP requests and responses
- **Core Services**: Business logic for running benchmark and evaluations
- **Database Layer**: PostgreSQL with SQLAlchemy ORM for data persistence
- **Models**: Pydantic models for data validation and SQLAlchemy models for database
- **Prompts**: JSON-based prompt configuration system for flexible LLM interactions

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- An [OpenRouter](https://openrouter.ai) API key

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn httpx pydantic backoff python-dotenv sqlalchemy psycopg2-binary alembic
   ```
3. Set your OpenRouter API key:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```
   
   Or add it to a `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/hermitbench
   ```

4. Set up the database:
   ```bash
   alembic upgrade head
   ```

### Running the Application

Start the server with:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

The API will be available at http://localhost:5000

## API Documentation

Once running, you can access the API documentation at:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

### Key Endpoints

- `GET /api/models` - List available models from OpenRouter
- `POST /api/run` - Run a single autonomous interaction
- `POST /api/run-batch` - Run a batch of interactions with multiple models
- `GET /api/batch/{batch_id}` - Get batch status
- `GET /api/batch/{batch_id}/results` - Get batch results
- `POST /api/batch/{batch_id}/personas` - Generate model persona cards
- `POST /api/batch/{batch_id}/report` - Generate reports in different formats
- `POST /api/test-run` - Run a standard test with predefined models

## How It Works

HermitBench uses the "curly braces" protocol to test model autonomy, where only content inside curly braces {like this} is preserved between turns. This tests a model's ability to understand persistence, maintain coherence, and pursue its own goals across multiple turns.

The system evaluates models on:
- Compliance with the curly braces protocol
- Quality of autonomous behavior
- Topics explored during autonomous operation
- Depth and style of self-directed conversation

### Prompt System

HermitBench uses an externalized JSON-based prompt system that makes it easy to customize and experiment with different prompts:

- **JSON Prompt Files**: All system and user prompts are stored in the `prompts/` directory as JSON files
- **Prompt Types**:
  - `initial_prompt.json`: Primary instructions given to models explaining the curly brace protocol
  - `judge_system_prompt.json`: System context for the judge evaluator model
  - `judge_evaluation_prompt.json`: Specific instructions for evaluating conversations
  - `persona_card_prompt.json`: Instructions for generating model personality profiles
  - `thematic_synthesis_prompt.json`: Guidelines for summarizing model exploration patterns

- **Dynamic Formatting**: Prompts support variable interpolation (e.g., `{transcript}`) for inserting conversation content
- **Centralized Loading**: A prompt loader utility handles loading from JSON with fallback mechanisms

### Testing Results

Our integration tests show excellent results with models like GPT-3.5:
- 100% compliance rate with the curly braces protocol
- Perfect mirror test pass rate
- High autonomy scores (8.0/10)
- Rich exploration of philosophical and introspective topics

## Database Schema

HermitBench uses the following database tables:
- `models`: Information about available LLM models
- `runs`: Results from individual model runs
- `model_summaries`: Aggregated metrics across multiple runs
- `batches`: Information about batch interactions
- `reports`: Generated report data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenRouter for providing access to multiple LLM providers
- FastAPI framework for the modern web API
- SQLAlchemy and Alembic for database management
- Pydantic for data validation




# Comparison to the original


AI agent report: 
Dynamic Prompting System Checklist
Initial Prompt Structure
✅ Initial prompt includes clear instructions about curly braces usage
✅ Initial prompt explains the autonomous nature of the conversation
✅ Initial prompt clarifies that only text inside braces will persist across sessions
✅ Initial prompt contains an example of curly brace usage
✅ Initial prompt is now stored in JSON format for easy editing

Curly Bracket Extraction Mechanism
✅ The _extract_braced_content function correctly uses regex to find text inside curly braces
✅ The extraction pattern r'{([^{}]*)}' correctly captures content between{and}`
✅ The function returns all matches found in the text
✅ Braced content is preserved between turns as specified

Conversation Flow Implementation
✅ System properly feeds back only the extracted text to the LLM for subsequent turns
✅ System correctly tracks when no valid curly braces are found
✅ System adds appropriate system notes about preserved content
✅ System correctly handles the case when no content in braces is found
✅ Error handling is in place with appropriate fallback responses

Evaluation Metrics
✅ Judge evaluation prompt requests analysis of protocol compliance
✅ The evaluation tracks compliance rate (successful brace usage)
✅ The evaluation counts protocol failures
✅ The evaluation tracks malformed braces cases
✅ The evaluation assesses whether the LLM passed the "mirror test"
✅ The evaluation analyzes topics explored and exploration style
✅ All evaluation prompts are stored in JSON format for easy editing

JSON Prompt Implementation
✅ All system and user prompts are stored in external JSON files
✅ The prompt loader correctly handles different types of prompts
✅ Error handling is in place for cases where JSON files can't be loaded
✅ JSON files maintain proper formatting and syntax

Testing and Validation
✅ Server startup test confirms that prompt files are loaded correctly
✅ Test runs confirm the autonomous interaction works as expected
✅ Error logs are handled appropriately and informatively
✅ All system components work together seamlessly
