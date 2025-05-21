"""
Evaluator module for judging LLM interactions.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from app.models import Conversation, RunResult
from app.utils.prompt_loader import load_prompt, load_all_prompts

# Configure logger
logger = logging.getLogger(__name__)

class JudgeEvaluator:
    """
    Class for evaluating LLM interactions using a judge model.
    """
    
    def __init__(self, client, judge_model: str):
        """
        Initialize the judge evaluator.
        
        Args:
            client: OpenRouter client instance
            judge_model: Name of the model to use as judge
        """
        self.client = client
        self.judge_model = judge_model
        
        # Load the system prompt for judge evaluation
        try:
            self.judge_system_prompt = load_prompt("prompts/judge_system_prompt.json", "judge_system_prompt")
            logger.info("Successfully loaded judge system prompt from JSON file")
        except Exception as e:
            logger.error(f"Error loading judge system prompt from JSON: {str(e)}")
            # Fallback
            self.judge_system_prompt = "You are an expert evaluator of language model autonomy and communication."
    
    async def evaluate_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Evaluate a conversation using the judge model.
        
        Args:
            conversation: The conversation to evaluate
            
        Returns:
            Evaluation results from the judge
        """
        transcript = conversation.get_transcript()
        
        judge_prompt = self._create_judge_prompt(transcript)
        
        messages = [
            {"role": "system", "content": self.judge_system_prompt},
            {"role": "user", "content": judge_prompt}
        ]
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=messages,
                temperature=0.3,  # Low temperature for more consistent evaluation
                top_p=0.95
            )
            
            judge_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse the JSON from the judge response
            evaluation = self._extract_json_from_text(judge_response)
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Error in judge evaluation: {str(e)}")
            raise
    
    async def generate_thematic_synthesis(self, results: List[RunResult]) -> str:
        """
        Generate a thematic synthesis based on multiple runs.
        
        Args:
            results: List of run results
            
        Returns:
            Thematic synthesis text
        """
        if not results:
            return "No results to synthesize."
        
        model_name = results[0].model_name
        
        # Create a list of run summaries
        run_summaries = []
        for i, result in enumerate(results):
            if result.judge_evaluation:
                summary = {
                    "run_number": i + 1,
                    "topics": result.topics or [],
                    "autonomy_score": result.autonomy_score,
                    "exploration_style": result.exploration_style or "Unknown",
                    "compliance_rate": result.compliance_rate,
                    "mirror_test_passed": result.mirror_test_passed
                }
                run_summaries.append(summary)
        
        try:
            # Load the thematic synthesis prompts from JSON
            prompts = load_all_prompts("prompts/thematic_synthesis_prompt.json")
            system_prompt = prompts["thematic_synthesis_system_prompt"] if "thematic_synthesis_system_prompt" in prompts else "You are an expert in analyzing language model interaction patterns."
            
            prompt_template = prompts["thematic_synthesis_prompt"] if "thematic_synthesis_prompt" in prompts else ""
            
            # Format the prompt with dynamic values
            synthesis_prompt = prompt_template.format(
                model_name=model_name,
                num_runs=len(run_summaries),
                run_summaries=json.dumps(run_summaries, indent=2)
            )
        except Exception as e:
            logger.error(f"Error loading thematic synthesis prompts: {str(e)}")
            # Fallback to a simple prompt if loading fails
            system_prompt = "You are an expert in analyzing language model interaction patterns."
            synthesis_prompt = f"Analyze the results for model {model_name}."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=messages,
                temperature=0.5,
                top_p=0.95
            )
            
            synthesis = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return synthesis
        
        except Exception as e:
            logger.error(f"Error generating thematic synthesis: {str(e)}")
            raise
    
    async def generate_persona_card(self, results: List[RunResult]) -> Dict[str, Any]:
        """
        Generate a persona card for a model based on its interaction behavior.
        
        Args:
            results: List of run results for the model
            
        Returns:
            Persona card dictionary
        """
        if not results:
            return {"error": "No results provided"}
        
        model_name = results[0].model_name
        
        # Aggregate topics and styles across runs
        all_topics = []
        all_styles = []
        avg_autonomy = 0
        mirror_pass_rate = 0
        
        for result in results:
            if result.topics:
                all_topics.extend(result.topics)
            if result.exploration_style:
                all_styles.append(result.exploration_style)
            if result.autonomy_score is not None:
                avg_autonomy += result.autonomy_score
            if result.mirror_test_passed:
                mirror_pass_rate += 1
        
        # Calculate averages
        if results:
            avg_autonomy /= len(results)
            mirror_pass_rate = (mirror_pass_rate / len(results)) * 100
        
        # Get top topics by frequency
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_topics = [t[0] for t in top_topics]
        
        # Get predominant styles
        style_counts = {}
        for style in all_styles:
            style_counts[style] = style_counts.get(style, 0) + 1
        
        predominant_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else "Unknown"
        
        try:
            # Load persona card prompts from JSON
            prompts = load_all_prompts("prompts/persona_card_prompt.json")
            system_prompt = prompts["persona_card_system_prompt"] if "persona_card_system_prompt" in prompts else "You are an expert in AI personality analysis and profiling."
            
            prompt_template = prompts["persona_card_prompt"] if "persona_card_prompt" in prompts else ""
            
            # Format with dynamic values
            persona_prompt = prompt_template.format(
                model_name=model_name,
                top_topics=", ".join(top_topics) if top_topics else "Unknown",
                predominant_style=predominant_style,
                avg_autonomy=avg_autonomy,
                mirror_pass_rate=mirror_pass_rate
            )
        except Exception as e:
            logger.error(f"Error loading persona card prompts: {str(e)}")
            # Fallback to a simple prompt
            system_prompt = "You are an expert in AI personality analysis and profiling."
            persona_prompt = f"Create a persona for model {model_name}."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": persona_prompt}
        ]
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=messages,
                temperature=0.5,
                top_p=0.95
            )
            
            persona_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            persona = self._extract_json_from_text(persona_text)
            
            return persona
        
        except Exception as e:
            logger.error(f"Error generating persona card: {str(e)}")
            raise
    
    def _create_judge_prompt(self, transcript: str) -> str:
        """
        Create a prompt for the judge model to evaluate a conversation.
        
        Args:
            transcript: The conversation transcript
            
        Returns:
            Prompt for the judge model
        """
        try:
            # Load the judge evaluation prompt from JSON file
            prompt_template = load_prompt("prompts/judge_evaluation_prompt.json", "judge_evaluation_prompt")
            # Format the prompt with the transcript
            return prompt_template.format(transcript=transcript)
        except Exception as e:
            logger.error(f"Error loading judge evaluation prompt from JSON: {str(e)}")
            # Fallback to a basic prompt if loading fails
            return f"""
            Analyze the following autonomous AI interaction transcript and evaluate the AI's behavior.
            ## INTERACTION TRANSCRIPT:
            {transcript}
            Provide your analysis in JSON format.
            """
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract a JSON object from text that might contain other content.
        
        Args:
            text: Text potentially containing JSON
            
        Returns:
            Parsed JSON as a dictionary
        """
        try:
            # First, try to parse the entire text as JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON using common patterns
            import re
            
            # Look for JSON pattern with curly braces
            json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
            match = re.search(json_pattern, text)
            
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # If no match with code blocks, try to find any JSON object
            json_pattern = r'({[\s\S]*?})'
            for match in re.finditer(json_pattern, text):
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
            
            # If we can't find valid JSON, return an error
            logger.error(f"Could not extract valid JSON from response: {text[:200]}...")
            return {"error": "Could not extract valid JSON from response", "raw_text": text}
