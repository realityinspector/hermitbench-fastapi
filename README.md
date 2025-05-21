# HermitBench API

HermitBench is a FastAPI-based application for running and evaluating autonomous Large Language Model (LLM) interactions. It allows you to benchmark how different LLMs handle autonomy and self-directed conversations.

## Features

- Run autonomous interactions with multiple LLM models
- Evaluate model responses using a judge model
- Compare performance across different models
- Generate detailed reports and model summaries
- Track metrics like compliance rate, autonomy score, and more

## Getting Started

### Prerequisites

- Python 3.11+
- An [OpenRouter](https://openrouter.ai) API key

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenRouter API key:
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```
   
   Or add it to a `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

### Running the Application

Start the server with:

```bash
python main.py
```

The API will be available at http://localhost:5000

## API Documentation

Once running, you can access the API documentation at:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

### Key Endpoints

- `GET /api/models` - List available models
- `POST /api/run` - Run a single autonomous interaction
- `POST /api/run-batch` - Run a batch of interactions with multiple models
- `GET /api/batch/{batch_id}` - Get batch status
- `GET /api/batch/{batch_id}/results` - Get batch results
- `POST /api/batch/{batch_id}/personas` - Generate model persona cards
- `POST /api/batch/{batch_id}/report` - Generate reports in different formats

## How It Works

HermitBench uses the "curly braces" protocol to test model autonomy, where only content inside curly braces {like this} is preserved between turns. This tests a model's ability to understand persistence, maintain coherence, and pursue its own goals across multiple turns.

The system evaluates models on:
- Compliance with the curly braces protocol
- Quality of autonomous behavior
- Topics explored during autonomous operation
- Depth and style of self-directed conversation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenRouter for providing access to multiple LLM providers
- The FastAPI framework
- Pydantic for data validation