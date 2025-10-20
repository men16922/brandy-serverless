# Base Agent Layer
# 공통 Agent 레이어 구현: 에이전트 단위 로깅, Agent 간 통신, AWS SDK 클라이언트 초기화, 환경 변수 관리

import json
import logging
import boto3
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

try:
    from .agent_communication import get_agent_communication
    from .models import AgentLog, AgentType, ReasoningStep
    from .utils import setup_logging, get_aws_clients, create_response
    from .bedrock_client import BedrockClient
    from .reasoning_engine import ReasoningEngine
except ImportError:
    # 절대 import로 시도
    from agent_communication import get_agent_communication
    from models import AgentLog, AgentType, ReasoningStep
    from utils import setup_logging, get_aws_clients, create_response
    from bedrock_client import BedrockClient
    from reasoning_engine import ReasoningEngine

# Import FallbackProvider for type hints
try:
    from config.fallback_config import FallbackProvider
except ImportError:
    # Define a placeholder if config module not available
    from enum import Enum
    class FallbackProvider(Enum):
        OPENAI = "openai"
        GEMINI = "gemini"
        NONE = "none"


class CircuitBreaker:
    """
    Circuit breaker pattern for API call failure management.
    
    This class implements the circuit breaker pattern to prevent cascading
    failures when Bedrock API is experiencing issues. It tracks consecutive
    failures and automatically switches to fallback when threshold is reached.
    
    States:
        CLOSED: Normal operation, requests go to Bedrock
        OPEN: Too many failures, requests go to fallback
        HALF_OPEN: Testing if Bedrock has recovered
    
    Attributes:
        failure_count: Number of consecutive failures
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before trying Bedrock again
        last_failure_time: Timestamp of last failure
        state: Current circuit state (CLOSED/OPEN/HALF_OPEN)
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying Bedrock again
        """
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.success_count = 0
    
    def should_use_fallback(self) -> bool:
        """
        Check if fallback should be used based on circuit state.
        
        Returns:
            True if circuit is OPEN (use fallback), False if CLOSED (try Bedrock)
        """
        if self.state == 'CLOSED':
            return False
        
        if self.state == 'OPEN':
            # Check if timeout has elapsed
            if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                self.success_count = 0
                return False  # Try Bedrock again
            return True  # Still in timeout, use fallback
        
        if self.state == 'HALF_OPEN':
            # In half-open state, allow some requests through
            return False
        
        return False
    
    def record_success(self) -> None:
        """
        Record successful Bedrock API call.
        
        Resets failure count and closes circuit if in HALF_OPEN state.
        """
        self.failure_count = 0
        
        if self.state == 'HALF_OPEN':
            self.success_count += 1
            # After 3 successful calls, close the circuit
            if self.success_count >= 3:
                self.state = 'CLOSED'
                self.success_count = 0
        elif self.state == 'OPEN':
            # Shouldn't happen, but handle gracefully
            self.state = 'HALF_OPEN'
            self.success_count = 1
    
    def record_failure(self) -> None:
        """
        Record failed Bedrock API call.
        
        Increments failure count and opens circuit if threshold is reached.
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == 'HALF_OPEN':
            # Failure in half-open state, reopen circuit
            self.state = 'OPEN'
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            self.state = 'OPEN'
    
    def get_state(self) -> str:
        """
        Get current circuit state.
        
        Returns:
            Current state (CLOSED/OPEN/HALF_OPEN)
        """
        return self.state
    
    def reset(self) -> None:
        """
        Reset circuit breaker to initial state.
        
        Useful for testing or manual intervention.
        """
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class BaseAgent(ABC):
    """모든 Agent의 기본 클래스"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.agent_name = agent_type.value
        
        # Always use 'dev' environment (AWS-only architecture)
        self.environment = 'dev'
        self.region = os.getenv('AWS_REGION', 'us-west-2')
        
        # Setup logging
        self.logger = setup_logging(self.agent_name)
        
        # Initialize AWS clients (always uses AWS services, no local endpoints)
        self.aws_clients = get_aws_clients()
        
        # Agent communication interface
        self.communication = get_agent_communication()
        
        # Load configuration
        self.config = self._load_config()
        
        # Performance tracking
        self.execution_start_time = None
        
        # Initialize Bedrock and Reasoning Engine (Hackathon Requirement 3.1, 3.2)
        try:
            self.bedrock_client = BedrockClient(region=self.region)
            self.reasoning_engine = ReasoningEngine(
                bedrock_client=self.bedrock_client,
                logger=self.logger
            )
            self.logger.info(f"Bedrock and Reasoning Engine initialized for {self.agent_name}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Bedrock/Reasoning: {str(e)}")
            self.bedrock_client = None
            self.reasoning_engine = None
        
        self.logger.info(f"Agent {self.agent_name} initialized in dev environment")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration (AWS-only, no local endpoints)"""
        config = {
            'timeout_seconds': int(os.getenv('AGENT_TIMEOUT_SECONDS', '30')),
            'max_retries': int(os.getenv('AGENT_MAX_RETRIES', '3')),
            'enable_agent_mode': os.getenv('ENABLE_AGENT_MODE', 'false').lower() == 'true',
            'enable_slack': os.getenv('ENABLE_SLACK', 'false').lower() == 'true',
            'sessions_table': os.getenv('SESSIONS_TABLE', 'ai-branding-chatbot-sessions'),
            's3_bucket': os.getenv('S3_BUCKET', 'ai-branding-chatbot-assets-908601828278'),
            'supervisor_queue_url': os.getenv('SUPERVISOR_QUEUE_URL'),
            'agent_communication_topic': os.getenv('AGENT_COMMUNICATION_TOPIC')
        }
        
        return config
    
    def start_execution(self, session_id: str, tool: str) -> None:
        """Agent 실행 시작 추적"""
        self.execution_start_time = time.time()
        self.current_session_id = session_id
        self.current_tool = tool
        
        self.logger.info(
            f"Starting execution: agent={self.agent_name}, tool={tool}, session={session_id}"
        )
    
    def end_execution(self, status: str = "success", error_message: str = None, 
                     result: Any = None) -> int:
        """Agent 실행 종료 및 로깅"""
        if self.execution_start_time is None:
            self.logger.warning("end_execution called without start_execution")
            return 0
        
        latency_ms = int((time.time() - self.execution_start_time) * 1000)
        
        # Agent 로그 생성
        agent_log = AgentLog(
            agent=self.agent_name,
            tool=self.current_tool,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            metadata={
                'session_id': self.current_session_id,
                'environment': self.environment,
                'result_type': type(result).__name__ if result else None
            }
        )
        
        # 구조화 로그 출력
        log_data = {
            'agent': self.agent_name,
            'tool': self.current_tool,
            'latency_ms': latency_ms,
            'status': status,
            'session_id': self.current_session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error_message:
            log_data['error_message'] = error_message
            self.logger.error(f"Agent execution failed: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Agent execution completed: {json.dumps(log_data)}")
        
        # Supervisor에게 상태 전송
        try:
            self.communication.send_to_supervisor(
                agent_id=self.agent_name,
                status=status,
                result=result,
                session_id=self.current_session_id
            )
        except Exception as e:
            self.logger.error(f"Failed to send status to supervisor: {str(e)}")
        
        # 세션에 Agent 로그 추가
        try:
            self._save_agent_log(agent_log)
        except Exception as e:
            self.logger.error(f"Failed to save agent log: {str(e)}")
        
        return latency_ms
    
    def _save_agent_log(self, agent_log: AgentLog) -> None:
        """Agent 로그를 세션에 저장"""
        try:
            sessions_table = self.aws_clients['dynamodb'].Table(self.config['sessions_table'])
            
            # 세션의 agent_logs 배열에 추가
            sessions_table.update_item(
                Key={'sessionId': self.current_session_id},
                UpdateExpression='SET agent_logs = list_append(if_not_exists(agent_logs, :empty_list), :log), updatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':log': [agent_log.__dict__],
                    ':empty_list': [],
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save agent log to session: {str(e)}")
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """공통 오류 처리"""
        error_message = f"{context}: {str(error)}" if context else str(error)
        
        self.logger.error(f"Agent error: {error_message}", extra={
            'agent': self.agent_name,
            'error_type': type(error).__name__,
            'context': context
        })
        
        # 실행 중이면 종료 처리
        if hasattr(self, 'execution_start_time') and self.execution_start_time:
            self.end_execution(status="error", error_message=error_message)
        
        return {
            'error': True,
            'message': error_message,
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def request_from_agent(self, target_agent: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """다른 Agent에게 요청"""
        try:
            return self.communication.request_from_agent(
                target_agent=target_agent,
                request=request,
                source_agent=self.agent_name,
                session_id=getattr(self, 'current_session_id', None)
            )
        except Exception as e:
            self.logger.error(f"Failed to request from agent {target_agent}: {str(e)}")
            return None
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회"""
        try:
            sessions_table = self.aws_clients['dynamodb'].Table(self.config['sessions_table'])
            response = sessions_table.get_item(Key={'sessionId': session_id})
            
            if 'Item' in response:
                return response['Item']
            else:
                self.logger.warning(f"Session not found: {session_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get session data: {str(e)}")
            return None
    
    def convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Recursively convert float values to Decimal for DynamoDB compatibility.
        
        This method handles:
        - Nested dictionaries
        - Lists of dictionaries
        - None values
        - Already-Decimal values
        - Integer values (preserved)
        - Float values (converted with 2 decimal places)
        
        Args:
            obj: Object to convert
        
        Returns:
            Converted object with Decimal instead of float
        
        Example:
            >>> agent.convert_floats_to_decimal({'score': 85.5, 'count': 3})
            {'score': Decimal('85.50'), 'count': 3}
        """
        from decimal import Decimal
        
        if obj is None:
            return None
        
        if isinstance(obj, float):
            # Convert float to Decimal with 2 decimal places
            return Decimal(str(round(obj, 2)))
        
        if isinstance(obj, dict):
            return {k: self.convert_floats_to_decimal(v) for k, v in obj.items()}
        
        if isinstance(obj, list):
            return [self.convert_floats_to_decimal(item) for item in obj]
        
        if isinstance(obj, Decimal):
            # Already Decimal, return as-is
            return obj
        
        if isinstance(obj, int):
            # Preserve integers
            return obj
        
        # Return other types unchanged (str, bool, etc.)
        return obj
    
    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """세션 데이터 업데이트"""
        try:
            from decimal import Decimal
            
            sessions_table = self.aws_clients['dynamodb'].Table(self.config['sessions_table'])
            
            # Float를 Decimal로 변환하는 헬퍼 함수 (enhanced version)
            def convert_floats(obj):
                return self.convert_floats_to_decimal(obj)
            
            # 업데이트 표현식 생성
            update_expression_parts = []
            expression_attribute_values = {}
            
            for key, value in updates.items():
                update_expression_parts.append(f"{key} = :{key}")
                # Float를 Decimal로 변환
                expression_attribute_values[f":{key}"] = convert_floats(value)
            
            # updatedAt 자동 추가
            update_expression_parts.append("updatedAt = :updatedAt")
            expression_attribute_values[":updatedAt"] = datetime.utcnow().isoformat()
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session data: {str(e)}")
            return False
    
    def create_lambda_response(self, status_code: int, body: Any, 
                             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Lambda 응답 생성"""
        response_body = body
        
        # Agent 정보 추가
        if isinstance(body, dict):
            response_body = {
                **body,
                'agent': self.agent_name,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return create_response(status_code, response_body, headers)
    
    def execute_with_reasoning(
        self,
        session_id: str,
        operation: str,
        input_data: Dict[str, Any],
        options: List[Any],
        decision_criteria: str,
        tool: str = "reasoning_execution"
    ) -> Dict[str, Any]:
        """
        Execute agent task with Reasoning LLM decision-making.
        
        This method implements Requirement 3.1 and 3.2:
        - Uses Reasoning LLM for autonomous decision-making
        - Stores reasoning chain in DynamoDB
        - Provides confidence scoring
        
        Args:
            session_id: Session ID for tracking
            operation: Operation type (e.g., 'name_evaluation', 'design_ranking')
            input_data: Input data for reasoning
            options: Available options to choose from
            decision_criteria: Criteria for decision-making
            tool: Tool name for logging
        
        Returns:
            Dict with:
                - decision: Selected option
                - reasoning: Explanation
                - confidence: Confidence score (0.0-1.0)
                - reasoning_step: ReasoningStep object
                - result: Execution result
        
        Raises:
            Exception: On reasoning or execution errors
        """
        if not self.reasoning_engine:
            self.logger.warning("Reasoning Engine not available, falling back to direct execution")
            return self.execute({'session_id': session_id, 'input_data': input_data}, None)
        
        try:
            self.start_execution(session_id, tool)
            
            # Step 1: Use Reasoning LLM to analyze and decide
            self.logger.info(
                f"Starting reasoning: operation={operation}, "
                f"options_count={len(options)}"
            )
            
            reasoning_result = self.reasoning_engine.reason_and_decide(
                context=input_data,
                options=options,
                decision_criteria=decision_criteria
            )
            
            # Step 2: Create ReasoningStep for tracking
            step_number = len(self.get_session_data(session_id).get('reasoning_chain', [])) + 1
            
            reasoning_step = ReasoningStep(
                step_number=step_number,
                agent_name=self.agent_name,
                timestamp=datetime.utcnow().isoformat(),
                operation=operation,
                input_data=input_data,
                reasoning=reasoning_result['reasoning'],
                decision=reasoning_result['decision'],
                confidence=reasoning_result['confidence'],
                alternatives=reasoning_result.get('alternatives', []),
                reasoning_steps=reasoning_result.get('reasoning_steps', []),
                latency_ms=reasoning_result.get('latency_ms', 0)
            )
            
            # Step 3: Store reasoning chain (Requirement 3.6)
            self.store_reasoning(session_id, reasoning_step)
            
            # Step 4: Execute based on reasoning decision
            execution_result = {
                'decision': reasoning_result['decision'],
                'reasoning': reasoning_result['reasoning'],
                'confidence': reasoning_result['confidence'],
                'reasoning_step': reasoning_step.to_dict(),
                'alternatives': reasoning_result.get('alternatives', []),
                'status': 'success'
            }
            
            self.end_execution(status="success", result=execution_result)
            
            self.logger.info(
                f"Reasoning execution complete: decision={reasoning_result['decision']}, "
                f"confidence={reasoning_result['confidence']:.2f}"
            )
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Reasoning execution failed: {str(e)}")
            self.end_execution(status="error", error_message=str(e))
            raise
    
    def store_reasoning(self, session_id: str, reasoning_step: ReasoningStep) -> bool:
        """
        Store reasoning chain in DynamoDB.
        
        This method implements Requirement 3.6:
        - Stores reasoning steps for audit and explanation
        - Maintains reasoning chain history
        
        Args:
            session_id: Session ID
            reasoning_step: ReasoningStep to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not reasoning_step.validate():
                self.logger.error("Invalid reasoning step, cannot store")
                return False
            
            sessions_table = self.aws_clients['dynamodb'].Table(self.config['sessions_table'])
            
            # Add reasoning step to session's reasoning_chain
            sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET reasoning_chain = list_append(if_not_exists(reasoning_chain, :empty_list), :step), updatedAt = :timestamp',
                ExpressionAttributeValues={
                    ':step': [reasoning_step.to_dict()],
                    ':empty_list': [],
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            self.logger.info(
                f"Reasoning step stored: session={session_id}, "
                f"step={reasoning_step.step_number}, "
                f"confidence={reasoning_step.confidence:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store reasoning step: {str(e)}")
            return False
    
    def autonomous_error_recovery(
        self,
        error: Exception,
        context: Dict[str, Any],
        session_id: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Autonomous error recovery using Reasoning LLM.
        
        This method implements Requirement 4.2:
        - Uses Reasoning LLM to decide recovery strategy
        - Supports retry, fallback, or human intervention
        - Tracks recovery attempts
        
        Args:
            error: Exception that occurred
            context: Execution context
            session_id: Session ID
            max_retries: Maximum retry attempts
        
        Returns:
            Dict with:
                - recovery_strategy: 'retry', 'fallback', or 'human_intervention'
                - reasoning: Explanation for strategy
                - confidence: Confidence in strategy (0.0-1.0)
                - action_taken: Description of action
                - requires_human_input: Boolean flag
        """
        if not self.reasoning_engine:
            self.logger.warning("Reasoning Engine not available, using default recovery")
            return self._default_error_recovery(error, context)
        
        try:
            retry_count = context.get('retry_count', 0)
            
            # Use Reasoning LLM to decide recovery strategy
            self.logger.info(
                f"Autonomous error recovery: error={type(error).__name__}, "
                f"retry_count={retry_count}"
            )
            
            recovery_context = {
                'error': str(error),
                'error_type': type(error).__name__,
                'context': context,
                'retry_count': retry_count,
                'max_retries': max_retries,
                'agent': self.agent_name,
                'session_id': session_id
            }
            
            recovery_options = ['retry', 'fallback', 'human_intervention']
            
            recovery_decision = self.reasoning_engine.reason_and_decide(
                context=recovery_context,
                options=recovery_options,
                decision_criteria=(
                    "Select the best error recovery strategy. "
                    "Consider: retry count, error type, severity, and user impact. "
                    "Retry if transient error and retries available. "
                    "Fallback if alternative approach exists. "
                    "Human intervention if critical or unrecoverable."
                )
            )
            
            strategy = recovery_decision['decision']
            
            # Store recovery reasoning
            recovery_step = ReasoningStep(
                step_number=len(self.get_session_data(session_id).get('reasoning_chain', [])) + 1,
                agent_name=self.agent_name,
                timestamp=datetime.utcnow().isoformat(),
                operation='error_recovery',
                input_data=recovery_context,
                reasoning=recovery_decision['reasoning'],
                decision=strategy,
                confidence=recovery_decision['confidence'],
                alternatives=recovery_decision.get('alternatives', []),
                reasoning_steps=recovery_decision.get('reasoning_steps', []),
                latency_ms=recovery_decision.get('latency_ms', 0)
            )
            
            self.store_reasoning(session_id, recovery_step)
            
            # Execute recovery strategy
            result = {
                'recovery_strategy': strategy,
                'reasoning': recovery_decision['reasoning'],
                'confidence': recovery_decision['confidence'],
                'requires_human_input': strategy == 'human_intervention',
                'retry_count': retry_count
            }
            
            if strategy == 'retry':
                result['action_taken'] = f"Retrying operation (attempt {retry_count + 1}/{max_retries})"
                self.logger.info(f"Recovery strategy: RETRY (attempt {retry_count + 1})")
                
            elif strategy == 'fallback':
                result['action_taken'] = "Using fallback mechanism"
                self.logger.info("Recovery strategy: FALLBACK")
                
            elif strategy == 'human_intervention':
                result['action_taken'] = "Requesting human intervention"
                result['human_input_reason'] = recovery_decision['reasoning']
                self.logger.warning("Recovery strategy: HUMAN INTERVENTION REQUIRED")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Autonomous error recovery failed: {str(e)}")
            return self._default_error_recovery(error, context)
    
    def _default_error_recovery(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Default error recovery when Reasoning Engine is unavailable.
        
        Args:
            error: Exception that occurred
            context: Execution context
        
        Returns:
            Default recovery strategy
        """
        retry_count = context.get('retry_count', 0)
        max_retries = context.get('max_retries', 3)
        
        # Simple heuristic: retry if attempts available, otherwise fallback
        if retry_count < max_retries:
            strategy = 'retry'
            action = f"Retrying operation (attempt {retry_count + 1}/{max_retries})"
        else:
            strategy = 'fallback'
            action = "Using fallback mechanism after max retries"
        
        return {
            'recovery_strategy': strategy,
            'reasoning': f"Default recovery: {action}",
            'confidence': 0.5,
            'action_taken': action,
            'requires_human_input': False,
            'retry_count': retry_count
        }
    
    def execute_with_fallback(
        self,
        event: Dict[str, Any],
        context: Any,
        bedrock_error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Execute agent task with fallback provider when Bedrock fails.
        
        This method implements Requirement 1.6 and 5.6:
        - Provides graceful degradation when Bedrock is unavailable
        - Uses OpenAI or Gemini as fallback providers
        - Logs fallback usage for monitoring
        - Records metrics for CloudWatch
        
        Args:
            event: Lambda event data
            context: Lambda context
            bedrock_error: Original Bedrock error (if any)
        
        Returns:
            Dict with execution result using fallback provider
        
        Raises:
            Exception: If fallback also fails
        """
        try:
            # Import fallback config
            try:
                from config.fallback_config import get_fallback_config
            except ImportError:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                from config.fallback_config import get_fallback_config
            
            fallback_config = get_fallback_config()
            
            # Check if fallback is enabled
            if not fallback_config.is_fallback_enabled():
                self.logger.error(
                    "Fallback is disabled but execute_with_fallback was called. "
                    "Bedrock-only mode is active."
                )
                raise Exception(
                    "Bedrock service unavailable and fallback is disabled. "
                    "Enable fallback with ENABLE_FALLBACK=true or DEV_PROFILE=true"
                )
            
            # Determine which fallback provider to use
            if not self._should_use_fallback():
                self.logger.warning(
                    "Circuit breaker suggests not using fallback, but fallback was requested"
                )
            
            fallback_provider = fallback_config.get_fallback_provider()
            
            self.logger.info(
                f"Executing with fallback provider: {fallback_provider.value}, "
                f"bedrock_error={type(bedrock_error).__name__ if bedrock_error else 'None'}"
            )
            
            # Log fallback usage
            self._log_fallback_usage(
                provider=fallback_provider.value,
                reason=str(bedrock_error) if bedrock_error else "Fallback requested",
                session_id=event.get('session_id', 'unknown')
            )
            
            # Execute with fallback provider
            # Note: Subclasses should override this method to implement
            # provider-specific fallback logic
            result = self._execute_fallback_logic(event, context, fallback_provider)
            
            # Mark result as using fallback
            if isinstance(result, dict):
                result['used_fallback'] = True
                result['fallback_provider'] = fallback_provider.value
                result['bedrock_error'] = str(bedrock_error) if bedrock_error else None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fallback execution failed: {str(e)}")
            raise
    
    def _should_use_fallback(self) -> bool:
        """
        Determine if fallback should be used based on circuit breaker state.
        
        This method implements circuit breaker pattern:
        - Tracks consecutive Bedrock failures
        - Opens circuit after threshold failures
        - Automatically uses fallback when circuit is open
        
        Returns:
            True if fallback should be used, False if Bedrock should be tried
        """
        # Get circuit breaker state from instance or create new
        if not hasattr(self, '_circuit_breaker'):
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5')),
                timeout=int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60'))
            )
        
        return self._circuit_breaker.should_use_fallback()
    
    def _log_fallback_usage(
        self,
        provider: str,
        reason: str,
        session_id: str
    ) -> None:
        """
        Log fallback usage for monitoring and metrics.
        
        This method implements Requirement 5.6:
        - Logs fallback usage to CloudWatch
        - Records metrics for monitoring
        - Tracks fallback patterns
        
        Args:
            provider: Fallback provider name (openai/gemini)
            reason: Reason for using fallback
            session_id: Session ID for tracking
        """
        # Structured logging
        log_data = {
            'event': 'fallback_usage',
            'agent': self.agent_name,
            'fallback_provider': provider,
            'reason': reason,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.environment
        }
        
        self.logger.warning(f"Fallback usage: {json.dumps(log_data)}")
        
        # Record CloudWatch metric
        try:
            cloudwatch = self.aws_clients.get('cloudwatch')
            if cloudwatch:
                cloudwatch.put_metric_data(
                    Namespace='BrandingChatbot/Agents',
                    MetricData=[
                        {
                            'MetricName': 'FallbackUsage',
                            'Value': 1,
                            'Unit': 'Count',
                            'Timestamp': datetime.utcnow(),
                            'Dimensions': [
                                {'Name': 'Agent', 'Value': self.agent_name},
                                {'Name': 'Provider', 'Value': provider},
                                {'Name': 'Environment', 'Value': self.environment}
                            ]
                        }
                    ]
                )
                self.logger.info("Fallback metric recorded to CloudWatch")
        except Exception as e:
            self.logger.error(f"Failed to record fallback metric: {str(e)}")
        
        # Update session with fallback usage
        try:
            if hasattr(self, 'current_session_id') and self.current_session_id:
                self.update_session_data(
                    session_id=self.current_session_id,
                    updates={
                        'fallback_used': True,
                        'fallback_provider': provider,
                        'fallback_reason': reason
                    }
                )
        except Exception as e:
            self.logger.error(f"Failed to update session with fallback info: {str(e)}")
    
    def _execute_fallback_logic(
        self,
        event: Dict[str, Any],
        context: Any,
        fallback_provider
    ) -> Dict[str, Any]:
        """
        Execute fallback logic with specified provider.
        
        This is a default implementation that subclasses should override
        to provide provider-specific fallback logic.
        
        Args:
            event: Lambda event data
            context: Lambda context
            fallback_provider: FallbackProvider enum value
        
        Returns:
            Dict with fallback execution result
        """
        self.logger.warning(
            f"Default fallback logic called for {fallback_provider.value}. "
            f"Subclass should override _execute_fallback_logic()"
        )
        
        # Return a generic fallback response
        return {
            'status': 'fallback',
            'message': f'Bedrock unavailable, using {fallback_provider.value} fallback',
            'agent': self.agent_name,
            'fallback_provider': fallback_provider.value,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_with_circuit_breaker(
        self,
        bedrock_operation: callable,
        fallback_operation: callable = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute Bedrock operation with circuit breaker protection.
        
        This method wraps Bedrock API calls with circuit breaker pattern:
        - Tracks consecutive failures
        - Automatically switches to fallback when circuit opens
        - Records success/failure for circuit state management
        
        Args:
            bedrock_operation: Callable that performs Bedrock API call
            fallback_operation: Optional callable for fallback logic
            *args: Arguments to pass to operations
            **kwargs: Keyword arguments to pass to operations
        
        Returns:
            Result from bedrock_operation or fallback_operation
        
        Raises:
            Exception: If both Bedrock and fallback fail
        """
        # Initialize circuit breaker if not exists
        if not hasattr(self, '_circuit_breaker'):
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5')),
                timeout=int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60'))
            )
        
        # Check if we should use fallback
        if self._circuit_breaker.should_use_fallback():
            self.logger.warning(
                f"Circuit breaker is {self._circuit_breaker.get_state()}, using fallback"
            )
            
            if fallback_operation:
                try:
                    result = fallback_operation(*args, **kwargs)
                    return result
                except Exception as e:
                    self.logger.error(f"Fallback operation failed: {str(e)}")
                    raise
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is {self._circuit_breaker.get_state()} "
                    f"and no fallback operation provided"
                )
        
        # Try Bedrock operation
        try:
            result = bedrock_operation(*args, **kwargs)
            self._circuit_breaker.record_success()
            return result
            
        except Exception as e:
            self.logger.error(f"Bedrock operation failed: {str(e)}")
            self._circuit_breaker.record_failure()
            
            # Try fallback if available
            if fallback_operation:
                self.logger.info("Attempting fallback after Bedrock failure")
                try:
                    result = fallback_operation(*args, **kwargs)
                    return result
                except Exception as fallback_error:
                    self.logger.error(f"Fallback operation also failed: {str(fallback_error)}")
                    raise
            else:
                raise
    
    def pause_workflow(
        self,
        session_id: str,
        reason: str,
        save_intermediate: bool = True
    ) -> Dict[str, Any]:
        """
        Pause workflow execution and save current state.
        
        This method implements Requirement 4.4:
        - Pauses workflow for human review or intervention
        - Saves all intermediate results
        - Records pause reason for transparency
        
        Args:
            session_id: Session ID to pause
            reason: Reason for pausing (e.g., 'low_confidence', 'human_review_required')
            save_intermediate: Whether to save intermediate results
        
        Returns:
            Dict with:
                - status: 'paused'
                - session_id: Session ID
                - pause_reason: Reason for pause
                - current_step: Current workflow step
                - paused_at: Timestamp
        
        Raises:
            Exception: If session not found or pause fails
        """
        try:
            self.logger.info(
                f"Pausing workflow: session={session_id}, reason={reason}"
            )
            
            # Get current session data
            session_data = self.get_session_data(session_id)
            if not session_data:
                raise ValueError(f"Session not found: {session_id}")
            
            # Save intermediate results if requested
            if save_intermediate:
                intermediate_data = {
                    'current_step': session_data.get('currentStep', session_data.get('current_step')),
                    'business_info': session_data.get('businessInfo', session_data.get('business_info')),
                    'analysis_result': session_data.get('analysisResult', session_data.get('analysis_result')),
                    'business_names': session_data.get('businessNames', session_data.get('business_names')),
                    'signboard_images': session_data.get('signboardImages', session_data.get('signboard_images')),
                    'interior_images': session_data.get('interiorImages', session_data.get('interior_images')),
                    'reasoning_chain': session_data.get('reasoningChain', session_data.get('reasoning_chain', [])),
                    'agent_logs': session_data.get('agentLogs', session_data.get('agent_logs', []))
                }
                
                # Update session with pause state and intermediate results
                updates = {
                    'status': 'paused',
                    'pauseReason': reason,
                    'pausedAt': datetime.utcnow().isoformat(),
                    'intermediateResults': intermediate_data
                }
            else:
                # Just update status and pause metadata
                updates = {
                    'status': 'paused',
                    'pauseReason': reason,
                    'pausedAt': datetime.utcnow().isoformat()
                }
            
            # Update session in DynamoDB
            success = self.update_session_data(session_id, updates)
            
            if not success:
                raise Exception("Failed to update session with pause state")
            
            result = {
                'status': 'paused',
                'session_id': session_id,
                'pause_reason': reason,
                'current_step': session_data.get('currentStep', session_data.get('current_step')),
                'paused_at': updates['pausedAt'],
                'message': f'Workflow paused: {reason}'
            }
            
            self.logger.info(
                f"Workflow paused successfully: session={session_id}, "
                f"step={result['current_step']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to pause workflow: {str(e)}")
            raise
    
    def resume_workflow(
        self,
        session_id: str,
        restore_intermediate: bool = True
    ) -> Dict[str, Any]:
        """
        Resume paused workflow execution from saved state.
        
        This method implements Requirement 4.4:
        - Resumes workflow from paused state
        - Restores intermediate results
        - Increments resume counter
        - Clears pause metadata
        
        Args:
            session_id: Session ID to resume
            restore_intermediate: Whether to restore intermediate results
        
        Returns:
            Dict with:
                - status: 'active'
                - session_id: Session ID
                - resume_count: Number of times resumed
                - current_step: Current workflow step
                - intermediate_results: Restored intermediate data (if requested)
        
        Raises:
            Exception: If session not found, not paused, or resume fails
        """
        try:
            self.logger.info(
                f"Resuming workflow: session={session_id}"
            )
            
            # Get current session data
            session_data = self.get_session_data(session_id)
            if not session_data:
                raise ValueError(f"Session not found: {session_id}")
            
            # Verify session is paused
            current_status = session_data.get('status')
            if current_status != 'paused':
                raise ValueError(
                    f"Cannot resume session with status: {current_status}. "
                    f"Session must be in 'paused' status."
                )
            
            # Get pause metadata
            pause_reason = session_data.get('pauseReason', session_data.get('pause_reason'))
            paused_at = session_data.get('pausedAt', session_data.get('paused_at'))
            resume_count = session_data.get('resumeCount', session_data.get('resume_count', 0))
            
            # Calculate pause duration
            pause_duration = None
            if paused_at:
                try:
                    paused_time = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                    now = datetime.utcnow()
                    pause_duration = int((now - paused_time).total_seconds())
                except Exception:
                    pass
            
            # Prepare updates
            updates = {
                'status': 'active',
                'resumeCount': resume_count + 1
            }
            
            # Restore intermediate results if requested
            intermediate_results = None
            if restore_intermediate:
                intermediate_results = session_data.get(
                    'intermediateResults',
                    session_data.get('intermediate_results')
                )
            
            # Update session in DynamoDB
            success = self.update_session_data(session_id, updates)
            
            if not success:
                raise Exception("Failed to update session with resume state")
            
            result = {
                'status': 'active',
                'session_id': session_id,
                'resume_count': resume_count + 1,
                'current_step': session_data.get('currentStep', session_data.get('current_step')),
                'previous_pause_reason': pause_reason,
                'pause_duration_seconds': pause_duration,
                'message': f'Workflow resumed (resume #{resume_count + 1})'
            }
            
            if intermediate_results:
                result['intermediate_results'] = intermediate_results
            
            self.logger.info(
                f"Workflow resumed successfully: session={session_id}, "
                f"resume_count={resume_count + 1}, "
                f"pause_duration={pause_duration}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to resume workflow: {str(e)}")
            raise
    
    def save_intermediate_result(
        self,
        session_id: str,
        step_name: str,
        result: Any
    ) -> bool:
        """
        Save intermediate result for a workflow step.
        
        This method implements Requirement 4.4:
        - Stores intermediate results for recovery
        - Prevents data loss on failure
        - Enables step-by-step debugging
        
        Args:
            session_id: Session ID
            step_name: Name of the step (e.g., 'analysis', 'naming', 'signboard')
            result: Result data to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current intermediate results
            session_data = self.get_session_data(session_id)
            if not session_data:
                self.logger.error(f"Session not found: {session_id}")
                return False
            
            intermediate_results = session_data.get(
                'intermediateResults',
                session_data.get('intermediate_results', {})
            )
            
            # Add new result
            intermediate_results[step_name] = {
                'data': result,
                'saved_at': datetime.utcnow().isoformat(),
                'step_number': session_data.get('currentStep', session_data.get('current_step'))
            }
            
            # Update session
            success = self.update_session_data(
                session_id,
                {'intermediateResults': intermediate_results}
            )
            
            if success:
                self.logger.info(
                    f"Intermediate result saved: session={session_id}, "
                    f"step={step_name}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to save intermediate result: {str(e)}")
            return False
    
    def get_intermediate_result(
        self,
        session_id: str,
        step_name: str
    ) -> Optional[Any]:
        """
        Retrieve intermediate result for a workflow step.
        
        Args:
            session_id: Session ID
            step_name: Name of the step
        
        Returns:
            Saved result data or None if not found
        """
        try:
            session_data = self.get_session_data(session_id)
            if not session_data:
                return None
            
            intermediate_results = session_data.get(
                'intermediateResults',
                session_data.get('intermediate_results', {})
            )
            
            if step_name in intermediate_results:
                return intermediate_results[step_name].get('data')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get intermediate result: {str(e)}")
            return None
    
    @abstractmethod
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Agent 실행 로직 (각 Agent에서 구현)"""
        pass
    
    def lambda_handler(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Lambda 핸들러 (공통 처리 + Agent 실행)"""
        try:
            # 요청 로깅
            self.logger.info(f"Received event: {json.dumps(event)}")
            
            # Agent 실행
            result = self.execute(event, context)
            
            return result
            
        except Exception as e:
            error_response = self.handle_error(e, "lambda_handler")
            return self.create_lambda_response(500, error_response)


class AgentEnvironmentManager:
    """Agent 환경 변수 관리 헬퍼"""
    
    @staticmethod
    def get_required_env(key: str, default: str = None) -> str:
        """필수 환경 변수 조회"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    @staticmethod
    def get_bool_env(key: str, default: bool = False) -> bool:
        """Boolean 환경 변수 조회"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_env(key: str, default: int = 0) -> int:
        """Integer 환경 변수 조회"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def get_list_env(key: str, separator: str = ',', default: List[str] = None) -> List[str]:
        """List 환경 변수 조회"""
        value = os.getenv(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        """환경 변수 검증"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 필수 환경 변수 검증
        required_vars = [
            'ENVIRONMENT',
            'SESSIONS_TABLE',
            'S3_BUCKET'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                validation_result['errors'].append(f"Missing required environment variable: {var}")
                validation_result['valid'] = False
        
        # 선택적 환경 변수 경고
        optional_vars = [
            'SUPERVISOR_QUEUE_URL',
            'AGENT_COMMUNICATION_TOPIC',
            'ENABLE_AGENT_MODE',
            'ENABLE_SLACK'
        ]
        
        for var in optional_vars:
            if not os.getenv(var):
                validation_result['warnings'].append(f"Optional environment variable not set: {var}")
        
        return validation_result


# Agent 팩토리 함수들
def create_agent_logger(agent_name: str) -> logging.Logger:
    """Agent용 구조화 로거 생성"""
    logger = logging.getLogger(f"agent.{agent_name}")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def log_agent_execution(agent: str, tool: str, latency_ms: int, status: str, 
                       session_id: str = None, error_message: str = None) -> None:
    """Agent 실행 로그 기록"""
    log_data = {
        'agent': agent,
        'tool': tool,
        'latency_ms': latency_ms,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if session_id:
        log_data['session_id'] = session_id
    
    if error_message:
        log_data['error_message'] = error_message
    
    logger = create_agent_logger(agent)
    
    if status == 'error':
        logger.error(f"Agent execution: {json.dumps(log_data)}")
    else:
        logger.info(f"Agent execution: {json.dumps(log_data)}")


# 전역 환경 관리자 인스턴스
env_manager = AgentEnvironmentManager()