# Agent Communication Interface
# Agent 간 메시지 전송, Supervisor Agent 상태 브로드캐스트
# Enhanced with Bedrock AgentCore Tool Use primitive support

import json
import boto3
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
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
        
        # AgentCore Tool Use configuration
        self.use_agentcore = os.getenv('USE_AGENTCORE', 'false').lower() == 'true'
        self.bedrock_agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.bedrock_agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        
    def _get_aws_clients(self):
        """AWS 클라이언트 초기화"""
        if self.environment == 'local':
            return {
                'sqs': boto3.client('sqs', endpoint_url='http://localhost:9324'),
                'sns': boto3.client('sns', endpoint_url='http://localhost:4566'),
                'dynamodb': boto3.resource('dynamodb', endpoint_url='http://localhost:8000'),
                'bedrock_agent_runtime': boto3.client('bedrock-agent-runtime')  # No local endpoint
            }
        else:
            return {
                'sqs': boto3.client('sqs'),
                'sns': boto3.client('sns'),
                'dynamodb': boto3.resource('dynamodb'),
                'bedrock_agent_runtime': boto3.client('bedrock-agent-runtime')
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
    
    # ========================================================================
    # AgentCore Tool Use Primitive Implementation (Requirement 2.2, 2.3)
    # ========================================================================
    
    def invoke_agent_with_tool(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Invoke agent using AgentCore Tool Use primitive.
        
        This implements the Tool Use primitive by treating each agent
        as a tool that can be invoked with structured input/output.
        
        Tool Schema:
        - Tool name: "invoke_agent"
        - Input schema: {agent_name, input_data, session_id}
        - Output schema: {result, status, latency_ms}
        
        Args:
            agent_name: Name of agent to invoke (e.g., "reporter", "signboard")
            input_data: Input data for agent execution
            session_id: Session ID for tracking and context
            timeout: Maximum execution time in seconds
        
        Returns:
            Dict with:
                - result: Agent execution result
                - status: 'success', 'error', or 'timeout'
                - latency_ms: Execution time in milliseconds
                - agent_name: Name of invoked agent
                - session_id: Session ID
                - timestamp: ISO timestamp
        
        Raises:
            ValueError: If agent_name is invalid
            TimeoutError: If execution exceeds timeout
        """
        start_time = time.time()
        
        try:
            # Validate agent name
            valid_agents = [
                'supervisor', 'product_insight', 'market_analyst',
                'reporter', 'signboard', 'interior', 'report_generator'
            ]
            
            if agent_name not in valid_agents:
                raise ValueError(
                    f"Invalid agent name: {agent_name}. "
                    f"Valid agents: {', '.join(valid_agents)}"
                )
            
            self.logger.info(
                f"Tool Use: Invoking agent '{agent_name}' "
                f"(session={session_id}, use_agentcore={self.use_agentcore})"
            )
            
            # Define tool invocation schema
            tool_invocation = {
                'tool_name': 'invoke_agent',
                'tool_version': '1.0',
                'input_schema': {
                    'agent_name': agent_name,
                    'input_data': input_data,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'output_schema': {
                    'result': None,
                    'status': 'pending',
                    'latency_ms': 0
                }
            }
            
            # Execute agent invocation
            if self.use_agentcore and self.bedrock_agent_id:
                # Use Bedrock AgentCore for invocation
                result = self._invoke_via_agentcore(
                    agent_name=agent_name,
                    input_data=input_data,
                    session_id=session_id,
                    timeout=timeout
                )
            else:
                # Fallback to direct Lambda invocation
                result = self._invoke_via_lambda(
                    agent_name=agent_name,
                    input_data=input_data,
                    session_id=session_id,
                    timeout=timeout
                )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build tool output
            tool_output = {
                'result': result,
                'status': 'success',
                'latency_ms': latency_ms,
                'agent_name': agent_name,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'invocation_method': 'agentcore' if self.use_agentcore else 'lambda'
            }
            
            # Log tool execution
            self._log_tool_execution(
                tool_name='invoke_agent',
                agent_name=agent_name,
                session_id=session_id,
                latency_ms=latency_ms,
                status='success'
            )
            
            self.logger.info(
                f"Tool Use: Agent '{agent_name}' invoked successfully "
                f"(latency_ms={latency_ms})"
            )
            
            return tool_output
            
        except TimeoutError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Tool Use: Agent '{agent_name}' timed out "
                f"(timeout={timeout}s, latency_ms={latency_ms})"
            )
            
            return {
                'result': None,
                'status': 'timeout',
                'latency_ms': latency_ms,
                'agent_name': agent_name,
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Tool Use: Agent '{agent_name}' failed: {str(e)} "
                f"(latency_ms={latency_ms})"
            )
            
            # Log tool execution failure
            self._log_tool_execution(
                tool_name='invoke_agent',
                agent_name=agent_name,
                session_id=session_id,
                latency_ms=latency_ms,
                status='error',
                error_message=str(e)
            )
            
            return {
                'result': None,
                'status': 'error',
                'latency_ms': latency_ms,
                'agent_name': agent_name,
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _invoke_via_agentcore(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        session_id: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Invoke agent via Bedrock AgentCore.
        
        This uses the Bedrock Agent Runtime API to invoke agents
        through the AgentCore orchestration layer.
        
        Args:
            agent_name: Name of agent to invoke
            input_data: Input data for agent
            session_id: Session ID
            timeout: Timeout in seconds
        
        Returns:
            Agent execution result
        """
        try:
            # Build AgentCore invocation request
            request = {
                'agentId': self.bedrock_agent_id,
                'agentAliasId': self.bedrock_agent_alias_id,
                'sessionId': session_id or f"session-{datetime.utcnow().timestamp()}",
                'inputText': json.dumps({
                    'action': 'invoke_agent',
                    'agent_name': agent_name,
                    'input_data': input_data
                })
            }
            
            self.logger.info(
                f"AgentCore: Invoking agent '{agent_name}' via Bedrock "
                f"(agent_id={self.bedrock_agent_id})"
            )
            
            # Invoke Bedrock Agent
            response = self.aws_clients['bedrock_agent_runtime'].invoke_agent(**request)
            
            # Parse streaming response
            result_text = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result_text += chunk['bytes'].decode('utf-8')
            
            # Parse result
            try:
                result = json.loads(result_text) if result_text else {}
            except json.JSONDecodeError:
                result = {'text': result_text}
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"AgentCore invocation failed for '{agent_name}': {str(e)}"
            )
            raise
    
    def _invoke_via_lambda(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        session_id: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Invoke agent via direct Lambda invocation (fallback).
        
        Args:
            agent_name: Name of agent to invoke
            input_data: Input data for agent
            session_id: Session ID
            timeout: Timeout in seconds
        
        Returns:
            Agent execution result
        """
        try:
            # Get Lambda function name from environment
            function_name = os.getenv(
                f'{agent_name.upper()}_FUNCTION_NAME',
                f'branding-chatbot-{agent_name}-{self.environment}'
            )
            
            self.logger.info(
                f"Lambda: Invoking agent '{agent_name}' "
                f"(function={function_name})"
            )
            
            # Build Lambda payload
            payload = {
                'action': 'execute',
                'agent_name': agent_name,
                'input_data': input_data,
                'session_id': session_id
            }
            
            # Invoke Lambda function
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            # Check for Lambda errors
            if 'FunctionError' in response:
                raise Exception(
                    f"Lambda function error: {response_payload.get('errorMessage')}"
                )
            
            return response_payload
            
        except Exception as e:
            self.logger.error(
                f"Lambda invocation failed for '{agent_name}': {str(e)}"
            )
            raise
    
    def parse_tool_result(
        self,
        tool_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse and validate tool execution result.
        
        This ensures the tool output conforms to the expected schema
        and extracts key information for downstream processing.
        
        Args:
            tool_output: Raw tool execution output
        
        Returns:
            Parsed and validated result with:
                - success: Boolean indicating success
                - data: Extracted result data
                - error: Error message if failed
                - metadata: Additional metadata
        """
        try:
            # Validate required fields
            required_fields = ['status', 'agent_name', 'latency_ms']
            missing_fields = [
                field for field in required_fields
                if field not in tool_output
            ]
            
            if missing_fields:
                raise ValueError(
                    f"Tool output missing required fields: {', '.join(missing_fields)}"
                )
            
            # Extract status
            status = tool_output.get('status')
            success = status == 'success'
            
            # Extract result data
            result_data = tool_output.get('result', {})
            
            # Build parsed result
            parsed = {
                'success': success,
                'data': result_data,
                'error': tool_output.get('error'),
                'metadata': {
                    'agent_name': tool_output.get('agent_name'),
                    'session_id': tool_output.get('session_id'),
                    'latency_ms': tool_output.get('latency_ms'),
                    'timestamp': tool_output.get('timestamp'),
                    'invocation_method': tool_output.get('invocation_method')
                }
            }
            
            self.logger.info(
                f"Tool result parsed: agent={parsed['metadata']['agent_name']}, "
                f"success={success}, latency_ms={parsed['metadata']['latency_ms']}"
            )
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Failed to parse tool result: {str(e)}")
            
            return {
                'success': False,
                'data': None,
                'error': f"Tool result parsing failed: {str(e)}",
                'metadata': {}
            }
    
    def handle_tool_error(
        self,
        tool_output: Dict[str, Any],
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Handle tool execution errors with retry logic.
        
        Args:
            tool_output: Failed tool execution output
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
        
        Returns:
            Dict with error handling decision:
                - should_retry: Boolean
                - retry_delay: Delay before retry (seconds)
                - fallback_action: Alternative action if retries exhausted
        """
        try:
            status = tool_output.get('status')
            error = tool_output.get('error', '')
            agent_name = tool_output.get('agent_name')
            
            self.logger.warning(
                f"Tool error for agent '{agent_name}': status={status}, "
                f"error={error}, retry_count={retry_count}/{max_retries}"
            )
            
            # Determine if error is retryable
            retryable_errors = [
                'timeout', 'throttling', 'service_unavailable',
                'connection_error', 'temporary_failure'
            ]
            
            is_retryable = (
                status in ['timeout', 'error'] and
                any(err_type in error.lower() for err_type in retryable_errors)
            )
            
            should_retry = is_retryable and retry_count < max_retries
            
            # Calculate retry delay (exponential backoff)
            retry_delay = 2 ** retry_count if should_retry else 0
            
            # Determine fallback action
            if not should_retry:
                if retry_count >= max_retries:
                    fallback_action = 'use_cached_result'
                elif status == 'timeout':
                    fallback_action = 'skip_agent'
                else:
                    fallback_action = 'request_human_intervention'
            else:
                fallback_action = None
            
            decision = {
                'should_retry': should_retry,
                'retry_delay': retry_delay,
                'fallback_action': fallback_action,
                'retry_count': retry_count,
                'max_retries': max_retries,
                'error_type': status,
                'is_retryable': is_retryable
            }
            
            self.logger.info(
                f"Tool error handling decision: should_retry={should_retry}, "
                f"retry_delay={retry_delay}s, fallback_action={fallback_action}"
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Failed to handle tool error: {str(e)}")
            
            return {
                'should_retry': False,
                'retry_delay': 0,
                'fallback_action': 'request_human_intervention',
                'error': str(e)
            }
    
    def _log_tool_execution(
        self,
        tool_name: str,
        agent_name: str,
        session_id: Optional[str],
        latency_ms: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log tool execution with structured data.
        
        Args:
            tool_name: Name of tool executed
            agent_name: Name of agent invoked
            session_id: Session ID
            latency_ms: Execution latency
            status: 'success' or 'error'
            error_message: Error message if failed
        """
        log_data = {
            'tool_execution': tool_name,
            'agent_name': agent_name,
            'session_id': session_id,
            'latency_ms': latency_ms,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'use_agentcore': self.use_agentcore
        }
        
        if error_message:
            log_data['error_message'] = error_message
        
        if status == 'error':
            self.logger.error(f"Tool execution failed: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Tool execution succeeded: {json.dumps(log_data)}")

# 전역 인스턴스 (Lambda 재사용을 위해)
_agent_comm_instance = None

def get_agent_communication() -> AgentCommunication:
    """AgentCommunication 싱글톤 인스턴스 반환"""
    global _agent_comm_instance
    if _agent_comm_instance is None:
        _agent_comm_instance = AgentCommunication()
    return _agent_comm_instance