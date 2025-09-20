# Supervisor Agent Lambda Function
# 전체 워크플로 상태 감시, Step Functions 실행 상태 추적, 에이전트 간 조정 및 통제

import json
import boto3
import uuid
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, Any, List, Optional

# 공통 유틸리티 import
import sys
sys.path.append('/opt/python')
from shared.utils import setup_logging, get_aws_clients, create_response
from shared.agent_communication import AgentCommunication

logger = setup_logging()

class SupervisorAgent:
    def __init__(self):
        self.aws_clients = get_aws_clients()
        self.dynamodb = self.aws_clients['dynamodb']
        self.stepfunctions = boto3.client('stepfunctions')
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        self.agent_comm = AgentCommunication()
        
    def lambda_handler(self, event, context):
        """
        Supervisor Agent 메인 핸들러
        - 전체 워크플로 상태 감시
        - Step Functions 실행 상태 추적  
        - GET /status/{id} 엔드포인트 제공
        - 실패 시 재시도/폴백 트리거
        - 에이전트 간 조정 및 통제
        """
        try:
            logger.info("Supervisor Agent started", extra={
                "agent": "supervisor",
                "tool": "workflow.monitor",
                "session_id": event.get('pathParameters', {}).get('id'),
                "event": event
            })
            
            start_time = datetime.now()
            
            # HTTP 메서드에 따른 라우팅
            http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
            path = event.get('path') or event.get('rawPath', '')
            
            if http_method == 'GET' and '/status/' in path:
                result = self.get_workflow_status(event)
            elif http_method == 'POST' and path.endswith('/monitor'):
                result = self.monitor_workflow(event)
            elif http_method == 'POST' and path.endswith('/trigger-fallback'):
                result = self.trigger_fallback(event)
            else:
                result = create_response(400, {"error": "Unsupported operation"})
            
            # 실행 시간 로깅
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info("Supervisor Agent completed", extra={
                "agent": "supervisor",
                "tool": "workflow.monitor", 
                "latency_ms": latency_ms,
                "status": "success"
            })
            
            return result
            
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error("Supervisor Agent failed", extra={
                "agent": "supervisor",
                "tool": "workflow.monitor",
                "latency_ms": latency_ms,
                "error": str(e)
            })
            return create_response(500, {"error": "Internal server error"})
    
    def get_workflow_status(self, event) -> Dict[str, Any]:
        """전체 워크플로 상태 반환 (GET /status/{id})"""
        session_id = event['pathParameters']['id']
        
        try:
            # 세션 정보 조회
            response = self.sessions_table.get_item(Key={'sessionId': session_id})
            
            if 'Item' not in response:
                return create_response(404, {"error": "Session not found"})
            
            session = response['Item']
            
            # Step Functions 실행 상태 조회
            workflow_status = self._get_stepfunctions_status(session)
            
            # 에이전트별 실행 상태 조회
            agent_statuses = self._get_agent_statuses(session)
            
            status_response = {
                "sessionId": session_id,
                "currentStep": session.get('currentStep', 1),
                "status": session.get('status', 'active'),
                "progress": self._calculate_progress(session),
                "workflowStatus": workflow_status,
                "agentStatuses": agent_statuses,
                "createdAt": session.get('createdAt'),
                "updatedAt": session.get('updatedAt'),
                "estimatedTimeRemaining": self._estimate_time_remaining(session)
            }
            
            return create_response(200, status_response)
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {str(e)}")
            return create_response(500, {"error": "Failed to retrieve status"})
    
    def monitor_workflow(self, event) -> Dict[str, Any]:
        """워크플로 모니터링 및 상태 업데이트"""
        body = json.loads(event['body'])
        session_id = body.get('sessionId')
        agent_id = body.get('agentId')
        status = body.get('status')
        result = body.get('result')
        
        # 에이전트 상태 업데이트
        self._update_agent_status(session_id, agent_id, status, result)
        
        # 실패 감지 시 폴백 트리거
        if status == 'failed':
            self._trigger_fallback_if_needed(session_id, agent_id)
        
        return create_response(200, {"message": "Status updated"})
    
    def trigger_fallback(self, event) -> Dict[str, Any]:
        """실패 시 재시도/폴백 트리거"""
        body = json.loads(event['body'])
        session_id = body.get('sessionId')
        failed_agent = body.get('failedAgent')
        
        # 폴백 전략 실행
        fallback_result = self._execute_fallback_strategy(session_id, failed_agent)
        
        return create_response(200, fallback_result)
    
    def _get_stepfunctions_status(self, session) -> Dict[str, Any]:
        """Step Functions 실행 상태 조회"""
        # 구현 예정: Step Functions ARN을 통한 상태 조회
        return {
            "expressWorkflow": "RUNNING",
            "standardWorkflow": "WAITING_FOR_INPUT"
        }
    
    def _get_agent_statuses(self, session) -> Dict[str, Any]:
        """에이전트별 실행 상태 조회"""
        return {
            "productInsight": session.get('agentStatuses', {}).get('productInsight', 'pending'),
            "marketAnalyst": session.get('agentStatuses', {}).get('marketAnalyst', 'pending'),
            "reporter": session.get('agentStatuses', {}).get('reporter', 'pending'),
            "signboard": session.get('agentStatuses', {}).get('signboard', 'pending'),
            "interior": session.get('agentStatuses', {}).get('interior', 'pending'),
            "reportGenerator": session.get('agentStatuses', {}).get('reportGenerator', 'pending')
        }
    
    def _calculate_progress(self, session) -> float:
        """워크플로 진행률 계산"""
        current_step = session.get('currentStep', 1)
        total_steps = 5
        return (current_step - 1) / total_steps * 100
    
    def _estimate_time_remaining(self, session) -> Optional[int]:
        """남은 예상 시간 계산 (초)"""
        current_step = session.get('currentStep', 1)
        if current_step >= 5:
            return 0
        
        # 단계별 예상 시간 (초)
        step_times = {1: 30, 2: 30, 3: 180, 4: 180, 5: 60}
        remaining_time = sum(step_times[i] for i in range(current_step + 1, 6))
        return remaining_time
    
    def _update_agent_status(self, session_id: str, agent_id: str, status: str, result: Any):
        """에이전트 상태 업데이트"""
        try:
            self.sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET agentStatuses.#agent = :status, updatedAt = :timestamp',
                ExpressionAttributeNames={'#agent': agent_id},
                ExpressionAttributeValues={
                    ':status': status,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to update agent status: {str(e)}")
    
    def _trigger_fallback_if_needed(self, session_id: str, failed_agent: str):
        """필요시 폴백 메커니즘 트리거"""
        logger.warning(f"Agent {failed_agent} failed for session {session_id}, triggering fallback")
        # 구현 예정: 에이전트별 폴백 전략
    
    def _execute_fallback_strategy(self, session_id: str, failed_agent: str) -> Dict[str, Any]:
        """폴백 전략 실행"""
        # 구현 예정: 에이전트별 폴백 로직
        return {"message": f"Fallback executed for {failed_agent}"}

# Lambda 핸들러
supervisor_agent = SupervisorAgent()

def lambda_handler(event, context):
    return supervisor_agent.lambda_handler(event, context)