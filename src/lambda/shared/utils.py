# Shared utilities for Agent Lambda functions
# Agent-aware logging, error handling, and AWS client initialization

import json
import logging
import boto3
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps

class AgentLogger:
    """Agent-aware structured logger"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.warning(message, extra=extra)
    
    def log_agent_execution(self, tool: str, latency_ms: int, status: str, 
                           session_id: str = None, error_message: str = None, 
                           metadata: Dict[str, Any] = None):
        """Agent 실행 로그 기록 (구조화된 형태)"""
        log_data = {
            'agent': self.agent_name,
            'tool': tool,
            'latency_ms': latency_ms,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if session_id:
            log_data['session_id'] = session_id
        
        if error_message:
            log_data['error_message'] = error_message
        
        if metadata:
            log_data['metadata'] = metadata
        
        if status == 'error':
            self.error(f"Agent execution: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.info(f"Agent execution: {json.dumps(log_data, ensure_ascii=False)}")

def setup_logging(agent_name: str = "unknown") -> AgentLogger:
    """Setup agent-aware structured logging"""
    return AgentLogger(agent_name)

def get_aws_clients():
    """Initialize AWS service clients based on environment"""
    environment = os.getenv('ENVIRONMENT', 'local')
    
    if environment == 'local':
        # Local development configuration
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        s3 = boto3.client('s3', endpoint_url='http://localhost:9000')
        stepfunctions = boto3.client('stepfunctions', endpoint_url='http://localhost:8083')
        sqs = boto3.client('sqs', endpoint_url='http://localhost:9324')
        sns = boto3.client('sns', endpoint_url='http://localhost:4566')
    else:
        # AWS environment configuration
        dynamodb = boto3.resource('dynamodb')
        s3 = boto3.client('s3')
        stepfunctions = boto3.client('stepfunctions')
        sqs = boto3.client('sqs')
        sns = boto3.client('sns')
    
    return {
        'dynamodb': dynamodb,
        's3': s3,
        'stepfunctions': stepfunctions,
        'sqs': sqs,
        'sns': sns
    }

def create_response(status_code, body, headers=None):
    """Create standardized API response"""
    if headers is None:
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, ensure_ascii=False)
    }

def measure_latency(func):
    """Decorator to measure function execution latency"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            return result, latency_ms
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            raise e
    return wrapper


def agent_execution_tracker(agent_name: str, tool_name: str):
    """Agent 실행 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = setup_logging(agent_name)
            
            try:
                logger.info(f"Starting {tool_name} execution")
                result = func(*args, **kwargs)
                latency_ms = int((time.time() - start_time) * 1000)
                
                logger.log_agent_execution(
                    tool=tool_name,
                    latency_ms=latency_ms,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                
                logger.log_agent_execution(
                    tool=tool_name,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(e)
                )
                
                raise e
        
        return wrapper
    return decorator


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """지수 백오프를 사용한 재시도 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_session_id(session_id: str) -> bool:
    """세션 ID 유효성 검증"""
    if not session_id or not isinstance(session_id, str):
        return False
    
    # UUID 형식 검증 (간단한 형태)
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    return bool(uuid_pattern.match(session_id))


def extract_session_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """Lambda 이벤트에서 세션 ID 추출"""
    # API Gateway 경로 파라미터에서 추출
    if 'pathParameters' in event and event['pathParameters']:
        session_id = event['pathParameters'].get('id') or event['pathParameters'].get('sessionId')
        if session_id:
            return session_id
    
    # 요청 본문에서 추출
    if 'body' in event and event['body']:
        try:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            session_id = body.get('sessionId') or body.get('session_id')
            if session_id:
                return session_id
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 쿼리 파라미터에서 추출
    if 'queryStringParameters' in event and event['queryStringParameters']:
        session_id = event['queryStringParameters'].get('sessionId') or event['queryStringParameters'].get('session_id')
        if session_id:
            return session_id
    
    return None


def create_agent_response(agent_name: str, status_code: int, data: Any, 
                         error_message: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Agent용 표준화된 응답 생성"""
    response_data = {
        'agent': agent_name,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'success' if status_code < 400 else 'error'
    }
    
    if error_message:
        response_data['error'] = error_message
    else:
        response_data['data'] = data
    
    if metadata:
        response_data['metadata'] = metadata
    
    return create_response(status_code, response_data)