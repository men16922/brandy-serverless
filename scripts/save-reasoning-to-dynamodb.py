#!/usr/bin/env python3
"""
Save ReasoningEngine results to DynamoDB Local (without cleanup)
Leaves data in DynamoDB for inspection
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda'))

from shared.models import (
    WorkflowSession, BusinessInfo, ReasoningStep
)
from shared.reasoning_engine import ReasoningEngine


def main():
    """Save reasoning data to DynamoDB Local"""
    print("="*60)
    print("Saving Reasoning Data to DynamoDB Local")
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
        
        print("\n✓ Connected to DynamoDB Local (http://localhost:8000)")
        
        # Create table if not exists
        try:
            dynamodb.describe_table(TableName='WorkflowSessions')
            print("✓ Table 'WorkflowSessions' exists")
        except:
            print("\nCreating table 'WorkflowSessions'...")
            dynamodb.create_table(
                TableName='WorkflowSessions',
                KeySchema=[
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'session_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print("✓ Table created")
        
        # Create session with business info
        print("\n" + "="*60)
        print("Creating Session with Reasoning Chain")
        print("="*60)
        
        business_info = BusinessInfo(
            industry='restaurant',
            region='seoul',
            size='small',
            description='Modern cafe targeting young professionals in Gangnam'
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"\n✓ Session created: {session.session_id}")
        
        # Check if Bedrock is available
        try:
            engine = ReasoningEngine()
            print("✓ ReasoningEngine initialized")
            
            # Use real Bedrock API
            print("\n" + "-"*60)
            print("Calling Bedrock Claude to evaluate business name...")
            print("-"*60)
            
            result = engine.evaluate_business_name(
                name='CafeBreeze',
                business_info={
                    'industry': 'restaurant',
                    'region': 'seoul',
                    'size': 'small'
                }
            )
            
            print(f"\n✓ Evaluation complete!")
            print(f"  Name: {result['name']}")
            print(f"  Overall Score: {result['overall_score']}/100")
            print(f"  Confidence: {result['confidence']}")
            
            # Create ReasoningStep from real result
            reasoning_step = ReasoningStep(
                step_number=1,
                agent_name='reporter',
                timestamp=result['timestamp'],
                operation='evaluation',
                input_data={'name': 'CafeBreeze', 'industry': 'restaurant'},
                reasoning=result['reasoning'],
                decision=result['name'],
                confidence=result['confidence'],
                alternatives=[],
                reasoning_steps=[
                    f"Pronunciation: {result['pronunciation_score']}/100",
                    f"Memorability: {result['memorability_score']}/100",
                    f"Brand Fit: {result['brand_fit_score']}/100"
                ],
                latency_ms=result['latency_ms']
            )
            
            session.add_reasoning_step(reasoning_step)
            print(f"\n✓ Reasoning step added (from real Bedrock API)")
            
        except Exception as e:
            print(f"\n⚠️  Bedrock not available, using mock data: {str(e)}")
            
            # Add mock reasoning steps
            step1 = ReasoningStep(
                step_number=1,
                agent_name='product_insight',
                timestamp=datetime.utcnow().isoformat(),
                operation='decision',
                input_data={
                    'industry': 'restaurant',
                    'region': 'seoul',
                    'target_audience': 'young professionals'
                },
                reasoning='Young professionals in Seoul prefer modern, Instagram-worthy spaces with industrial chic aesthetics. The Gangnam area specifically favors trendy, sophisticated designs.',
                decision='Industrial Chic',
                confidence=0.88,
                alternatives=[
                    {'option': 'Modern Minimalist', 'score': 85},
                    {'option': 'Traditional Korean', 'score': 72}
                ],
                reasoning_steps=[
                    'Analyzed target demographic preferences',
                    'Evaluated Gangnam location characteristics',
                    'Compared design style options',
                    'Assessed social media appeal',
                    'Made final recommendation'
                ],
                latency_ms=20000
            )
            
            step2 = ReasoningStep(
                step_number=2,
                agent_name='reporter',
                timestamp=datetime.utcnow().isoformat(),
                operation='evaluation',
                input_data={'name': 'CafeBreeze', 'industry': 'restaurant'},
                reasoning='CafeBreeze is easy to pronounce for both Korean and English speakers (85/100). The name is memorable and evokes a fresh, relaxed atmosphere (75/100). Brand fit is good for a casual restaurant (70/100).',
                decision='CafeBreeze',
                confidence=0.85,
                alternatives=[
                    {'name': 'UrbanBite', 'score': 75},
                    {'name': 'FreshFusion', 'score': 70}
                ],
                reasoning_steps=[
                    'Pronunciation: 85/100 - Easy for bilingual speakers',
                    'Memorability: 75/100 - Fresh and catchy',
                    'Brand Fit: 70/100 - Matches casual dining'
                ],
                latency_ms=12000
            )
            
            step3 = ReasoningStep(
                step_number=3,
                agent_name='signboard',
                timestamp=datetime.utcnow().isoformat(),
                operation='ranking',
                input_data={'designs': ['modern', 'classic', 'playful']},
                reasoning='Modern design ranks highest (88/100) for young professional target audience. Clean lines and minimalist approach align with brand identity.',
                decision='modern',
                confidence=0.90,
                alternatives=[
                    {'design': 'classic', 'score': 75},
                    {'design': 'playful', 'score': 62}
                ],
                reasoning_steps=[
                    'Evaluated visual appeal',
                    'Assessed target audience fit',
                    'Compared brand alignment',
                    'Ranked by overall score'
                ],
                latency_ms=10000
            )
            
            session.add_reasoning_step(step1)
            session.add_reasoning_step(step2)
            session.add_reasoning_step(step3)
            
            print(f"\n✓ Added {len(session.reasoning_chain)} mock reasoning steps")
        
        # Save to DynamoDB
        print("\n" + "="*60)
        print("Saving to DynamoDB Local")
        print("="*60)
        
        session_dict = session.to_dict()
        
        # Prepare DynamoDB item
        item = {
            'session_id': {'S': session_dict['session_id']},
            'current_step': {'N': str(session_dict['current_step'])},
            'status': {'S': session_dict['status']},
            'created_at': {'S': session_dict['created_at']},
            'updated_at': {'S': session_dict['updated_at']},
            'ttl': {'N': str(session_dict['ttl'])},
            'business_info': {'S': session_dict['business_info']},
            'reasoning_chain': {'S': session_dict['reasoning_chain']}
        }
        
        # Add optional fields if present
        if session_dict.get('analysis_result'):
            item['analysis_result'] = {'S': session_dict['analysis_result']}
        if session_dict.get('business_names'):
            item['business_names'] = {'S': session_dict['business_names']}
        if session_dict.get('agent_logs'):
            item['agent_logs'] = {'S': session_dict['agent_logs']}
        
        dynamodb.put_item(
            TableName='WorkflowSessions',
            Item=item
        )
        
        print(f"\n✓ Session saved to DynamoDB!")
        print(f"  Session ID: {session.session_id}")
        print(f"  Reasoning steps: {len(session.reasoning_chain)}")
        print(f"  Reasoning chain size: {len(session_dict['reasoning_chain'])} chars")
        
        # Display reasoning chain summary
        print(f"\n" + "="*60)
        print("Reasoning Chain Summary")
        print("="*60)
        
        for step in session.reasoning_chain:
            print(f"\nStep {step.step_number}: {step.operation.upper()}")
            print(f"  Agent: {step.agent_name}")
            print(f"  Decision: {step.decision}")
            print(f"  Confidence: {step.confidence:.2f} ({int(step.confidence * 100)}%)")
            print(f"  Latency: {step.latency_ms}ms")
            print(f"  Reasoning: {step.reasoning[:100]}...")
        
        # How to view the data
        print(f"\n" + "="*60)
        print("How to View the Data")
        print("="*60)
        print(f"\n1. DynamoDB Admin UI:")
        print(f"   http://localhost:8002")
        print(f"   → Select 'WorkflowSessions' table")
        print(f"   → Find session: {session.session_id}")
        
        print(f"\n2. AWS CLI:")
        print(f"   aws dynamodb get-item \\")
        print(f"     --table-name WorkflowSessions \\")
        print(f"     --key '{{'\"session_id\": {{'\"S\": \"{session.session_id}\"}}}}' \\")
        print(f"     --endpoint-url http://localhost:8000")
        
        print(f"\n3. Python boto3:")
        print(f"   dynamodb.get_item(")
        print(f"       TableName='WorkflowSessions',")
        print(f"       Key={{'session_id': {{'S': '{session.session_id}'}}}}")
        print(f"   )")
        
        print(f"\n" + "="*60)
        print("✓ DATA SAVED SUCCESSFULLY!")
        print("="*60)
        print(f"\nData is now in DynamoDB Local and will persist until you:")
        print(f"  - Stop the Docker container")
        print(f"  - Delete the table")
        print(f"  - Delete the item")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
