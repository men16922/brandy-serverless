# Configuration Module

This directory contains configuration management for the AI Branding Chatbot project.

## Modules

- **bedrock_config.py**: Amazon Bedrock service configuration
- **fallback_config.py**: Fallback provider governance and selection

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

- `BEDROCK_REGION`: AWS region for Bedrock services (default: `us-west-2`)
- `CLAUDE_MODEL_ID`: Model ID for Claude 4 Sonnet (default: `us.anthropic.claude-sonnet-4-20250514-v1:0`)
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
BEDROCK_REGION=us-west-2
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
```

#### Production/Hackathon Submission

```bash
# .env.prod
ENVIRONMENT=prod
DEV_PROFILE=false
ENABLE_FALLBACK=false
BEDROCK_REGION=us-west-2
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
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
    Default: us-west-2
  
  ClaudeModelId:
    Type: String
    Default: us.anthropic.claude-sonnet-4-20250514-v1:0
  
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

## Fallback Configuration

The `fallback_config.py` module provides fallback governance for AI providers when Amazon Bedrock is unavailable or when running in development mode.

### Usage

```python
from config.fallback_config import FallbackConfig, FallbackProvider, get_fallback_config

# Get configuration from environment variables
config = FallbackConfig.from_env()

# Or use the global singleton
config = get_fallback_config()

# Check if fallback is enabled
if config.is_fallback_enabled():
    provider = config.get_fallback_provider()
    print(f"Using fallback provider: {provider.value}")
    
    if provider == FallbackProvider.OPENAI:
        openai_config = config.get_openai_config()
        print(f"OpenAI model: {openai_config['model']}")
    elif provider == FallbackProvider.GEMINI:
        gemini_config = config.get_gemini_config()
        print(f"Gemini model: {gemini_config['model']}")
else:
    print("Bedrock-only mode (no fallback)")

# Validate for hackathon submission
issues = config.validate_hackathon_submission()
if issues:
    print("Configuration issues for hackathon:")
    for issue in issues:
        print(f"  - {issue}")
```

### Environment Variables

#### Fallback Control Variables

- `ENABLE_FALLBACK`: Explicit fallback enable flag (`true`/`false`, default: `false`)
- `DEV_PROFILE`: Development profile flag (`true`/`false`, default: `false`)
- `ENVIRONMENT`: Current environment (`local`/`dev`/`prod`, default: `prod`)
- `FALLBACK_PROVIDER`: Preferred fallback provider (`openai`/`gemini`, default: `openai`)
- `USE_AGENTCORE`: Enable Bedrock AgentCore (`true`/`false`, default: `true`)

#### OpenAI Configuration (Fallback)

- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_SECRET_NAME`: AWS Secrets Manager secret name (default: `openai-api-key`)
- `OPENAI_MODEL`: OpenAI text model (default: `gpt-4`)
- `OPENAI_DALLE_MODEL`: OpenAI image model (default: `dall-e-3`)

#### Gemini Configuration (Fallback)

- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_MODEL`: Gemini text model (default: `gemini-pro`)
- `GEMINI_VISION_MODEL`: Gemini vision model (default: `gemini-pro-vision`)

### Fallback Governance Rules

Fallback is **enabled** when ANY of these conditions are met:

1. `ENABLE_FALLBACK=true` (explicit activation)
2. `DEV_PROFILE=true` (development mode)
3. `ENVIRONMENT=local` (local development)

Fallback is **disabled** (Bedrock-only) when:

- `ENABLE_FALLBACK=false`
- `DEV_PROFILE=false`
- `ENVIRONMENT=prod`

### Hackathon Submission Requirements

For AWS AI Agent Global Hackathon submission, ensure:

```bash
ENVIRONMENT=prod
ENABLE_FALLBACK=false
DEV_PROFILE=false
USE_AGENTCORE=true
```

Validate your configuration:

```bash
python scripts/validate-fallback-config.py
```

### Provider Selection Logic

The `get_fallback_provider()` method returns:

- `FallbackProvider.NONE` - If fallback is disabled (Bedrock-only)
- `FallbackProvider.OPENAI` - If `FALLBACK_PROVIDER=openai`
- `FallbackProvider.GEMINI` - If `FALLBACK_PROVIDER=gemini`

### Configuration Modes

The module supports different operational modes:

#### Production Mode (Hackathon)

```bash
ENVIRONMENT=prod
ENABLE_FALLBACK=false
DEV_PROFILE=false
USE_AGENTCORE=true
```

- Bedrock-only (no fallback)
- AgentCore enabled
- Suitable for hackathon submission

#### Local Development Mode

```bash
ENVIRONMENT=local
ENABLE_FALLBACK=true
DEV_PROFILE=true
FALLBACK_PROVIDER=openai
USE_AGENTCORE=true
```

- Fallback enabled
- Uses OpenAI/Gemini when Bedrock unavailable
- Suitable for local testing

#### Development Server Mode

```bash
ENVIRONMENT=dev
ENABLE_FALLBACK=true
DEV_PROFILE=true
FALLBACK_PROVIDER=openai
USE_AGENTCORE=true
```

- Fallback enabled
- Deployed to AWS but with fallback safety net
- Suitable for testing in AWS environment

### Validation Script

Use the validation script to check your configuration:

```bash
# Validate current configuration
python scripts/validate-fallback-config.py

# Output includes:
# - Current environment variables
# - Fallback configuration analysis
# - Provider selection test
# - Hackathon submission validation
# - Configuration recommendations
```

### Example Configurations

#### Local Development (.env.local)

```bash
ENVIRONMENT=local
LOG_LEVEL=DEBUG
DEV_PROFILE=true
USE_AGENTCORE=true
ENABLE_FALLBACK=true
FALLBACK_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

#### Development Server (.env.dev)

```bash
ENVIRONMENT=dev
LOG_LEVEL=INFO
DEV_PROFILE=true
USE_AGENTCORE=true
ENABLE_FALLBACK=true
FALLBACK_PROVIDER=openai
```

#### Production/Hackathon (.env.prod)

```bash
ENVIRONMENT=prod
LOG_LEVEL=INFO
DEV_PROFILE=false
USE_AGENTCORE=true
ENABLE_FALLBACK=false
# No fallback provider needed
```

### Integration with BaseAgent

The fallback configuration integrates with the BaseAgent class:

```python
from config.fallback_config import get_fallback_config, FallbackProvider

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.MY_AGENT)
        self.fallback_config = get_fallback_config()
    
    def execute_with_fallback(self, input_data: dict) -> dict:
        try:
            # Try Bedrock first
            return self.execute_with_bedrock(input_data)
        except Exception as e:
            if self.fallback_config.is_fallback_enabled():
                provider = self.fallback_config.get_fallback_provider()
                if provider == FallbackProvider.OPENAI:
                    return self.execute_with_openai(input_data)
                elif provider == FallbackProvider.GEMINI:
                    return self.execute_with_gemini(input_data)
            raise
```

## Related Documentation

- [Bedrock Client Module](../src/lambda/shared/BEDROCK_CLIENT_README.md)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Hackathon Guidelines](../.kiro/steering/hackathon.md)
- [Fallback Configuration Validation Script](../scripts/validate-fallback-config.py)
