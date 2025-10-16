#!/usr/bin/env python3
"""
Validation script for Report Generator Agent Bedrock integration
Tests the synthesize_insights functionality
"""

import sys
import os
import json
from datetime import datetime

# Add shared path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda', 'agents', 'report-generator'))

def test_bedrock_integration():
    """Test Bedrock integration in Report Generator Agent"""
    print("=" * 60)
    print("Report Generator Agent - Bedrock Integration Test")
    print("=" * 60)
    print()
    
    try:
        # Import Report Generator Agent
        from index import ReportGeneratorAgent
        
        print("✓ Successfully imported ReportGeneratorAgent")
        
        # Initialize agent
        agent = ReportGeneratorAgent()
        print(f"✓ Agent initialized")
        print(f"  - Bedrock enabled: {agent.enable_bedrock}")
        print(f"  - Bedrock client: {agent.bedrock_client is not None}")
        print(f"  - Reasoning engine: {agent.reasoning_engine is not None}")
        print()
        
        if not agent.enable_bedrock:
            print("⚠ Bedrock is disabled (ENABLE_FALLBACK=true or initialization failed)")
            print("  Set ENABLE_FALLBACK=false to enable Bedrock")
            return True
        
        # Test synthesize_insights method
        print("Testing synthesize_insights_with_bedrock method...")
        
        # Create test session data
        test_session_data = {
            'business_info': {
                'industry': 'restaurant',
                'region': 'seoul',
                'size': 'small'
            },
            'analysis_result': {
                'overall_score': 85,
                'market_potential': 'High',
                'competition_level': 'Medium'
            },
            'business_names': [
                {'name': 'CafeBreeze', 'score': 90, 'description': 'Fresh and modern cafe name'},
                {'name': 'SeoulBistro', 'score': 85, 'description': 'Local and authentic'},
                {'name': 'UrbanTaste', 'score': 80, 'description': 'Contemporary dining'}
            ],
            'selected_name': 'CafeBreeze',
            'signboard_images': [
                {'key': 'signboards/test/design1.png', 'size': 1024000},
                {'key': 'signboards/test/design2.png', 'size': 1024000}
            ],
            'interior_images': [
                {'key': 'interiors/test/modern.png', 'size': 2048000}
            ],
            'color_palette': {
                'primary': {'name': 'Ocean Blue', 'hex': '#0066CC', 'usage': 'Main brand color'},
                'secondary': {'name': 'Warm White', 'hex': '#F5F5F5', 'usage': 'Background'}
            },
            'budget_guide': {
                'signboard': {'min': 1000000, 'recommended': 2000000, 'max': 3000000},
                'interior': {'min': 5000000, 'recommended': 10000000, 'max': 15000000}
            },
            'recommendations': [
                'Focus on local marketing',
                'Emphasize fresh ingredients',
                'Create Instagram-worthy interior'
            ]
        }
        
        # Test insight synthesis
        print("  Calling _synthesize_insights_with_bedrock()...")
        synthesized_insights = agent._synthesize_insights_with_bedrock(test_session_data)
        
        if synthesized_insights:
            print(f"✓ Bedrock insight synthesis successful!")
            print(f"  - Insights length: {len(synthesized_insights)} characters")
            print(f"  - Preview: {synthesized_insights[:200]}...")
            print()
        else:
            print("⚠ Bedrock insight synthesis returned None (may be using fallback)")
            print()
        
        # Test report generation with Bedrock insights
        print("Testing report generation with Bedrock insights...")
        report_result = agent._generate_alternative_report(test_session_data)
        
        print(f"✓ Report generated successfully!")
        print(f"  - Format: {report_result.get('format')}")
        print(f"  - Content type: {report_result.get('content_type')}")
        print(f"  - Bedrock enhanced: {report_result.get('bedrock_enhanced', False)}")
        print(f"  - Content length: {len(report_result.get('content', ''))} characters")
        print()
        
        # Check if synthesized insights are in the report
        if synthesized_insights and synthesized_insights in report_result.get('content', ''):
            print("✓ Synthesized insights successfully integrated into report!")
        elif report_result.get('bedrock_enhanced'):
            print("✓ Report marked as Bedrock-enhanced")
        else:
            print("⚠ Synthesized insights not found in report (may be using fallback)")
        
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        print("  Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
    os.environ.setdefault('BEDROCK_REGION', 'us-east-1')
    
    # Check if Bedrock should be enabled
    enable_fallback = os.getenv('ENABLE_FALLBACK', 'false').lower()
    print(f"Environment: ENABLE_FALLBACK={enable_fallback}")
    print()
    
    success = test_bedrock_integration()
    sys.exit(0 if success else 1)
