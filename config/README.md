# Configuration Module

This directory contains configuration management for the AI Branding Chatbot project.

## Bedrock Configuration

The `bedrock_config.py` module provides centralized configuration for Amazon Bedrock services.

### Usage

```python
from config.bedrock_config import BedrockConfig, get_bedrock_config

# Get configuration from environment variables
config = BedrockConfig.from_env()

# Or use the global singleton
config = get_bedrock_config()

# Check feature flags
if config.is_fallback_enabled():
    print("Fallback to OpenAI/Gemini is enabled")

if config.is_agentcore_enabled():
    print("Bedrock AgentCore is configured")

if config.is_knowledge_base_enabled():
    print("Bedrock Knowledge Base is configured")

# Get API parameters
claude_params = config.get_claude_params(temperature=0.8)
sdxl_params = config.get_sdxl_params(width=512, height=512)

# Validate configuration
issues = config.validate()
if issues:
    for issue in issues:
        print(f"Configuration issue: {issue}")
```

### Environment Variables

#### Required Variables

- `BEDROCK_REGION`: AWS region for Bedrock services (default: `us-east-1`)
- `CLAUDE_MODEL_ID`: Model ID for Claude 3.5 Sonnet (default: `anthropic.claude-3-5-sonnet-20241022-v2:0`)
- `SDXL_MODEL_ID`: Model ID for Stable Diffusion XL (default: `stability.stable-diffusion-xl-v1`)

#### Optional Variables

- `BEDROCK_KB_ID`: Bedrock Knowledge Base ID for vector search
- `BEDROCK_AGENT_ID`: Bedrock Agent ID for AgentCore orchestration
- `BEDROCK_AGENT_ALIAS_ID`: Bedrock Agent Alias ID for AgentCore
- `ENABLE_FALLBACK`: Enable fallback to OpenAI/Gemini (`true`/`false`, default: `false`)
- `BEDROCK_MAX_RETRIES`: Maximum retry attempts (default: `3`)
- `BEDROCK_TIMEOUT`: Timeout in seconds (default: `30`)
- `BEDROCK_MAX_TOKENS`: Maximum tokens for text generation (default: `2048`)
- `BEDROCK_TEMPERATURE`: Temperature for text generation (default: `0.7`)

### Fallback Governance

The configuration module implements fallback governance based on environment settings:

**Fallback is enabled when:**
- `ENABLE_FALLBACK=true` (explicit)
- `DEV_PROFILE=true` (development mode)
- `ENVIRONMENT=local` (local development)

**For hackathon submission:**
- Set `ENABLE_FALLBACK=false`
- Set `DEV_PROFILE=false`
- Set `ENVIRONMENT=prod`

This ensures the system uses Bedrock exclusively in production.

### Configuration Validation

The `validate()` method checks for common configuration issues:

```python
config = BedrockConfig.from_env()
issues = config.validate()

if issues:
    print("Configuration errors:")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)
```

Validation checks:
- Required fields are not empty
- Numeric values are within valid ranges
- Temperature is between 0.0 and 1.0
- Timeout and max_retries are positive

### Testing Configuration

For testing, you can reset the global configuration:

```python
from config.bedrock_config import reset_bedrock_config

# Update environment variables
os.environ['BEDROCK_REGION'] = 'us-west-2'

# Reset to reload from environment
reset_bedrock_config()

# Get fresh configuration
config = get_bedrock_config()
```

### Example Configurations

#### Local Development

```bash
# .env.local
ENVIRONMENT=local
DEV_PROFILE=true
ENABLE_FALLBACK=true
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
```

#### Production/Hackathon Submission

```bash
# .env.prod
ENVIRONMENT=prod
DEV_PROFILE=false
ENABLE_FALLBACK=false
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
BEDROCK_KB_ID=your-knowledge-base-id
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-agent-alias-id
```

## Integration with SAM Template

The `template.yaml` file defines these environment variables as parameters:

```yaml
Parameters:
  BedrockRegion:
    Type: String
    Default: us-east-1
  
  ClaudeModelId:
    Type: String
    Default: anthropic.claude-3-5-sonnet-20241022-v2:0
  
  # ... other parameters
```

These are automatically injected into Lambda functions via the `Globals` section.

## Best Practices

1. **Never hardcode credentials**: Always use environment variables or AWS Secrets Manager
2. **Validate on startup**: Call `config.validate()` when your Lambda function initializes
3. **Use feature flags**: Check `is_fallback_enabled()` before using fallback providers
4. **Log configuration**: Log the configuration (without sensitive data) on startup for debugging
5. **Test both modes**: Test with both Bedrock-only and fallback-enabled configurations

## Troubleshooting

### Configuration not loading

```python
# Check if environment variables are set
import os
print(os.environ.get('BEDROCK_REGION'))
print(os.environ.get('CLAUDE_MODEL_ID'))

# Validate configuration
config = BedrockConfig.from_env()
issues = config.validate()
print(issues)
```

### Fallback not working

```python
config = get_bedrock_config()
print(f"Fallback enabled: {config.is_fallback_enabled()}")
print(f"ENABLE_FALLBACK: {os.getenv('ENABLE_FALLBACK')}")
print(f"DEV_PROFILE: {os.getenv('DEV_PROFILE')}")
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
```

### AgentCore not configured

```python
config = get_bedrock_config()
if not config.is_agentcore_enabled():
    print("AgentCore is not configured")
    print(f"BEDROCK_AGENT_ID: {config.agent_id}")
    print(f"BEDROCK_AGENT_ALIAS_ID: {config.agent_alias_id}")
```

## Related Documentation

- [Bedrock Client Module](../src/lambda/shared/BEDROCK_CLIENT_README.md)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Hackathon Guidelines](../.kiro/steering/hackathon.md)
