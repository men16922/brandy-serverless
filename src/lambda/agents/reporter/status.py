# Reporter Status Agent Lambda Function
# 상호명 생성 상태 조회

import json
import os
import sys

# 공통 유틸리티 import - Lambda Layer 사용
sys.path.insert(0, '/opt/python/python')

from shared.base_agent import BaseAgent
from shared.models import AgentType


class ReporterStatusAgent(BaseAgent):
    """Reporter Status Agent - 상호명 생성 상태 조회"""
    
    def __init__(self):
        super().__init__(AgentType.REPORTER)
    
    def execute(self, event: dict, context: any) -> dict:
        """상호명 생성 상태 조회"""
        try:
            # Path parameter에서 session_id 추출
            session_id = event.get('pathParameters', {}).get('sessionId')
            
            if not session_id:
                return self.create_lambda_response(400, {
                    'error': 'sessionId is required'
                })
            
            self.logger.info(f"Checking name generation status for session: {session_id}")
            
            # 세션 데이터 조회
            session_data = self.get_session_data(session_id)
            if not session_data:
                return self.create_lambda_response(404, {
                    'status': 'not_found',
                    'error': 'Session not found'
                })
            
            # 상태 확인
            status = session_data.get('nameGenerationStatus', 'not_started')
            
            self.logger.info(f"Name generation status: {status}")
            
            if status == 'completed':
                # 완료: 200 OK
                business_names = session_data.get('business_names', {})
                if isinstance(business_names, str):
                    business_names = json.loads(business_names)
                
                return self.create_lambda_response(200, {
                    'statusCode': 200,
                    'status': 'completed',
                    'sessionId': session_id,
                    'suggestions': business_names.get('suggestions', []),
                    'canRegenerate': business_names.get('regeneration_count', 0) < 3,
                    'completedAt': session_data.get('nameGenerationCompletedAt')
                })
            
            elif status == 'processing':
                # 진행 중: 202 Accepted
                return self.create_lambda_response(202, {
                    'statusCode': 202,
                    'status': 'processing',
                    'sessionId': session_id,
                    'message': 'Name generation in progress',
                    'startedAt': session_data.get('nameGenerationStartedAt')
                })
            
            elif status == 'failed':
                # 실패: 500 Internal Server Error
                return self.create_lambda_response(500, {
                    'statusCode': 500,
                    'status': 'failed',
                    'sessionId': session_id,
                    'error': session_data.get('nameGenerationError', 'Unknown error'),
                    'failedAt': session_data.get('nameGenerationFailedAt')
                })
            
            else:
                # 시작 안됨: 404 Not Found
                return self.create_lambda_response(404, {
                    'statusCode': 404,
                    'status': 'not_started',
                    'sessionId': session_id,
                    'message': 'Name generation not started'
                })
        
        except Exception as e:
            error_message = f"Status check failed: {str(e)}"
            self.logger.error(error_message)
            
            return self.create_lambda_response(500, {
                'error': error_message
            })


def lambda_handler(event, context):
    """Lambda handler"""
    agent = ReporterStatusAgent()
    return agent.lambda_handler(event, context)
