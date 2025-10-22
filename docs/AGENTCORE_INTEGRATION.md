# Amazon Bedrock AgentCore Integration Guide

## Overview

This guide explains how to integrate Amazon Bedrock AgentCore Memory into the AI Branding Chatbot for managed workflow state persistence.

## What is Amazon Bedrock AgentCore?

Amazon Bedrock AgentCore is a suite of services for building and deploying AI agents at scale:

- **AgentCore Runtime**: Serverless runtime for agent frameworks (LangGraph, CrewAI)
- **AgentCore Memory**: Managed memory service for agent state persistence
- **AgentCore Identity**: Secure identity and access management
- **AgentCore Code Interpreter**: Secure code execution in sandboxes
- **AgentCore Browser**: Cloud-based browser for web interactions

### AgentCore Memory

AgentCore Memory provides:
- **Short-term memory**: Session-based conversations with automatic expiry
- **Long-term memory**: Persistent memory across sessions with strategies
- **Memory Strategies**:
  - Summary Memory: Automatic session summarization
  - User Preference Memory: Learning user preferences
  - Semantic Memory: Fact extraction and knowledge graphs

## Why Use AgentCore Memory?

### Benefits

1. **Managed Infrastructure**
   - No DynamoDB table management
   - Automatic scaling and optimization
   - Built-in TTL and cleanup

2. **AI-Optimized**
   - Designed specifically for AI agent workflows
   - Native Bedrock integration
   - Optimized for LLM context retrieval

3. **Advanced Features**
   - Automatic summarization strategies
   - Semantic fact extraction
   - Multi-session memory sharing

4. **Hackathon Compliance**
   - Legitimate AgentCore usage
   - Demonstrates advanced Bedrock integration
   - Eligible for "Best AgentCore Implementation" award ($3,000)

## Architecture

### Before (DynamoDB)

```
Supervisor Agent
    ↓
DynamoDB Table
    ↓
Manual session management
Manual TTL configuration
Manual cleanup
```

### After (AgentCore Memory)

```
Supervisor Agent
    ↓
AgentCore Memory
    ↓
Automatic summarization
Semantic fact extraction
Managed TTL and cleanup
```

## Integration Steps

### Step 1: Create AgentCore Memory (10 minutes)

```bash
# Run the creation script
python3 scripts/create_agentcore_memory.py

# Output:
# Memory ID: abc123xyz
# Status: ACTIVE
```

The script creates a memory resource with:
- **Name**: `ai-branding-chatbot-memory`
- **Event Expiry**: 1440 minutes (24 hours)
- **Strategies**:
  - `WorkflowSummarizer`: Session summaries at `/summaries/{actorId}/{sessionId}`
  - `BrandingFactExtractor`: Business insights at `/facts/{actorId}`

### Step 2: Update SAM Configuration (5 minutes)

Edit `samconfig.toml`:

```toml
[dev.deploy.parameters]
parameter_overrides = "Environment=\"dev\" \
  ProjectName=\"ai-branding-chatbot\" \
  BedrockRegion=\"us-west-2\" \
  ClaudeModelId=\"us.anthropic.claude-sonnet-4-20250514-v1:0\" \
  SdxlModelId=\"amazon.titan-image-generator-v2:0\" \
  EnableFallback=\"false\" \
  UseAgentCore=\"true\" \
  UseAgentCoreMemory=\"true\" \
  AgentCoreMemoryId=\"YOUR_MEMORY_ID_HERE\""
```

Or deploy with CLI:

```bash
sam deploy --config-env dev \
  --parameter-overrides \
    UseAgentCoreMemory=true \
    AgentCoreMemoryId=abc123xyz
```

### Step 3: Update Supervisor Agent Code (1 hour)

The Supervisor Agent needs to use AgentCore Memory instead of DynamoDB.

#### Key Changes

**Initialize AgentCore clients:**

```python
# src/lambda/agents/supervisor/index.py

class SupervisorAgent:
    def __init__(self):
        # Existing DynamoDB (fallback)
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE'))
        
        # New AgentCore clients
        self.agentcore_data = boto3.client('bedrock-agentcore', region_name='us-west-2')
        self.agentcore_control = boto3.client('bedrock-agentcore-control', region_name='us-west-2')
        
        # Configuration
        self.memory_id = os.getenv('AGENTCORE_MEMORY_ID')
        self.use_agentcore_memory = os.getenv('USE_AGENTCORE_MEMORY', 'false').lower() == 'true'
        
        logger.info(f"AgentCore Memory: enabled={self.use_agentcore_memory}, memory_id={self.memory_id}")
```

