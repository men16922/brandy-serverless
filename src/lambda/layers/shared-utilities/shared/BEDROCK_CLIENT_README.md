# Bedrock Client Module

## Overview

The `bedrock_client.py` module provides a unified interface for Amazon Bedrock services, including:
- **Claude 4.0 Sonnet** - Reasoning and text generation
- **Stable Diffusion XL (SDXL)** - Image generation
- **Knowledge Base** - Vector search and retrieval

## Features

✅ **Automatic Retry Logic** - Exponential backoff for throttling and service unavailability
✅ **Structured Logging** - JSON-formatted logs with latency, tokens, and status
✅ **Error Handling** - Specific exceptions for different error types
✅ **Environment Configuration** - Flexible configuration via environment variables
✅ **Type Safety** - Full type hints for better IDE support

## Installation

The module requires `boto3` and is included in the Lambda layer dependencies:

```bash
pip install boto3
```

## Quick Start

```python
from bedrock_client import create_bedrock_client

# Create client
client = create_bedrock_client(region='us-west-2')

# Generate text with Claude
response = client.invoke_claude(
    prompt="Explain quantum computing in simple terms",
    max_tokens=500,
    temperature=0.7
)
print(response['text'])

# Generate image with SDXL
image_response = client.invoke_sdxl(
    prompt="A modern coffee shop interior with warm lighting",
    width=1024,
    height=1024
)
# image_response['image_base64'] contains the base64-encoded image

# Query Knowledge Base
kb_response = client.query_knowledge_base(
    query="What are the latest market trends in retail?",
    max_results=5
)
for result in kb_response['results']:
    print(f"Score: {result['score']}, Content: {result['content']}")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_REGION` | `us-west-2` | AWS region for Bedrock services |
| `CLAUDE_MODEL_ID` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Claude 4 Sonnet model ID |
| `SDXL_MODEL_ID` | `stability.stable-diffusion-xl-v1` | SDXL model ID |
| `BEDROCK_KB_ID` | None | Knowledge Base ID (required for KB queries) |
| `BEDROCK_MAX_RETRIES` | `3` | Maximum retry attempts |
| `BEDROCK_TIMEOUT` | `30` | Request timeout in seconds |

## API Reference

### BedrockClient

#### `__init__(region: str = None, logger: logging.Logger = None)`

Initialize Bedrock client.

**Parameters:**
- `region` (str, optional): AWS region. Defaults to `BEDROCK_REGION` env var or `us-west-2`
- `logger` (logging.Logger, optional): Custom logger instance

**Raises:**
- `BedrockException`: If client initialization fails

---

#### `invoke_claude(prompt: str, system_prompt: str = None, max_tokens: int = 2048, temperature: float = 0.7, top_p: float = 0.9, stop_sequences: List[str] = None) -> Dict[str, Any]`

Invoke Claude 4.0 Sonnet for text generation.

**Parameters:**
- `prompt` (str): User prompt/question
- `system_prompt` (str, optional): System instructions
- `max_tokens` (int): Maximum tokens to generate (default: 2048)
- `temperature` (float): Sampling temperature 0-1 (default: 0.7)
- `top_p` (float): Nucleus sampling parameter (default: 0.9)
- `stop_sequences` (List[str], optional): Stop sequences

**Returns:**
```python
{
    'text': str,              # Generated text
    'stop_reason': str,       # Why generation stopped
    'usage': {                # Token usage
        'input_tokens': int,
        'output_tokens': int,
        'total_tokens': int
    },
    'latency_ms': int,        # API call latency
    'model_id': str           # Model ID used
}
```

**Raises:**
- `ThrottlingException`: API rate limit exceeded
- `ValidationException`: Invalid parameters
- `ServiceUnavailableException`: Service temporarily unavailable
- `BedrockException`: Other API errors

**Example:**
```python
response = client.invoke_claude(
    prompt="Write a business name for a modern cafe",
    system_prompt="You are a creative branding expert",
    max_tokens=100,
    temperature=0.8
)
print(response['text'])
print(f"Used {response['usage']['total_tokens']} tokens")
```

---

#### `invoke_sdxl(prompt: str, negative_prompt: str = None, width: int = 1024, height: int = 1024, cfg_scale: float = 7.0, steps: int = 30, seed: int = None) -> Dict[str, Any]`

Invoke Stable Diffusion XL for image generation.

**Parameters:**
- `prompt` (str): Image generation prompt
- `negative_prompt` (str, optional): What to avoid in the image
- `width` (int): Image width, must be divisible by 64 (default: 1024)
- `height` (int): Image height, must be divisible by 64 (default: 1024)
- `cfg_scale` (float): Classifier-free guidance scale (default: 7.0)
- `steps` (int): Number of diffusion steps (default: 30)
- `seed` (int, optional): Random seed for reproducibility

