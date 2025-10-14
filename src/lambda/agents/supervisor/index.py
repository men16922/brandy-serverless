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
        # DynamoDB 설정 (로컬 환경 감지)
        self.environment = os.getenv('ENVIRONMENT', 'local')
        
        if self.environment == 'local':
            # 로컬 DynamoDB 연결
            # host.docker.internal은 Docker 컨테이너 내부용
            # 로컬 스크립트 실행 시에는 localhost 사용
            endpoint_url = os.getenv('DYNAMODB_ENDPOINT', 'http://localhost:8000')
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # AWS DynamoDB 연결
            self.dynamodb = boto3.resource('dynamodb')
        
        # 테이블 이름
        table_name = os.getenv('SESSIONS_TABLE', 'ai-branding-chatbot-sessions')
        
        try:
            self.table = self.dynamodb.Table(table_name)
            # 테이블이 없으면 생성
            self._ensure_table_exists(table_name)
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
    
    def execute_workflow(self, session_id: str, business_info: Dict[str, Any], current_step: int = 1) -> Dict[str, Any]:
        """
        워크플로 실행 (AgentCore 또는 Step Functions)
        
        Args:
            session_id: 세션 ID
            business_info: 비즈니스 정보
            current_step: 현재 단계 (1-5)
        
        Returns:
            워크플로 실행 결과
        """
        try:
            orchestration_mode = 'agentcore' if self.use_agentcore else 'stepfunctions'
            
            logger.info(
                f"Executing workflow: session={session_id}, "
                f"step={current_step}, mode={orchestration_mode}"
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
                # Step Functions fallback
                logger.info(
                    f"Using Step Functions fallback for session {session_id}"
                )
                
                # 기존 Step Functions 로직 (향후 구현)
                # 현재는 placeholder 응답 반환
                result = {
                    'status': 'pending',
                    'session_id': session_id,
                    'current_step': current_step,
                    'next_step': current_step + 1 if current_step < 5 else 5,
                    'message': 'Step Functions orchestration (not yet implemented)',
                    'orchestration_mode': 'stepfunctions'
                }
                
                # 구조화된 로깅
                logger.info(
                    json.dumps({
                        'orchestration_mode': 'stepfunctions',
                        'session_id': session_id,
                        'current_step': current_step,
                        'next_step': result.get('next_step'),
                        'status': result.get('status'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                )
                
                return result
                
        except Exception as e:
            logger.error(
                f"Workflow execution failed: session={session_id}, "
                f"error={str(e)}"
            )
            
            return {
                'status': 'error',
                'session_id': session_id,
                'current_step': current_step,
                'error': str(e),
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
                    'names': session_data.get('namesResult'),
                    'signboards': session_data.get('signboardsResult'),
                    'interiors': session_data.get('interiorsResult'),
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