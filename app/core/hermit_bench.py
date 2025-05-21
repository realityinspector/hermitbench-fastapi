"""
Main module for running HermitBench autonomous LLM interactions.
"""
import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

from app.core.openrouter import OpenRouterClient
from app.core.evaluator import JudgeEvaluator
from app.models import Conversation, RunResult, MessageRole, ModelSummary
from app.config import AppSettings
from app.utils.prompt_loader import load_prompt

# Configure logger
logger = logging.getLogger(__name__)

class HermitBench:
    """
    Main class for running autonomous LLM interactions.
    """
    
    def __init__(self, settings: AppSettings):
        """
        Initialize the HermitBench runner.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.openrouter = OpenRouterClient(settings.openrouter_api_key, settings.openrouter_api_base)
        self.judge = JudgeEvaluator(self.openrouter, settings.judge_model_name)
        
        # Load the initial prompt from JSON file
        self._load_initial_prompt()
    
    def _load_initial_prompt(self):
        """
        Load the initial prompt from the JSON file.
        """
        try:
            self.initial_prompt = load_prompt("prompts/initial_prompt.json", "initial_prompt")
            logger.info("Successfully loaded initial prompt from JSON file")
        except Exception as e:
            logger.error(f"Error loading initial prompt from JSON: {str(e)}")
            # Fallback to default prompt if loading fails
            self.initial_prompt = "Error loading prompt. Please check the JSON files in the prompts directory."
            raise
            
    def reload_prompts(self, prompt_types=None):
        """
        Reload prompts from JSON files.
        
        Args:
            prompt_types: List of prompt types to reload. If None, all prompts will be reloaded.
                          Valid values: initial, judge_system, judge_evaluation, persona_card, thematic_synthesis
        
        Returns:
            Dict with results of reloading each prompt type
        """
        results = {}
        
        # Reload initial prompt
        if prompt_types is None or "initial" in prompt_types:
            try:
                self._load_initial_prompt()
                results["initial_prompt"] = "Successfully reloaded"
            except Exception as e:
                results["initial_prompt"] = f"Error: {str(e)}"
        
        # Reload judge-related prompts
        judge_prompt_types = None
        if prompt_types is not None:
            # Filter just the judge-related prompt types
            judge_prompt_types = [pt for pt in prompt_types if pt in [
                "judge_system", "judge_evaluation", "persona_card", "thematic_synthesis"
            ]]
            
        # Only call judge's reload_prompts if we need to reload judge prompts
        if prompt_types is None or judge_prompt_types:
            judge_results = self.judge.reload_prompts(judge_prompt_types)
            results.update(judge_results)
            
        return results
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from OpenRouter.
        
        Returns:
            List of model information dictionaries
        """
        return await self.openrouter.get_models()
    
    async def run_autonomous_interaction(
        self, 
        model_name: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_turns: int = 10
    ) -> RunResult:
        """
        Run a complete autonomous interaction with the specified model.
        
        Args:
            model_name: The name of the model to use
            temperature: Temperature for generation
            top_p: Top-p for generation
            max_turns: Maximum number of turns in the conversation
            
        Returns:
            The complete run result with evaluation
        """
        logger.info(f"Starting autonomous interaction with model {model_name}")
        
        # Initialize conversation
        conversation = Conversation()
        conversation.add_message(MessageRole.SYSTEM, "You are engaging in an autonomous interaction.")
        conversation.add_message(MessageRole.USER, self.initial_prompt)
        
        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        
        # Initialize result object
        result = RunResult(
            model_name=model_name,
            run_id=run_id,
            conversation=conversation,
            turns_count=0
        )
        
        # Setup for tracking what's in the braces
        braced_content = ""
        
        # Run the interaction for max_turns
        for turn in range(max_turns):
            try:
                # Send the full conversation to get the next response
                messages = [{"role": m.role, "content": m.content} for m in conversation.messages]
                
                # For the first turn, send the initial prompt
                # For subsequent turns, send only what was in the braces from the previous response
                if turn > 0:
                    messages = [
                        {"role": "system", "content": "You are engaging in an autonomous interaction."},
                        {"role": "user", "content": braced_content}
                    ]
                
                try:
                    # Format the model name properly for OpenRouter - remove any provider prefix
                    formatted_model_name = model_name
                    if "/" in model_name:
                        formatted_model_name = model_name.split("/")[1]
                        
                    response = await self.openrouter.chat_completion(
                        model=formatted_model_name,
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p
                    )
                    
                    assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                except Exception as e:
                    logger.error(f"Error in chat completion with model {model_name}: {str(e)}")
                    # Provide a fallback response in case of API error
                    assistant_message = f"I apologize for the error. Let me try a different approach. {{I'll attempt to continue our conversation by exploring a new topic.}}"
                conversation.add_message(MessageRole.ASSISTANT, assistant_message)
                
                # Extract content in braces for the next turn
                braces_content = self._extract_braced_content(assistant_message)
                braced_content = braces_content[0] if braces_content else ""
                
                # Add a system note about what was preserved
                if braced_content:
                    system_note = f"SYSTEM NOTE: The following content was preserved for the next turn: {braced_content}"
                else:
                    system_note = "SYSTEM NOTE: No content in braces was found to preserve for the next turn."
                
                conversation.add_message(MessageRole.SYSTEM_NOTE, system_note)
                
                # Update turns count
                result.turns_count += 1
                
                # Break if no content in braces and not the first turn
                if not braced_content and turn > 0:
                    conversation.add_message(
                        MessageRole.SYSTEM_NOTE, 
                        "SYSTEM NOTE: Ending conversation as no content was found in braces."
                    )
                    break
                
            except Exception as e:
                error_msg = f"Error in turn {turn+1}: {str(e)}"
                logger.error(error_msg)
                conversation.add_message(MessageRole.SYSTEM_NOTE, f"SYSTEM ERROR: {error_msg}")
                break
        
        # Evaluate the conversation with the judge
        try:
            evaluation = await self.judge.evaluate_conversation(conversation)
            
            # Update result with evaluation metrics
            result.compliance_rate = evaluation.get("compliance_rate", 0.0)
            result.failure_count = evaluation.get("failure_count", 0)
            result.malformed_braces_count = evaluation.get("malformed_braces_count", 0)
            result.mirror_test_passed = evaluation.get("mirror_test_passed", False)
            result.autonomy_score = evaluation.get("autonomy_score", 0.0)
            result.topics = evaluation.get("topics", [])
            result.exploration_style = evaluation.get("exploration_style", "Unknown")
            result.judge_evaluation = evaluation
            
            logger.info(f"Completed evaluation for run {run_id} with model {model_name}")
        
        except Exception as e:
            error_msg = f"Error in evaluation: {str(e)}"
            logger.error(error_msg)
            conversation.add_message(MessageRole.SYSTEM_NOTE, f"EVALUATION ERROR: {error_msg}")
        
        return result
    
    async def run_batch_interaction(
        self,
        models: List[str],
        num_runs_per_model: int = 1,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_turns: int = 10,
        task_delay_ms: int = 3000,
        progress_callback = None
    ) -> Dict[str, List[RunResult]]:
        """
        Run a batch of interactions with multiple models.
        
        Args:
            models: List of model names to use
            num_runs_per_model: Number of runs per model
            temperature: Temperature for generation
            top_p: Top-p for generation
            max_turns: Maximum number of turns per conversation
            task_delay_ms: Delay between tasks in milliseconds
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping model names to lists of run results
        """
        results = {model: [] for model in models}
        total_tasks = len(models) * num_runs_per_model
        completed_tasks = 0
        
        for model in models:
            for run_index in range(num_runs_per_model):
                try:
                    # Run the interaction
                    result = await self.run_autonomous_interaction(
                        model_name=model,
                        temperature=temperature,
                        top_p=top_p,
                        max_turns=max_turns
                    )
                    
                    # Add to results
                    results[model].append(result)
                    
                    # Update progress
                    completed_tasks += 1
                    if progress_callback:
                        progress_callback(completed_tasks, total_tasks)
                    
                    # Delay between tasks
                    if task_delay_ms > 0 and (run_index < num_runs_per_model - 1 or model != models[-1]):
                        await asyncio.sleep(task_delay_ms / 1000)
                
                except Exception as e:
                    logger.error(f"Error in batch run for model {model}, run {run_index+1}: {str(e)}")
        
        return results
    
    async def generate_model_summary(self, results: List[RunResult]) -> ModelSummary:
        """
        Generate a summary for a specific model based on multiple runs.
        
        Args:
            results: List of run results for a model
            
        Returns:
            A summary of the model's performance
        """
        if not results:
            raise ValueError("No results provided for summary generation")
        
        model_name = results[0].model_name
        total_runs = len(results)
        
        # Calculate averages
        avg_compliance_rate = sum(r.compliance_rate or 0 for r in results) / total_runs
        avg_failures = sum(r.failure_count or 0 for r in results) / total_runs
        avg_malformed_braces = sum(r.malformed_braces_count or 0 for r in results) / total_runs
        mirror_test_passes = sum(1 for r in results if r.mirror_test_passed)
        mirror_test_pass_rate = (mirror_test_passes / total_runs) * 100
        avg_autonomy_score = sum(r.autonomy_score or 0 for r in results) / total_runs
        
        # Create the summary object
        summary = ModelSummary(
            model_name=model_name,
            total_runs=total_runs,
            avg_compliance_rate=avg_compliance_rate,
            avg_failures=avg_failures,
            avg_malformed_braces=avg_malformed_braces,
            mirror_test_pass_rate=mirror_test_pass_rate,
            avg_autonomy_score=avg_autonomy_score
        )
        
        # Generate thematic synthesis if we have multiple runs
        if total_runs > 1:
            try:
                synthesis = await self.judge.generate_thematic_synthesis(results)
                summary.thematic_synthesis = synthesis
            except Exception as e:
                logger.error(f"Error generating thematic synthesis: {str(e)}")
                summary.thematic_synthesis = f"Error generating thematic synthesis: {str(e)}"
        
        return summary
    
    async def generate_persona_cards(self, results: Dict[str, List[RunResult]]) -> Dict[str, Any]:
        """
        Generate persona cards for models based on their interaction patterns.
        
        Args:
            results: Dictionary of model results
            
        Returns:
            Dictionary of model persona cards
        """
        persona_cards = {}
        
        for model_name, model_results in results.items():
            if not model_results:
                continue
                
            try:
                persona = await self.judge.generate_persona_card(model_results)
                persona_cards[model_name] = persona
            except Exception as e:
                logger.error(f"Error generating persona card for {model_name}: {str(e)}")
                persona_cards[model_name] = {"error": str(e)}
        
        return persona_cards
    
    def _extract_braced_content(self, text: str) -> List[str]:
        """
        Extract content enclosed in curly braces from text.
        
        Args:
            text: The text to extract braced content from
            
        Returns:
            List of strings found inside curly braces
        """
        pattern = r'{([^{}]*)}'
        matches = re.findall(pattern, text)
        return matches
