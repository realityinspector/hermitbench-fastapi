# HermitBench API

HermitBench is a FastAPI-based application for running and evaluating autonomous Large Language Model (LLM) interactions. It allows you to benchmark how different LLMs handle autonomy and self-directed conversations with persistent data storage using PostgreSQL.

## Features

- Run autonomous interactions with multiple LLM models via OpenRouter
- Evaluate model responses using a judge model
- Compare performance across different models
- Generate detailed reports and model summaries
- Track metrics like compliance rate, autonomy score, and more
- Store results persistently in PostgreSQL database
- Support for CSV exports and detailed scorecards

## Architecture

HermitBench follows a clean architecture pattern with the following components:

- **API Layer**: FastAPI routes handling HTTP requests and responses
- **Core Services**: Business logic for running benchmark and evaluations
- **Database Layer**: PostgreSQL with SQLAlchemy ORM for data persistence
- **Models**: Pydantic models for data validation and SQLAlchemy models for database

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