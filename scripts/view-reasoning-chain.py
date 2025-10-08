#!/usr/bin/env python3
"""
View reasoning chain from DynamoDB Local
Pretty print the reasoning data
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda'))


def main():
    """View reasoning chain from DynamoDB"""
    print("="*60)
    print("Viewing Reasoning Chain from DynamoDB Local")
    print("="*60)
    
    try:
        import boto3
        
        # Connect to DynamoDB Local
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        # Scan all sessions
        response = dynamodb.scan(TableName='WorkflowSessions')
        
        if response['Count'] == 0:
            print("\n⚠️  No sessions found in DynamoDB")
            print("\nRun this first:")
            print("  python3 scripts/save-reasoning-to-dynamodb.py")
            return 1
        
        print(f"\n✓ Found {response['Count']} session(s)")
        
        # Display each session
        for idx, item in enumerate(response['Items'], 1):
            print(f"\n" + "="*60)
            print(f"Session {idx}")
            print("="*60)
            
            session_id = item['session_id']['S']
            status = item['status']['S']
            created_at = item['created_at']['S']
            
            print(f"\nSession ID: {session_id}")
            print(f"Status: {status}")
            print(f"Created: {created_at}")
            
            # Parse business info
            if 'business_info' in item:
                business_info = json.loads(item['business_info']['S'])
                print(f"\nBusiness Info:")
                print(f"  Industry: {business_info['industry']}")
                print(f"  Region: {business_info['region']}")
                print(f"  Size: {business_info['size']}")
                if business_info.get('description'):
                    print(f"  Description: {business_info['description']}")
            
            # Parse reasoning chain
            if 'reasoning_chain' in item:
                reasoning_chain = json.loads(item['reasoning_chain']['S'])
                
                print(f"\n" + "-"*60)
                print(f"Reasoning Chain ({len(reasoning_chain)} steps)")
                print("-"*60)
                
                for step in reasoning_chain:
                    print(f"\n📍 Step {step['step_number']}: {step['operation'].upper()}")
                    print(f"   Agent: {step['agent_name']}")
                    print(f"   Timestamp: {step['timestamp']}")
                    print(f"   Decision: {step['decision']}")
                    print(f"   Confidence: {step['confidence']:.2f} ({int(step['confidence'] * 100)}%)")
                    print(f"   Latency: {step['latency_ms']}ms")
                    
                    print(f"\n   💭 Reasoning:")
                    # Wrap reasoning text
                    reasoning = step['reasoning']
                    max_width = 70
                    words = reasoning.split()
                    line = "      "
                    for word in words:
                        if len(line) + len(word) + 1 > max_width:
                            print(line)
                            line = "      " + word
                        else:
                            line += " " + word if line != "      " else word
                    if line.strip():
                        print(line)
                    
                    if step.get('reasoning_steps'):
                        print(f"\n   📝 Reasoning Steps:")
                        for rs in step['reasoning_steps']:
                            print(f"      • {rs}")
                    
                    if step.get('alternatives') and len(step['alternatives']) > 0:
                        print(f"\n   🔄 Alternatives:")
                        for alt in step['alternatives']:
                            if isinstance(alt, dict):
                                if 'option' in alt:
                                    print(f"      • {alt['option']}: {alt.get('score', 'N/A')}")
                                elif 'name' in alt:
                                    print(f"      • {alt['name']}: {alt.get('score', 'N/A')}")
                                elif 'design' in alt:
                                    print(f"      • {alt['design']}: {alt.get('score', 'N/A')}")
                    
                    print()
                
                # Summary statistics
                print("-"*60)
                print("📊 Summary Statistics")
                print("-"*60)
                
                avg_confidence = sum(s['confidence'] for s in reasoning_chain) / len(reasoning_chain)
                total_latency = sum(s['latency_ms'] for s in reasoning_chain)
                
                print(f"  Total Steps: {len(reasoning_chain)}")
                print(f"  Average Confidence: {avg_confidence:.2f} ({int(avg_confidence * 100)}%)")
                print(f"  Total Latency: {total_latency}ms ({total_latency/1000:.1f}s)")
                
                # By agent
                from collections import defaultdict
                by_agent = defaultdict(int)
                for step in reasoning_chain:
                    by_agent[step['agent_name']] += 1
                
                print(f"\n  By Agent:")
                for agent, count in by_agent.items():
                    print(f"    • {agent}: {count} step(s)")
                
                # By operation
                by_operation = defaultdict(int)
                for step in reasoning_chain:
                    by_operation[step['operation']] += 1
                
                print(f"\n  By Operation:")
                for operation, count in by_operation.items():
                    print(f"    • {operation}: {count} step(s)")
        
        print(f"\n" + "="*60)
        print("✓ View Complete")
        print("="*60)
        
        print(f"\nTo view in DynamoDB Admin UI:")
        print(f"  http://localhost:8002")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