**Returns:**
```python
{
    'image_base64': str,      # Base64-encoded image
    'seed': int,              # Seed used (for reproducibility)
    'finish_reason': str,     # Completion reason
    'latency_ms': int,        # API call latency
    'model_id': str           # Model ID used
}
```

**Raises:**
- `ValidationException`: Invalid dimensions or parameters
- `ThrottlingException`: API rate limit exceeded
- `ServiceUnavailableException`: Service temporarily unavailable
- `BedrockException`: Other API errors

**Example:**
```python
response = client.invoke_sdxl(
    prompt="Modern minimalist cafe signboard with coffee cup logo",
    negative_prompt="blurry, low quality, distorted",
    width=1024,
    height=1024,
    cfg_scale=7.5,
    steps=40
)

# Save image
import base64
image_data = base64.b64decode(response['image_base64'])
with open('signboard.png', 'wb') as f:
    f.write(image_data)
```

---

#### `query_knowledge_base(query: str, kb_id: str = None, max_results: int = 5, min_score: float = 0.5) -> Dict[str, Any]`

Query Bedrock Knowledge Base for vector search.

**Parameters:**
- `query` (str): Search query
- `kb_id` (str, optional): Knowledge Base ID. Defaults to `BEDROCK_KB_ID` env var
- `max_results` (int): Maximum results to return (default: 5)
- `min_score` (float): Minimum relevance score 0-1 (default: 0.5)

**Returns:**
```python
{
    'results': [              # List of search results
        {
            'content': str,   # Retrieved text content
            'score': float,   # Relevance score (0-1)
            'location': dict, # Source location metadata
            'metadata': dict  # Additional metadata
        }
    ],
    'total_results': int,     # Number of results returned
    'latency_ms': int,        # API call latency
    'kb_id': str              # Knowledge Base ID used
}
```

**Raises:**
- `ValidationException`: KB ID not provided
- `ThrottlingException`: API rate limit exceeded
- `ServiceUnavailableException`: Service temporarily unavailable
- `BedrockException`: Other API errors

**Example:**
```python
response = client.query_knowledge_base(
    query="What are the latest trends in restaurant design?",
    max_results=3,
    min_score=0.7
)

for result in response['results']:
    print(f"Score: {result['score']:.2f}")
    print(f"Content: {result['content'][:200]}...")
    print("---")
```

---

#### `invoke_with_retry(func: Callable, max_retries: int = None) -> Any`

Execute function with exponential backoff retry logic.

**Parameters:**
- `func` (Callable): Function to execute
- `max_retries` (int, optional): Maximum retry attempts. Defaults to `BEDROCK_MAX_RETRIES`

**Returns:**
- Function result

**Raises:**
- `ThrottlingException`: Max retries exceeded due to throttling
- `ServiceUnavailableException`: Service unavailable after retries
- Original exception for non-retryable errors

**Retry Strategy:**
- Attempt 1: Immediate
- Attempt 2: Wait 1 second
- Attempt 3: Wait 2 seconds
- Attempt 4: Wait 4 seconds
- And so on (exponential backoff)

**Example:**
```python
# Automatically used internally by invoke_claude, invoke_sdxl, etc.
# Can also be used for custom Bedrock API calls:

def custom_bedrock_call():
    return bedrock_runtime.invoke_model(...)

result = client.invoke_with_retry(custom_bedrock_call, max_retries=5)
```

## Exception Hierarchy

```
BedrockException (base)
├── ThrottlingException (retryable)
├── ValidationException (not retryable)
└── ServiceUnavailableException (retryable)
```

### Exception Handling Examples

```python
from bedrock_client import (
    BedrockClient,
    ThrottlingException,
    ValidationException,
    ServiceUnavailableException
)

client = BedrockClient()

try:
    response = client.invoke_claude(prompt="Hello")
except ThrottlingException as e:
    # Rate limit exceeded - already retried automatically
    print(f"API throttled after retries: {e}")
except ValidationException as e:
    # Invalid parameters - fix your request
    print(f"Invalid request: {e}")
except ServiceUnavailableException as e:
    # Service down - try again later
    print(f"Service unavailable: {e}")
except BedrockException as e:
    # Other Bedrock errors
    print(f"Bedrock error: {e}")
```

## Structured Logging

All API calls are logged with structured JSON data:

