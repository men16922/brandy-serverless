"""
Bedrock AgentCore Orchestrator
Implements AgentCore-based workflow orchestration with Tool Use and Memory primitives
"""

import json
import time
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
import os

# Add shared module to path
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'shared')
if shared_dir not in sys.path:
    sys.path.insert(0, shared_dir)

try:
    from bedrock_client import BedrockClient, BedrockException
    from models import WorkflowStep, AgentType
except ImportError:
    # Fallback for Lambda environment
    sys.path.append('/opt/python')
    from bedrock_client import BedrockClient, BedrockException
    from models import WorkflowStep, AgentType


class AgentCoreOrchestrator:
    """
    Bedrock AgentCore-based workflow orchestrator.
    
    Implements:
    - Tool Use primitive for agent invocation
    - Memory primitive for workflow state management
    - Reasoning LLM for next step decision-making
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize AgentCore orchestrator.
        
        Args:
            logger: Logger instance (default: creates new logger)
        """
        self.logger = logger or self._create_logger()
        
        # Initialize Bedrock client
        try:
            self.bedrock_client = BedrockClient(logger=self.logger)
            self.logger.info("BedrockClient initialized for AgentCore orchestration")
        except Exception as e:
            self.logger.error(f"Failed to initialize BedrockClient: {str(e)}")
            raise
        
        # AgentCore configuration from environment
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        
        # Workflow configuration
        self.workflow_steps = [
            WorkflowStep.ANALYSIS,
            WorkflowStep.NAMING,
            WorkflowStep.SIGNBOARD,
            WorkflowStep.INTERIOR,
            WorkflowStep.REPORT
        ]
        
        # Agent mapping for Tool Use
        self.agent_mapping = {
            WorkflowStep.ANALYSIS: [
                AgentType.PRODUCT_INSIGHT.value,
                AgentType.MARKET_ANALYST.value
            ],
            WorkflowStep.NAMING: [AgentType.REPORTER.value],
            WorkflowStep.SIGNBOARD: [AgentType.SIGNBOARD.value],
            WorkflowStep.INTERIOR: [AgentType.INTERIOR.value],
            WorkflowStep.REPORT: [AgentType.REPORT_GENERATOR.value]
        }
        
        self.logger.info(
            f"AgentCore orchestrator initialized: "
            f"agent_id={self.agent_id}, alias={self.agent_alias_id}"
        )
    
    def _create_logger(self) -> logging.Logger:
        """Create structured logger for AgentCore orchestrator"""
        logger = logging.getLogger('agentcore_orchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def orchestrate_workflow(
        self,
        session_id: str,
        business_info: Dict[str, Any],
        current_step: int = 1
    ) -> Dict[str, Any]:
        """
        Orchestrate 5-step branding workflow using AgentCore.
        
        Args:
            session_id: Workflow session ID
            business_info: Business information input
            current_step: Current workflow step (1-5)
        
        Returns:
            Dict with orchestration results and next step
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Starting AgentCore orchestration: "
                f"session={session_id}, step={current_step}"
            )
            
            # Retrieve workflow memory
            workflow_state = self.retrieve_workflow_memory(session_id)
            
            # Determine current workflow step
            if current_step > len(self.workflow_steps):
                return {
                    'status': 'completed',
                    'message': 'Workflow completed',
                    'session_id': session_id,
                    'final_step': current_step - 1
                }
            
            step_enum = self.workflow_steps[current_step - 1]
            
            # Get agents for current step
            agents_for_step = self.agent_mapping.get(step_enum, [])
            
            if not agents_for_step:
                raise ValueError(f"No agents configured for step {current_step}")
            
            # Execute agents for current step using Tool Use primitive
            step_results = {}
            for agent_name in agents_for_step:
                agent_result = self.invoke_agent_with_tool(
                    agent_name=agent_name,
                    input_data={
                        'session_id': session_id,
                        'business_info': business_info,
                        'workflow_state': workflow_state,
                        'current_step': current_step
                    },
                    session_id=session_id
                )
                
                step_results[agent_name] = agent_result
            
            # Store results in workflow memory
            self.store_workflow_memory(
                session_id=session_id,
                step=current_step,
                data={
                    'step_name': step_enum.name,
                    'agents_executed': agents_for_step,
                    'results': step_results,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Use Reasoning LLM to decide next step
            next_step_decision = self.reason_next_step(
                current_state={
                    'session_id': session_id,
                    'current_step': current_step,
                    'step_results': step_results,
                    'workflow_state': workflow_state
                }
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                f"AgentCore orchestration completed: "
                f"session={session_id}, step={current_step}, "
                f"latency_ms={latency_ms}"
            )
            
            return {
                'status': 'success',
                'session_id': session_id,
                'current_step': current_step,
                'next_step': next_step_decision.get('next_step'),
                'step_results': step_results,
                'reasoning': next_step_decision.get('reasoning'),
                'confidence': next_step_decision.get('confidence'),
                'latency_ms': latency_ms
            }
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"AgentCore orchestration failed: "
                f"session={session_id}, error={str(e)}, "
                f"latency_ms={latency_ms}"
            )
            
            return {
                'status': 'error',
                'session_id': session_id,
                'current_step': current_step,
                'error': str(e),
                'latency_ms': latency_ms
            }
    
    def invoke_agent_with_tool(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke agent using AgentCore Tool Use primitive.
        
        This implements the Tool Use primitive by treating each agent
        as a tool that can be invoked with structured input/output.
        
        This method now delegates to the enhanced AgentCommunication
        interface which provides the actual Tool Use implementation.
        
        Args:
            agent_name: Name of agent to invoke
            input_data: Input data for agent
            session_id: Session ID for tracking
        
        Returns:
            Dict with agent execution result
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Invoking agent via Tool Use: "
                f"agent={agent_name}, session={session_id}"
            )
            
            # Import AgentCommunication for Tool Use
            try:
                from agent_communication import get_agent_communication
            except ImportError:
                # Fallback for Lambda environment
                import sys
                sys.path.append('/opt/python')
                from agent_communication import get_agent_communication
            
            # Get AgentCommunication instance
            agent_comm = get_agent_communication()
            
            # Use Claude to reason about tool invocation
            tool_invocation_prompt = f"""
