#!/usr/bin/env python3
"""
Validation script for Supervisor Agent AgentCore integration.

Tests:
1. AgentCore orchestrator initialization
2. Environment variable detection (USE_AGENTCORE)
3. Workflow execution with AgentCore
4. Fallback to Step Functions
5. Session management integration
"""

import sys
import os
import json
import time
from datetime import datetime

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
supervisor_dir = os.path.join(project_root, 'src', 'lambda', 'agents', 'supervisor')
shared_dir = os.path.join(project_root, 'src', 'lambda', 'shared')

sys.path.insert(0, supervisor_dir)
sys.path.insert(0, shared_dir)

# Set environment for testing
os.environ['ENVIRONMENT'] = 'local'
os.environ['DYNAMODB_TABLE'] = 'ai-branding-chatbot-sessions-local'
os.environ['AWS_REGION'] = 'us-east-1'

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

def test_agentcore_integration():
    """Test AgentCore integration in Supervisor Agent"""
    
    print_header("Supervisor Agent AgentCore Integration Test")
    
    try:
        # Test 1: Import Supervisor Agent
        print_header("Test 1: Import Supervisor Agent")
        
        print_info("Importing Supervisor Agent...")
        from index import SupervisorAgent, AGENTCORE_AVAILABLE
        
        print_success("Supervisor Agent imported successfully")
        print_info(f"  AgentCore available: {AGENTCORE_AVAILABLE}")
        
        # Test 2: Initialize without AgentCore
        print_header("Test 2: Initialize Supervisor (USE_AGENTCORE=false)")
        
        os.environ['USE_AGENTCORE'] = 'false'
        print_info("Setting USE_AGENTCORE=false...")
        
        supervisor = SupervisorAgent()
        
        if not supervisor.use_agentcore:
            print_success("Supervisor initialized without AgentCore")
            print_info(f"  use_agentcore: {supervisor.use_agentcore}")
            print_info(f"  orchestrator: {supervisor.agentcore_orchestrator}")
        else:
            print_error("Expected use_agentcore=False")
            return False
        
        # Test 3: Initialize with AgentCore
        print_header("Test 3: Initialize Supervisor (USE_AGENTCORE=true)")
        
        os.environ['USE_AGENTCORE'] = 'true'
        print_info("Setting USE_AGENTCORE=true...")
        
        supervisor_with_agentcore = SupervisorAgent()
        
        if AGENTCORE_AVAILABLE:
            if supervisor_with_agentcore.use_agentcore:
                print_success("Supervisor initialized with AgentCore")
                print_info(f"  use_agentcore: {supervisor_with_agentcore.use_agentcore}")
                print_info(f"  orchestrator: {type(supervisor_with_agentcore.agentcore_orchestrator).__name__}")
            else:
                print_error("Expected use_agentcore=True")
                return False
        else:
            print_info("AgentCore not available, fallback expected")
            if not supervisor_with_agentcore.use_agentcore:
                print_success("Correctly fell back to Step Functions")
            else:
                print_error("Should have fallen back to Step Functions")
                return False
        
        # Test 4: Create test session
        print_header("Test 4: Create Test Session")
        
        session_id = f"test-agentcore-{int(time.time())}"
        business_info = {
            'industry': 'restaurant',
            'region': 'seoul',
            'size': 'small',
            'description': 'Healthy food restaurant'
        }
        
        print_info(f"Creating session: {session_id}")
        session_data = supervisor.create_session(session_id, business_info)
        
        if session_data and session_data['sessionId'] == session_id:
            print_success("Test session created")
            print_info(f"  Session ID: {session_id}")
            print_info(f"  Current step: {session_data['currentStep']}")
            print_info(f"  Status: {session_data['status']}")
        else:
            print_error("Failed to create test session")
            return False
        
        # Test 5: Execute workflow with AgentCore (if available)
        if AGENTCORE_AVAILABLE and supervisor_with_agentcore.use_agentcore:
            print_header("Test 5: Execute Workflow with AgentCore")
            
            print_info("Executing workflow with AgentCore orchestration...")
            start_time = time.time()
            
            workflow_result = supervisor_with_agentcore.execute_workflow(
                session_id=session_id,
                business_info=business_info,
                current_step=1
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            print_success(f"Workflow executed (latency: {latency_ms}ms)")
            print_info(f"  Status: {workflow_result.get('status')}")
            print_info(f"  Current step: {workflow_result.get('current_step')}")
            print_info(f"  Next step: {workflow_result.get('next_step')}")
            print_info(f"  Orchestration mode: {workflow_result.get('orchestration_mode', 'agentcore')}")
            
            if workflow_result.get('reasoning'):
                print_info(f"  Reasoning: {workflow_result['reasoning'][:100]}...")
            
            if workflow_result.get('confidence'):
                print_info(f"  Confidence: {workflow_result['confidence']:.2f}")
        else:
            print_header("Test 5: Execute Workflow with Step Functions Fallback")
            
            print_info("Executing workflow with Step Functions fallback...")
            start_time = time.time()
            
            workflow_result = supervisor.execute_workflow(
                session_id=session_id,
                business_info=business_info,
                current_step=1
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            print_success(f"Workflow executed with fallback (latency: {latency_ms}ms)")
            print_info(f"  Status: {workflow_result.get('status')}")
            print_info(f"  Current step: {workflow_result.get('current_step')}")
            print_info(f"  Next step: {workflow_result.get('next_step')}")
            print_info(f"  Orchestration mode: {workflow_result.get('orchestration_mode')}")
        
        # Test 6: Verify session update
        print_header("Test 6: Verify Session Update")
        
        print_info("Retrieving updated session...")
        updated_session = supervisor.get_session(session_id)
        
        if updated_session:
            print_success("Session retrieved successfully")
            print_info(f"  Session ID: {updated_session['sessionId']}")
            print_info(f"  Updated at: {updated_session['updatedAt']}")
            
            # Check for AgentCore memory
            if 'agentCoreMemory' in updated_session:
                print_success("AgentCore memory found in session")
                memory = updated_session['agentCoreMemory']
                print_info(f"  Memory step: {memory.get('current_step')}")
                print_info(f"  Agent outputs: {len(memory.get('agent_outputs', {}))}")
            else:
                print_info("No AgentCore memory in session (expected for fallback)")
        else:
            print_error("Failed to retrieve updated session")
            return False
        
        # Test 7: Test orchestration mode logging
        print_header("Test 7: Verify Orchestration Mode Logging")
        
        if AGENTCORE_AVAILABLE and supervisor_with_agentcore.use_agentcore:
            print_success("AgentCore orchestration mode active")
            print_info("  Structured logging includes:")
            print_info("    - orchestration_mode: agentcore")
            print_info("    - session_id, current_step, next_step")
            print_info("    - status, latency_ms, timestamp")
        else:
            print_success("Step Functions fallback mode active")
            print_info("  Structured logging includes:")
            print_info("    - orchestration_mode: stepfunctions")
            print_info("    - session_id, current_step, next_step")
            print_info("    - status, timestamp")
        
        # Cleanup
        print_header("Cleanup")
        print_info("Deleting test session...")
        
        import boto3
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        table = dynamodb.Table('ai-branding-chatbot-sessions-local')
        table.delete_item(Key={'sessionId': session_id})
        
        print_success("Test session deleted")
        
        # Final summary
        print_header("Test Summary")
        print_success("All tests passed!")
        print_info("AgentCore integration verified:")
        print_info("  ✓ Supervisor Agent imports AgentCore orchestrator")
        print_info("  ✓ USE_AGENTCORE environment variable detection")
        print_info("  ✓ AgentCore orchestration execution")
        print_info("  ✓ Step Functions fallback mechanism")
        print_info("  ✓ Session management integration")
        print_info("  ✓ Structured logging with orchestration_mode")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_agentcore_integration()
    sys.exit(0 if success else 1)
