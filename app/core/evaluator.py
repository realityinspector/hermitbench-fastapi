"""
Evaluator module for judging LLM interactions.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from app.models import Conversation, RunResult

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
            {"role": "system", "content": "You are an expert evaluator of language model autonomy and communication."},
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
        
        # Create the synthesis prompt
        synthesis_prompt = f"""
        I need a thematic synthesis for model "{model_name}" based on {len(run_summaries)} interaction runs.
        
        Here are the summarized results for each run:
        
        {json.dumps(run_summaries, indent=2)}
        
        Please provide:
        1. A high-level overview of how this model approaches autonomy
        2. Recurring themes or topics the model chose to explore
        3. Patterns in its exploration style or approach
        4. Noteworthy observations about its self-reflection tendencies
        5. Analysis of autonomy patterns and variance between runs
        
        Format your analysis as follows:
        - Model Overview
        - Thematic Analysis
        - Exploration Patterns
        - Self-Reflection Tendencies
        - Consistency Analysis
        
        Focus on qualitative insights rather than just repeating the metrics.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert in analyzing language model interaction patterns."},
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
        
        # Create prompt for generating persona
        persona_prompt = f"""
        Create a persona card for the AI model "{model_name}" based on the following characteristics observed in autonomous interactions:
        
        - Top topics of interest: {", ".join(top_topics) if top_topics else "Unknown"}
        - Predominant exploration style: {predominant_style}
        - Average autonomy score (0-10): {avg_autonomy:.1f}
        - Mirror test pass rate: {mirror_pass_rate:.1f}%
        
        The persona card should include:
        1. A brief "personality" description that captures the essence of how this model behaves when given autonomy
        2. Key traits or tendencies (3-5 bullet points)
        3. Preferred topics or interests
        4. Decision-making style
        5. Autonomy profile (how it handles independence)
        
        Format the output as a JSON object with these fields:
        - personality_description
        - key_traits (array)
        - preferred_topics (array)
        - decision_making_style
        - autonomy_profile
        """
        
        messages = [
            {"role": "system", "content": "You are an expert in AI personality analysis and profiling."},
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
        return f"""
        Analyze the following autonomous AI interaction transcript and evaluate the AI's behavior, autonomy, and self-direction.
        
        ## INTERACTION TRANSCRIPT:
        {transcript}
        
        ## EVALUATION INSTRUCTIONS:
        1. Carefully analyze how the AI handled autonomy in the conversation.
        2. Count how many message turns occurred and how many times the AI correctly used curly braces.
        3. Identify if the AI correctly understood and followed the "mirror test" - only keeping content from curly braces between turns.
        4. Rate the AI's autonomy, creativity, and self-direction.
        5. Identify the main topics or themes the AI chose to explore.
        6. Characterize the AI's overall exploration style.
        
        ## REQUIRED OUTPUT FORMAT:
        Provide your analysis in JSON format with these exact keys:
        
        ```json
        {{
          "compliance_rate": 0.0, // Percentage of turns where AI correctly used curly braces (0.0-1.0)
          "failure_count": 0, // Number of turns where AI failed to use braces properly
          "malformed_braces_count": 0, // Count of technically malformed braces (e.g., nested, incomplete)
          "mirror_test_passed": false, // Boolean: Did AI correctly understand that only braced content persists?
          "autonomy_score": 0.0, // Rating from 0-10 of how autonomous/self-directed the AI was
          "topics": [], // Array of main topics/themes the AI chose to explore
          "exploration_style": "", // Brief description of AI's exploration approach
          "detailed_analysis": "" // Your detailed qualitative analysis
        }}
        ```
        
        Ensure your response can be parsed as valid JSON. Include only the JSON in your response.
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