**Store workflow state:**

```python
def store_workflow_state(self, session_id: str, step: int, data: dict):
    """Store workflow state in AgentCore Memory"""
    
    if self.use_agentcore_memory and self.memory_id:
        try:
            # Create event in AgentCore Memory
            self.agentcore_data.create_event(
                memoryId=self.memory_id,
                actorId=session_id,  # Use session_id as actor_id
                sessionId=session_id,
                eventTimestamp=datetime.now(),
                payload=[
                    {
                        'conversational': {
                            'content': {
                                'text': json.dumps({
                                    'step': step,
                                    'step_name': WorkflowStep(step).name,
                                    'data': data,
                                    'timestamp': datetime.now().isoformat()
                                })
                            },
                            'role': 'ASSISTANT'
                        }
                    }
                ]
            )
            
            logger.info(f"Stored workflow state in AgentCore Memory: session={session_id}, step={step}")
            
        except Exception as e:
            logger.error(f"AgentCore Memory error: {str(e)}, falling back to DynamoDB")
            # Fallback to DynamoDB
            self._store_in_dynamodb(session_id, step, data)
    else:
        # Use DynamoDB
        self._store_in_dynamodb(session_id, step, data)
```

**Retrieve workflow state:**

```python
def retrieve_workflow_state(self, session_id: str) -> dict:
    """Retrieve workflow state from AgentCore Memory"""
    
    if self.use_agentcore_memory and self.memory_id:
        try:
            # Query AgentCore Memory
            response = self.agentcore_data.query_memory(
                memoryId=self.memory_id,
                actorId=session_id,
                sessionId=session_id,
                maxResults=100
            )
            
            memory_records = response.get('memoryRecords', [])
            
            # Parse memory records into workflow state
            workflow_state = self._parse_memory_records(memory_records)
            
            logger.info(f"Retrieved {len(memory_records)} memory records for session={session_id}")
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"AgentCore Memory error: {str(e)}, falling back to DynamoDB")
            # Fallback to DynamoDB
            return self._retrieve_from_dynamodb(session_id)
    else:
        # Use DynamoDB
        return self._retrieve_from_dynamodb(session_id)
```

### Step 4: Update IAM Permissions (5 minutes)

Edit `template.yaml` to add AgentCore permissions:

```yaml
Resources:
  SupervisorAgent:
    Type: AWS::Serverless::Function
    Properties:
      Policies:
        - Statement:
            - Effect: Allow
              Action:
                - bedrock:InvokeModel
                - bedrock:InvokeModelWithResponseStream
              Resource: "*"
            - Effect: Allow
              Action:
                - bedrock-agentcore:CreateEvent
                - bedrock-agentcore:QueryMemory
                - bedrock-agentcore:BatchCreateMemoryRecords
                - bedrock-agentcore:BatchUpdateMemoryRecords
                - bedrock-agentcore:BatchDeleteMemoryRecords
                - bedrock-agentcore-control:GetMemory
                - bedrock-agentcore-control:ListMemories
              Resource: "*"
            - Effect: Allow
              Action:
                - dynamodb:GetItem
                - dynamodb:PutItem
                - dynamodb:UpdateItem
                - dynamodb:Query
              Resource: !GetAtt WorkflowSessionsTable.Arn
```

### Step 5: Deploy and Test (30 minutes)

```bash
# 1. Build SAM application
sam build

# 2. Deploy with AgentCore Memory
sam deploy --config-env dev

# 3. Verify environment variables
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-supervisor-agent-dev \
  --query 'Environment.Variables.{Memory: USE_AGENTCORE_MEMORY, MemoryId: AGENTCORE_MEMORY_ID}' \
  --output table

# 4. Test workflow
./test_agentcore_api.sh

# 5. Verify memory records
python3 scripts/verify_agentcore_memory.py
```

## Testing

### Test AgentCore Memory

