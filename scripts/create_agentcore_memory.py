#!/usr/bin/env python3
"""
Create Amazon Bedrock AgentCore Memory for AI Branding Chatbot

This script creates a managed memory resource with strategies for:
- Session summarization
- Semantic fact extraction
- 24-hour automatic expiry
"""

import boto3
import sys
from datetime import datetime
from botocore.exceptions import ClientError

def create_agentcore_memory():
    """Create AgentCore Memory with strategies"""
    
    print("🚀 Creating Amazon Bedrock AgentCore Memory")
    print("=" * 60)
    
    try:
        # Initialize AgentCore Control client
        control_client = boto3.client('bedrock-agentcore-control', region_name='us-west-2')
        
        # Create memory with strategies
        print("\n📝 Creating memory resource...")
        response = control_client.create_memory(
            name="ai-branding-chatbot-memory",
            description="Memory for AI branding workflow sessions with 5-step process (Analysis → Names → Signboard → Interior → Report)",
            eventExpiryDuration=1440,  # 24 hours (same as DynamoDB TTL)
            memoryStrategies=[
                {
                    'summaryMemoryStrategy': {
                        'name': 'WorkflowSummarizer',
                        'description': 'Automatically summarize workflow sessions',
                        'namespaces': ['/summaries/{actorId}/{sessionId}']
                    }
                },
                {
                    'semanticMemoryStrategy': {
                        'name': 'BrandingFactExtractor',
                        'description': 'Extract key business insights and branding facts',
                        'namespaces': ['/facts/{actorId}']
                    }
                }
            ]
        )
        
        memory = response['memory']
        memory_id = memory['id']
        memory_status = memory['status']
        
        print(f"✅ AgentCore Memory created successfully!")
        print(f"\n📊 Memory Details:")
        print(f"   Memory ID: {memory_id}")
        print(f"   Name: {memory['name']}")
        print(f"   Status: {memory_status}")
        print(f"   Event Expiry: {memory['eventExpiryDuration']} minutes (24 hours)")
        print(f"   Strategies: {len(memory.get('memoryStrategies', []))}")
        
        # Print strategies
        if 'memoryStrategies' in memory:
            print(f"\n🧠 Memory Strategies:")
            for strategy in memory['memoryStrategies']:
                if 'summaryMemoryStrategy' in strategy:
                    s = strategy['summaryMemoryStrategy']
                    print(f"   • Summary: {s['name']}")
                    print(f"     Namespaces: {', '.join(s['namespaces'])}")
                elif 'semanticMemoryStrategy' in strategy:
                    s = strategy['semanticMemoryStrategy']
                    print(f"   • Semantic: {s['name']}")
                    print(f"     Namespaces: {', '.join(s['namespaces'])}")
        
        # Configuration instructions
        print(f"\n" + "=" * 60)
        print(f"📋 Next Steps:")
        print(f"\n1. Update samconfig.toml:")
        print(f"   [dev.deploy.parameters]")
        print(f"   parameter_overrides = \"...")
        print(f"     AgentCoreMemoryId=\\\"{memory_id}\\\"")
        print(f"     UseAgentCoreMemory=\\\"true\\\"")
        print(f"     ...\"")
        
        print(f"\n2. Or deploy with CLI:")
        print(f"   sam deploy --config-env dev \\")
        print(f"     --parameter-overrides \\")
        print(f"       AgentCoreMemoryId={memory_id} \\")
        print(f"       UseAgentCoreMemory=true")
        
        print(f"\n3. Verify deployment:")
        print(f"   aws lambda get-function-configuration \\")
        print(f"     --function-name ai-branding-chatbot-supervisor-agent-dev \\")
        print(f"     --query 'Environment.Variables.AGENTCORE_MEMORY_ID'")
        
        print(f"\n" + "=" * 60)
        print(f"✨ AgentCore Memory is ready to use!")
        
        return memory_id
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"\n❌ Error creating AgentCore Memory:")
        print(f"   Code: {error_code}")
        print(f"   Message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            print(f"\n💡 Solution:")
            print(f"   Add these permissions to your IAM role:")
            print(f"   - bedrock-agentcore-control:CreateMemory")
            print(f"   - bedrock-agentcore-control:GetMemory")
            print(f"   - bedrock-agentcore-control:ListMemories")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

def list_existing_memories():
    """List existing AgentCore memories"""
    
    try:
        control_client = boto3.client('bedrock-agentcore-control', region_name='us-west-2')
        
        print("\n🔍 Checking existing memories...")
        response = control_client.list_memories()
        
        memories = response.get('memories', [])
        
        if memories:
            print(f"   Found {len(memories)} existing memory resource(s):")
            for memory in memories:
                print(f"   • {memory['name']} (ID: {memory['id']}, Status: {memory['status']})")
            
            # Ask if user wants to use existing
            print(f"\n⚠️  Memory resources already exist.")
            print(f"   You can reuse an existing memory or create a new one.")
            return memories
        else:
            print(f"   No existing memories found.")
            return []
            
    except Exception as e:
        print(f"   Warning: Could not list memories - {str(e)}")
        return []

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Amazon Bedrock AgentCore Memory Setup")
    print("AI Branding Chatbot")
    print("=" * 60)
    
    # Check for existing memories
    existing = list_existing_memories()
    
    if existing:
        print(f"\n❓ Do you want to:")
        print(f"   1. Create a new memory")
        print(f"   2. Use existing memory: {existing[0]['id']}")
        choice = input(f"\nEnter choice (1 or 2): ").strip()
        
        if choice == "2":
            memory_id = existing[0]['id']
            print(f"\n✅ Using existing memory: {memory_id}")
            print(f"\nUpdate samconfig.toml with:")
            print(f"  AgentCoreMemoryId=\"{memory_id}\"")
            sys.exit(0)
    
    # Create new memory
    memory_id = create_agentcore_memory()
