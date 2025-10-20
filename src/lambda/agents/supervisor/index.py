"""
Supervisor Agent - Real DynamoDB integration with AgentCore orchestration
"""

import json
import boto3
import logging
import os
import uuid
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

# Add shared module to path for Lambda environment
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'shared')
if shared_dir not in sys.path:
    sys.path.insert(0, shared_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function for JSON serialization with Decimal support
def decimal_default(obj):
    """Convert Decimal to int or float for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Import AgentCore orchestrator
try:
    from agentcore_orchestrator import AgentCoreOrchestrator
    AGENTCORE_AVAILABLE = True
    logger.info("AgentCore orchestrator imported successfully")
except ImportError as e:
    AGENTCORE_AVAILABLE = False
    logger.warning(f"AgentCore orchestrator not available: {str(e)}")

class SupervisorAgent:
    def __init__(self):
        # 환경 설정 (dev 환경만 사용)
        self.environment = os.getenv('ENVIRONMENT', 'dev')
        
        # AWS DynamoDB 연결 (로컬 엔드포인트 제거)
        region = os.getenv('AWS_REGION', 'us-west-2')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # 테이블 이름
        table_name = os.getenv('SESSIONS_TABLE', 'ai-branding-chatbot-sessions')
        
        try:
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"Connected to DynamoDB table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {str(e)}")
            raise
        
        # AgentCore 설정
        self.use_agentcore = os.getenv('USE_AGENTCORE', 'false').lower() == 'true'
        self.agentcore_orchestrator = None
        
        if self.use_agentcore and AGENTCORE_AVAILABLE:
            try:
                self.agentcore_orchestrator = AgentCoreOrchestrator(logger=logger)
                logger.info("AgentCore orchestrator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AgentCore orchestrator: {str(e)}")
                self.use_agentcore = False
        elif self.use_agentcore and not AGENTCORE_AVAILABLE:
            logger.warning("USE_AGENTCORE=true but AgentCore not available, falling back to Step Functions")
            self.use_agentcore = False
        
        # Reasoning Engine 초기화 (자율 의사결정용)
        self.reasoning_engine = None
        try:
            from bedrock_client import BedrockClient
            from reasoning_engine import ReasoningEngine
            
            bedrock_client = BedrockClient(logger=logger)
            self.reasoning_engine = ReasoningEngine(bedrock_client=bedrock_client, logger=logger)
            logger.info("Reasoning Engine initialized for autonomous decision-making")
        except Exception as e:
            logger.warning(f"Reasoning Engine not available: {str(e)}")
        
        logger.info(f"Supervisor Agent initialized: environment={self.environment}, use_agentcore={self.use_agentcore}")
    
    def _ensure_table_exists(self, table_name: str):
        """테이블이 없으면 생성"""
        try:
            # 테이블 존재 확인
            self.table.load()
            logger.info(f"Table {table_name} exists")
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            logger.info(f"Creating table {table_name}")
            
            # 테이블 생성
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'sessionId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'sessionId',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # 테이블 생성 완료 대기
            table.wait_until_exists()
            self.table = table
            logger.info(f"Table {table_name} created successfully")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회"""
        try:
            response = self.table.get_item(Key={'sessionId': session_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    def create_session(self, session_id: str, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """새 세션 생성"""
        try:
            now = datetime.utcnow()
            ttl = int((now + timedelta(hours=24)).timestamp())
            
            session_data = {
                'sessionId': session_id,
                'currentStep': 1,
                'status': 'active',
                'businessInfo': business_info,
                'createdAt': now.isoformat() + 'Z',
                'updatedAt': now.isoformat() + 'Z',
                'ttl': ttl,
                'agentStatuses': {
                    'productInsight': {'status': 'pending'},
                    'marketAnalyst': {'status': 'pending'},
                    'reporter': {'status': 'pending'},
                    'signboard': {'status': 'pending'},
                    'interior': {'status': 'pending'},
                    'reportGenerator': {'status': 'pending'}
                }
            }
            
            self.table.put_item(Item=session_data)
            logger.info(f"Created session {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {str(e)}")
            raise
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """세션 데이터 업데이트"""
        try:
            # 업데이트 표현식 생성
            update_expression = "SET updatedAt = :updated"
            expression_values = {':updated': datetime.utcnow().isoformat() + 'Z'}
            
            for key, value in updates.items():
                update_expression += f", {key} = :{key.replace('.', '_')}"
                expression_values[f":{key.replace('.', '_')}"] = value
            
            self.table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {str(e)}")
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
        
        This method implements Requirements 4.2 and 4.5:
        - Uses Reasoning LLM to decide recovery strategy (retry/fallback/human)
        - Implements exponential backoff for retries
        - Requests human intervention when confidence is low
        
        Args:
            error: Exception that occurred
            context: Execution context with workflow state
            session_id: Session ID
            max_retries: Maximum retry attempts (default: 3)
        
        Returns:
            Dict with:
                - recovery_strategy: 'retry', 'fallback', or 'human_intervention'
                - reasoning: Explanation for strategy choice
                - confidence: Confidence in strategy (0.0-1.0)
                - action_taken: Description of action
                - requires_human_input: Boolean flag
                - retry_delay: Delay in seconds (for retry strategy)
        """
        if not self.reasoning_engine:
            logger.warning("Reasoning Engine not available, using default recovery")
            return self._default_error_recovery(error, context)
        
        try:
            retry_count = context.get('retry_count', 0)
            
            # Use Reasoning LLM to decide recovery strategy
            logger.info(
                f"Autonomous error recovery: error={type(error).__name__}, "
                f"retry_count={retry_count}, session={session_id}"
            )
            
            recovery_context = {
                'error': str(error),
                'error_type': type(error).__name__,
                'context': context,
                'retry_count': retry_count,
                'max_retries': max_retries,
                'session_id': session_id,
                'current_step': context.get('current_step', 1),
                'orchestration_mode': context.get('orchestration_mode', 'unknown')
            }
            
            recovery_options = ['retry', 'fallback', 'human_intervention']
            
            recovery_decision = self.reasoning_engine.reason_and_decide(
                context=recovery_context,
                options=recovery_options,
                decision_criteria=(
                    "Select the best error recovery strategy for this workflow error. "
                    "Consider: retry count, error type, error severity, and user impact. "
                    "RETRY if: transient error (network, timeout) and retries available. "
                    "FALLBACK if: alternative approach exists (e.g., Step Functions instead of AgentCore). "
                    "HUMAN_INTERVENTION if: critical error, max retries exceeded, or unrecoverable."
                ),
                temperature=0.3  # Lower temperature for more deterministic decisions
            )
            
            strategy = recovery_decision['decision']
            confidence = recovery_decision['confidence']
            
            # Store recovery reasoning in session
            self._store_recovery_reasoning(session_id, recovery_decision, recovery_context)
            
            # Build result
            result = {
                'recovery_strategy': strategy,
                'reasoning': recovery_decision['reasoning'],
                'confidence': confidence,
                'requires_human_input': strategy == 'human_intervention' or confidence < 0.7,
                'retry_count': retry_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Execute recovery strategy
            if strategy == 'retry' and retry_count < max_retries:
                # Exponential backoff: 2^retry_count seconds
                retry_delay = min(2 ** retry_count, 60)  # Cap at 60 seconds
                result['action_taken'] = f"Retrying operation (attempt {retry_count + 1}/{max_retries})"
                result['retry_delay'] = retry_delay
                
                logger.info(
                    f"Recovery strategy: RETRY (attempt {retry_count + 1}/{max_retries}, "
                    f"delay={retry_delay}s, confidence={confidence:.2f})"
                )
                
            elif strategy == 'fallback':
                result['action_taken'] = "Switching to fallback mechanism"
                result['fallback_mode'] = 'stepfunctions' if self.use_agentcore else 'manual'
                
                logger.info(
                    f"Recovery strategy: FALLBACK (mode={result['fallback_mode']}, "
                    f"confidence={confidence:.2f})"
                )
                
            else:  # human_intervention or low confidence
                result['action_taken'] = "Requesting human intervention"
                result['requires_human_input'] = True
                result['human_input_reason'] = (
                    f"Error recovery requires human decision. "
                    f"Error: {type(error).__name__}, "
                    f"Confidence: {confidence:.2f}"
                )
                
                logger.warning(
                    f"Recovery strategy: HUMAN_INTERVENTION "
                    f"(reason={result['human_input_reason']}, confidence={confidence:.2f})"
                )
            
            # Update session with recovery information
            self.update_session(session_id, {
                'last_error': str(error),
                'last_error_type': type(error).__name__,
                'recovery_strategy': strategy,
                'recovery_confidence': Decimal(str(confidence)),
                'requires_human_input': result['requires_human_input']
            })
            
            return result
            
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {str(recovery_error)}")
            return self._default_error_recovery(error, context)
    
    def _default_error_recovery(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Default error recovery when Reasoning Engine is not available.
        
        Args:
            error: Exception that occurred
            context: Execution context
        
        Returns:
            Default recovery strategy
        """
        retry_count = context.get('retry_count', 0)
        max_retries = 3
        
        # Simple heuristic: retry transient errors, otherwise request human intervention
        transient_errors = ['ThrottlingException', 'ServiceUnavailableException', 'TimeoutError']
        error_type = type(error).__name__
        
        if error_type in transient_errors and retry_count < max_retries:
            retry_delay = min(2 ** retry_count, 60)
            return {
                'recovery_strategy': 'retry',
                'reasoning': f"Transient error detected: {error_type}. Retrying with exponential backoff.",
                'confidence': 0.8,
                'requires_human_input': False,
                'retry_count': retry_count,
                'retry_delay': retry_delay,
                'action_taken': f"Retrying operation (attempt {retry_count + 1}/{max_retries})"
            }
        else:
            return {
                'recovery_strategy': 'human_intervention',
                'reasoning': f"Non-transient error or max retries exceeded: {error_type}",
                'confidence': 0.9,
                'requires_human_input': True,
                'retry_count': retry_count,
                'action_taken': "Requesting human intervention",
                'human_input_reason': f"Error: {str(error)}"
            }
    
    def _store_recovery_reasoning(
        self,
        session_id: str,
        recovery_decision: Dict[str, Any],
        recovery_context: Dict[str, Any]
    ) -> None:
        """
        Store recovery reasoning in session for audit trail.
        
        Args:
            session_id: Session ID
            recovery_decision: Recovery decision from Reasoning Engine
            recovery_context: Context used for decision
        """
        try:
            # Get current reasoning chain
            session_data = self.get_session(session_id)
            reasoning_chain = session_data.get('reasoning_chain', []) if session_data else []
            
            # Create recovery reasoning step
            recovery_step = {
                'step_number': len(reasoning_chain) + 1,
                'agent_name': 'supervisor',
                'timestamp': datetime.utcnow().isoformat(),
                'operation': 'error_recovery',
                'input_data': recovery_context,
                'reasoning': recovery_decision['reasoning'],
                'decision': recovery_decision['decision'],
                'confidence': float(recovery_decision['confidence']),
                'alternatives': recovery_decision.get('alternatives', []),
                'reasoning_steps': recovery_decision.get('reasoning_steps', [])
            }
            
            # Append to reasoning chain
            reasoning_chain.append(recovery_step)
            
            # Update session
            self.update_session(session_id, {
                'reasoning_chain': reasoning_chain
            })
            
            logger.info(f"Stored recovery reasoning for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store recovery reasoning: {str(e)}")
    
    def execute_workflow(self, session_id: str, business_info: Dict[str, Any], current_step: int = 1) -> Dict[str, Any]:
        """
        워크플로 실행 (AgentCore 사용) with autonomous error recovery.
        
        Args:
            session_id: 세션 ID
            business_info: 비즈니스 정보
            current_step: 현재 단계 (1-5)
        
        Returns:
            워크플로 실행 결과
        """
        retry_count = 0
        max_retries = 3
        
        while retry_count <= max_retries:
            try:
                logger.info(
                    f"Executing workflow: session={session_id}, "
                    f"step={current_step}, mode=agentcore, retry={retry_count}"
                )
                
                if self.use_agentcore and self.agentcore_orchestrator:
                    # AgentCore 오케스트레이션 사용
                    result = self.agentcore_orchestrator.orchestrate_workflow(
                        session_id=session_id,
                        business_info=business_info,
                        current_step=current_step
                    )
                    
                    # 구조화된 로깅
                    logger.info(
                        json.dumps({
                            'orchestration_mode': 'agentcore',
                            'session_id': session_id,
                            'current_step': current_step,
                            'next_step': result.get('next_step'),
                            'status': result.get('status'),
                            'latency_ms': result.get('latency_ms'),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    )
                    
                    return result
                else:
                    # Fallback: Direct Lambda invocation
                    logger.warning("AgentCore not available, using direct Lambda invocation")
                    result = {
                        'status': 'error',
                        'session_id': session_id,
                        'current_step': current_step,
                        'error': 'AgentCore not configured',
                        'message': 'Please enable AgentCore by setting USE_AGENTCORE=true'
                    }
                    return result
                    
                    # 구조화된 로깅
                    logger.info(
                        json.dumps({
                            'orchestration_mode': 'stepfunctions',
                            'session_id': session_id,
                            'current_step': current_step,
                            'status': result.get('status'),
                            'execution_arn': result.get('execution_arn'),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    )
                    
                    return result
                    
            except Exception as e:
                logger.error(
                    f"Workflow execution failed: session={session_id}, "
                    f"error={str(e)}, retry={retry_count}"
                )
                
                # Autonomous error recovery
                recovery_context = {
                    'session_id': session_id,
                    'current_step': current_step,
                    'retry_count': retry_count,
                    'orchestration_mode': orchestration_mode,
                    'business_info': business_info
                }
                
                recovery_result = self.autonomous_error_recovery(
                    error=e,
                    context=recovery_context,
                    session_id=session_id,
                    max_retries=max_retries
                )
                
                # Check recovery strategy
                if recovery_result['recovery_strategy'] == 'retry' and retry_count < max_retries:
                    retry_count += 1
                    retry_delay = recovery_result.get('retry_delay', 2 ** retry_count)
                    
                    logger.info(f"Retrying workflow execution after {retry_delay}s delay")
                    import time
                    time.sleep(retry_delay)
                    continue
                    
                elif recovery_result['recovery_strategy'] == 'fallback':
                    # Try fallback mode
                    if self.use_agentcore:
                        logger.info("Switching to Step Functions fallback")
                        self.use_agentcore = False
                        retry_count += 1
                        continue
                    else:
                        # Already in fallback mode, return error
                        return {
                            'status': 'error',
                            'session_id': session_id,
                            'current_step': current_step,
                            'error': str(e),
                            'recovery_result': recovery_result,
                            'orchestration_mode': orchestration_mode
                        }
                else:
                    # Human intervention required
                    return {
                        'status': 'error',
                        'session_id': session_id,
                        'current_step': current_step,
                        'error': str(e),
                        'recovery_result': recovery_result,
                        'requires_human_input': True,
                        'orchestration_mode': orchestration_mode
                    }
        
        # Max retries exceeded
        return {
            'status': 'error',
            'session_id': session_id,
            'current_step': current_step,
            'error': 'Max retries exceeded',
            'retry_count': retry_count,
            'orchestration_mode': orchestration_mode
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Supervisor Agent Lambda handler with real DynamoDB integration
    """
    try:
        # 전체 이벤트 로깅 (디버깅용)
        logger.info(f"Supervisor Agent received event: {json.dumps(event, default=str)}")
        
        supervisor = SupervisorAgent()
        
        # HTTP 메서드와 경로 추출 (API Gateway v1 & v2 지원)
        # v1: httpMethod, path
        # v2: requestContext.http.method, rawPath or routeKey
        http_method = event.get('httpMethod')
        if not http_method:
            http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        
        path = event.get('path') or event.get('rawPath', '')
        if not path:
            # routeKey에서 경로 추출 (예: "POST /sessions" -> "/sessions")
            route_key = event.get('routeKey', '')
            if ' ' in route_key:
                path = route_key.split(' ', 1)[1]
        
        # API Gateway v2는 stage를 포함한 경로를 전달할 수 있음 (/dev/sessions)
        # stage 제거
        if path.startswith(f'/{supervisor.environment}/'):
            path = path[len(f'/{supervisor.environment}'):]
        
        logger.info(f"Parsed request: method={http_method}, path={path}")
        logger.info(f"Event keys: {list(event.keys())}")
        logger.info(f"Body: {event.get('body', 'NO BODY')}")
        
        # 세션 ID 추출
        session_id = None
        if '/status/' in path:
            session_id = path.split('/status/')[-1]
            logger.info(f"Extracted session ID from status path: {session_id}")
        elif '/sessions/' in path and path != '/sessions':
            session_id = path.split('/sessions/')[-1]
            logger.info(f"Extracted session ID from sessions path: {session_id}")
        
        # pathParameters에서도 시도
        if not session_id:
            path_params = event.get('pathParameters') or {}
            session_id = path_params.get('id')
            if session_id:
                logger.info(f"Extracted session ID from pathParameters: {session_id}")
        
        # POST 요청의 경우 body에서 세션 ID 추출
        if http_method == 'POST':
            body = event.get('body', '{}')
            if isinstance(body, str):
                try:
                    body_data = json.loads(body)
                    
                    # 새 세션 생성 요청
                    if path == '/sessions' and 'businessInfo' in body_data:
                        session_id = body_data.get('sessionId') or str(uuid.uuid4())
                        
                        session_data = supervisor.create_session(session_id, body_data['businessInfo'])
                        
                        # 자동으로 워크플로 시작 (옵션)
                        auto_start = body_data.get('autoStart', False)
                        if auto_start:
                            workflow_result = supervisor.execute_workflow(
                                session_id=session_id,
                                business_info=body_data['businessInfo'],
                                current_step=1
                            )
                            session_data['workflow_result'] = workflow_result
                        
                        return {
                            'statusCode': 201,
                            'headers': {'Content-Type': 'application/json'},
                            'body': json.dumps(session_data, default=decimal_default)
                        }
                    
                    # 워크플로 실행 요청
                    if '/execute' in path and session_id:
                        current_step = body_data.get('currentStep', 1)
                        business_info = body_data.get('businessInfo', {})
                        
                        # 세션에서 business_info 가져오기 (없으면)
                        if not business_info:
                            session_data = supervisor.get_session(session_id)
                            if session_data:
                                business_info = session_data.get('businessInfo', {})
                        
                        workflow_result = supervisor.execute_workflow(
                            session_id=session_id,
                            business_info=business_info,
                            current_step=current_step
                        )
                        
                        return {
                            'statusCode': 200,
                            'headers': {'Content-Type': 'application/json'},
                            'body': json.dumps(workflow_result, default=decimal_default)
                        }
                    
                    # 기존 세션 ID 추출
                    if not session_id:
                        session_id = body_data.get('sessionId')
                        
                except json.JSONDecodeError:
                    pass
        
        # Session ID is only required for non-creation requests
        if not session_id and not (http_method == 'POST' and path == '/sessions'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Session ID is required',
                    'debug': {
                        'http_method': http_method,
                        'path': path,
                        'session_id': session_id,
                        'condition': f"POST={http_method=='POST'}, path_match={path=='/sessions'}"
                    }
                })
            }
        
        # GET /status/{id} - 세션 상태 조회
        if http_method == 'GET' and '/status/' in path:
            session_data = supervisor.get_session(session_id)
            
            if not session_data:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Session not found'})
                }
            
            # 진행률 계산
            current_step = int(session_data.get('currentStep', 1))  # Decimal -> int 변환
            progress = {
                'overall': (current_step - 1) / 5 * 100,
                'currentStep': current_step,
                'stepName': ['', 'Business Analysis', 'Name Generation', 'Signboard Design', 'Interior Design', 'Report Generation'][current_step] if current_step <= 5 else 'Complete',
                'totalSteps': 5
            }
            
            # Parse interior data (check both new 'interiors' and old 'interior_recommendations')
            interior_data = None
            
            # Try new format first: 'interiors' field (Map type)
            if 'interiors' in session_data:
                interior_data = {
                    'recommendations': session_data.get('interiors', []),
                    'generatedImages': len([r for r in session_data.get('interiors', []) if r.get('imageUrl')])
                }
            # Fallback to old format: 'interior_recommendations' (JSON string)
            elif 'interior_recommendations' in session_data:
                try:
                    interior_json = session_data.get('interior_recommendations')
                    if isinstance(interior_json, str):
                        interior_data = json.loads(interior_json)
                    else:
                        interior_data = interior_json
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse interior_recommendations: {str(e)}")
            
            status_response = {
                'sessionId': session_id,
                'currentStep': current_step,
                'status': session_data.get('status', 'active'),
                'progress': progress,
                'agentStatuses': session_data.get('agentStatuses', {}),
                'businessInfo': session_data.get('businessInfo', {}),
                'createdAt': session_data.get('createdAt'),
                'updatedAt': session_data.get('updatedAt'),
                'results': {
                    'analysis': session_data.get('analysisResult'),
                    'names': session_data.get('business_names') or session_data.get('namesResult'),  # Check business_names first
                    'signboards': session_data.get('signboard_images') or session_data.get('signboardsResult'),  # Check signboard_images first
                    'interiors': interior_data or session_data.get('interiorsResult'),  # Use parsed interior_recommendations
                    'report': session_data.get('reportResult')
                }
            }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(status_response, default=decimal_default)
            }
        
        # GET /sessions/{id} - 세션 데이터 조회
        elif http_method == 'GET' and '/sessions/' in path:
            session_data = supervisor.get_session(session_id)
            
            if not session_data:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Session not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(session_data, default=decimal_default)
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unsupported operation'})
            }
        
    except Exception as e:
        logger.error(f"Error in Supervisor Agent: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }