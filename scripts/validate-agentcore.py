#!/usr/bin/env python3
"""
Validation script for AgentCore Orchestrator implementation
Verifies that all required methods and functionality are present
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, 'src/lambda/agents/supervisor')
sys.path.insert(0, 'src/lambda/shared')

def validate_agentcore_implementation():
    """Validate AgentCore orchestrator implementation"""
    
    print("=" * 60)
    print("AgentCore Orchestrator Implementation Validation")
    print("=" * 60)
    
    # Test 1: Import check
    print("\n1. Testing imports...")
    try:
        from agentcore_orchestrator import (
            AgentCoreOrchestrator,
            create_agentcore_orchestrator
        )
        print("   ✓ AgentCore orchestrator imports successfully")
    except ImportError as e:
        print(f"   ✗ Import failed: {str(e)}")
        return False
    
    # Test 2: Class instantiation
    print("\n2. Testing class instantiation...")
    try:
        orchestrator = create_agentcore_orchestrator()
        print("   ✓ AgentCore orchestrator instantiated successfully")
    except Exception as e:
        print(f"   ✗ Instantiation failed: {str(e)}")
        return False
    
    # Test 3: Required methods check
    print("\n3. Checking required methods...")
    required_methods = [
        'orchestrate_workflow',
        'invoke_agent_with_tool',
        'store_workflow_memory',
        'retrieve_workflow_memory',
        'reason_next_step'
    ]
    
    for method_name in required_methods:
        if hasattr(orchestrator, method_name):
            print(f"   ✓ Method '{method_name}' exists")
        else:
            print(f"   ✗ Method '{method_name}' missing")
            return False
    
    # Test 4: Bedrock client integration
    print("\n4. Checking Bedrock client integration...")
    if hasattr(orchestrator, 'bedrock_client') and orchestrator.bedrock_client is not None:
        print("   ✓ Bedrock client integrated")
    else:
        print("   ✗ Bedrock client not integrated")
        return False
    
    # Test 5: Workflow configuration
    print("\n5. Checking workflow configuration...")
    if hasattr(orchestrator, 'workflow_steps') and len(orchestrator.workflow_steps) == 5:
        print(f"   ✓ Workflow steps configured: {len(orchestrator.workflow_steps)} steps")
    else:
        print("   ✗ Workflow steps not properly configured")
        return False
    
    if hasattr(orchestrator, 'agent_mapping') and len(orchestrator.agent_mapping) == 5:
        print(f"   ✓ Agent mapping configured: {len(orchestrator.agent_mapping)} mappings")
    else:
        print("   ✗ Agent mapping not properly configured")
        return False
    
    # Test 6: Method signatures
    print("\n6. Validating method signatures...")
    
    # Check orchestrate_workflow signature
    import inspect
    sig = inspect.signature(orchestrator.orchestrate_workflow)
    params = list(sig.parameters.keys())
    expected_params = ['session_id', 'business_info', 'current_step']
    if all(p in params for p in expected_params):
        print("   ✓ orchestrate_workflow signature correct")
    else:
        print(f"   ✗ orchestrate_workflow signature incorrect. Expected: {expected_params}, Got: {params}")
        return False
    
    # Check invoke_agent_with_tool signature
    sig = inspect.signature(orchestrator.invoke_agent_with_tool)
    params = list(sig.parameters.keys())
    expected_params = ['agent_name', 'input_data', 'session_id']
    if all(p in params for p in expected_params):
        print("   ✓ invoke_agent_with_tool signature correct")
    else:
        print(f"   ✗ invoke_agent_with_tool signature incorrect. Expected: {expected_params}, Got: {params}")
        return False
    
    # Check store_workflow_memory signature
    sig = inspect.signature(orchestrator.store_workflow_memory)
    params = list(sig.parameters.keys())
    expected_params = ['session_id', 'step', 'data']
    if all(p in params for p in expected_params):
        print("   ✓ store_workflow_memory signature correct")
    else:
        print(f"   ✗ store_workflow_memory signature incorrect. Expected: {expected_params}, Got: {params}")
        return False
    
    # Check reason_next_step signature
    sig = inspect.signature(orchestrator.reason_next_step)
    params = list(sig.parameters.keys())
    expected_params = ['current_state']
    if all(p in params for p in expected_params):
        print("   ✓ reason_next_step signature correct")
    else:
        print(f"   ✗ reason_next_step signature incorrect. Expected: {expected_params}, Got: {params}")
        return False
    
    # Test 7: Documentation check
    print("\n7. Checking documentation...")
    if orchestrator.__doc__:
        print("   ✓ Class documentation present")
    else:
        print("   ⚠ Class documentation missing (warning)")
    
    for method_name in required_methods:
        method = getattr(orchestrator, method_name)
        if method.__doc__:
            print(f"   ✓ Method '{method_name}' documented")
        else:
            print(f"   ⚠ Method '{method_name}' documentation missing (warning)")
    
    print("\n" + "=" * 60)
    print("✓ All validation checks passed!")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    try:
        success = validate_agentcore_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
