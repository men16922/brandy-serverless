# Agent Communication Interface
# Agent 간 메시지 전송, Supervisor Agent 상태 브로드캐스트

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

class AgentCommunication:
    """Agent 간 통신을 위한 인터페이스"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'local')
        self.aws_clients = self._get_aws_clients()
        self.logger = logging.getLogger(__name__)
        
        # Agent 통신용 SQS 큐 (환경별)
        self.supervisor_queue_url = os.getenv('SUPERVISOR_QUEUE_URL')
        self.agent_communication_topic = os.getenv('AGENT_COMMUNICATION_TOPIC')
        
    def _get_aws_clients(self):
        """AWS 클라이언트 초기화"""
        if self.environment == 'local':
            return {
                'sqs': boto3.client('sqs', endpoint_url='http://localhost:9324'),
                'sns': boto3.client('sns', endpoint_url='http://localhost:4566'),
                'dynamodb': boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
            }
        else:
            return {
                'sqs': boto3.client('sqs'),
                'sns': boto3.client('sns'),
                'dynamodb': boto3.resource('dynamodb')
            }
    
    def send_to_supervisor(self, agent_id: str, status: str, result: Any, session_id: str = None):
        """Supervisor Agent로 상태 전송"""
        try:
            message = {
                'agentId': agent_id,
                'status': status,
                'result': result,
                'sessionId': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'messageType': 'agent_status_update'
            }
            
            if self.supervisor_queue_url:
                # SQS를 통한 비동기 메시지 전송
                self.aws_clients['sqs'].send_message(
                    QueueUrl=self.supervisor_queue_url,
                    MessageBody=json.dumps(message, ensure_ascii=False),
                    MessageAttributes={
                        'AgentId': {
                            'StringValue': agent_id,
                            'DataType': 'String'
                        },
                        'Status': {
                            'StringValue': status,
                            'DataType': 'String'
                        }
                    }
                )
                
                self.logger.info(f"Status sent to Supervisor: {agent_id} -> {status}")
            else:
                # 로컬 환경에서는 로그로만 처리
                self.logger.info(f"[LOCAL] Agent status: {agent_id} -> {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to send status to Supervisor: {str(e)}")
    
    def request_from_agent(self, target_agent: str, request: Dict[str, Any], 
                          source_agent: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """다른 Agent에게 요청"""
        try:
            message = {
                'targetAgent': target_agent,
                'sourceAgent': source_agent,
                'request': request,
                'sessionId': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'messageType': 'agent_request'
            }
            
            if self.agent_communication_topic:
                # SNS를 통한 Agent 간 통신
                self.aws_clients['sns'].publish(
                    TopicArn=self.agent_communication_topic,
                    Message=json.dumps(message, ensure_ascii=False),
                    MessageAttributes={
                        'TargetAgent': {
                            'StringValue': target_agent,
                            'DataType': 'String'
                        },
                        'SourceAgent': {
                            'StringValue': source_agent,
                            'DataType': 'String'
                        }
                    }
                )
                
                self.logger.info(f"Request sent: {source_agent} -> {target_agent}")
            else:
                # 로컬 환경에서는 로그로만 처리
                self.logger.info(f"[LOCAL] Agent request: {source_agent} -> {target_agent}")
                
        except Exception as e:
            self.logger.error(f"Failed to send request to agent: {str(e)}")
            return None
    
    def broadcast_status(self, workflow_status: Dict[str, Any], source_agent: str = "supervisor"):
        """전체 워크플로 상태 브로드캐스트"""
        try:
            message = {
                'workflowStatus': workflow_status,
                'sourceAgent': source_agent,
                'timestamp': datetime.utcnow().isoformat(),
                'messageType': 'workflow_status_broadcast'
            }
            
            if self.agent_communication_topic:
                # SNS를 통한 브로드캐스트
                self.aws_clients['sns'].publish(
                    TopicArn=self.agent_communication_topic,
                    Message=json.dumps(message, ensure_ascii=False),
                    MessageAttributes={
                        'MessageType': {
                            'StringValue': 'workflow_status_broadcast',
                            'DataType': 'String'
                        },
                        'SourceAgent': {
                            'StringValue': source_agent,
                            'DataType': 'String'
                        }
                    }
                )
                
                self.logger.info(f"Workflow status broadcasted by {source_agent}")
            else:
                # 로컬 환경에서는 로그로만 처리
                self.logger.info(f"[LOCAL] Workflow status broadcast by {source_agent}")
                
        except Exception as e:
            self.logger.error(f"Failed to broadcast workflow status: {str(e)}")
    
    def log_agent_interaction(self, source_agent: str, target_agent: str, 
                            interaction_type: str, session_id: str = None, 
                            latency_ms: int = None, status: str = "success"):
        """Agent 간 상호작용 로깅"""
        try:
            # DynamoDB에 Agent 상호작용 로그 저장
            interactions_table = self.aws_clients['dynamodb'].Table(
                os.getenv('AGENT_INTERACTIONS_TABLE', 'agent-interactions')
            )
            
            log_entry = {
                'interactionId': f"{source_agent}-{target_agent}-{datetime.utcnow().isoformat()}",
                'sourceAgent': source_agent,
                'targetAgent': target_agent,
                'interactionType': interaction_type,
                'sessionId': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'latencyMs': latency_ms,
                'status': status,
                'ttl': int((datetime.utcnow().timestamp() + 86400 * 7))  # 7일 후 만료
            }
            
            interactions_table.put_item(Item=log_entry)
            
        except Exception as e:
            self.logger.error(f"Failed to log agent interaction: {str(e)}")
    
    def get_agent_status(self, agent_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """특정 Agent의 현재 상태 조회"""
        try:
            sessions_table = self.aws_clients['dynamodb'].Table(
                os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local')
            )
            
            response = sessions_table.get_item(Key={'sessionId': session_id})
            
            if 'Item' in response:
                agent_statuses = response['Item'].get('agentStatuses', {})
                return agent_statuses.get(agent_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get agent status: {str(e)}")
            return None
    
    def update_agent_status(self, agent_id: str, session_id: str, status: str, 
                          result: Any = None, latency_ms: int = None):
        """Agent 상태 업데이트"""
        try:
            sessions_table = self.aws_clients['dynamodb'].Table(
                os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local')
            )
            
            update_data = {
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if result is not None:
                update_data['result'] = result
            
            if latency_ms is not None:
                update_data['latencyMs'] = latency_ms
            
            sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET agentStatuses.#agent = :status_data, updatedAt = :timestamp',
                ExpressionAttributeNames={'#agent': agent_id},
                ExpressionAttributeValues={
                    ':status_data': update_data,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update agent status: {str(e)}")

# 전역 인스턴스 (Lambda 재사용을 위해)
_agent_comm_instance = None

def get_agent_communication() -> AgentCommunication:
    """AgentCommunication 싱글톤 인스턴스 반환"""
    global _agent_comm_instance
    if _agent_comm_instance is None:
        _agent_comm_instance = AgentCommunication()
    return _agent_comm_instance