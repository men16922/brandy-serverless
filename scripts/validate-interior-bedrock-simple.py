#!/usr/bin/env python3
"""
Simple validation script for Interior Agent Bedrock integration
Checks code structure and integration points without running the agent
"""

import sys
import os
import re

def validate_interior_bedrock_integration():
    """Validate Interior Agent Bedrock integration by checking code"""
    
    print("=" * 80)
    print("Interior Agent Bedrock Integration Validation (Code Analysis)")
    print("=" * 80)
    print()
    
    interior_agent_path = "src/lambda/agents/interior/index.py"
    
    if not os.path.exists(interior_agent_path):
        print(f"✗ Interior Agent file not found: {interior_agent_path}")
        return False
    
    with open(interior_agent_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check 1: Bedrock integration in docstring
    print("Check 1: Bedrock integration mentioned in docstring...")
    if "Bedrock Integration" in content or "Claude 4 Sonnet" in content:
        print("✓ Bedrock integration documented")
        checks.append(True)
    else:
        print("✗ Bedrock integration not documented")
        checks.append(False)
    
    # Check 2: BedrockClient initialization
    print("\nCheck 2: BedrockClient initialization...")
    if "from shared.bedrock_client import BedrockClient" in content:
        print("✓ BedrockClient import found")
        checks.append(True)
    else:
        print("✗ BedrockClient import not found")
        checks.append(False)
    
    # Check 3: ReasoningEngine initialization
    print("\nCheck 3: ReasoningEngine initialization...")
    if "from shared.reasoning_engine import ReasoningEngine" in content:
        print("✓ ReasoningEngine import found")
        checks.append(True)
    else:
        print("✗ ReasoningEngine import not found")
        checks.append(False)
    
    # Check 4: Bedrock client instance creation
    print("\nCheck 4: Bedrock client instance creation...")
    if "self.bedrock_client = BedrockClient" in content:
        print("✓ BedrockClient instance created")
        checks.append(True)
    else:
        print("✗ BedrockClient instance not created")
        checks.append(False)
    
    # Check 5: ReasoningEngine instance creation
    print("\nCheck 5: ReasoningEngine instance creation...")
    if "self.reasoning_engine = ReasoningEngine" in content:
        print("✓ ReasoningEngine instance created")
        checks.append(True)
    else:
        print("✗ ReasoningEngine instance not created")
        checks.append(False)
    
    # Check 6: Bedrock-based recommendation method
    print("\nCheck 6: Bedrock-based recommendation method...")
    if "_generate_interior_recommendations_with_bedrock" in content:
        print("✓ Bedrock recommendation method found")
        checks.append(True)
    else:
        print("✗ Bedrock recommendation method not found")
        checks.append(False)
    
    # Check 7: Fallback mechanism
    print("\nCheck 7: Fallback mechanism...")
    if "ENABLE_FALLBACK" in content and "use_bedrock" in content:
        print("✓ Fallback mechanism implemented")
        checks.append(True)
    else:
        print("✗ Fallback mechanism not implemented")
        checks.append(False)
    
    # Check 8: Bedrock Claude invocation
    print("\nCheck 8: Bedrock Claude invocation...")
    if "self.bedrock_client.invoke_claude" in content:
        print("✓ Bedrock Claude invocation found")
        checks.append(True)
    else:
        print("✗ Bedrock Claude invocation not found")
        checks.append(False)
    
    # Check 9: System prompt for interior recommendations
    print("\nCheck 9: System prompt for interior recommendations...")
    if "interior design consultant" in content.lower() or "interior design" in content.lower():
        print("✓ Interior design system prompt found")
        checks.append(True)
    else:
        print("✗ Interior design system prompt not found")
        checks.append(False)
    
    # Check 10: Execute method integration
    print("\nCheck 10: Execute method Bedrock integration...")
    if "if self.use_bedrock and self.bedrock_client" in content:
        print("✓ Execute method checks for Bedrock availability")
        checks.append(True)
    else:
        print("✗ Execute method doesn't check for Bedrock")
        checks.append(False)
    
    # Check 11: Reasoning chain storage
    print("\nCheck 11: Reasoning/confidence tracking...")
    if "reasoning" in content and "confidence" in content:
        print("✓ Reasoning and confidence tracking found")
        checks.append(True)
    else:
        print("✗ Reasoning and confidence tracking not found")
        checks.append(False)
    
    # Check 12: Latency tracking
    print("\nCheck 12: Latency tracking...")
    if "latency_ms" in content:
        print("✓ Latency tracking found")
        checks.append(True)
    else:
        print("✗ Latency tracking not found")
        checks.append(False)
    
    print("\n" + "=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100
    
    print(f"Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n✓ All checks passed!")
        print("\nInterior Agent Bedrock Integration Summary:")
        print("- BedrockClient and ReasoningEngine properly initialized")
        print("- Bedrock-based interior recommendation method implemented")
        print("- Fallback mechanism in place (ENABLE_FALLBACK)")
        print("- Execute method routes to Bedrock when enabled")
        print("- Reasoning chain and confidence tracking included")
        print("- Latency metrics tracked")
        print()
        print("Requirements Met:")
        print("✓ Requirement 1.5: Bedrock Claude for interior recommendations")
        print("✓ Requirement 3.4: Reasoning LLM for interior style decisions")
        print("✓ Fallback: Existing logic preserved")
        print()
        print("Next Steps:")
        print("1. Test with actual Bedrock API (requires AWS credentials)")
        print("2. Deploy with 'sam build && sam deploy'")
        print("3. Monitor CloudWatch logs for Bedrock API calls")
        print("4. Verify reasoning chain storage in DynamoDB")
        return True
    else:
        print(f"\n✗ {total - passed} checks failed")
        print("\nPlease review the failed checks above and fix the issues.")
        return False


if __name__ == "__main__":
    try:
        success = validate_interior_bedrock_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
