# AgentCore Orchestrator - Developer Guide

## Quick Start

```python
from agentcore_orchestrator import create_agentcore_orchestrator

# Create orchestrator instance
orchestrator = create_agentcore_orchestrator()

# Orchestrate workflow
result = orchestrator.orchestrate_workflow(
    session_id='your-session-id',
    business_info={
        'industry': 'restaurant',
        'region': 'seoul',
        'size': 'small'
    },
    current_step=1
)
```

## Core Methods

### 1. orchestrate_workflow()

Orchestrate the complete 5-step branding workflow.

**Parameters**:
- `session_id` (str): Unique session identifier
- `business_info` (dict): Business information input
- `current_step` (int): Current workflow step (1-5)

**Returns**:
```python
{
    'status': 'success',
    'session_id': 'session-123',
    'current_step': 1,
    'next_step': 2,
    'step_results': {...},
    'reasoning': 'Chain-of-thought explanation',
    'confidence': 0.85,
    'latency_ms': 2500
}
```

### 2. invoke_agent_with_tool()

Invoke an agent using AgentCore Tool Use primitive.

**Parameters**:
- `agent_name` (str): Name of agent to invoke
- `input_data` (dict): Input data for agent
- `session_id` (str, optional): Session ID for tracking

**Returns**:
```python
{
    'tool_name': 'invoke_product_insight',
    'agent_name': 'product_insight',
    'status': 'invoked',
    'reasoning': 'Tool invocation reasoning',
    'input_data': {...},
    'latency_ms': 1200
}
```

### 3. store_workflow_memory()

Store workflow state using AgentCore Memory primitive.

**Parameters**:
- `session_id` (str): Session ID (memory key)
- `step` (int): Workflow step number
- `data` (dict): Data to store

**Returns**: `bool` - True if successful

### 4. retrieve_workflow_memory()

Retrieve workflow state from AgentCore Memory.

**Parameters**:
- `session_id` (str): Session ID (memory key)

**Returns**:
```python
{
    'session_id': 'session-123',
    'retrieved_at': '2025-10-07T12:00:00Z',
    'steps_completed': [1, 2],
    'agent_outputs': {...}
}
```

### 5. reason_next_step()

Use Reasoning LLM to determine next workflow step.

**Parameters**:
- `current_state` (dict): Current workflow state

**Returns**:
```python
{
    'next_step': 2,
    'reasoning': 'Chain-of-thought explanation',
    'confidence': 0.85,
    'current_step': 1,
    'decision_latency_ms': 800
}
```

## Workflow Steps

1. **ANALYSIS** (Step 1)
   - Agents: Product Insight, Market Analyst
   - Purpose: Analyze business information

2. **NAMING** (Step 2)
   - Agent: Reporter
   - Purpose: Generate business name suggestions

3. **SIGNBOARD** (Step 3)
   - Agent: Signboard
   - Purpose: Create signboard designs

4. **INTERIOR** (Step 4)
   - Agent: Interior
   - Purpose: Generate interior recommendations

5. **REPORT** (Step 5)
   - Agent: Report Generator
   - Purpose: Create final branding report

## Environment Variables

```bash
# Required
BEDROCK_REGION=us-west-2

# Optional
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=TSTALIASID
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_MAX_RETRIES=3
BEDROCK_TIMEOUT=30
```

## Error Handling

All methods return structured error responses:

```python
{
    'status': 'error',
    'error': 'Error message',
    'latency_ms': 500
}
```

## Logging

Structured logs are automatically generated:

```json
{
    "bedrock_api_call": "invoke_claude",
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "latency_ms": 2500,
    "status": "success",
    "timestamp": "2025-10-07T12:00:00Z"
}
```

## Best Practices

1. **Always check status**: Verify `result['status'] == 'success'`
2. **Handle errors gracefully**: Implement fallback logic
3. **Monitor latency**: Track `latency_ms` for performance
4. **Use confidence scores**: Check `confidence` for decision quality
5. **Store memory regularly**: Call `store_workflow_memory()` after each step

## Integration with Supervisor Agent

```python
# In supervisor/index.py
from agentcore_orchestrator import create_agentcore_orchestrator

class SupervisorAgent:
    def __init__(self):
        self.orchestrator = create_agentcore_orchestrator()
    
    def execute_workflow(self, session_id, business_info):
        # Use AgentCore for orchestration
        result = self.orchestrator.orchestrate_workflow(
            session_id=session_id,
            business_info=business_info,
            current_step=1
        )
        return result
```

## Testing

Run validation script:

```bash
python scripts/validate-agentcore.py
```

Run integration tests:

```bash
pytest tests/integration/test_agentcore_orchestrator.py -v
```

## Troubleshooting

### Import Errors

If you get import errors, ensure paths are set:

```python
import sys
sys.path.insert(0, 'src/lambda/shared')
from agentcore_orchestrator import create_agentcore_orchestrator
```

### Bedrock Client Errors

Check AWS credentials and region:

```bash
aws configure list
aws bedrock list-foundation-models --region us-west-2
```

### Memory Storage Issues

Verify DynamoDB table exists and has proper permissions.

## Support

- **Documentation**: See `docs/implementation/TASK_5_AGENTCORE_IMPLEMENTATION.md`
- **Tests**: See `tests/integration/test_agentcore_orchestrator.py`
- **Validation**: Run `scripts/validate-agentcore.py`

## License

MIT License - Part of AI Branding Chatbot project
