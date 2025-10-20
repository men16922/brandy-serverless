# Design Document

## Overview

The signboard generation feature is failing because the Bedrock SDXL provider is not properly initialized or is encountering runtime errors. The current implementation in `ai_providers.py` shows that the SDXLProvider exists but may be failing silently, causing the system to fall back to placeholder images.

This design addresses the root causes and implements a robust solution with:
1. Enhanced error detection and logging
2. Proper Bedrock SDXL configuration validation
3. Improved retry logic with exponential backoff
4. Clear fallback behavior based on environment
5. Comprehensive testing strategy

## Architecture

### Current Flow (Broken)

```
User selects name
    ↓
SignboardAgent.execute()
    ↓
_generate_signboard_images()
    ↓
_generate_images_async()
    ↓
AIProviderFactory.create_provider("sdxl")  ← FAILS SILENTLY
    ↓
SDXLProvider initialization fails
    ↓
Falls back to placeholder images
    ↓
User sees "⚠️ 폴백 이미지"
```

### Proposed Flow (Fixed)

```
User selects name
    ↓
SignboardAgent.execute()
    ↓
_generate_signboard_images()
    ↓
_generate_images_async()
    ↓
AIProviderFactory.create_provider("sdxl")
    ↓
SDXLProvider initialization
    ├─ Verify AWS credentials ✓
    ├─ Verify IAM permissions ✓
    ├─ Test Bedrock connection ✓
    └─ Log initialization status ✓
    ↓
SDXLProvider.generate_image()
    ├─ Build SDXL request payload
    ├─ Call bedrock_runtime.invoke_model()
    ├─ Retry on throttling (3x with backoff)
    ├─ Parse response and extract base64 image
    └─ Upload to S3 and return URL
    ↓
Success: Return actual AI-generated images
    OR
Failure: Log detailed error + use fallback (if enabled)
```

## Components and Interfaces

### 1. Enhanced SDXLProvider

**Location:** `src/lambda/shared/ai_providers.py`

**Key Changes:**
- Add initialization validation
- Implement proper error handling
- Add detailed logging at each step
- Use BedrockClient for standardized API calls
- Implement exponential backoff retry logic

**Interface:**
```python
class SDXLProvider(AIProvider):
    def __init__(self, region: str = None, logger: logging.Logger = None):
        """
        Initialize SDXL provider with validation.
        
        Raises:
            BedrockException: If initialization fails
        """
        
    async def generate_image(
        self, 
        prompt: str, 
        style: str = "default",
        **kwargs
    ) -> ImageResult:
        """
        Generate image using Bedrock SDXL.
        
        Args:
            prompt: Image generation prompt
            style: Style preset (modern, classic, vibrant)
            **kwargs: Additional parameters (cfg_scale, steps, seed)
            
        Returns:
            ImageResult with URL or base64 data
            
        Raises:
            BedrockException: On API errors
        """
        
    def _validate_initialization(self) -> bool:
        """Validate Bedrock client and credentials"""
        
    def _build_sdxl_payload(
        self, 
        prompt: str, 
        style: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Build SDXL API request payload"""
        
    async def _invoke_with_retry(
        self, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Bedrock SDXL with retry logic"""
```

### 2. AIProviderFactory

**Location:** `src/lambda/shared/ai_providers.py`

**Purpose:** Centralized provider creation with error handling

**Interface:**
```python
class AIProviderFactory:
    @staticmethod
    def create_provider(
        provider_name: str,
        **kwargs
    ) -> AIProvider:
        """
        Create AI provider instance.
        
        Args:
            provider_name: "sdxl", "dalle", "gemini"
            **kwargs: Provider-specific configuration
            
        Returns:
            Initialized AIProvider instance
            
        Raises:
            ValueError: If provider_name is invalid
            BedrockException: If provider initialization fails
        """
        
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers based on environment"""
```

### 3. Enhanced SignboardAgent

**Location:** `src/lambda/agents/signboard/index.py`

**Key Changes:**
- Add provider initialization validation
- Implement detailed error logging
- Improve fallback logic
- Add health check endpoint

**New Methods:**
```python
class SignboardAgent(BaseAgent):
    def _validate_providers(self) -> Dict[str, bool]:
        """
        Validate all AI providers on initialization.
        
        Returns:
            Dict mapping provider names to availability status
        """
        
    def _log_generation_attempt(
        self,
        provider_name: str,
        style: str,
        session_id: str,
        prompt: str
    ) -> None:
        """Log image generation attempt with context"""
        
    def _log_generation_result(
        self,
        provider_name: str,
        style: str,
        success: bool,
        error: Optional[str] = None,
        latency_ms: Optional[int] = None
    ) -> None:
        """Log image generation result"""
        
    def _should_use_fallback(self) -> bool:
        """Determine if fallback providers should be used"""
```

### 4. BedrockClient Integration

**Location:** `src/lambda/shared/bedrock_client.py`

**New Method:**
```python
class BedrockClient:
    def invoke_sdxl(
        self,
        prompt: str,
        style_preset: str = "photographic",
        cfg_scale: float = 7.0,
        steps: int = 30,
        width: int = 1024,
        height: int = 1024,
        seed: int = 0
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock SDXL for image generation.
        
        Args:
            prompt: Image generation prompt
            style_preset: SDXL style preset
            cfg_scale: Classifier-free guidance scale
            steps: Number of diffusion steps
            width: Image width (must be multiple of 64)
            height: Image height (must be multiple of 64)
            seed: Random seed for reproducibility
            
        Returns:
            Dict with 'image_base64', 'finish_reason', 'latency_ms'
            
        Raises:
            BedrockException: On API errors
            ThrottlingException: On rate limiting
            ValidationException: On invalid parameters
        """
```

## Data Models

### ImageResult Enhancement

**Location:** `src/lambda/shared/models.py`

**Changes:**
```python
class ImageResult:
    url: str
    provider: str
    style: str
    prompt: str
    metadata: Dict[str, Any]
    is_fallback: bool
    error_message: Optional[str] = None  # NEW
    generation_time_ms: Optional[int] = None  # NEW
    retry_count: Optional[int] = None  # NEW
```

### Provider Status Model

**New Model:**
```python
class ProviderStatus:
    """Track AI provider availability and health"""
    provider_name: str
    is_available: bool
    last_check: datetime
    error_message: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
```

## Error Handling

### Error Classification

1. **Initialization Errors** (Fatal)
   - AWS credentials not configured
   - IAM permissions insufficient
   - Bedrock service unavailable in region
   - **Action:** Log error, fail fast, use fallback if enabled

2. **Runtime Errors** (Retryable)
   - ThrottlingException (rate limiting)
   - ServiceUnavailableException (temporary outage)
   - Network timeouts
   - **Action:** Retry with exponential backoff (3 attempts)

3. **Validation Errors** (Non-retryable)
   - Invalid prompt (content policy violation)
   - Invalid parameters (width/height not multiple of 64)
   - Model not found
   - **Action:** Log error, skip retry, use fallback

### Retry Strategy

```python
def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
    """
    Calculate retry delay with exponential backoff and jitter.
    
    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, 0.1 * delay)
    return min(delay + jitter, 30.0)  # Max 30 seconds
```

### Fallback Logic

```python
def should_use_fallback() -> bool:
    """
    Determine if fallback providers should be used.
    
    Returns:
        True if fallback is enabled
    """
    environment = os.getenv('ENVIRONMENT', 'prod')
    enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
    dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
    
    # Fallback enabled in local/dev or when explicitly enabled
    return (
        environment in ['local', 'dev'] or
        enable_fallback or
        dev_profile
    )
```

## Testing Strategy

### 1. Unit Tests (Provider Level)

**File:** `tests/integration/test_sdxl_provider.py`

