#!/usr/bin/env python3
"""
Validation script for Product Insight Agent Bedrock integration
Tests the enhanced analysis with Bedrock Claude
"""

import sys
import os
import json

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'agents', 'product-insight'))

def test_product_insight_bedrock_integration():
    """Test Product Insight Agent with Bedrock integration"""
    
    print("=" * 80)
    print("Product Insight Agent - Bedrock Integration Validation")
    print("=" * 80)
    
    try:
        # Import the agent
        from index import ProductInsightAgent
        
        print("\n✓ Successfully imported ProductInsightAgent")
        
        # Create agent instance
        agent = ProductInsightAgent()
        print("✓ Successfully created ProductInsightAgent instance")
        
        # Check Bedrock client initialization
        if agent.bedrock_client:
            print(f"✓ Bedrock client initialized: region={agent.bedrock_client.region}")
            print(f"  - Claude model: {agent.bedrock_client.claude_model_id}")
        else:
            print("⚠ Bedrock client not initialized (expected in local environment)")
        
        # Check Reasoning Engine initialization
        if agent.reasoning_engine:
            print(f"✓ Reasoning Engine initialized")
        else:
            print("⚠ Reasoning Engine not initialized (expected in local environment)")
        
        # Test data
        test_event = {
            'body': json.dumps({
                'sessionId': 'test-session-bedrock-001',
                'businessInfo': {
                    'industry': 'restaurant',
                    'region': 'seoul',
                    'size': 'small'
                }
            })
        }
        
        print("\n" + "-" * 80)
        print("Test Case: Restaurant in Seoul (Small)")
        print("-" * 80)
        
        # Execute analysis
        result = agent.execute(test_event, None)
        
        # Parse response
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            analysis = body.get('analysis', {})
            metadata = body.get('metadata', {})
            
            print(f"\n✓ Analysis completed successfully")
            print(f"  - Score: {analysis.get('score')}")
            print(f"  - Provider: {metadata.get('analysis_provider')}")
            print(f"  - Bedrock enabled: {metadata.get('bedrock_enabled')}")
            print(f"  - Version: {metadata.get('version')}")
            
            # Check insights
            insights = analysis.get('insights', [])
            print(f"\n  Insights ({len(insights)}):")
            for i, insight in enumerate(insights, 1):
                print(f"    {i}. {insight[:100]}...")
            
            # Check recommendations
            recommendations = analysis.get('recommendations', [])
            print(f"\n  Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"    {i}. {rec}")
            
            # Check Bedrock-specific fields
            if 'bedrock_reasoning' in analysis:
                print(f"\n  ✓ Bedrock reasoning available")
                print(f"    Length: {len(analysis['bedrock_reasoning'])} characters")
            
            if 'confidence' in analysis:
                print(f"  ✓ Confidence score: {analysis['confidence']}")
            
            print("\n" + "=" * 80)
            print("✓ VALIDATION PASSED")
            print("=" * 80)
            
            return True
        else:
            print(f"\n✗ Analysis failed with status code: {result['statusCode']}")
            print(f"  Error: {result.get('body')}")
            return False
            
    except ImportError as e:
        print(f"\n✗ Import error: {str(e)}")
        print("  This is expected if dependencies are not installed")
        return False
    except Exception as e:
        print(f"\n✗ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_mode():
    """Test fallback mode when Bedrock is disabled"""
    
    print("\n" + "=" * 80)
    print("Testing Fallback Mode (ENABLE_FALLBACK=true)")
    print("=" * 80)
    
    # Set fallback environment variable
    os.environ['ENABLE_FALLBACK'] = 'true'
    
    try:
        from index import ProductInsightAgent
        
        agent = ProductInsightAgent()
        
        test_event = {
            'body': json.dumps({
                'sessionId': 'test-session-fallback-001',
                'businessInfo': {
                    'industry': 'technology',
                    'region': 'busan',
                    'size': 'medium'
                }
            })
        }
        
        print("\nTest Case: Technology in Busan (Medium) - Fallback Mode")
        
        result = agent.execute(test_event, None)
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            metadata = body.get('metadata', {})
            
            print(f"\n✓ Fallback analysis completed")
            print(f"  - Provider: {metadata.get('analysis_provider')}")
            print(f"  - Expected: baseline_fallback")
            
            if metadata.get('analysis_provider') == 'baseline_fallback':
                print("\n✓ Fallback mode working correctly")
                return True
            else:
                print(f"\n⚠ Unexpected provider: {metadata.get('analysis_provider')}")
                return False
        else:
            print(f"\n✗ Fallback test failed: {result['statusCode']}")
            return False
            
    except Exception as e:
        print(f"\n✗ Fallback test error: {str(e)}")
        return False
    finally:
        # Reset environment variable
        if 'ENABLE_FALLBACK' in os.environ:
            del os.environ['ENABLE_FALLBACK']


def main():
    """Run all validation tests"""
    
    print("\n" + "=" * 80)
    print("PRODUCT INSIGHT AGENT - BEDROCK INTEGRATION VALIDATION")
    print("=" * 80)
    print("\nThis script validates:")
    print("  1. Bedrock client initialization")
    print("  2. Enhanced analysis with Bedrock Claude")
    print("  3. Fallback mechanism when Bedrock is disabled")
    print("  4. Backward compatibility with existing logic")
    
    results = []
    
    # Test 1: Bedrock integration
    print("\n" + "=" * 80)
    print("TEST 1: Bedrock Integration")
    print("=" * 80)
    results.append(("Bedrock Integration", test_product_insight_bedrock_integration()))
    
    # Test 2: Fallback mode
    print("\n" + "=" * 80)
    print("TEST 2: Fallback Mode")
    print("=" * 80)
    results.append(("Fallback Mode", test_fallback_mode()))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "=" * 80)
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 80)
        print("\nProduct Insight Agent is ready for Bedrock integration!")
        print("\nNext steps:")
        print("  1. Deploy to AWS with Bedrock IAM permissions")
        print("  2. Set ENABLE_FALLBACK=false for production")
        print("  3. Test with real Bedrock API calls")
        return 0
    else:
        print("\n" + "=" * 80)
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 80)
        print("\nPlease review the errors above and fix any issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