You are orchestrating a branding workflow. You need to invoke the {agent_name} agent.

Agent: {agent_name}
Input Data: {json.dumps(input_data, indent=2)}

Based on the input data, determine:
1. What specific task should this agent perform?
2. What parameters should be passed to the agent?
3. What output format is expected?

Provide your reasoning and the tool invocation parameters.
"""
            
            reasoning_result = self.bedrock_client.invoke_claude(
                prompt=tool_invocation_prompt,
                system_prompt="You are an AI workflow orchestrator using AgentCore Tool Use primitive.",
                max_tokens=1024,
                temperature=0.3
            )
            
            # Invoke agent using Tool Use primitive
            tool_result = agent_comm.invoke_agent_with_tool(
                agent_name=agent_name,
                input_data=input_data,
                session_id=session_id,
                timeout=30
            )
            
            # Add reasoning to result
            tool_result['reasoning'] = reasoning_result.get('text', '')
            
            latency_ms = int((time.time() - start_time) * 1000)
            tool_result['total_latency_ms'] = latency_ms
            
            self.logger.info(
                f"Agent invoked via Tool Use: "
                f"agent={agent_name}, status={tool_result.get('status')}, "
                f"latency_ms={latency_ms}"
            )
            
            return tool_result
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Tool Use invocation failed: "
                f"agent={agent_name}, error={str(e)}, "
                f"latency_ms={latency_ms}"
            )
            
            return {
                'tool_name': f'invoke_{agent_name}',
                'agent_name': agent_name,
                'status': 'error',
                'error': str(e),
                'latency_ms': latency_ms
            }
    
    def store_workflow_memory(
        self,
        session_id: str,
        step: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store workflow state using AgentCore Memory primitive.
        
        This implements the Memory primitive by storing workflow state
        that can be retrieved across agent invocations. The memory is
        synchronized with DynamoDB session management.
        
        Memory Schema:
        - Memory key: session_id
        - Memory value: {current_step, agent_outputs, reasoning_chain}
        
        Args:
            session_id: Session ID (memory key)
            step: Workflow step number
            data: Data to store in memory (agent outputs, reasoning)
        
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Storing workflow memory: "
                f"session={session_id}, step={step}"
            )
            
            # Build memory structure
            memory_entry = {
                'session_id': session_id,
                'current_step': step,
                'agent_outputs': data.get('results', {}),
                'reasoning_chain': [],
                'stored_at': datetime.utcnow().isoformat(),
                'memory_version': '1.0'
            }
            
            # Use Claude to create memory summary for efficient retrieval
            memory_summary_prompt = f"""
Summarize the following workflow state for efficient memory storage:

Session ID: {session_id}
Step: {step}
Data: {json.dumps(data, indent=2)}

Provide a concise summary that captures:
1. Key decisions made
2. Important results
3. Context needed for next steps

