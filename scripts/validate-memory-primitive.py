#!/usr/bin/env python3
"""
Validation script for AgentCore Memory primitive implementation.

This script validates that the Memory primitive is correctly implemented
by testing store and retrieve operations against local DynamoDB.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
shared_dir = os.path.join(project_root, 'src', 'lambda', 'shared')
supervisor_dir = os.path.join(project_root, 'src', 'lambda', 'agents', 'supervisor')

sys.path.insert(0, shared_dir)
sys.path.insert(0, supervisor_dir)

# Set environment for local testing
os.environ['ENVIRONMENT'] = 'local'
os.environ['SESSIONS_TABLE'] = 'ai-branding-chatbot-sessions-local'
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

def validate_memory_primitive():
    """Validate Memory primitive implementation"""
    
    print_header("AgentCore Memory Primitive Validation")
    
    try:
        # Import required modules
        print_info("Importing modules...")
        from agentcore_orchestrator import AgentCoreOrchestrator
        import boto3
        
        print_success("Modules imported successfully")
        
        # Create orchestrator
        print_info("Creating AgentCore orchestrator...")
        orchestrator = AgentCoreOrchestrator()
        print_success("Orchestrator created")
        
        # Create test session
        print_info("Creating test session in DynamoDB...")
        session_id = f"test-memory-{int(time.time())}"
        
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        table = dynamodb.Table('ai-branding-chatbot-sessions-local')
        
        session_data = {
            'sessionId': session_id,
            'currentStep': 1,
            'status': 'active',
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'ttl': int(time.time() + 86400),
            'businessInfo': json.dumps({
                'industry': 'restaurant',
                'region': 'seoul',
                'size': 'small'
            })
        }
        
        table.put_item(Item=session_data)
        print_success(f"Test session created: {session_id}")
        
        # Test 1: Store workflow memory
        print_header("Test 1: Store Workflow Memory")
        
        test_data = {
            'step_name': 'ANALYSIS',
            'agents_executed': ['product_insight', 'market_analyst'],
            'results': {
                'product_insight': {
                    'summary': 'Restaurant analysis complete',
                    'score': 85.5,
                    'insights': ['High competition', 'Growing market']
                },
                'market_analyst': {
                    'market_trends': ['healthy eating', 'local sourcing'],
                    'competition_level': 'medium'
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print_info("Storing memory...")
        start_time = time.time()
        result = orchestrator.store_workflow_memory(
            session_id=session_id,
            step=1,
            data=test_data
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        if result:
            print_success(f"Memory stored successfully (latency: {latency_ms}ms)")
        else:
            print_error("Memory storage failed")
            return False
        
        # Verify in DynamoDB
        print_info("Verifying memory in DynamoDB...")
        response = table.get_item(Key={'sessionId': session_id})
        
        if 'Item' not in response:
            print_error("Session not found in DynamoDB")
            return False
        
        session_item = response['Item']
        
        if 'agentCoreMemory' not in session_item:
            print_error("agentCoreMemory field not found in session")
            return False
        
        memory = session_item['agentCoreMemory']
        print_success("Memory found in DynamoDB")
        
        # Validate memory schema
        print_info("Validating memory schema...")
        required_fields = ['session_id', 'current_step', 'agent_outputs', 'reasoning_chain', 'summary', 'stored_at']
        missing_fields = [field for field in required_fields if field not in memory]
        
        if missing_fields:
            print_error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        
        print_success("Memory schema valid")
        print_info(f"  - session_id: {memory['session_id']}")
        print_info(f"  - current_step: {memory['current_step']}")
        print_info(f"  - agent_outputs: {len(memory['agent_outputs'])} agents")
        print_info(f"  - reasoning_chain: {len(memory['reasoning_chain'])} steps")
        print_info(f"  - summary length: {len(memory.get('summary', ''))} chars")
        
        # Test 2: Retrieve workflow memory
        print_header("Test 2: Retrieve Workflow Memory")
        
        print_info("Retrieving memory...")
        start_time = time.time()
        retrieved_memory = orchestrator.retrieve_workflow_memory(session_id=session_id)
        latency_ms = int((time.time() - start_time) * 1000)
        
        if not retrieved_memory:
            print_error("Memory retrieval failed")
            return False
        
        print_success(f"Memory retrieved successfully (latency: {latency_ms}ms)")
        
        # Validate retrieved memory
        print_info("Validating retrieved memory...")
        
        if retrieved_memory['session_id'] != session_id:
            print_error(f"Session ID mismatch: {retrieved_memory['session_id']} != {session_id}")
            return False
        
        if retrieved_memory['current_step'] != 1:
            print_error(f"Step mismatch: {retrieved_memory['current_step']} != 1")
            return False
        
        if retrieved_memory['source'] != 'agentcore_memory':
            print_error(f"Source mismatch: {retrieved_memory['source']} != agentcore_memory")
            return False
        
        print_success("Retrieved memory valid")
        print_info(f"  - session_id: {retrieved_memory['session_id']}")
        print_info(f"  - current_step: {retrieved_memory['current_step']}")
        print_info(f"  - source: {retrieved_memory['source']}")
        print_info(f"  - agent_outputs: {len(retrieved_memory['agent_outputs'])} agents")
        
        # Test 3: Memory synchronization with session
        print_header("Test 3: Memory Synchronization with Session")
        
        print_info("Storing memory for step 2...")
        step2_data = {
            'step_name': 'NAMING',
            'agents_executed': ['reporter'],
            'results': {
                'reporter': {
                    'suggestions': [
                        {'name': 'CafeBreeze', 'score': 92.5},
                        {'name': 'FreshBite', 'score': 88.0}
                    ]
                }
            }
        }
        
        orchestrator.store_workflow_memory(
            session_id=session_id,
            step=2,
            data=step2_data
        )
        
        # Verify session update
        response = table.get_item(Key={'sessionId': session_id})
        updated_session = response['Item']
        
        if updated_session['currentStep'] != 2:
            print_error(f"Session step not updated: {updated_session['currentStep']} != 2")
            return False
        
        print_success("Session synchronized with memory")
        print_info(f"  - currentStep updated: {updated_session['currentStep']}")
        print_info(f"  - updatedAt: {updated_session['updatedAt']}")
        
        # Test 4: Retrieve memory for non-existent session
        print_header("Test 4: Retrieve Memory for Non-Existent Session")
        
        non_existent_id = f"non-existent-{int(time.time())}"
        print_info(f"Retrieving memory for non-existent session: {non_existent_id}")
        
        empty_memory = orchestrator.retrieve_workflow_memory(session_id=non_existent_id)
        
        if not empty_memory:
            print_error("Should return empty memory structure")
            return False
        
        if empty_memory['source'] != 'empty':
            print_error(f"Source should be 'empty', got: {empty_memory['source']}")
            return False
        
        if empty_memory['current_step'] != 1:
            print_error(f"Default step should be 1, got: {empty_memory['current_step']}")
            return False
        
        print_success("Empty memory structure returned correctly")
        print_info(f"  - source: {empty_memory['source']}")
        print_info(f"  - current_step: {empty_memory['current_step']}")
        print_info(f"  - agent_outputs: {len(empty_memory['agent_outputs'])}")
        
        # Cleanup
        print_header("Cleanup")
        print_info("Deleting test session...")
        table.delete_item(Key={'sessionId': session_id})
        print_success("Test session deleted")
        
        # Final summary
        print_header("Validation Summary")
        print_success("All tests passed!")
        print_info("Memory primitive implementation is correct:")
        print_info("  ✓ Memory storage to DynamoDB")
        print_info("  ✓ Memory retrieval from DynamoDB")
        print_info("  ✓ Memory schema validation")
        print_info("  ✓ Session synchronization")
        print_info("  ✓ Empty memory handling")
        
        return True
        
    except Exception as e:
        print_error(f"Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = validate_memory_primitive()
    sys.exit(0 if success else 1)