```python
class TestSDXLProvider:
    def test_initialization_success(self):
        """Test successful SDXL provider initialization"""
        
    def test_initialization_failure_no_credentials(self):
        """Test initialization fails without AWS credentials"""
        
    def test_generate_image_success(self):
        """Test successful image generation"""
        
    def test_generate_image_throttling_retry(self):
        """Test retry logic on throttling"""
        
    def test_generate_image_validation_error(self):
        """Test handling of validation errors"""
        
    def test_fallback_on_failure(self):
        """Test fallback image generation on failure"""
```

### 2. Integration Tests (End-to-End)

**File:** `tests/integration/test_signboard_generation.py`

```python
class TestSignboardGeneration:
    def test_full_workflow_with_bedrock(self):
        """Test complete signboard generation workflow"""
        
    def test_provider_initialization_validation(self):
        """Test provider validation on agent startup"""
        
    def test_parallel_generation_three_styles(self):
        """Test parallel generation of 3 signboard styles"""
        
    def test_error_handling_and_logging(self):
        """Test error handling and log output"""
        
    def test_fallback_behavior(self):
        """Test fallback to placeholder images"""
```

### 3. AWS Environment Tests

**File:** `tests/integration/test_aws_bedrock_sdxl.py`

```python
class TestAWSBedrockSDXL:
    def test_bedrock_credentials(self):
        """Verify AWS credentials are configured"""
        
    def test_bedrock_iam_permissions(self):
        """Verify IAM permissions for Bedrock"""
        
    def test_bedrock_sdxl_model_access(self):
        """Verify SDXL model is accessible"""
        
    def test_bedrock_api_call(self):
        """Test actual Bedrock SDXL API call"""
```

### 4. Manual Testing Checklist

- [ ] Run Streamlit app locally
- [ ] Create new session with business info
- [ ] Select a business name
- [ ] Verify 3 signboard images are generated
- [ ] Check CloudWatch logs for errors
- [ ] Verify images are uploaded to S3
- [ ] Test with ENABLE_FALLBACK=false
- [ ] Test with invalid AWS credentials
- [ ] Test with rate limiting (rapid requests)

## Logging Strategy

### Log Levels

1. **INFO** - Normal operations
   - Provider initialization
   - Image generation start/success
   - Fallback usage

2. **WARNING** - Recoverable issues
   - Retry attempts
   - Fallback provider usage
   - Slow response times (>10s)

3. **ERROR** - Failures
   - Provider initialization failure
   - Image generation failure after retries
   - Invalid configuration

### Structured Log Format

```json
{
  "timestamp": "2025-10-19T02:04:00Z",
  "level": "INFO",
  "agent": "signboard",
  "tool": "generate_image",
  "session_id": "abc123",
  "provider": "bedrock_sdxl",
  "style": "modern",
  "latency_ms": 2500,
  "status": "success",
  "metadata": {
    "prompt_length": 150,
    "cfg_scale": 7.0,
    "steps": 30,
    "retry_count": 0
  }
}
```

### Key Log Points

1. **Agent Initialization**
   ```python
   self.logger.info(
       f"SignboardAgent initialized with {len(self.ai_providers)} providers: "
       f"{list(self.ai_providers.keys())}"
   )
   ```

2. **Image Generation Start**
   ```python
   self.logger.info(
       f"Starting image generation: session={session_id}, "
       f"provider={provider_name}, style={style}"
   )
   ```

3. **Image Generation Success**
   ```python
   self.logger.info(
       f"Image generated successfully: provider={provider_name}, "
       f"style={style}, latency_ms={latency_ms}"
   )
   ```

4. **Image Generation Failure**
   ```python
   self.logger.error(
       f"Image generation failed: provider={provider_name}, "
       f"style={style}, error={error_message}, retry_count={retry_count}"
   )
   ```

5. **Fallback Usage**
   ```python
   self.logger.warning(
       f"Using fallback image: style={style}, "
       f"reason={error_message}"
   )
   ```

## Deployment Considerations

### Environment Variables

**Required:**
- `AWS_REGION` - AWS region for Bedrock (default: us-west-2)
- `BEDROCK_REGION` - Bedrock-specific region (default: us-west-2)

**Optional:**
- `ENABLE_FALLBACK` - Enable fallback providers (default: true)
- `DEV_PROFILE` - Enable dev mode with fallbacks (default: false)
- `SDXL_MODEL_ID` - SDXL model ID (default: stability.stable-diffusion-xl-v1)
- `BEDROCK_MAX_RETRIES` - Max retry attempts (default: 3)
- `BEDROCK_TIMEOUT` - API timeout in seconds (default: 30)

### IAM Permissions

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/stability.stable-diffusion-xl-v1"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::ai-branding-chatbot-assets-*/*"
      ]
    }
  ]
}
```

### SAM Template Updates

**File:** `template.yaml`

```yaml
SignboardAgentFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/lambda/agents/signboard/
    Handler: index.lambda_handler
    Runtime: python3.11
    Timeout: 60  # Increased for image generation
    MemorySize: 1024  # Increased for image processing
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        AWS_REGION: !Ref AWS::Region
        BEDROCK_REGION: !Ref AWS::Region
        ENABLE_FALLBACK: !Ref EnableFallback
        SDXL_MODEL_ID: stability.stable-diffusion-xl-v1
    Policies:
      - Statement:
          - Effect: Allow
            Action:
              - bedrock:InvokeModel
              - bedrock:InvokeModelWithResponseStream
            Resource:
              - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/stability.stable-diffusion-xl-v1'
          - Effect: Allow
            Action:
              - s3:PutObject
              - s3:GetObject
            Resource:
              - !Sub '${AssetsBucket.Arn}/*'
```

## Performance Targets

- **Image Generation Latency:** ≤ 30 seconds per image
- **Total Workflow Time:** ≤ 90 seconds for 3 images (parallel)
- **Success Rate:** ≥ 95% with Bedrock SDXL
- **Retry Overhead:** ≤ 10 seconds for 3 retry attempts
- **Fallback Activation:** < 5% of requests in production

## Monitoring and Alerts

### CloudWatch Metrics

1. **ImageGenerationSuccess** - Count of successful generations
2. **ImageGenerationFailure** - Count of failed generations
3. **ImageGenerationLatency** - P50, P95, P99 latencies
4. **FallbackImageUsage** - Count of fallback image usage
5. **BedrockThrottling** - Count of throttling errors

### CloudWatch Alarms

1. **High Failure Rate**
   - Metric: ImageGenerationFailure
   - Threshold: > 10% of requests in 5 minutes
   - Action: SNS notification

2. **High Latency**
   - Metric: ImageGenerationLatency (P95)
   - Threshold: > 45 seconds
   - Action: SNS notification

3. **Frequent Throttling**
   - Metric: BedrockThrottling
   - Threshold: > 5 errors in 1 minute
   - Action: SNS notification

## Rollback Plan

If the fix introduces regressions:

1. **Immediate:** Revert to previous Lambda version
   ```bash
   aws lambda update-function-configuration \
     --function-name ai-branding-chatbot-signboard-agent-dev \
     --environment Variables={ENABLE_FALLBACK=true}
   ```

2. **Short-term:** Enable fallback mode for all environments
   ```bash
   sam deploy --parameter-overrides EnableFallback=true
   ```

3. **Long-term:** Investigate root cause and re-deploy fix

## Success Criteria

1. ✅ Bedrock SDXL successfully generates images in dev environment
2. ✅ No "⚠️ 폴백 이미지" messages for successful generations
3. ✅ Detailed error logs available in CloudWatch
4. ✅ Integration tests pass with actual AWS Bedrock
5. ✅ Fallback behavior works correctly when Bedrock fails
6. ✅ Performance targets met (≤30s per image)
7. ✅ IAM permissions correctly configured
8. ✅ Manual testing checklist completed
