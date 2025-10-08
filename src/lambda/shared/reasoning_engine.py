"""
Reasoning Engine for AI Branding Chatbot
Provides Chain-of-Thought reasoning and autonomous decision-making using Claude 4.0 Sonnet
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .bedrock_client import BedrockClient, BedrockException


class ReasoningEngine:
    """
    Bedrock Claude-based Reasoning Engine for autonomous decision-making.
    
    Features:
    - Chain-of-Thought reasoning
    - Multi-step planning
    - Confidence scoring (0.0-1.0)
    - Explanation generation
    - Business name evaluation
    - Design ranking
    - Insight synthesis
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize Reasoning Engine.
        
        Args:
            bedrock_client: BedrockClient instance (creates new if None)
            logger: Logger instance (creates new if None)
        """
        self.bedrock_client = bedrock_client or BedrockClient()
        self.logger = logger or self._create_logger()
        self.model_id = self.bedrock_client.claude_model_id
        
        self.logger.info(f"ReasoningEngine initialized with model: {self.model_id}")
    
    def _create_logger(self) -> logging.Logger:
        """Create structured logger for Reasoning Engine"""
        logger = logging.getLogger('reasoning_engine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def reason_and_decide(
        self,
        context: Dict[str, Any],
        options: List[Any],
        decision_criteria: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Perform Chain-of-Thought reasoning to make a decision.
        
        Args:
            context: Context information for decision-making
            options: List of available options to choose from
            decision_criteria: Criteria for making the decision
            temperature: Sampling temperature (lower = more deterministic)
        
        Returns:
            Dict with:
                - decision: Selected option
                - reasoning: Step-by-step explanation
                - confidence: Confidence score (0.0-1.0)
                - alternatives: Alternative options with scores
                - reasoning_steps: List of reasoning steps
        
        Raises:
            BedrockException: On API errors
        """
        try:
            # Build reasoning prompt
            system_prompt = """You are an expert decision-making AI assistant. 
Your task is to analyze the given context and options, then make a well-reasoned decision.

Use Chain-of-Thought reasoning:
1. Analyze the context thoroughly
2. Evaluate each option against the criteria
3. Consider pros and cons
4. Make a final decision with confidence score

Respond in JSON format with:
{
    "reasoning_steps": ["step 1", "step 2", ...],
    "option_evaluations": [
        {"option": "...", "score": 0-100, "pros": [...], "cons": [...]}
    ],
    "decision": "selected option",
    "confidence": 0.0-1.0,
    "explanation": "final reasoning"
}"""
            
            prompt = f"""Context:
{json.dumps(context, indent=2)}

Available Options:
{json.dumps(options, indent=2)}

Decision Criteria:
{decision_criteria}

Please analyze the context, evaluate each option, and make a decision following the Chain-of-Thought reasoning process."""
            
            self.logger.info(
                f"Reasoning: criteria='{decision_criteria}', "
                f"options_count={len(options)}"
            )
            
            # Invoke Claude for reasoning
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=temperature
            )
            
            # Parse reasoning response
            reasoning_text = response['text']
            
            # Try to extract JSON from response
            reasoning_data = self._extract_json_from_response(reasoning_text)
            if reasoning_data is None:
                # Fallback: create structured response from text
                reasoning_data = self._parse_reasoning_text(reasoning_text, options)
            
            # Build result
            result = {
                'decision': reasoning_data.get('decision', options[0] if options else None),
                'reasoning': reasoning_data.get('explanation', reasoning_text),
                'confidence': float(reasoning_data.get('confidence', 0.7)),
                'alternatives': reasoning_data.get('option_evaluations', []),
                'reasoning_steps': reasoning_data.get('reasoning_steps', []),
                'latency_ms': response['latency_ms'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"Reasoning complete: decision='{result['decision']}', "
                f"confidence={result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Reasoning failed: {str(e)}")
            raise BedrockException(f"Reasoning engine error: {str(e)}")
    
    def evaluate_business_name(
        self,
        name: str,
        business_info: Dict[str, Any],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Evaluate a business name using reasoning LLM.
        
        Args:
            name: Business name to evaluate
            business_info: Business context (industry, region, size)
            temperature: Sampling temperature
        
        Returns:
            Dict with:
                - name: Business name
                - overall_score: Overall score (0-100)
                - pronunciation_score: Pronunciation score (0-100)
                - memorability_score: Memorability score (0-100)
                - brand_fit_score: Brand fit score (0-100)
                - reasoning: Detailed explanation
                - confidence: Confidence in evaluation (0.0-1.0)
                - suggestions: Improvement suggestions
        
        Raises:
            BedrockException: On API errors
        """
        try:
            system_prompt = """You are an expert brand naming consultant.
Evaluate business names based on:
1. Pronunciation (easy to say, no tongue twisters)
2. Memorability (catchy, unique, easy to remember)
3. Brand Fit (matches industry, region, target audience)
4. Search/Domain availability considerations

Respond in JSON format with:
{
    "pronunciation_score": 0-100,
    "memorability_score": 0-100,
    "brand_fit_score": 0-100,
    "overall_score": 0-100,
    "reasoning": "detailed explanation",
    "confidence": 0.0-1.0,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "suggestions": ["suggestion 1", "suggestion 2"]
}"""
            
            prompt = f"""Business Name: {name}

Business Context:
- Industry: {business_info.get('industry', 'unknown')}
- Region: {business_info.get('region', 'unknown')}
- Size: {business_info.get('size', 'unknown')}

Please evaluate this business name comprehensively."""
            
            self.logger.info(f"Evaluating business name: '{name}'")
            
            # Invoke Claude for evaluation
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=temperature
            )
            
            # Parse evaluation response
            evaluation_text = response['text']
            
            # Try to extract JSON from response
            evaluation_data = self._extract_json_from_response(evaluation_text)
            if evaluation_data is None:
                # Fallback: create default scores
                evaluation_data = self._create_default_evaluation(name, evaluation_text)
            
            # Build result
            result = {
                'name': name,
                'overall_score': float(evaluation_data.get('overall_score', 70)),
                'pronunciation_score': float(evaluation_data.get('pronunciation_score', 70)),
                'memorability_score': float(evaluation_data.get('memorability_score', 70)),
                'brand_fit_score': float(evaluation_data.get('brand_fit_score', 70)),
                'reasoning': evaluation_data.get('reasoning', evaluation_text),
                'confidence': float(evaluation_data.get('confidence', 0.75)),
                'strengths': evaluation_data.get('strengths', []),
                'weaknesses': evaluation_data.get('weaknesses', []),
                'suggestions': evaluation_data.get('suggestions', []),
                'latency_ms': response['latency_ms'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"Name evaluation complete: '{name}' scored {result['overall_score']:.1f}/100"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Name evaluation failed: {str(e)}")
            raise BedrockException(f"Name evaluation error: {str(e)}")
    
    def rank_designs(
        self,
        designs: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        temperature: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Rank design options using reasoning LLM.
        
        Args:
            designs: List of design options to rank
            criteria: Ranking criteria (brand_identity, target_audience, etc.)
            temperature: Sampling temperature
        
        Returns:
            List of designs sorted by rank with:
                - rank: Rank position (1, 2, 3, ...)
                - design: Original design data
                - score: Overall score (0-100)
                - reasoning: Explanation for ranking
                - confidence: Confidence in ranking (0.0-1.0)
        
        Raises:
            BedrockException: On API errors
        """
        try:
            system_prompt = """You are an expert design critic and brand consultant.
Rank design options based on the given criteria.

Consider:
1. Visual appeal and aesthetics
2. Brand identity alignment
3. Target audience fit
4. Memorability and impact
5. Professional quality

Respond in JSON format with:
{
    "rankings": [
        {
            "rank": 1,
            "design_index": 0,
            "score": 0-100,
            "reasoning": "explanation",
            "confidence": 0.0-1.0
        }
    ],
    "overall_reasoning": "comparative analysis"
}"""
            
            # Simplify designs for prompt (remove large data like images)
            simplified_designs = []
            for i, design in enumerate(designs):
                simplified = {
                    'index': i,
                    'style': design.get('style', 'unknown'),
                    'provider': design.get('provider', 'unknown'),
                    'prompt': design.get('prompt', '')[:200]  # Truncate long prompts
                }
                simplified_designs.append(simplified)
            
            prompt = f"""Design Options:
{json.dumps(simplified_designs, indent=2)}

Ranking Criteria:
{json.dumps(criteria, indent=2)}

Please rank these designs from best to worst, providing detailed reasoning for each ranking."""
            
            self.logger.info(f"Ranking {len(designs)} designs")
            
            # Invoke Claude for ranking
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1536,
                temperature=temperature
            )
            
            # Parse ranking response
            ranking_text = response['text']
            
            # Try to extract JSON from response
            ranking_data = self._extract_json_from_response(ranking_text)
            if ranking_data is None:
                # Fallback: create default ranking
                ranking_data = self._create_default_ranking(len(designs))
            
            # Build ranked results
            rankings = ranking_data.get('rankings', [])
            ranked_designs = []
            
            for ranking in rankings:
                design_index = ranking.get('design_index', 0)
                if 0 <= design_index < len(designs):
                    ranked_designs.append({
                        'rank': ranking.get('rank', len(ranked_designs) + 1),
                        'design': designs[design_index],
                        'score': float(ranking.get('score', 70)),
                        'reasoning': ranking.get('reasoning', ''),
                        'confidence': float(ranking.get('confidence', 0.75))
                    })
            
            # If some designs weren't ranked, add them at the end
            ranked_indices = {r.get('design_index', -1) for r in rankings}
            for i, design in enumerate(designs):
                if i not in ranked_indices:
                    ranked_designs.append({
                        'rank': len(ranked_designs) + 1,
                        'design': design,
                        'score': 50.0,
                        'reasoning': 'Not explicitly ranked',
                        'confidence': 0.5
                    })
            
            self.logger.info(f"Design ranking complete: {len(ranked_designs)} designs ranked")
            
            return ranked_designs
            
        except Exception as e:
            self.logger.error(f"Design ranking failed: {str(e)}")
            raise BedrockException(f"Design ranking error: {str(e)}")
    
    def synthesize_insights(
        self,
        agent_outputs: Dict[str, Any],
        temperature: float = 0.5
    ) -> str:
        """
        Synthesize insights from multiple agent outputs.
        
        Args:
            agent_outputs: Dictionary of agent outputs to synthesize
            temperature: Sampling temperature (higher for more creative synthesis)
        
        Returns:
            Synthesized insights as a comprehensive narrative string
        
        Raises:
            BedrockException: On API errors
        """
        try:
            system_prompt = """You are an expert business consultant synthesizing insights.
Create a comprehensive, cohesive narrative that:
1. Integrates findings from multiple analyses
2. Identifies key themes and patterns
3. Provides actionable recommendations
4. Maintains a professional, insightful tone

Focus on:
- Business viability and market fit
- Brand identity and positioning
- Design and aesthetic considerations
- Practical implementation steps"""
            
            prompt = f"""Agent Outputs to Synthesize:

{json.dumps(agent_outputs, indent=2)}

Please create a comprehensive synthesis of these insights, weaving them into a cohesive narrative that provides clear value to the business owner."""
            
            self.logger.info(f"Synthesizing insights from {len(agent_outputs)} agents")
            
            # Invoke Claude for synthesis
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=temperature
            )
            
            synthesis = response['text']
            
            self.logger.info(
                f"Insight synthesis complete: {len(synthesis)} characters, "
                f"latency={response['latency_ms']}ms"
            )
            
            return synthesis
            
        except Exception as e:
            self.logger.error(f"Insight synthesis failed: {str(e)}")
            raise BedrockException(f"Insight synthesis error: {str(e)}")
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude response (may be wrapped in markdown).
        
        Args:
            text: Response text from Claude
        
        Returns:
            Parsed JSON dict or None if extraction fails
        """
        try:
            # Find JSON in response (may be wrapped in markdown)
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _parse_reasoning_text(self, text: str, options: List[Any]) -> Dict[str, Any]:
        """
        Parse reasoning text when JSON extraction fails.
        
        Args:
            text: Reasoning text from Claude
            options: Original options list
        
        Returns:
            Structured reasoning data
        """
        # Create fallback structured response
        return {
            'decision': options[0] if options else None,
            'explanation': text,
            'confidence': 0.7,
            'reasoning_steps': [text],
            'option_evaluations': [
                {'option': opt, 'score': 70, 'pros': [], 'cons': []}
                for opt in options
            ]
        }
    
    def _create_default_evaluation(self, name: str, text: str) -> Dict[str, Any]:
        """
        Create default evaluation when JSON extraction fails.
        
        Args:
            name: Business name
            text: Evaluation text from Claude
        
        Returns:
            Default evaluation data
        """
        return {
            'pronunciation_score': 70,
            'memorability_score': 70,
            'brand_fit_score': 70,
            'overall_score': 70,
            'reasoning': text,
            'confidence': 0.7,
            'strengths': ['Evaluated by AI'],
            'weaknesses': [],
            'suggestions': []
        }
    
    def _create_default_ranking(self, num_designs: int) -> Dict[str, Any]:
        """
        Create default ranking when JSON extraction fails.
        
        Args:
            num_designs: Number of designs to rank
        
        Returns:
            Default ranking data
        """
        return {
            'rankings': [
                {
                    'rank': i + 1,
                    'design_index': i,
                    'score': 70 - (i * 5),  # Decreasing scores
                    'reasoning': f'Design {i + 1}',
                    'confidence': 0.7
                }
                for i in range(num_designs)
            ],
            'overall_reasoning': 'Default ranking applied'
        }


# Convenience function for creating Reasoning Engine
def create_reasoning_engine(
    bedrock_client: Optional[BedrockClient] = None,
    logger: Optional[logging.Logger] = None
) -> ReasoningEngine:
    """
    Create and return a configured Reasoning Engine.
    
    Args:
        bedrock_client: BedrockClient instance (creates new if None)
        logger: Logger instance (creates new if None)
    
    Returns:
        ReasoningEngine instance
    """
    return ReasoningEngine(bedrock_client=bedrock_client, logger=logger)