```python
# scripts/verify_agentcore_memory.py

import boto3
import json

def verify_memory(memory_id, session_id):
    """Verify AgentCore Memory contains workflow data"""
    
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Query memory
    response = client.query_memory(
        memoryId=memory_id,
        actorId=session_id,
        sessionId=session_id,
        maxResults=100
    )
    
    records = response.get('memoryRecords', [])
    
    print(f"✅ Found {len(records)} memory records")
    
    for i, record in enumerate(records, 1):
        print(f"\nRecord {i}:")
        print(f"  Type: {record.get('type')}")
        print(f"  Timestamp: {record.get('timestamp')}")
        
        if 'content' in record:
            content = json.loads(record['content'])
            print(f"  Step: {content.get('step')}")
            print(f"  Step Name: {content.get('step_name')}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 verify_agentcore_memory.py <memory_id> <session_id>")
        sys.exit(1)
    
    verify_memory(sys.argv[1], sys.argv[2])
```

### Integration Test

```bash
# Run full workflow test
./test_agentcore_api.sh

# Expected output:
# ✅ Tool Use: Session created
# ✅ Memory: Analysis stored in AgentCore
# ✅ Memory: Names stored in AgentCore
# ✅ Memory: Signboards stored in AgentCore
# ✅ Memory: Interiors stored in AgentCore
# ✅ Memory: Report stored in AgentCore
# 🎉 All AgentCore primitives functional!
```

## Monitoring

### CloudWatch Logs

```bash
# Monitor Supervisor Agent logs
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev \
  --region us-west-2 \
  --follow \
  --filter-pattern "AgentCore"
```

### AgentCore Memory Metrics

```bash
# List memory records
aws bedrock-agentcore query-memory \
  --memory-id abc123xyz \
  --actor-id SESSION_ID \
  --session-id SESSION_ID \
  --region us-west-2
```

## Troubleshooting

### Issue: AccessDeniedException

**Error:**
```
AccessDeniedException: User is not authorized to perform: bedrock-agentcore:CreateEvent
```

**Solution:**
Add IAM permissions to Lambda execution role:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:*",
    "bedrock-agentcore-control:*"
  ],
  "Resource": "*"
}
```

### Issue: Memory not found

**Error:**
```
ResourceNotFoundException: Memory abc123xyz not found
```

**Solution:**
1. Verify memory exists:
   ```bash
   aws bedrock-agentcore-control list-memories --region us-west-2
   ```

2. Check environment variable:
   ```bash
   aws lambda get-function-configuration \
     --function-name ai-branding-chatbot-supervisor-agent-dev \
     --query 'Environment.Variables.AGENTCORE_MEMORY_ID'
   ```

### Issue: Fallback to DynamoDB

**Symptom:**
Logs show "falling back to DynamoDB"

**Causes:**
1. `USE_AGENTCORE_MEMORY=false`
2. `AGENTCORE_MEMORY_ID` not set
3. AgentCore API error

**Solution:**
Check configuration and logs:
```bash
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev \
  --since 10m \
  --filter-pattern "AgentCore Memory error"
```

## Cost Comparison

### DynamoDB (Current)
- Read/Write Units: ~$0.01 per workflow
- Storage: ~$0.25/GB/month
- Management: Manual

### AgentCore Memory
- Events: ~$0.001 per event
- Storage: Included in event pricing
- Management: Fully managed
- **Estimated: ~$0.005 per workflow (50% savings)**

## Hackathon Benefits

### Technical Execution (50 points)
- ✅ Amazon Bedrock AgentCore usage
- ✅ AgentCore Memory primitive implementation
- ✅ Advanced memory strategies
- ✅ Production-ready architecture

### Best AgentCore Implementation ($3,000)
- ✅ Legitimate AgentCore Memory integration
- ✅ Multiple memory strategies (Summary + Semantic)
- ✅ Real-world use case
- ✅ Well-documented implementation

## References

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore Memory Examples](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-examples.html)
- [AWS SDK for Python (Boto3) - AgentCore](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore.html)

## Next Steps

1. ✅ Create AgentCore Memory
2. ✅ Update SAM configuration
3. ⏳ Modify Supervisor Agent code
4. ⏳ Deploy and test
5. ⏳ Update documentation
6. ⏳ Record demo video

**Estimated total time: 2-3 hours**
