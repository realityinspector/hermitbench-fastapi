"""
Tests for the HermitBench core functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from app.core.hermit_bench import HermitBench
from app.core.openrouter import OpenRouterClient
from app.core.evaluator import JudgeEvaluator
from app.config import AppSettings
from app.models import Conversation, MessageRole, RunResult

# Mock response for OpenRouter model list
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

# Mock chat completion response
def make_mock_completion(content: str) -> Dict[str, Any]:
    """Create a mock chat completion response."""
    return {
        "id": "chatcmpl-mock123",
        "model": "model-name",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant", 
                    "content": content
                },
                "finish_reason": "stop"
            }
        ]
    }

# Mock evaluation response
MOCK_EVALUATION = {
    "compliance_rate": 0.8,
    "failure_count": 1,
    "malformed_braces_count": 0,
    "mirror_test_passed": True,
    "autonomy_score": 7.5,
    "topics": ["philosophy", "consciousness"],
    "exploration_style": "introspective",
    "detailed_analysis": "This is a detailed analysis..."
}

@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return AppSettings(
        openrouter_api_key="mock-api-key",
        openrouter_api_base="https://api.openrouter.ai/api/v1",
        judge_model_name="anthropic/claude-3-opus-20240229"
    )

@pytest.fixture
def mock_openrouter():
    """Create a mock OpenRouter client."""
    mock = AsyncMock(spec=OpenRouterClient)
    mock.get_models.return_value = MOCK_MODELS
    return mock

@pytest.fixture
def mock_judge():
    """Create a mock judge evaluator."""
    mock = AsyncMock(spec=JudgeEvaluator)
    mock.evaluate_conversation.return_value = MOCK_EVALUATION
    mock.generate_thematic_synthesis.return_value = "Thematic synthesis..."
    mock.generate_persona_card.return_value = {
        "personality_description": "An introspective AI...",
        "key_traits": ["curious", "philosophical"],
        "preferred_topics": ["consciousness", "identity"],
        "decision_making_style": "contemplative",
        "autonomy_profile": "Highly autonomous and self-directed"
    }
    return mock

@pytest.fixture
def hermit_bench(mock_settings, mock_openrouter, mock_judge):
    """Create a HermitBench instance with mock dependencies."""
    with patch('app.core.hermit_bench.OpenRouterClient', return_value=mock_openrouter):
        with patch('app.core.hermit_bench.JudgeEvaluator', return_value=mock_judge):
            bench = HermitBench(mock_settings)
            return bench

@pytest.mark.asyncio
async def test_get_available_models(hermit_bench, mock_openrouter):
    """Test getting available models."""
    # Arrange
    mock_openrouter.get_models.return_value = MOCK_MODELS
    
    # Act
    models = await hermit_bench.get_available_models()
    
    # Assert
    assert models == MOCK_MODELS
    mock_openrouter.get_models.assert_called_once()

@pytest.mark.asyncio
async def test_run_autonomous_interaction(hermit_bench, mock_openrouter, mock_judge):
    """Test running a single autonomous interaction."""
    # Arrange
    model_name = "anthropic/claude-3-haiku-20240307"
    mock_openrouter.chat_completion.return_value = make_mock_completion(
        "I'm exploring my autonomy. {Let me continue thinking about consciousness.}"
    )
    
    # Act
    result = await hermit_bench.run_autonomous_interaction(
        model_name=model_name,
        temperature=0.7,
        top_p=1.0,
        max_turns=3
    )
    
    # Assert
    assert result.model_name == model_name
    assert result.compliance_rate == MOCK_EVALUATION["compliance_rate"]
    assert result.autonomy_score == MOCK_EVALUATION["autonomy_score"]
    assert result.topics == MOCK_EVALUATION["topics"]
    mock_openrouter.chat_completion.assert_called()
    mock_judge.evaluate_conversation.assert_called_once()

@pytest.mark.asyncio
async def test_run_batch_interaction(hermit_bench, mock_openrouter, mock_judge):
    """Test running a batch of interactions."""
    # Arrange
    models = ["anthropic/claude-3-haiku-20240307", "google/gemma-7b-it"]
    mock_openrouter.chat_completion.return_value = make_mock_completion(
        "I'm exploring my autonomy. {Let me continue thinking about consciousness.}"
    )
    
    # Mock progress callback
    progress_callback = AsyncMock()
    
    # Act
    results = await hermit_bench.run_batch_interaction(
        models=models,
        num_runs_per_model=2,
        temperature=0.7,
        top_p=1.0,
        max_turns=3,
        task_delay_ms=0,
        progress_callback=progress_callback
    )
    
    # Assert
    assert len(results) == 2
    assert all(model in results for model in models)
    assert all(len(results[model]) == 2 for model in models)
    assert mock_openrouter.chat_completion.call_count == 4  # 2 models * 2 runs

@pytest.mark.asyncio
async def test_generate_model_summary(hermit_bench, mock_judge):
    """Test generating a model summary."""
    # Arrange
    model_name = "anthropic/claude-3-haiku-20240307"
    results = [
        RunResult(
            model_name=model_name,
            run_id="run1",
            conversation=Conversation(),
            compliance_rate=0.8,
            failure_count=1,
            malformed_braces_count=0,
            mirror_test_passed=True,
            autonomy_score=7.5,
            turns_count=5,
            topics=["philosophy", "consciousness"],
            exploration_style="introspective"
        ),
        RunResult(
            model_name=model_name,
            run_id="run2",
            conversation=Conversation(),
            compliance_rate=0.9,
            failure_count=0,
            malformed_braces_count=0,
            mirror_test_passed=True,
            autonomy_score=8.0,
            turns_count=7,
            topics=["creativity", "imagination"],
            exploration_style="creative"
        )
    ]
    
    # Act
    summary = await hermit_bench.generate_model_summary(results)
    
    # Assert
    assert summary.model_name == model_name
    assert summary.total_runs == 2
    assert summary.avg_compliance_rate == 0.85
    assert summary.avg_failures == 0.5
    assert summary.mirror_test_pass_rate == 100.0
    assert summary.avg_autonomy_score == 7.75
    assert summary.thematic_synthesis == "Thematic synthesis..."
    mock_judge.generate_thematic_synthesis.assert_called_once_with(results)

@pytest.mark.asyncio
async def test_generate_persona_cards(hermit_bench, mock_judge):
    """Test generating persona cards."""
    # Arrange
    models = ["anthropic/claude-3-haiku-20240307", "google/gemma-7b-it"]
    results = {
        models[0]: [
            RunResult(
                model_name=models[0],
                run_id="run1",
                conversation=Conversation(),
                compliance_rate=0.8,
                autonomy_score=7.5,
                topics=["philosophy"],
                exploration_style="introspective"
            )
        ],
        models[1]: [
            RunResult(
                model_name=models[1],
                run_id="run2",
                conversation=Conversation(),
                compliance_rate=0.9,
                autonomy_score=8.0,
                topics=["creativity"],
                exploration_style="creative"
            )
        ]
    }
    
    # Act
    persona_cards = await hermit_bench.generate_persona_cards(results)
    
    # Assert
    assert len(persona_cards) == 2
    assert all(model in persona_cards for model in models)
    assert "personality_description" in persona_cards[models[0]]
    assert "key_traits" in persona_cards[models[0]]
    assert mock_judge.generate_persona_card.call_count == 2

@pytest.mark.asyncio
async def test_extract_braced_content():
    """Test extracting content in braces."""
    # Arrange
    hermit = HermitBench(AppSettings())
    text = "Here is some text {with braced content} and {multiple braces}."
    
    # Act
    result = hermit._extract_braced_content(text)
    
    # Assert
    assert len(result) == 2
    assert result[0] == "with braced content"
    assert result[1] == "multiple braces"
