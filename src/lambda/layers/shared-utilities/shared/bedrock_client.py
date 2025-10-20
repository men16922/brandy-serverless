"""
Amazon Bedrock Integration Client
Provides unified interface for Bedrock services: Claude, SDXL, Knowledge Base
"""

import json
import time
import logging
import os
import random
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


class BedrockException(Exception):
    """Base exception for Bedrock client errors"""
    pass


class ThrottlingException(BedrockException):
    """Bedrock API throttling exception"""
    pass


class ValidationException(BedrockException):
    """Bedrock API validation exception"""
    pass


class ServiceUnavailableException(BedrockException):
    """Bedrock service unavailable exception"""
    pass


class BedrockClient:
    """
    Amazon Bedrock API client with retry logic and structured logging.
    
    Supports:
    - Claude 4.0 Sonnet (reasoning, text generation)
    - SDXL (image generation)
    - Knowledge Base (vector search)
    """
    
    def __init__(self, region: str = None, logger: logging.Logger = None):
        """
        Initialize Bedrock client.
        
        Args:
            region: AWS region (default: from env or us-west-2)
            logger: Logger instance (default: creates new logger)
        """
        self.region = region or os.getenv('BEDROCK_REGION', 'us-west-2')
        self.logger = logger or self._create_logger()
        
        # Initialize Bedrock clients
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            self.logger.info(f"Bedrock client initialized in region: {self.region}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock clients: {str(e)}")
            raise BedrockException(f"Bedrock client initialization failed: {str(e)}")
        
        # Model IDs from environment or defaults
        # Using inference profile for Claude Sonnet 4
        self.claude_model_id = os.getenv(
            'CLAUDE_MODEL_ID',
            'us.anthropic.claude-sonnet-4-20250514-v1:0'
        )
        self.sdxl_model_id = os.getenv(
            'SDXL_MODEL_ID',
            'stability.stable-diffusion-xl-v1'
        )
        
        # Configuration
        self.max_retries = int(os.getenv('BEDROCK_MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('BEDROCK_TIMEOUT', '30'))
        self.base_delay = float(os.getenv('BEDROCK_BASE_DELAY', '1.0'))
        self.max_delay = float(os.getenv('BEDROCK_MAX_DELAY', '30.0'))
        self.rate_limit_delay = float(os.getenv('BEDROCK_RATE_LIMIT_DELAY', '2.0'))
        
        self.logger.info(
            f"Bedrock models configured: Claude={self.claude_model_id}, "
            f"SDXL={self.sdxl_model_id}"
        )
        self.logger.info(
            f"Throttle protection: max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}s, max_delay={self.max_delay}s, "
            f"rate_limit_delay={self.rate_limit_delay}s"
        )
    
    def _create_logger(self) -> logging.Logger:
        """Create structured logger for Bedrock client"""
        logger = logging.getLogger('bedrock_client')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def invoke_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Invoke Claude 4.0 Sonnet for reasoning and text generation.
        
        Args:
            prompt: User prompt/question
            system_prompt: System instructions (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            stop_sequences: Stop sequences for generation
        
        Returns:
            Dict with 'text', 'stop_reason', 'usage', 'latency_ms'
        
        Raises:
            BedrockException: On API errors
        """
        start_time = time.time()
        
        try:
            # Build request body for Claude
            messages = [{"role": "user", "content": prompt}]
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            if system_prompt:
                request_body["system"] = system_prompt
            
            if stop_sequences:
                request_body["stop_sequences"] = stop_sequences
            
            # Log API call
            self.logger.info(
                f"Invoking Claude: model={self.claude_model_id}, "
                f"max_tokens={max_tokens}, temperature={temperature}"
            )
            
            # Invoke with retry
            response = self.invoke_with_retry(
                lambda: self.bedrock_runtime.invoke_model(
                    modelId=self.claude_model_id,
                    body=json.dumps(request_body),
                    contentType='application/json',
                    accept='application/json'
                )
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract text from response
            text = response_body.get('content', [{}])[0].get('text', '')
            
            result = {
                'text': text,
                'stop_reason': response_body.get('stop_reason'),
                'usage': response_body.get('usage', {}),
                'latency_ms': latency_ms,
                'model_id': self.claude_model_id
            }
            
            # Structured logging
            self._log_api_call(
                model_id=self.claude_model_id,
                operation='invoke_claude',
                latency_ms=latency_ms,
                status='success',
                tokens_used=response_body.get('usage', {}).get('total_tokens', 0)
            )
            
            return result
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self._log_api_call(
                model_id=self.claude_model_id,
                operation='invoke_claude',
                latency_ms=latency_ms,
                status='error',
                error_message=str(e)
            )
            raise self._handle_bedrock_error(e, 'invoke_claude')
    
    def invoke_sdxl(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        cfg_scale: float = 7.0,
        steps: int = 30,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Invoke Stable Diffusion XL for image generation.
        
        Args:
            prompt: Image generation prompt
            negative_prompt: Negative prompt (what to avoid)
            width: Image width (must be divisible by 64)
            height: Image height (must be divisible by 64)
            cfg_scale: Classifier-free guidance scale
            steps: Number of diffusion steps
            seed: Random seed for reproducibility
        
        Returns:
            Dict with 'image_base64', 'seed', 'latency_ms'
        
        Raises:
            BedrockException: On API errors
        """
        start_time = time.time()
        
        try:
            # Validate dimensions
            if width % 64 != 0 or height % 64 != 0:
                raise ValidationException(
                    f"Width and height must be divisible by 64. Got: {width}x{height}"
                )
            
            # Build request body for SDXL
            request_body = {
                "text_prompts": [{"text": prompt, "weight": 1.0}],
                "cfg_scale": cfg_scale,
                "steps": steps,
                "width": width,
                "height": height
            }
            
            if negative_prompt:
                request_body["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
            
            if seed is not None:
                request_body["seed"] = seed
            
            # Log API call
            self.logger.info(
                f"Invoking SDXL: model={self.sdxl_model_id}, "
                f"size={width}x{height}, steps={steps}"
            )
            
            # Invoke with retry
            response = self.invoke_with_retry(
                lambda: self.bedrock_runtime.invoke_model(
                    modelId=self.sdxl_model_id,
                    body=json.dumps(request_body),
                    contentType='application/json',
                    accept='application/json'
                )
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract image data
            artifacts = response_body.get('artifacts', [])
            if not artifacts:
                raise BedrockException("No image artifacts in SDXL response")
            
            result = {
                'image_base64': artifacts[0].get('base64'),
                'seed': response_body.get('seed'),
                'finish_reason': artifacts[0].get('finishReason'),
                'latency_ms': latency_ms,
                'model_id': self.sdxl_model_id
            }
            
            # Structured logging
            self._log_api_call(
                model_id=self.sdxl_model_id,
                operation='invoke_sdxl',
                latency_ms=latency_ms,
                status='success'
            )
            
            return result
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self._log_api_call(
                model_id=self.sdxl_model_id,
                operation='invoke_sdxl',
                latency_ms=latency_ms,
                status='error',
                error_message=str(e)
            )
            raise self._handle_bedrock_error(e, 'invoke_sdxl')
    
    def batch_evaluate_names(
        self,
        names: List[str],
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple business names in a single Bedrock API call.
        
        This method batches name evaluation to reduce API calls from N to 1,
        significantly improving performance and reducing throttling risk.
        
        Args:
            names: List of business names to evaluate (typically 3)
            business_info: Business context (industry, region, size)
            analysis_result: Analysis results for context
        
        Returns:
            List of evaluation results with scores (as floats, convert to Decimal later)
        
        Example:
            [
                {
                    "name": "CafeBreeze",
                    "pronunciation_score": 85.0,
                    "memorability_score": 90.0,
                    "relevance_score": 80.0,
                    "search_score": 75.0,
                    "overall_score": 82.5,
                    "reasoning": "Easy to pronounce and memorable..."
                },
                ...
            ]
        
        Raises:
            BedrockException: On API errors
        """
        start_time = time.time()
        
        try:
            # Build batched evaluation prompt
            names_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(names)])
            
            industry = business_info.get('industry', 'general')
            region = business_info.get('region', 'unknown')
            size = business_info.get('size', 'medium')
            description = business_info.get('description', '')
            
            # Get market trends from analysis if available
            market_context = ""
            if analysis_result:
                trends = analysis_result.get('market_trends', [])
                if trends:
                    market_context = "\n\nMarket trends:\n" + "\n".join([f"- {t}" for t in trends[:3]])
            
            prompt = f"""You are a business naming expert. Evaluate the following {len(names)} business names for a {industry} business in {region} (size: {size}).

Names to evaluate:
{names_list}

Business context:
- Industry: {industry}
- Region: {region}
- Size: {size}
{f"- Description: {description}" if description else ""}
{market_context}

For each name, provide:
1. pronunciation_score (0-100): How easy is it to pronounce?
2. memorability_score (0-100): How memorable is it?
3. relevance_score (0-100): How relevant to the business?
4. search_score (0-100): How SEO-friendly?
5. overall_score (0-100): Weighted average (pronunciation 20%, memorability 30%, relevance 30%, search 20%)
6. reasoning: Brief explanation (2-3 sentences)

Return ONLY a valid JSON array with this exact format (no markdown, no code blocks):
[
  {{
    "name": "Name1",
    "pronunciation_score": 85.0,
    "memorability_score": 90.0,
    "relevance_score": 80.0,
    "search_score": 75.0,
    "overall_score": 82.5,
    "reasoning": "Brief explanation"
  }},
  ...
]"""

            self.logger.info(f"Batch evaluating {len(names)} names")
            
            # Invoke Claude with throttle protection
            response = self.invoke_claude(
                prompt=prompt,
                max_tokens=2048,
                temperature=0.3  # Lower temperature for more consistent scoring
            )
            
            # Parse JSON response
            response_text = response['text'].strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Extract JSON from code block
                lines = response_text.split('\n')
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not line.startswith('```')):
                        json_lines.append(line)
                response_text = '\n'.join(json_lines).strip()
            
            try:
                evaluations = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {response_text[:200]}")
                # Return default scores if parsing fails
                evaluations = [
                    {
                        "name": name,
                        "pronunciation_score": 75.0,
                        "memorability_score": 75.0,
                        "relevance_score": 75.0,
                        "search_score": 75.0,
                        "overall_score": 75.0,
                        "reasoning": "Default scores due to parsing error"
                    }
                    for name in names
                ]
            
            # Validate and ensure all names are present
            evaluated_names = {e['name'] for e in evaluations if 'name' in e}
            for name in names:
                if name not in evaluated_names:
                    self.logger.warning(f"Name '{name}' missing from evaluation, adding default scores")
                    evaluations.append({
                        "name": name,
                        "pronunciation_score": 70.0,
                        "memorability_score": 70.0,
                        "relevance_score": 70.0,
                        "search_score": 70.0,
                        "overall_score": 70.0,
                        "reasoning": "Default scores - not evaluated"
                    })
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                f"Batch evaluation complete: {len(evaluations)} names evaluated in {latency_ms}ms"
            )
            
            return evaluations
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Batch evaluation failed after {latency_ms}ms: {str(e)}")
            
            # Return default scores for all names on error
            return [
                {
                    "name": name,
                    "pronunciation_score": 70.0,
                    "memorability_score": 70.0,
                    "relevance_score": 70.0,
                    "search_score": 70.0,
                    "overall_score": 70.0,
                    "reasoning": f"Default scores due to error: {str(e)[:100]}"
                }
                for name in names
            ]
    
    def query_knowledge_base(
        self,
        query: str,
        kb_id: Optional[str] = None,
        max_results: int = 5,
        min_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Query Bedrock Knowledge Base for vector search.
        
        Args:
            query: Search query
            kb_id: Knowledge Base ID (default: from env)
            max_results: Maximum number of results
            min_score: Minimum relevance score (0-1)
        
        Returns:
            Dict with 'results', 'latency_ms'
        
        Raises:
            BedrockException: On API errors
        """
        start_time = time.time()
        
        try:
            kb_id = kb_id or os.getenv('BEDROCK_KB_ID')
            if not kb_id:
                raise ValidationException(
                    "Knowledge Base ID not provided and BEDROCK_KB_ID not set"
                )
            
            # Log API call
            self.logger.info(
                f"Querying Knowledge Base: kb_id={kb_id}, "
                f"max_results={max_results}"
            )
            
            # Invoke with retry
            response = self.invoke_with_retry(
                lambda: self.bedrock_agent_runtime.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': max_results
                        }
                    }
                )
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parse and filter results
            retrieval_results = response.get('retrievalResults', [])
            filtered_results = [
                {
                    'content': result.get('content', {}).get('text', ''),
                    'score': result.get('score', 0.0),
                    'location': result.get('location', {}),
                    'metadata': result.get('metadata', {})
                }
                for result in retrieval_results
                if result.get('score', 0.0) >= min_score
            ]
            
            result = {
                'results': filtered_results,
                'total_results': len(filtered_results),
                'latency_ms': latency_ms,
                'kb_id': kb_id
            }
            
            # Structured logging
            self._log_api_call(
                model_id=f"kb:{kb_id}",
                operation='query_knowledge_base',
                latency_ms=latency_ms,
                status='success',
                results_count=len(filtered_results)
            )
            
            return result
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self._log_api_call(
                model_id=f"kb:{kb_id or 'unknown'}",
                operation='query_knowledge_base',
                latency_ms=latency_ms,
                status='error',
                error_message=str(e)
            )
            raise self._handle_bedrock_error(e, 'query_knowledge_base')
    
    def calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.
        
        Formula: min(max_delay, base_delay * 2^attempt + random(0, 1))
        
        Args:
            attempt: Retry attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        
        Example:
            - Attempt 0: 1.0 * 2^0 + jitter = 1.0-2.0s
            - Attempt 1: 1.0 * 2^1 + jitter = 2.0-3.0s
            - Attempt 2: 1.0 * 2^2 + jitter = 4.0-5.0s
            - Attempt 3: 1.0 * 2^3 + jitter = 8.0-9.0s
        """
        delay = min(self.max_delay, self.base_delay * (2 ** attempt))
        jitter = random.uniform(0, 1)
        return delay + jitter
    
    def add_rate_limit_delay(self, delay_seconds: Optional[float] = None) -> None:
        """
        Add delay between API calls to prevent throttling.
        
        Args:
            delay_seconds: Delay duration (default: from config)
        """
        delay = delay_seconds or self.rate_limit_delay
        if delay > 0:
            self.logger.info(f"Rate limiting: sleeping for {delay}s")
            time.sleep(delay)
    
    def invoke_with_throttle_protection(
        self,
        model_id: str,
        prompt: str,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock with exponential backoff and jitter for throttle protection.
        
        This is a high-level wrapper that handles throttling gracefully with:
        - Exponential backoff with jitter
        - Structured logging of throttling events
        - Configurable retry parameters
        
        Args:
            model_id: Bedrock model ID
            prompt: Input prompt
            max_retries: Maximum retry attempts (default: from config)
            base_delay: Initial delay in seconds (default: from config)
            max_delay: Maximum delay in seconds (default: from config)
        
        Returns:
            API response dict
        
        Raises:
            ThrottlingException: After max retries exceeded
        """
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_delay
        max_delay = max_delay or self.max_delay
        
        start_time = time.time()
        total_retry_time = 0.0
        throttle_count = 0
        
        for attempt in range(max_retries + 1):
            try:
                # Use appropriate invoke method based on model
                if 'claude' in model_id.lower() or 'anthropic' in model_id.lower():
                    result = self.invoke_claude(prompt)
                else:
                    # For other models, use generic invoke
                    result = self._invoke_generic(model_id, prompt)
                
                # Log success with throttling metrics
                if throttle_count > 0:
                    self.logger.info(
                        f"Succeeded after {throttle_count} throttling events. "
                        f"Total retry time: {total_retry_time:.2f}s"
                    )
                
                return result
                
            except (ThrottlingException, ClientError) as e:
                # Check if it's a throttling error
                is_throttling = False
                if isinstance(e, ThrottlingException):
                    is_throttling = True
                elif isinstance(e, ClientError):
                    error_code = e.response.get('Error', {}).get('Code', '')
                    is_throttling = (error_code == 'ThrottlingException')
                
                if is_throttling and attempt < max_retries:
                    throttle_count += 1
                    
                    # Calculate backoff delay with jitter
                    delay = min(max_delay, base_delay * (2 ** attempt))
                    jitter = random.uniform(0, 1)
                    wait_time = delay + jitter
                    total_retry_time += wait_time
                    
                    # Structured logging
                    self.logger.warning(
                        f"Throttled by Bedrock API. "
                        f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})",
                        extra={
                            'throttle_event': {
                                'model_id': model_id,
                                'attempt': attempt + 1,
                                'max_retries': max_retries,
                                'wait_time': wait_time,
                                'total_retry_time': total_retry_time,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                        }
                    )
                    
                    time.sleep(wait_time)
                    continue
                else:
                    # Max retries exceeded or non-throttling error
                    total_time = time.time() - start_time
                    self.logger.error(
                        f"Max retries exceeded or non-retryable error. "
                        f"Total time: {total_time:.2f}s, Throttle events: {throttle_count}",
                        extra={
                            'throttle_summary': {
                                'model_id': model_id,
                                'total_attempts': attempt + 1,
                                'throttle_count': throttle_count,
                                'total_retry_time': total_retry_time,
                                'total_time': total_time
                            }
                        }
                    )
                    raise
            
            except Exception as e:
                # Non-retryable error
                self.logger.error(f"Non-retryable error: {str(e)}")
                raise
        
        # Should not reach here
        raise ThrottlingException(
            f"Max retries exceeded for {model_id} after {max_retries} attempts"
        )
    
    def _invoke_generic(self, model_id: str, prompt: str) -> Dict[str, Any]:
        """
        Generic invoke method for non-Claude models.
        
        Args:
            model_id: Bedrock model ID
            prompt: Input prompt
        
        Returns:
            API response dict
        """
        request_body = {"prompt": prompt}
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body
    
    def invoke_with_retry(
        self,
        func: Callable,
        max_retries: Optional[int] = None
    ) -> Any:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            max_retries: Maximum retry attempts (default: from config)
        
        Returns:
            Function result
        
        Raises:
            BedrockException: After max retries exceeded
        """
        max_retries = max_retries or self.max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                last_exception = e
                
                # Check if retryable
                if error_code == 'ThrottlingException':
                    if attempt < max_retries:
                        # Use new backoff calculation with jitter
                        wait_time = self.calculate_backoff_delay(attempt)
                        self.logger.warning(
                            f"Throttled by Bedrock API. "
                            f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ThrottlingException(
                            f"Max retries exceeded due to throttling: {str(e)}"
                        )
                
                elif error_code == 'ServiceUnavailableException':
                    if attempt < max_retries:
                        wait_time = self.calculate_backoff_delay(attempt)
                        self.logger.warning(
                            f"Bedrock service unavailable. "
                            f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ServiceUnavailableException(
                            f"Bedrock service unavailable after {max_retries} retries: {str(e)}"
                        )
                
                else:
                    # Non-retryable error
                    raise
            
            except Exception as e:
                # Non-ClientError exceptions are not retried
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def _handle_bedrock_error(self, error: Exception, operation: str) -> BedrockException:
        """
        Convert boto3 errors to Bedrock-specific exceptions.
        
        Args:
            error: Original exception
            operation: Operation name for context
        
        Returns:
            BedrockException subclass
        """
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', '')
            error_message = error.response.get('Error', {}).get('Message', str(error))
            
            if error_code == 'ThrottlingException':
                return ThrottlingException(f"{operation}: {error_message}")
            elif error_code == 'ValidationException':
                return ValidationException(f"{operation}: {error_message}")
            elif error_code == 'ServiceUnavailableException':
                return ServiceUnavailableException(f"{operation}: {error_message}")
            else:
                return BedrockException(f"{operation}: {error_code} - {error_message}")
        
        elif isinstance(error, BedrockException):
            return error
        
        else:
            return BedrockException(f"{operation}: {str(error)}")
    
    def _log_api_call(
        self,
        model_id: str,
        operation: str,
        latency_ms: int,
        status: str,
        error_message: Optional[str] = None,
        tokens_used: Optional[int] = None,
        results_count: Optional[int] = None
    ) -> None:
        """
        Log Bedrock API call with structured data.
        
        Args:
            model_id: Bedrock model ID
            operation: Operation name
            latency_ms: Latency in milliseconds
            status: 'success' or 'error'
            error_message: Error message if status is 'error'
            tokens_used: Number of tokens used (for Claude)
            results_count: Number of results (for KB queries)
        """
        log_data = {
            'bedrock_api_call': operation,
            'model_id': model_id,
            'latency_ms': latency_ms,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region
        }
        
        if error_message:
            log_data['error_message'] = error_message
        
        if tokens_used is not None:
            log_data['tokens_used'] = tokens_used
        
        if results_count is not None:
            log_data['results_count'] = results_count
        
        if status == 'error':
            self.logger.error(f"Bedrock API call failed: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Bedrock API call succeeded: {json.dumps(log_data)}")


# Convenience function for creating Bedrock client
def create_bedrock_client(
    region: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> BedrockClient:
    """
    Create and return a configured Bedrock client.
    
    Args:
        region: AWS region (default: from env or us-west-2)
        logger: Logger instance (default: creates new logger)
    
    Returns:
        BedrockClient instance
    """
    return BedrockClient(region=region, logger=logger)
