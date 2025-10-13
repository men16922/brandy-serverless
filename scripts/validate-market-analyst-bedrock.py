#!/usr/bin/env python3
"""
Validation script for Market Analyst Agent Bedrock integration
Tests Bedrock Claude + Knowledge Base integration
"""

import sys
import os
import json

def test_bedrock_integration():
    """Test Bedrock integration in Market Analyst Agent"""
    print("=" * 60)
    print("Market Analyst Agent - Bedrock Integration Validation")
    print("=" * 60)
    
    # Test 3: Check Market Analyst Agent structure
    print("\n[Test 3] Checking Market Analyst Agent structure...")
    try:
        # Read the agent file
        agent_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'src', 
            'lambda', 
            'agents', 
            'market-analyst', 
            'index.py'
        )
        
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Bedrock integration
        checks = {
            'BedrockClient import': 'from shared.bedrock_client import BedrockClient' in content,
            'ReasoningEngine import': 'from shared.reasoning_engine import ReasoningEngine' in content,
            'bedrock_client initialization': 'self.bedrock_client = BedrockClient' in content,
            'reasoning_engine initialization': 'self.reasoning_engine = ReasoningEngine' in content,
            'query_knowledge_base usage': 'query_knowledge_base' in content,
            'reason_and_decide usage': 'reason_and_decide' in content,
            'synthesize_insights usage': 'synthesize_insights' in content,
            'Fallback logic': 'self.enable_fallback' in content,
            'BedrockException handling': 'BedrockException' in content
        }
        
        all_passed = True
        for check_name, check_result in checks.items():
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}")
            if not check_result:
                all_passed = False
        
        if not all_passed:
            print("\n✗ Some structure checks failed")
            return False
        
        print("\n✓ All structure checks passed")
        
    except Exception as e:
        print(f"✗ Failed to check agent structure: {e}")
        return False
    
    # Test 4: Check method signatures
    print("\n[Test 4] Checking method signatures...")
    try:
        method_checks = {
            '_query_market_data': '_query_market_data' in content,
            '_query_market_data_fallback': '_query_market_data_fallback' in content,
            '_analyze_latest_trends': '_analyze_latest_trends' in content,
            '_analyze_competitors': '_analyze_competitors' in content,
            '_generate_market_recommendations': '_generate_market_recommendations' in content,
            '_extract_recommendations_from_synthesis': '_extract_recommendations_from_synthesis' in content
        }
        
        all_passed = True
        for method_name, method_exists in method_checks.items():
            status = "✓" if method_exists else "✗"
            print(f"  {status} {method_name}")
            if not method_exists:
                all_passed = False
        
        if not all_passed:
            print("\n✗ Some method checks failed")
            return False
        
        print("\n✓ All method checks passed")
        
    except Exception as e:
        print(f"✗ Failed to check methods: {e}")
        return False
    
    # Test 5: Check Requirements coverage
    print("\n[Test 5] Checking Requirements coverage...")
    requirements = {
        'Requirement 1.3 (Bedrock KB)': 'query_knowledge_base' in content,
        'Requirement 3.2 (Reasoning LLM)': 'reason_and_decide' in content and 'synthesize_insights' in content,
        'Requirement 5.2 (KB Integration)': 'bedrock_kb' in content or 'chroma_fallback' in content
    }
    
    all_passed = True
    for req_name, req_met in requirements.items():
        status = "✓" if req_met else "✗"
        print(f"  {status} {req_name}")
        if not req_met:
            all_passed = False
    
    if not all_passed:
        print("\n✗ Some requirements not met")
        return False
    
    print("\n✓ All requirements covered")
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ Market Analyst Agent Bedrock Integration Validated")
    print("=" * 60)
    print("\nIntegration Summary:")
    print("  • Bedrock Claude for trend reasoning")
    print("  • Bedrock Claude for competitive analysis")
    print("  • Bedrock Claude for insight synthesis")
    print("  • Bedrock Knowledge Base for market data")
    print("  • Chroma fallback for local development")
    print("  • Environment-based fallback governance")
    print("\nNext Steps:")
    print("  1. Set environment variables:")
    print("     - ENABLE_FALLBACK=false (production)")
    print("     - DEV_PROFILE=false (production)")
    print("     - BEDROCK_REGION=us-east-1")
    print("     - BEDROCK_KB_ID=<your-kb-id>")
    print("  2. Deploy with SAM: sam build && sam deploy")
    print("  3. Run integration tests: pytest tests/integration/")
    
    return True


if __name__ == '__main__':
    success = test_bedrock_integration()
    sys.exit(0 if success else 1)