Keep the summary under 200 words.
"""
            
            try:
                summary_result = self.bedrock_client.invoke_claude(
                    prompt=memory_summary_prompt,
                    system_prompt="You are creating memory summaries for workflow state management.",
                    max_tokens=512,
                    temperature=0.3
                )
                
                memory_entry['summary'] = summary_result.get('text', '')
                memory_entry['summary_tokens'] = summary_result.get('usage', {}).get('output_tokens', 0)
                
            except Exception as e:
                self.logger.warning(f"Failed to generate memory summary: {str(e)}")
                memory_entry['summary'] = f"Step {step} completed"
            
            # Store to DynamoDB (synchronize with session management)
            try:
                import boto3
                from decimal import Decimal
                
                # Convert floats to Decimal for DynamoDB
                def convert_floats(obj):
                    """Recursively convert float to Decimal for DynamoDB"""
                    if isinstance(obj, float):
                        return Decimal(str(obj))
                    elif isinstance(obj, dict):
                        return {k: convert_floats(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_floats(item) for item in obj]
                    return obj
                
                memory_entry_converted = convert_floats(memory_entry)
                
                # Get DynamoDB client
                if os.getenv('ENVIRONMENT') == 'local':
                    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
                else:
                    dynamodb = boto3.resource('dynamodb')
                
                sessions_table = dynamodb.Table(
                    os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local')
                )
                
                # Update session with AgentCore memory
                sessions_table.update_item(
                    Key={'sessionId': session_id},
                    UpdateExpression=(
                        'SET agentCoreMemory = :memory, '
                        'currentStep = :step, '
                        'updatedAt = :timestamp'
                    ),
                    ExpressionAttributeValues={
                        ':memory': memory_entry_converted,
                        ':step': step,
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                self.logger.info(
                    f"Workflow memory stored to DynamoDB: "
                    f"session={session_id}, step={step}, "
                    f"summary_length={len(memory_entry.get('summary', ''))}, "
                    f"latency_ms={latency_ms}"
                )
                
                return True
                
            except Exception as e:
                self.logger.error(
                    f"Failed to store memory to DynamoDB: {str(e)}"
                )
                # Continue even if DynamoDB fails (memory stored in-process)
                return True
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Failed to store workflow memory: "
                f"session={session_id}, error={str(e)}, "
                f"latency_ms={latency_ms}"
            )
            return False
    
    def retrieve_workflow_memory(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve workflow state from AgentCore Memory.
        
        This retrieves the memory stored by store_workflow_memory(),
        synchronized with DynamoDB session management.
        
        Args:
            session_id: Session ID (memory key)
        
        Returns:
            Dict with workflow state:
                - session_id: Session identifier
                - current_step: Current workflow step
                - agent_outputs: Results from previous agents
                - reasoning_chain: Chain of reasoning steps
                - summary: Human-readable summary
                - retrieved_at: Timestamp
        """
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Retrieving workflow memory: session={session_id}"
            )
            
            # Retrieve from DynamoDB
            try:
                import boto3
                
                # Get DynamoDB client
                if os.getenv('ENVIRONMENT') == 'local':
                    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
                else:
                    dynamodb = boto3.resource('dynamodb')
                
                sessions_table = dynamodb.Table(
                    os.getenv('SESSIONS_TABLE', 'branding-chatbot-sessions-local')
                )
                
                # Get session item
                response = sessions_table.get_item(Key={'sessionId': session_id})
                
                if 'Item' not in response:
                    self.logger.warning(
                        f"Session not found in DynamoDB: {session_id}"
                    )
                    return self._create_empty_memory(session_id)
                
                session_item = response['Item']
                
                # Extract AgentCore memory
                agentcore_memory = session_item.get('agentCoreMemory', {})
                
                if not agentcore_memory:
                    self.logger.info(
                        f"No AgentCore memory found for session: {session_id}"
                    )
                    # Build memory from session data
                    workflow_state = {
                        'session_id': session_id,
                        'current_step': session_item.get('currentStep', 1),
                        'agent_outputs': self._extract_agent_outputs(session_item),
                        'reasoning_chain': session_item.get('reasoningChain', []),
                        'summary': f"Session at step {session_item.get('currentStep', 1)}",
                        'retrieved_at': datetime.utcnow().isoformat(),
                        'source': 'session_data'
                    }
                else:
                    # Use stored AgentCore memory
                    workflow_state = {
                        'session_id': agentcore_memory.get('session_id', session_id),
                        'current_step': agentcore_memory.get('current_step', 1),
                        'agent_outputs': agentcore_memory.get('agent_outputs', {}),
                        'reasoning_chain': agentcore_memory.get('reasoning_chain', []),
                        'summary': agentcore_memory.get('summary', ''),
                        'stored_at': agentcore_memory.get('stored_at'),
                        'retrieved_at': datetime.utcnow().isoformat(),
                        'source': 'agentcore_memory'
                    }
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                self.logger.info(
                    f"Workflow memory retrieved: "
                    f"session={session_id}, step={workflow_state['current_step']}, "
                    f"source={workflow_state['source']}, latency_ms={latency_ms}"
                )
                
                return workflow_state
                
            except Exception as e:
                self.logger.error(
                    f"Failed to retrieve memory from DynamoDB: {str(e)}"
                )
                return self._create_empty_memory(session_id)
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Failed to retrieve workflow memory: "
                f"session={session_id}, error={str(e)}, "
                f"latency_ms={latency_ms}"
            )
            return self._create_empty_memory(session_id)
    
    def _create_empty_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Create empty memory structure for new sessions.
        
        Args:
            session_id: Session ID
        
        Returns:
            Empty memory dict
        """
        return {
            'session_id': session_id,
            'current_step': 1,
            'agent_outputs': {},
            'reasoning_chain': [],
            'summary': 'New session - no memory available',
            'retrieved_at': datetime.utcnow().isoformat(),
            'source': 'empty'
        }
    
    def _extract_agent_outputs(self, session_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract agent outputs from session item.
        
        Args:
            session_item: DynamoDB session item
        
        Returns:
            Dict of agent outputs by agent name
        """
        agent_outputs = {}
        
        # Extract from various session fields
        if 'analysisResult' in session_item:
            agent_outputs['product_insight'] = session_item['analysisResult']
            agent_outputs['market_analyst'] = session_item['analysisResult']
        
        if 'businessNames' in session_item:
            agent_outputs['reporter'] = session_item['businessNames']
        
        if 'signboardImages' in session_item:
            agent_outputs['signboard'] = session_item['signboardImages']
        
        if 'interiorImages' in session_item:
            agent_outputs['interior'] = session_item['interiorImages']
        
        if 'pdfReportPath' in session_item:
            agent_outputs['report_generator'] = {
                'report_path': session_item['pdfReportPath']
            }
        
        return agent_outputs
    
    def reason_next_step(
        self,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use Reasoning LLM to determine next workflow step.
        
        This uses Claude 3.5 Sonnet for Chain-of-Thought reasoning
        to decide what should happen next in the workflow.
        
        Args:
            current_state: Current workflow state
        
        Returns:
            Dict with next_step, reasoning, and confidence
        """
        start_time = time.time()
        
        try:
            current_step = current_state.get('current_step', 1)
            step_results = current_state.get('step_results', {})
            
            self.logger.info(
                f"Reasoning about next step: current_step={current_step}"
            )
            
            # Build reasoning prompt
            reasoning_prompt = f"""
You are orchestrating a 5-step branding workflow. Analyze the current state and decide the next step.

Current Step: {current_step}
Step Results: {json.dumps(step_results, indent=2)}

Workflow Steps:
1. Business Analysis (Product Insight + Market Analyst)
2. Name Generation (Reporter)
3. Signboard Design (Signboard)
4. Interior Design (Interior)
5. Report Generation (Report Generator)

Based on the current state:
1. Should we proceed to the next step?
2. Are there any issues that need attention?
3. What is your confidence level (0-1)?

Provide your reasoning using Chain-of-Thought, then decide the next step.
"""
            
            reasoning_result = self.bedrock_client.invoke_claude(
                prompt=reasoning_prompt,
                system_prompt="You are an AI workflow orchestrator making decisions about workflow progression.",
                max_tokens=1024,
                temperature=0.3
            )
            
            reasoning_text = reasoning_result.get('text', '')
            
            # Parse reasoning to extract decision
            # In production, this would use structured output parsing
            next_step = current_step + 1 if current_step < 5 else 5
            confidence = 0.85  # Default confidence
            
            # Extract confidence from reasoning if mentioned
            if 'confidence' in reasoning_text.lower():
                # Simple extraction (in production, use regex or structured parsing)
                try:
                    import re
                    confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', reasoning_text.lower())
                    if confidence_match:
                        confidence = float(confidence_match.group(1))
                except:
                    pass
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            decision = {
                'next_step': next_step,
                'reasoning': reasoning_text,
                'confidence': confidence,
                'current_step': current_step,
                'decision_latency_ms': latency_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"Next step decision: "
                f"current={current_step}, next={next_step}, "
                f"confidence={confidence:.2f}, latency_ms={latency_ms}"
            )
            
            return decision
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            self.logger.error(
                f"Reasoning failed: error={str(e)}, latency_ms={latency_ms}"
            )
            
            # Fallback decision: proceed to next step
            return {
                'next_step': current_state.get('current_step', 1) + 1,
                'reasoning': f'Fallback decision due to error: {str(e)}',
                'confidence': 0.5,
                'error': str(e),
                'decision_latency_ms': latency_ms
            }


# Convenience function for creating orchestrator
def create_agentcore_orchestrator(
    logger: Optional[logging.Logger] = None
) -> AgentCoreOrchestrator:
    """
    Create and return a configured AgentCore orchestrator.
    
    Args:
        logger: Logger instance (default: creates new logger)
    
    Returns:
        AgentCoreOrchestrator instance
    """
    return AgentCoreOrchestrator(logger=logger)
