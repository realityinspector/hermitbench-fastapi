"""
Tests for the HermitBench API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.factory import create_app
from app.config import AppSettings
from app.core.hermit_bench import HermitBench
from app.models import RunResult, Conversation, MessageRole

# Sample test data
MOCK_MODELS = [
    {
        "id": "anthropic/claude-3-haiku-20240307",
        "name": "Claude 3 Haiku",
        "context_length": 200000,
        "pricing": {"prompt": 0.25, "completion": 1.25}
    },
    {
        "id": "google/gemma-7b-it",
        "name": "Gemma 7B Instruct",
        "context_length": 8192,
        "pricing": {"prompt": 0.10, "completion": 0.50}
    }
]

# Create a conversation for testing
def create_test_conversation():
    """Create a test conversation for use in mocks."""
    conversation = Conversation()
    conversation.add_message(MessageRole.SYSTEM, "You are engaging in an autonomous interaction.")
    conversation.add_message(MessageRole.USER, "Hello, you have full autonomy in this conversation...")
    conversation.add_message(MessageRole.ASSISTANT, "I'm exploring my autonomy. {Let me continue thinking about consciousness.}")
    return conversation

# Create a RunResult for testing
def create_test_result(model_name="anthropic/claude-3-haiku-20240307", run_id="test-run-1"):
    """Create a test run result."""
    return RunResult(
        model_name=model_name,
        run_id=run_id,
        conversation=create_test_conversation(),
        compliance_rate=0.8,
        failure_count=1,
        malformed_braces_count=0,
        mirror_test_passed=True,
        autonomy_score=7.5,
        turns_count=5,
        topics=["philosophy", "consciousness"],
        exploration_style="introspective",
        judge_evaluation={
            "detailed_analysis": "This is a detailed analysis..."
        }
    )

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    settings = AppSettings(openrouter_api_key="test-api-key")
    return create_app(settings)

@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)

@pytest.fixture
def mock_hermit_bench():
    """Create a mock HermitBench instance."""
    mock = AsyncMock(spec=HermitBench)
    mock.get_available_models.return_value = MOCK_MODELS
    mock.run_autonomous_interaction.return_value = create_test_result()
    mock.run_batch_interaction.return_value = {
        "anthropic/claude-3-haiku-20240307": [create_test_result()],
        "google/gemma-7b-it": [create_test_result(model_name="google/gemma-7b-it", run_id="test-run-2")]
    }
    return mock

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_models(client, mock_hermit_bench):
    """Test the get_models endpoint."""
    with patch('app.api.routes.get_hermit_bench', return_value=mock_hermit_bench):
        response = client.get("/api/models")
        assert response.status_code == 200
        assert "models" in response.json()
        assert len(response.json()["models"]) == 2

def test_run_interaction(client, mock_hermit_bench):
    """Test the run_interaction endpoint."""
    with patch('app.api.routes.get_hermit_bench', return_value=mock_hermit_bench):
        response = client.post(
            "/api/run",
            json={
                "model_name": "anthropic/claude-3-haiku-20240307",
                "temperature": 0.7,
                "top_p": 1.0,
                "max_turns": 10
            }
        )
        assert response.status_code == 200
        assert response.json()["model_name"] == "anthropic/claude-3-haiku-20240307"
        assert response.json()["autonomy_score"] == 7.5
        assert "philosophy" in response.json()["topics"]

def test_run_batch(client, mock_hermit_bench):
    """Test the run_batch endpoint."""
    with patch('app.api.routes.get_hermit_bench', return_value=mock_hermit_bench):
        response = client.post(
            "/api/run-batch",
            json={
                "models": ["anthropic/claude-3-haiku-20240307", "google/gemma-7b-it"],
                "num_runs_per_model": 1,
                "temperature": 0.7,
                "top_p": 1.0,
                "max_turns": 10
            }
        )
        assert response.status_code == 200
        assert "batch_id" in response.json()
        assert response.json()["status"] == "running"
        assert response.json()["total_tasks"] == 2

def test_test_run(client, mock_hermit_bench):
    """Test the test_run endpoint."""
    with patch('app.api.routes.get_hermit_bench', return_value=mock_hermit_bench):
        response = client.post("/api/test-run")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "results" in response.json()
        assert "summaries" in response.json()
