# Agent Configuration Management
# 환경 변수 관리 및 Agent별 설정

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """환경 타입"""
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


@dataclass
class AgentConfig:
    """Agent 설정 클래스"""
    # 기본 설정
    environment: Environment
    region: str
    timeout_seconds: int
    max_retries: int
    
    # AWS 리소스
    sessions_table: str
    s3_bucket: str
    supervisor_queue_url: Optional[str]
    agent_communication_topic: Optional[str]
    
    # 기능 플래그
    enable_agent_mode: bool
    enable_slack: bool
    enable_debug_logging: bool
    
    # 환경별 엔드포인트
    dynamodb_endpoint: Optional[str] = None
    s3_endpoint: Optional[str] = None
    stepfunctions_endpoint: Optional[str] = None
    sqs_endpoint: Optional[str] = None
    sns_endpoint: Optional[str] = None
    
    # Agent별 특화 설정
    agent_specific: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_environment(cls) -> 'AgentConfig':
        """환경 변수에서 설정 로드"""
        env_str = os.getenv('ENVIRONMENT', 'local').lower()
        environment = Environment(env_str)
        
        config = cls(
            environment=environment,
            region=os.getenv('AWS_REGION', 'us-east-1'),
            timeout_seconds=int(os.getenv('AGENT_TIMEOUT_SECONDS', '30')),
            max_retries=int(os.getenv('AGENT_MAX_RETRIES', '3')),
            
            sessions_table=os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local'),
            s3_bucket=os.getenv('S3_BUCKET', 'branding-chatbot-bucket-local'),
            supervisor_queue_url=os.getenv('SUPERVISOR_QUEUE_URL'),
            agent_communication_topic=os.getenv('AGENT_COMMUNICATION_TOPIC'),
            
            enable_agent_mode=os.getenv('ENABLE_AGENT_MODE', 'false').lower() == 'true',
            enable_slack=os.getenv('ENABLE_SLACK', 'false').lower() == 'true',
            enable_debug_logging=os.getenv('ENABLE_DEBUG_LOGGING', 'false').lower() == 'true'
        )
        
        # 환경별 엔드포인트 설정
        if environment == Environment.LOCAL:
            config.dynamodb_endpoint = os.getenv('DYNAMODB_ENDPOINT', 'http://localhost:8000')
            config.s3_endpoint = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
            config.stepfunctions_endpoint = os.getenv('STEPFUNCTIONS_ENDPOINT', 'http://localhost:8083')
            config.sqs_endpoint = os.getenv('SQS_ENDPOINT', 'http://localhost:9324')
            config.sns_endpoint = os.getenv('SNS_ENDPOINT', 'http://localhost:4566')
        
        # Agent별 특화 설정 로드
        config._load_agent_specific_config()
        
        return config
    
    def _load_agent_specific_config(self):
        """Agent별 특화 설정 로드"""
        # Supervisor Agent 설정
        self.agent_specific['supervisor'] = {
            'workflow_check_interval': int(os.getenv('SUPERVISOR_CHECK_INTERVAL', '5')),
            'max_workflow_duration': int(os.getenv('MAX_WORKFLOW_DURATION', '300')),
            'enable_auto_retry': os.getenv('SUPERVISOR_AUTO_RETRY', 'true').lower() == 'true'
        }
        
        # Product Insight Agent 설정
        self.agent_specific['product_insight'] = {
            'knowledge_base_id': os.getenv('BEDROCK_KB_ID'),
            'max_search_results': int(os.getenv('KB_MAX_RESULTS', '10')),
            'cache_ttl_seconds': int(os.getenv('KB_CACHE_TTL', '3600'))
        }
        
        # Market Analyst Agent 설정
        self.agent_specific['market_analyst'] = {
            'knowledge_base_id': os.getenv('BEDROCK_KB_ID'),
            'market_data_source': os.getenv('MARKET_DATA_SOURCE', 'bedrock_kb'),
            'analysis_depth': os.getenv('MARKET_ANALYSIS_DEPTH', 'standard')
        }
        
        # Reporter Agent 설정
        self.agent_specific['reporter'] = {
            'max_name_suggestions': int(os.getenv('MAX_NAME_SUGGESTIONS', '3')),
            'max_regenerations': int(os.getenv('MAX_NAME_REGENERATIONS', '3')),
            'scoring_weights': {
                'pronunciation': float(os.getenv('PRONUNCIATION_WEIGHT', '0.4')),
                'search': float(os.getenv('SEARCH_WEIGHT', '0.6'))
            }
        }
        
        # Signboard Agent 설정
        self.agent_specific['signboard'] = {
            'ai_providers': os.getenv('SIGNBOARD_AI_PROVIDERS', 'dalle,sdxl,gemini').split(','),
            'parallel_timeout': int(os.getenv('SIGNBOARD_TIMEOUT', '30')),
            'fallback_image_path': os.getenv('SIGNBOARD_FALLBACK_PATH', 'fallbacks/signs/')
        }
        
        # Interior Agent 설정
        self.agent_specific['interior'] = {
            'ai_providers': os.getenv('INTERIOR_AI_PROVIDERS', 'dalle,sdxl,gemini').split(','),
            'parallel_timeout': int(os.getenv('INTERIOR_TIMEOUT', '30')),
            'fallback_image_path': os.getenv('INTERIOR_FALLBACK_PATH', 'fallbacks/interiors/'),
            'budget_ranges': os.getenv('BUDGET_RANGES', 'low,medium,high').split(',')
        }
        
        # Report Generator Agent 설정
        self.agent_specific['report_generator'] = {
            'pdf_template_path': os.getenv('PDF_TEMPLATE_PATH', 'templates/pdf-templates/'),
            'report_timeout': int(os.getenv('REPORT_TIMEOUT', '60')),
            'include_metadata': os.getenv('INCLUDE_REPORT_METADATA', 'true').lower() == 'true'
        }
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """특정 Agent의 설정 반환"""
        return self.agent_specific.get(agent_name, {})
    
    def is_local_environment(self) -> bool:
        """로컬 환경 여부 확인"""
        return self.environment == Environment.LOCAL
    
    def is_production_environment(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.environment == Environment.PROD
    
    def get_aws_endpoint(self, service: str) -> Optional[str]:
        """AWS 서비스 엔드포인트 반환"""
        if not self.is_local_environment():
            return None
        
        endpoint_map = {
            'dynamodb': self.dynamodb_endpoint,
            's3': self.s3_endpoint,
            'stepfunctions': self.stepfunctions_endpoint,
            'sqs': self.sqs_endpoint,
            'sns': self.sns_endpoint
        }
        
        return endpoint_map.get(service)
    
    def validate(self) -> Dict[str, Any]:
        """설정 유효성 검증"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 필수 설정 검증
        required_fields = [
            'sessions_table',
            's3_bucket'
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                validation_result['errors'].append(f"Missing required configuration: {field}")
                validation_result['valid'] = False
        
        # Agent 모드 활성화 시 추가 검증
        if self.enable_agent_mode:
            if not self.supervisor_queue_url:
                validation_result['warnings'].append("Agent mode enabled but SUPERVISOR_QUEUE_URL not set")
            
            if not self.agent_communication_topic:
                validation_result['warnings'].append("Agent mode enabled but AGENT_COMMUNICATION_TOPIC not set")
        
        # Slack 모드 활성화 시 추가 검증
        if self.enable_slack:
            slack_required = [
                'SLACK_BOT_TOKEN',
                'SLACK_SIGNING_SECRET'
            ]
            
            for var in slack_required:
                if not os.getenv(var):
                    validation_result['errors'].append(f"Slack mode enabled but {var} not set")
                    validation_result['valid'] = False
        
        # 타임아웃 값 검증
        if self.timeout_seconds <= 0 or self.timeout_seconds > 900:  # Lambda 최대 15분
            validation_result['errors'].append("Invalid timeout_seconds value")
            validation_result['valid'] = False
        
        return validation_result
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'environment': self.environment.value,
            'region': self.region,
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'sessions_table': self.sessions_table,
            's3_bucket': self.s3_bucket,
            'supervisor_queue_url': self.supervisor_queue_url,
            'agent_communication_topic': self.agent_communication_topic,
            'enable_agent_mode': self.enable_agent_mode,
            'enable_slack': self.enable_slack,
            'enable_debug_logging': self.enable_debug_logging,
            'endpoints': {
                'dynamodb': self.dynamodb_endpoint,
                's3': self.s3_endpoint,
                'stepfunctions': self.stepfunctions_endpoint,
                'sqs': self.sqs_endpoint,
                'sns': self.sns_endpoint
            },
            'agent_specific': self.agent_specific
        }


class ConfigManager:
    """설정 관리자"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_config(self) -> AgentConfig:
        """설정 인스턴스 반환 (싱글톤)"""
        if self._config is None:
            self._config = AgentConfig.from_environment()
        return self._config
    
    def reload_config(self) -> AgentConfig:
        """설정 재로드"""
        self._config = AgentConfig.from_environment()
        return self._config
    
    def validate_config(self) -> Dict[str, Any]:
        """현재 설정 검증"""
        config = self.get_config()
        return config.validate()


# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()


def get_agent_config() -> AgentConfig:
    """Agent 설정 반환"""
    return config_manager.get_config()


def get_config_for_agent(agent_name: str) -> Dict[str, Any]:
    """특정 Agent의 설정 반환"""
    config = get_agent_config()
    return config.get_agent_config(agent_name)


def validate_environment_config() -> Dict[str, Any]:
    """환경 설정 검증"""
    return config_manager.validate_config()


def is_agent_mode_enabled() -> bool:
    """Agent 모드 활성화 여부"""
    config = get_agent_config()
    return config.enable_agent_mode


def is_slack_enabled() -> bool:
    """Slack 모드 활성화 여부"""
    config = get_agent_config()
    return config.enable_slack


def get_environment_type() -> Environment:
    """현재 환경 타입 반환"""
    config = get_agent_config()
    return config.environment