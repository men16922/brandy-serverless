#!/usr/bin/env python3
"""
Interior Agent 데이터 초기화 스크립트
"""

import sys
import os
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src', 'lambda'))

from shared.data_loader import initialize_data

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """메인 실행 함수"""
    try:
        # 환경 변수에서 환경 설정 가져오기
        environment = os.getenv('ENVIRONMENT', 'local')
        force_reload = os.getenv('FORCE_RELOAD', 'false').lower() == 'true'
        
        logger.info(f"Initializing interior data for environment: {environment}")
        logger.info(f"Force reload: {force_reload}")
        
        # 데이터 디렉토리 경로
        data_dir = os.path.join(project_root, 'data')
        
        if not os.path.exists(data_dir):
            logger.error(f"Data directory not found: {data_dir}")
            return False
        
        # 데이터 초기화
        success = initialize_data(
            data_dir=data_dir,
            force_reload=force_reload,
            environment=environment
        )
        
        if success:
            logger.info("✅ Interior data initialization completed successfully")
            return True
        else:
            logger.error("❌ Interior data initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during initialization: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)