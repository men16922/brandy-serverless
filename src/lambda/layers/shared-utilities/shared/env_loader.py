"""
환경변수 로더 - .env 파일과 시스템 환경변수를 로드
"""

import os
from typing import Optional

def load_env_file(env_file_path: str = None) -> None:
    """
    환경별 .env 파일에서 환경변수를 로드합니다.
    
    Args:
        env_file_path: .env 파일 경로 (기본값: 환경에 따라 자동 선택)
    """
    try:
        # 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..', '..')
        
        # 환경별 파일 경로 결정
        if env_file_path is None:
            # 환경변수에서 환경 확인
            environment = os.getenv('ENVIRONMENT', 'local')
            env_file_path = f".env.{environment}"
            
            # 환경별 파일이 없으면 기본 .env 파일 사용
            env_path = os.path.join(project_root, env_file_path)
            if not os.path.exists(env_path):
                env_file_path = ".env"
        
        env_path = os.path.join(project_root, env_file_path)
        
        if not os.path.exists(env_path):
            print(f"Warning: .env file not found at {env_path}")
            return
        
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 빈 줄이나 주석 건너뛰기
                if not line or line.startswith('#'):
                    continue
                
                # KEY=VALUE 형식 파싱
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 따옴표 제거
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # 환경변수가 이미 설정되어 있지 않은 경우만 설정
                    if key not in os.environ:
                        os.environ[key] = value
        
        print(f"✅ Environment variables loaded from {env_file_path}")
        
    except Exception as e:
        print(f"Warning: Failed to load .env file: {str(e)}")

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    환경변수를 안전하게 가져옵니다.
    
    Args:
        key: 환경변수 키
        default: 기본값
        required: 필수 여부
        
    Returns:
        환경변수 값 또는 기본값
        
    Raises:
        ValueError: required=True인데 환경변수가 없는 경우
    """
    value = os.getenv(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    return value

def is_local_environment() -> bool:
    """로컬 개발 환경인지 확인"""
    return get_env_var('ENVIRONMENT', 'local').lower() == 'local'

def get_openai_api_key() -> Optional[str]:
    """OpenAI API 키 가져오기"""
    return get_env_var('OPENAI_API_KEY')

def get_aws_credentials() -> dict:
    """AWS 자격증명 가져오기"""
    return {
        'access_key_id': get_env_var('AWS_ACCESS_KEY_ID'),
        'secret_access_key': get_env_var('AWS_SECRET_ACCESS_KEY'),
        'region': get_env_var('AWS_REGION', 'us-east-1')
    }

# 모듈 로드 시 자동으로 .env 파일 로드
load_env_file()