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

from .agent_communication import get_agent_communication
from .models import AgentLog, AgentType
from .utils import setup_logging, get_aws_clients, create_response


class BaseAgent(ABC):
    """모든 Agent의 기본 클래스"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.agent_name = agent_type.value
        
        # 환경 변수 관리
        self.environment = os.getenv('ENVIRONMENT', 'local')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # 로깅 설정
        self.logger = setup_logging(self.agent_name)
        
        # AWS 클라이언트 초기화
        self.aws_clients = get_aws_clients()
        
        # Agent 간 통신 인터페이스
        self.communication = get_agent_communication()
        
        # 환경별 설정
        self.config = self._load_environment_config()
        
        # 성능 추적
        self.execution_start_time = None
        
        self.logger.info(f"Agent {self.agent_name} initialized in {self.environment} environment")
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """환경별 설정 로드"""
        config = {
            'timeout_seconds': int(os.getenv('AGENT_TIMEOUT_SECONDS', '30')),
            'max_retries': int(os.getenv('AGENT_MAX_RETRIES', '3')),
            'enable_agent_mode': os.getenv('ENABLE_AGENT_MODE', 'false').lower() == 'true',
            'enable_slack': os.getenv('ENABLE_SLACK', 'false').lower() == 'true',
            'sessions_table': os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local'),
            's3_bucket': os.getenv('S3_BUCKET', 'branding-chatbot-bucket-local'),
            'supervisor_queue_url': os.getenv('SUPERVISOR_QUEUE_URL'),
            'agent_communication_topic': os.getenv('AGENT_COMMUNICATION_TOPIC')
        }
        
        # 환경별 특화 설정
        if self.environment == 'local':
            config.update({
                'dynamodb_endpoint': 'http://localhost:8000',
                's3_endpoint': 'http://localhost:9000',
                'stepfunctions_endpoint': 'http://localhost:8083'
            })
        
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
    
    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """세션 데이터 업데이트"""
        try:
            sessions_table = self.aws_clients['dynamodb'].Table(self.config['sessions_table'])
            
            # 업데이트 표현식 생성
            update_expression_parts = []
            expression_attribute_values = {}
            
            for key, value in updates.items():
                update_expression_parts.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = value
            
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