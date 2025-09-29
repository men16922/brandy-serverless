"""
Supervisor Agent - Real DynamoDB integration
"""

import json
import boto3
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupervisorAgent:
    def __init__(self):
        # DynamoDB 설정 (로컬 환경 감지)
        environment = os.getenv('ENVIRONMENT', 'local')
        
        if environment == 'local':
            # 로컬 DynamoDB 연결
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url='http://host.docker.internal:8000',
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # AWS DynamoDB 연결
            self.dynamodb = boto3.resource('dynamodb')
        
        # 테이블 이름
        table_name = os.getenv('DYNAMODB_TABLE', 'ai-branding-chatbot-sessions-local')
        
        try:
            self.table = self.dynamodb.Table(table_name)
            # 테이블이 없으면 생성
            self._ensure_table_exists(table_name)
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {str(e)}")
            raise
    
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

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Supervisor Agent Lambda handler with real DynamoDB integration
    """
    try:
        logger.info(f"Supervisor Agent received event: {json.dumps(event, default=str)}")
        
        supervisor = SupervisorAgent()
        
        # HTTP 메서드와 경로 추출
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('path', '')
        
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
                        
                        return {
                            'statusCode': 201,
                            'headers': {'Content-Type': 'application/json'},
                            'body': json.dumps(session_data)
                        }
                    
                    # 기존 세션 ID 추출
                    if not session_id:
                        session_id = body_data.get('sessionId')
                        
                except json.JSONDecodeError:
                    pass
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Session ID is required'})
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
            current_step = session_data.get('currentStep', 1)
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
                'body': json.dumps(status_response)
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
                'body': json.dumps(session_data)
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