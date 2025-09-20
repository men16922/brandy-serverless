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
from shared.base_agent import BaseAgent
from shared.models import AgentType, WorkflowStep, SessionStatus, WorkflowSession
from shared.agent_config import get_agent_config
from shared.utils import extract_session_id_from_event, validate_session_id, retry_with_backoff


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - 전체 워크플로 감시 및 제어"""
    
    def __init__(self):
        super().__init__(AgentType.SUPERVISOR)
        
        # Supervisor 특화 설정
        self.supervisor_config = self.config.get('agent_specific', {}).get('supervisor', {})
        self.workflow_check_interval = self.supervisor_config.get('workflow_check_interval', 5)
        self.max_workflow_duration = self.supervisor_config.get('max_workflow_duration', 300)
        self.enable_auto_retry = self.supervisor_config.get('enable_auto_retry', True)
        
        # Step Functions 클라이언트
        stepfunctions_endpoint = self.config.get('stepfunctions_endpoint')
        if stepfunctions_endpoint:
            self.stepfunctions = boto3.client('stepfunctions', endpoint_url=stepfunctions_endpoint)
        else:
            self.stepfunctions = boto3.client('stepfunctions')
        
        # 워크플로 상태 추적
        self.workflow_states = {}
        
        self.logger.info("Supervisor Agent initialized with enhanced monitoring capabilities")
        
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Supervisor Agent 메인 실행 로직
        - 전체 워크플로 상태 감시
        - Step Functions 실행 상태 추적  
        - GET /status/{id} 엔드포인트 제공
        - 실패 시 재시도/폴백 트리거
        - 에이전트 간 조정 및 통제
        """
        # 세션 ID 추출
        session_id = extract_session_id_from_event(event)
        if not session_id:
            return self.create_lambda_response(400, {"error": "Session ID is required"})
        
        if not validate_session_id(session_id):
            return self.create_lambda_response(400, {"error": "Invalid session ID format"})
        
        # HTTP 메서드에 따른 라우팅
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
        path = event.get('path') or event.get('rawPath', '')
        
        # 실행 시작
        if '/status/' in path:
            tool_name = 'workflow.status'
        elif '/monitor' in path:
            tool_name = 'workflow.monitor'
        elif '/trigger-fallback' in path:
            tool_name = 'workflow.fallback'
        else:
            tool_name = 'workflow.unknown'
        
        self.start_execution(session_id, tool_name)
        
        try:
            if http_method == 'GET' and '/status/' in path:
                result = self._get_workflow_status(session_id)
            elif http_method == 'POST' and path.endswith('/monitor'):
                result = self._monitor_workflow(event, session_id)
            elif http_method == 'POST' and path.endswith('/trigger-fallback'):
                result = self._trigger_fallback(event, session_id)
            elif http_method == 'POST' and path.endswith('/coordinate'):
                result = self._coordinate_agents(event, session_id)
            else:
                result = self.create_lambda_response(400, {"error": "Unsupported operation"})
            
            self.end_execution(status='success', result=result)
            return result
            
        except Exception as e:
            error_response = self.handle_error(e, f"Supervisor execution failed for {tool_name}")
            return self.create_lambda_response(500, error_response)
    
    def _get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """전체 워크플로 상태 반환 (GET /status/{id})"""
        try:
            # 세션 데이터 조회
            session_data = self.get_session_data(session_id)
            if not session_data:
                return self.create_lambda_response(404, {"error": "Session not found"})
            
            # Step Functions 실행 상태 조회
            workflow_status = self._get_stepfunctions_status(session_data)
            
            # 에이전트별 실행 상태 조회
            agent_statuses = self._get_agent_statuses(session_data)
            
            # 워크플로 건강성 체크
            health_status = self._check_workflow_health(session_data)
            
            # 상세 진행률 계산
            detailed_progress = self._calculate_detailed_progress(session_data)
            
            status_response = {
                "sessionId": session_id,
                "currentStep": session_data.get('currentStep', 1),
                "status": session_data.get('status', 'active'),
                "progress": detailed_progress,
                "workflowStatus": workflow_status,
                "agentStatuses": agent_statuses,
                "healthStatus": health_status,
                "createdAt": session_data.get('createdAt'),
                "updatedAt": session_data.get('updatedAt'),
                "estimatedTimeRemaining": self._estimate_time_remaining(session_data),
                "supervisorInfo": {
                    "lastCheckTime": datetime.utcnow().isoformat(),
                    "monitoringEnabled": True,
                    "autoRetryEnabled": self.enable_auto_retry
                }
            }
            
            return self.create_lambda_response(200, status_response)
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow status: {str(e)}")
            return self.create_lambda_response(500, {"error": "Failed to retrieve status"})
    
    def _monitor_workflow(self, event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """워크플로 모니터링 및 상태 업데이트"""
        try:
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            agent_id = body.get('agentId')
            status = body.get('status')
            result = body.get('result')
            latency_ms = body.get('latencyMs')
            
            if not agent_id or not status:
                return self.create_lambda_response(400, {"error": "Agent ID and status are required"})
            
            # 에이전트 상태 업데이트
            self._update_agent_status(session_id, agent_id, status, result, latency_ms)
            
            # 워크플로 상태 평가
            workflow_evaluation = self._evaluate_workflow_state(session_id)
            
            # 실패 감지 시 폴백 트리거
            if status == 'failed' or status == 'error':
                self._trigger_fallback_if_needed(session_id, agent_id, result)
            
            # 성공 시 다음 단계 진행 체크
            elif status == 'success':
                self._check_workflow_progression(session_id, agent_id)
            
            # 상태 브로드캐스트
            self.communication.broadcast_status({
                'sessionId': session_id,
                'agentId': agent_id,
                'status': status,
                'workflowEvaluation': workflow_evaluation,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return self.create_lambda_response(200, {
                "message": "Workflow monitoring completed",
                "agentStatus": status,
                "workflowEvaluation": workflow_evaluation
            })
            
        except Exception as e:
            self.logger.error(f"Failed to monitor workflow: {str(e)}")
            return self.create_lambda_response(500, {"error": "Failed to monitor workflow"})
    
    def _trigger_fallback(self, event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """실패 시 재시도/폴백 트리거"""
        try:
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            failed_agent = body.get('failedAgent')
            failure_reason = body.get('failureReason', 'Unknown error')
            retry_count = body.get('retryCount', 0)
            
            if not failed_agent:
                return self.create_lambda_response(400, {"error": "Failed agent ID is required"})
            
            # 폴백 전략 실행
            fallback_result = self._execute_fallback_strategy(session_id, failed_agent, failure_reason, retry_count)
            
            return self.create_lambda_response(200, fallback_result)
            
        except Exception as e:
            self.logger.error(f"Failed to trigger fallback: {str(e)}")
            return self.create_lambda_response(500, {"error": "Failed to trigger fallback"})
    
    def _coordinate_agents(self, event: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """에이전트 간 조정 및 통제"""
        try:
            body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
            coordination_type = body.get('type')  # 'start_next', 'pause_workflow', 'resume_workflow'
            target_agents = body.get('targetAgents', [])
            
            coordination_result = {}
            
            if coordination_type == 'start_next':
                coordination_result = self._start_next_workflow_step(session_id, target_agents)
            elif coordination_type == 'pause_workflow':
                coordination_result = self._pause_workflow(session_id)
            elif coordination_type == 'resume_workflow':
                coordination_result = self._resume_workflow(session_id)
            elif coordination_type == 'sync_agents':
                coordination_result = self._sync_agent_states(session_id, target_agents)
            else:
                return self.create_lambda_response(400, {"error": "Invalid coordination type"})
            
            return self.create_lambda_response(200, coordination_result)
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate agents: {str(e)}")
            return self.create_lambda_response(500, {"error": "Failed to coordinate agents"})
    
    @retry_with_backoff(max_retries=3)
    def _get_stepfunctions_status(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step Functions 실행 상태 조회"""
        try:
            workflow_status = {
                "expressWorkflow": {"status": "UNKNOWN", "executionArn": None},
                "standardWorkflow": {"status": "UNKNOWN", "executionArn": None}
            }
            
            # Express Workflow 상태 조회
            express_arn = session_data.get('expressExecutionArn')
            if express_arn:
                try:
                    response = self.stepfunctions.describe_execution(executionArn=express_arn)
                    workflow_status["expressWorkflow"] = {
                        "status": response['status'],
                        "executionArn": express_arn,
                        "startDate": response.get('startDate', '').isoformat() if response.get('startDate') else None,
                        "stopDate": response.get('stopDate', '').isoformat() if response.get('stopDate') else None
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get express workflow status: {str(e)}")
            
            # Standard Workflow 상태 조회
            standard_arn = session_data.get('standardExecutionArn')
            if standard_arn:
                try:
                    response = self.stepfunctions.describe_execution(executionArn=standard_arn)
                    workflow_status["standardWorkflow"] = {
                        "status": response['status'],
                        "executionArn": standard_arn,
                        "startDate": response.get('startDate', '').isoformat() if response.get('startDate') else None,
                        "stopDate": response.get('stopDate', '').isoformat() if response.get('stopDate') else None
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get standard workflow status: {str(e)}")
            
            return workflow_status
            
        except Exception as e:
            self.logger.error(f"Failed to get Step Functions status: {str(e)}")
            return {"error": "Failed to retrieve workflow status"}
    
    def _get_agent_statuses(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트별 실행 상태 조회"""
        agent_statuses = session_data.get('agentStatuses', {})
        
        # 기본 에이전트 상태 구조
        default_agents = {
            "productInsight": {"status": "pending", "lastUpdate": None, "latencyMs": None},
            "marketAnalyst": {"status": "pending", "lastUpdate": None, "latencyMs": None},
            "reporter": {"status": "pending", "lastUpdate": None, "latencyMs": None},
            "signboard": {"status": "pending", "lastUpdate": None, "latencyMs": None},
            "interior": {"status": "pending", "lastUpdate": None, "latencyMs": None},
            "reportGenerator": {"status": "pending", "lastUpdate": None, "latencyMs": None}
        }
        
        # 실제 상태로 업데이트
        for agent_name, default_status in default_agents.items():
            if agent_name in agent_statuses:
                agent_data = agent_statuses[agent_name]
                if isinstance(agent_data, dict):
                    default_status.update(agent_data)
                else:
                    default_status["status"] = agent_data
        
        return default_agents
    
    def _calculate_detailed_progress(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """상세 워크플로 진행률 계산"""
        current_step = session_data.get('currentStep', 1)
        total_steps = 5
        
        # 기본 진행률
        base_progress = (current_step - 1) / total_steps * 100
        
        # 현재 단계 내 세부 진행률
        step_progress = self._calculate_step_progress(session_data, current_step)
        
        # 전체 진행률 (현재 단계 세부 진행률 포함)
        detailed_progress = base_progress + (step_progress / total_steps)
        
        return {
            "overall": min(detailed_progress, 100.0),
            "currentStep": current_step,
            "stepProgress": step_progress,
            "stepName": self._get_step_name(current_step),
            "completedSteps": current_step - 1,
            "totalSteps": total_steps
        }
    
    def _calculate_step_progress(self, session_data: Dict[str, Any], current_step: int) -> float:
        """현재 단계 내 세부 진행률 계산"""
        agent_statuses = session_data.get('agentStatuses', {})
        
        if current_step == 1:  # Analysis step
            agents = ['productInsight', 'marketAnalyst']
        elif current_step == 2:  # Naming step
            agents = ['reporter']
        elif current_step == 3:  # Signboard step
            agents = ['signboard']
        elif current_step == 4:  # Interior step
            agents = ['interior']
        elif current_step == 5:  # Report step
            agents = ['reportGenerator']
        else:
            return 0.0
        
        completed_agents = 0
        for agent in agents:
            agent_status = agent_statuses.get(agent, {})
            if isinstance(agent_status, dict):
                status = agent_status.get('status', 'pending')
            else:
                status = agent_status
            
            if status in ['success', 'completed']:
                completed_agents += 1
        
        return (completed_agents / len(agents)) * 100 if agents else 0.0
    
    def _get_step_name(self, step: int) -> str:
        """단계 이름 반환"""
        step_names = {
            1: "Business Analysis",
            2: "Name Generation",
            3: "Signboard Design",
            4: "Interior Design",
            5: "Report Generation"
        }
        return step_names.get(step, "Unknown Step")
    
    def _estimate_time_remaining(self, session_data: Dict[str, Any]) -> Optional[int]:
        """남은 예상 시간 계산 (초)"""
        current_step = session_data.get('currentStep', 1)
        if current_step >= 5:
            return 0
        
        # 단계별 예상 시간 (초) - 에이전트 기반으로 조정
        step_times = {
            1: 30,   # Analysis (Product Insight + Market Analyst)
            2: 30,   # Naming (Reporter)
            3: 180,  # Signboard (병렬 AI 모델 호출)
            4: 180,  # Interior (병렬 AI 모델 호출)
            5: 60    # Report (PDF 생성)
        }
        
        # 현재 단계의 진행률을 고려한 남은 시간
        step_progress = self._calculate_step_progress(session_data, current_step)
        current_step_remaining = step_times.get(current_step, 0) * (1 - step_progress / 100)
        
        # 다음 단계들의 예상 시간
        future_steps_time = sum(step_times[i] for i in range(current_step + 1, 6))
        
        return int(current_step_remaining + future_steps_time)
    
    def _check_workflow_health(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로 건강성 체크"""
        health_status = {
            "overall": "healthy",
            "issues": [],
            "warnings": [],
            "lastHealthCheck": datetime.utcnow().isoformat()
        }
        
        # 세션 만료 체크
        ttl = session_data.get('ttl', 0)
        if datetime.utcnow().timestamp() > ttl:
            health_status["overall"] = "expired"
            health_status["issues"].append("Session has expired")
        
        # 워크플로 실행 시간 체크
        created_at = session_data.get('createdAt')
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                duration = (datetime.utcnow() - created_time).total_seconds()
                
                if duration > self.max_workflow_duration:
                    health_status["overall"] = "timeout"
                    health_status["issues"].append(f"Workflow duration exceeded {self.max_workflow_duration} seconds")
                elif duration > self.max_workflow_duration * 0.8:
                    health_status["warnings"].append("Workflow approaching timeout")
            except Exception as e:
                health_status["warnings"].append(f"Failed to parse creation time: {str(e)}")
        
        # 에이전트 상태 체크
        agent_statuses = session_data.get('agentStatuses', {})
        failed_agents = []
        for agent_name, status_data in agent_statuses.items():
            if isinstance(status_data, dict):
                status = status_data.get('status', 'pending')
            else:
                status = status_data
            
            if status in ['failed', 'error', 'timeout']:
                failed_agents.append(agent_name)
        
        if failed_agents:
            health_status["overall"] = "degraded"
            health_status["issues"].append(f"Failed agents: {', '.join(failed_agents)}")
        
        return health_status
    
    def _update_agent_status(self, session_id: str, agent_id: str, status: str, 
                           result: Any = None, latency_ms: int = None):
        """에이전트 상태 업데이트"""
        try:
            status_data = {
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'lastUpdate': datetime.utcnow().isoformat()
            }
            
            if result is not None:
                status_data['result'] = result
            
            if latency_ms is not None:
                status_data['latencyMs'] = latency_ms
            
            # DynamoDB 업데이트
            update_success = self.update_session_data(session_id, {
                f'agentStatuses.{agent_id}': status_data
            })
            
            if update_success:
                self.logger.info(f"Agent status updated: {agent_id} -> {status}")
            else:
                self.logger.error(f"Failed to update agent status: {agent_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update agent status: {str(e)}")
    
    def _evaluate_workflow_state(self, session_id: str) -> Dict[str, Any]:
        """워크플로 상태 평가"""
        session_data = self.get_session_data(session_id)
        if not session_data:
            return {"status": "error", "message": "Session not found"}
        
        current_step = session_data.get('currentStep', 1)
        agent_statuses = session_data.get('agentStatuses', {})
        
        evaluation = {
            "canProceed": False,
            "blockedBy": [],
            "readyAgents": [],
            "failedAgents": [],
            "nextAction": "wait"
        }
        
        # 현재 단계의 필수 에이전트 확인
        required_agents = self._get_required_agents_for_step(current_step)
        
        for agent in required_agents:
            agent_status = agent_statuses.get(agent, {})
            status = agent_status.get('status', 'pending') if isinstance(agent_status, dict) else agent_status
            
            if status in ['success', 'completed']:
                evaluation["readyAgents"].append(agent)
            elif status in ['failed', 'error', 'timeout']:
                evaluation["failedAgents"].append(agent)
                evaluation["blockedBy"].append(agent)
            else:
                evaluation["blockedBy"].append(agent)
        
        # 진행 가능 여부 결정
        if not evaluation["blockedBy"]:
            evaluation["canProceed"] = True
            evaluation["nextAction"] = "proceed"
        elif evaluation["failedAgents"] and self.enable_auto_retry:
            evaluation["nextAction"] = "retry"
        
        return evaluation
    
    def _get_required_agents_for_step(self, step: int) -> List[str]:
        """단계별 필수 에이전트 목록"""
        step_agents = {
            1: ['productInsight', 'marketAnalyst'],
            2: ['reporter'],
            3: ['signboard'],
            4: ['interior'],
            5: ['reportGenerator']
        }
        return step_agents.get(step, [])
    
    def _trigger_fallback_if_needed(self, session_id: str, failed_agent: str, result: Any = None):
        """필요시 폴백 메커니즘 트리거"""
        self.logger.warning(f"Agent {failed_agent} failed for session {session_id}, evaluating fallback options")
        
        # 폴백 전략 결정
        fallback_strategy = self._determine_fallback_strategy(failed_agent, result)
        
        if fallback_strategy['action'] == 'retry' and self.enable_auto_retry:
            self._schedule_agent_retry(session_id, failed_agent, fallback_strategy)
        elif fallback_strategy['action'] == 'fallback':
            self._execute_fallback_strategy(session_id, failed_agent, str(result), 0)
        else:
            self.logger.info(f"No fallback action needed for {failed_agent}")
    
    def _determine_fallback_strategy(self, failed_agent: str, result: Any) -> Dict[str, Any]:
        """폴백 전략 결정"""
        # 에이전트별 폴백 전략
        fallback_strategies = {
            'productInsight': {'action': 'fallback', 'fallback_data': 'cached_analysis'},
            'marketAnalyst': {'action': 'fallback', 'fallback_data': 'default_market_data'},
            'reporter': {'action': 'retry', 'max_retries': 2},
            'signboard': {'action': 'fallback', 'fallback_data': 'default_signboard_images'},
            'interior': {'action': 'fallback', 'fallback_data': 'default_interior_images'},
            'reportGenerator': {'action': 'retry', 'max_retries': 1}
        }
        
        return fallback_strategies.get(failed_agent, {'action': 'none'})
    
    def _execute_fallback_strategy(self, session_id: str, failed_agent: str, 
                                 failure_reason: str, retry_count: int) -> Dict[str, Any]:
        """폴백 전략 실행"""
        try:
            fallback_strategy = self._determine_fallback_strategy(failed_agent, failure_reason)
            
            if fallback_strategy['action'] == 'fallback':
                # 폴백 데이터 적용
                fallback_result = self._apply_fallback_data(session_id, failed_agent, fallback_strategy)
                
                self.logger.info(f"Fallback executed for {failed_agent}: {fallback_result}")
                
                return {
                    "message": f"Fallback executed for {failed_agent}",
                    "strategy": fallback_strategy,
                    "result": fallback_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif fallback_strategy['action'] == 'retry':
                max_retries = fallback_strategy.get('max_retries', 1)
                if retry_count < max_retries:
                    # 재시도 스케줄링
                    retry_result = self._schedule_agent_retry(session_id, failed_agent, fallback_strategy)
                    return {
                        "message": f"Retry scheduled for {failed_agent}",
                        "retryCount": retry_count + 1,
                        "maxRetries": max_retries,
                        "result": retry_result
                    }
                else:
                    # 최대 재시도 초과, 폴백으로 전환
                    return self._execute_fallback_strategy(session_id, failed_agent, failure_reason, 0)
            
            else:
                return {"message": f"No fallback strategy available for {failed_agent}"}
                
        except Exception as e:
            self.logger.error(f"Failed to execute fallback strategy: {str(e)}")
            return {"error": f"Fallback execution failed: {str(e)}"}
    
    def _apply_fallback_data(self, session_id: str, failed_agent: str, 
                           fallback_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """폴백 데이터 적용"""
        fallback_data_type = fallback_strategy.get('fallback_data')
        
        # 에이전트별 폴백 데이터 로직
        if failed_agent == 'productInsight' and fallback_data_type == 'cached_analysis':
            fallback_data = {
                "summary": "기본 비즈니스 분석 결과",
                "score": 75.0,
                "insights": ["일반적인 업종 특성", "지역별 시장 현황"],
                "is_fallback": True
            }
        elif failed_agent == 'signboard' and fallback_data_type == 'default_signboard_images':
            fallback_data = {
                "images": [
                    {"url": "fallbacks/signs/default-sign-1.jpg", "provider": "fallback", "is_fallback": True},
                    {"url": "fallbacks/signs/default-sign-2.jpg", "provider": "fallback", "is_fallback": True},
                    {"url": "fallbacks/signs/default-sign-3.jpg", "provider": "fallback", "is_fallback": True}
                ]
            }
        else:
            fallback_data = {"message": "Default fallback data", "is_fallback": True}
        
        # 세션에 폴백 데이터 저장
        self.update_session_data(session_id, {
            f'{failed_agent}_result': fallback_data,
            f'{failed_agent}_fallback_applied': True
        })
        
        return fallback_data
    
    def _schedule_agent_retry(self, session_id: str, failed_agent: str, 
                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 재시도 스케줄링"""
        # 실제 구현에서는 SQS나 EventBridge를 통한 지연 실행
        self.logger.info(f"Scheduling retry for agent {failed_agent}")
        
        # 재시도 카운트 업데이트
        retry_count_key = f'{failed_agent}_retry_count'
        session_data = self.get_session_data(session_id)
        current_retry_count = session_data.get(retry_count_key, 0)
        
        self.update_session_data(session_id, {
            retry_count_key: current_retry_count + 1,
            f'{failed_agent}_last_retry': datetime.utcnow().isoformat()
        })
        
        return {"scheduled": True, "retryCount": current_retry_count + 1}
    
    def _check_workflow_progression(self, session_id: str, completed_agent: str):
        """워크플로 진행 체크 및 다음 단계 트리거"""
        evaluation = self._evaluate_workflow_state(session_id)
        
        if evaluation["canProceed"]:
            self.logger.info(f"Workflow can proceed after {completed_agent} completion")
            # 다음 단계로 진행 로직 (실제로는 Step Functions 트리거)
            self._advance_workflow_step(session_id)
    
    def _advance_workflow_step(self, session_id: str):
        """워크플로 다음 단계로 진행"""
        session_data = self.get_session_data(session_id)
        current_step = session_data.get('currentStep', 1)
        
        if current_step < 5:
            next_step = current_step + 1
            self.update_session_data(session_id, {'currentStep': next_step})
            self.logger.info(f"Advanced workflow to step {next_step} for session {session_id}")
    
    def _start_next_workflow_step(self, session_id: str, target_agents: List[str]) -> Dict[str, Any]:
        """다음 워크플로 단계 시작"""
        # Step Functions 실행 트리거 로직
        return {"message": "Next workflow step started", "targetAgents": target_agents}
    
    def _pause_workflow(self, session_id: str) -> Dict[str, Any]:
        """워크플로 일시정지"""
        self.update_session_data(session_id, {'status': 'paused'})
        return {"message": "Workflow paused", "sessionId": session_id}
    
    def _resume_workflow(self, session_id: str) -> Dict[str, Any]:
        """워크플로 재개"""
        self.update_session_data(session_id, {'status': 'active'})
        return {"message": "Workflow resumed", "sessionId": session_id}
    
    def _sync_agent_states(self, session_id: str, target_agents: List[str]) -> Dict[str, Any]:
        """에이전트 상태 동기화"""
        sync_results = {}
        for agent in target_agents:
            # 에이전트 상태 동기화 로직
            sync_results[agent] = "synced"
        
        return {"message": "Agent states synchronized", "results": sync_results}

# Lambda 핸들러
supervisor_agent = SupervisorAgent()

def lambda_handler(event, context):
    """Lambda 진입점"""
    return supervisor_agent.lambda_handler(event, context)