```json
{
  "bedrock_api_call": "invoke_claude",
  "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "latency_ms": 2341,
  "status": "success",
  "timestamp": "2025-10-07T12:00:00.000Z",
  "region": "us-west-2",
  "tokens_used": 156
}
```

### Log Fields

| Field | Description |
|-------|-------------|
| `bedrock_api_call` | Operation name (invoke_claude, invoke_sdxl, query_knowledge_base) |
| `model_id` | Bedrock model ID or KB ID |
| `latency_ms` | API call latency in milliseconds |
| `status` | 'success' or 'error' |
| `timestamp` | ISO 8601 timestamp |
| `region` | AWS region |
| `tokens_used` | Token count (Claude only) |
| `results_count` | Number of results (KB queries only) |
| `error_message` | Error details (if status is 'error') |

## Integration with BaseAgent

The Bedrock client integrates seamlessly with the existing `BaseAgent` class:

```python
from base_agent import BaseAgent
from bedrock_client import create_bedrock_client
from models import AgentType

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.REPORTER)
        
        # Initialize Bedrock client with agent's logger
        self.bedrock_client = create_bedrock_client(
            region=self.region,
            logger=self.logger
        )
    
    def execute(self, event, context):
        session_id = event.get('sessionId')
        self.start_execution(session_id, 'generate_name')
        
        try:
            # Use Bedrock for reasoning
            response = self.bedrock_client.invoke_claude(
                prompt="Generate a creative business name",
                max_tokens=100
            )
            
            result = {'name': response['text']}
            self.end_execution(status='success', result=result)
            
            return self.create_lambda_response(200, result)
            
        except Exception as e:
            return self.create_lambda_response(
                500,
                self.handle_error(e, 'execute')
            )
```

## Performance Considerations

### Latency Expectations

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| Claude (short) | 1-3 seconds | ~100 tokens |
| Claude (long) | 3-10 seconds | ~2000 tokens |
| SDXL | 10-20 seconds | 1024x1024, 30 steps |
| Knowledge Base | 1-2 seconds | 5 results |

### Cost Optimization

1. **Token Management**: Use `max_tokens` to limit Claude costs
2. **Image Resolution**: Use 1024x1024 for demos (lower for testing)
3. **KB Queries**: Set appropriate `max_results` and `min_score`
4. **Caching**: Cache frequent queries in DynamoDB

### Rate Limits

Bedrock has service quotas that vary by model and region. The client automatically retries on throttling with exponential backoff.

**Recommended:**
- Monitor CloudWatch metrics for throttling
- Implement application-level rate limiting
- Use reserved capacity for production workloads

## Testing

### Unit Testing (Mock Bedrock)

```python
from unittest.mock import Mock, patch
from bedrock_client import BedrockClient

def test_invoke_claude():
    with patch('boto3.client') as mock_boto:
        # Mock Bedrock response
        mock_runtime = Mock()
        mock_runtime.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{'text': 'Test response'}],
                'usage': {'total_tokens': 10}
            }).encode())
        }
        mock_boto.return_value = mock_runtime
        
        client = BedrockClient()
        response = client.invoke_claude(prompt="Test")
        
        assert response['text'] == 'Test response'
        assert response['usage']['total_tokens'] == 10
```

### Integration Testing (Real Bedrock)

See `tests/integration/test_bedrock_integration.py` for full integration tests using Docker Compose environment.

## Troubleshooting

### Common Issues

**1. "No module named 'boto3'"**
```bash
pip install boto3
```

**2. "Unable to locate credentials"**
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2
```

**3. "ThrottlingException: Rate exceeded"**
- Reduce request frequency
- Implement exponential backoff (already built-in)
- Request quota increase from AWS Support

**4. "ValidationException: Invalid model ID"**
- Verify model availability: `aws bedrock list-foundation-models --region us-west-2`
- Check model ID spelling
- Ensure model is available in your region

**5. "ServiceUnavailableException"**
- Temporary service issue
- Client automatically retries
- Check AWS Service Health Dashboard

## Requirements

Satisfies the following hackathon requirements:

- ✅ **Requirement 1.1**: Amazon Bedrock as primary LLM provider
- ✅ **Requirement 1.2**: Claude 4.0 Sonnet for reasoning and text generation
- ✅ **Requirement 1.7**: Proper error handling and retry logic
- ✅ **Requirement 5.2**: Bedrock SDXL API integration
- ✅ **Requirement 5.6**: Bedrock Knowledge Base integration

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 4.0 Sonnet Model Card](https://docs.anthropic.com/claude/docs/models-overview)
- [Stable Diffusion XL Documentation](https://stability.ai/stable-diffusion)
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)

## License

MIT License - See project root LICENSE file
