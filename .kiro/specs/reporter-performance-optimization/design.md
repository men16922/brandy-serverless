# Design Document

## Overview

This design optimizes the Reporter Agent's performance by addressing Bedrock API throttling, reducing API call frequency, fixing DynamoDB type conversion, and adjusting client timeouts. The goal is to reduce execution time from 147s to <60s while maintaining reliability.

## Architecture

### Current Flow (Problematic)
```
Client Request → Lambda (async) → Bedrock API (3 separate calls) → DynamoDB (Float error) → Status endpoint
                                   ↓ Throttled (30-40s delay)
                                   ↓ Retry with backoff
                                   ↓ Throttled again
                                   Total: 147s
```

### Optimized Flow
```
Client Request → Lambda (async) → Bedrock API (1 batched call) → DynamoDB (Decimal) → Status endpoint
                                   ↓ Rate limiting (2s delay between calls)
                                   ↓ Exponential backoff with jitter
                                   ↓ Fallback after 60s
                                   Total: <60s
```

## Components and Interfaces

### 1. Bedrock Client Enhancement

**Location:** `src/lambda/shared/bedrock_client.py`

**New Methods:**
```python
class BedrockClient:
    def invoke_with_throttle_protection(
        self,
        model_id: str,
        prompt: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock with exponential backoff and jitter.
        
        Args:
            model_id: Bedrock model ID
            prompt: Input prompt
            max_retries: Maximum retry attempts (default: 3)
            base_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 30.0)
            
        Returns:
            API response dict
            
        Raises:
            ThrottlingException: After max retries exceeded
        """
        
    def batch_evaluate_names(
        self,
        names: List[str],
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple names in a single Bedrock API call.
        
        Args:
            names: List of business names to evaluate
            business_info: Business context
            analysis_result: Analysis results
            
        Returns:
            List of evaluation results with scores
        """
        
    def add_rate_limit_delay(self, delay_seconds: float = 2.0) -> None:
        """
        Add delay between API calls to prevent throttling.
        
        Args:
            delay_seconds: Delay duration (default: 2.0)
        """
```

**Throttle Protection Algorithm:**
```python
def calculate_backoff_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """
    Calculate exponential backoff with jitter.
    
    Formula: min(max_delay, base_delay * 2^attempt + random(0, 1))
    
    Example:
    - Attempt 1: 1.0 * 2^1 + jitter = 2.0-3.0s
    - Attempt 2: 1.0 * 2^2 + jitter = 4.0-5.0s
    - Attempt 3: 1.0 * 2^3 + jitter = 8.0-9.0s
    """
    delay = min(max_delay, base_delay * (2 ** attempt))
    jitter = random.uniform(0, 1)
    return delay + jitter
```

### 2. Reporter Agent Optimization

**Location:** `src/lambda/agents/reporter/index.py`

**Modified Methods:**
```python
async def generate_names_async(
    session_id: str,
    business_info: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Optimized async name generation with batched evaluation.
    
    Flow:
    1. Generate 3 name candidates (1 Bedrock call)
    2. Add 2s delay to prevent throttling
    3. Batch evaluate all 3 names (1 Bedrock call instead of 3)
    4. Convert scores to Decimal
    5. Store in DynamoDB
    
    Total Bedrock calls: 2 (down from 4)
    Expected time: 20-40s (down from 147s)
    """
```

**Batched Evaluation Prompt:**
```python
BATCH_EVALUATION_PROMPT = """
You are a business naming expert. Evaluate the following {count} business names for a {industry} business in {region}.

Names to evaluate:
{names_list}

Business context:
{business_context}

For each name, provide:
1. Pronunciation score (0-100): How easy is it to pronounce?
2. Memorability score (0-100): How memorable is it?
3. Relevance score (0-100): How relevant to the business?
4. Search score (0-100): How SEO-friendly?
5. Overall score (0-100): Weighted average

Return JSON array with format:
[
  {{
    "name": "Name1",
    "pronunciation_score": 85.0,
    "memorability_score": 90.0,
    "relevance_score": 80.0,
    "search_score": 75.0,
    "overall_score": 82.5,
    "reasoning": "Brief explanation"
  }},
  ...
]
"""
```

### 3. DynamoDB Type Conversion

**Location:** `src/lambda/shared/base_agent.py`

**Enhanced Conversion:**
```python
def convert_floats_to_decimal(obj: Any) -> Any:
    """
    Recursively convert float values to Decimal for DynamoDB.
    
    Handles:
    - Nested dictionaries
    - Lists of dictionaries
    - None values
    - Already-Decimal values
    - Integer values (preserved)
    
    Args:
        obj: Object to convert
        
    Returns:
        Converted object with Decimal instead of float
    """
    if obj is None:
        return None
    
    if isinstance(obj, float):
        # Convert float to Decimal with 2 decimal places
        return Decimal(str(round(obj, 2)))
    
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    
    if isinstance(obj, Decimal):
        # Already Decimal, return as-is
        return obj
    
    if isinstance(obj, int):
        # Preserve integers
        return obj
    
    # Return other types unchanged
    return obj
```

### 4. Streamlit Client Timeout

**Location:** `src/streamlit/app.py`

**Configuration:**
```python
# Polling configuration
POLLING_CONFIG = {
    "max_attempts": 60,  # 60 * 3s = 180s total
    "poll_interval": 3,  # Check every 3 seconds
    "timeout_message": "⏱️ 요청 시간 초과: 180초를 초과했습니다.",
    "progress_update_interval": 3,  # Update UI every 3 seconds
}

# Expected execution times (for progress estimation)
EXPECTED_EXECUTION_TIMES = {
    "analysis": 10,  # seconds
    "names": 60,     # seconds (optimized from 147s)
    "signboard": 30, # seconds
    "interior": 20,  # seconds
    "report": 15,    # seconds
}
```

## Data Models

### Name Evaluation Result
```python
@dataclass
class NameEvaluation:
    name: str
    pronunciation_score: Decimal  # Changed from float
    memorability_score: Decimal   # Changed from float
    relevance_score: Decimal      # Changed from float
    search_score: Decimal         # Changed from float
    overall_score: Decimal        # Changed from float
    reasoning: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to DynamoDB-compatible dict"""
        return {
            "name": self.name,
            "pronunciation_score": self.pronunciation_score,
            "memorability_score": self.memorability_score,
            "relevance_score": self.relevance_score,
            "search_score": self.search_score,
            "overall_score": self.overall_score,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp
        }
```

### Throttling Metrics
```python
@dataclass
class ThrottlingMetrics:
    total_calls: int
    throttled_calls: int
    total_retry_time: Decimal  # seconds
    max_retry_time: Decimal    # seconds
    fallback_used: bool
    
    def to_cloudwatch_metrics(self) -> List[Dict[str, Any]]:
        """Convert to CloudWatch metric format"""
        return [
            {
                "MetricName": "BedrockThrottling",
                "Value": self.throttled_calls,
                "Unit": "Count"
            },
            {
                "MetricName": "BedrockRetryTime",
                "Value": float(self.total_retry_time),
                "Unit": "Seconds"
            }
        ]
```

## Error Handling

### Throttling Error Flow
```
Bedrock API Call
    ↓
ThrottlingException?
    ↓ Yes
Log throttling event
    ↓
Calculate backoff delay (exponential + jitter)
    ↓
Sleep for delay
    ↓
Retry (attempt < max_retries)?
    ↓ Yes → Retry API call
    ↓ No
Total retry time > 60s?
    ↓ Yes → Use fallback (baseline names)
    ↓ No → Raise exception
```

### Fallback Strategy
```python
FALLBACK_NAMES = {
    "restaurant": ["미담", "맛있는집", "행복한식탁"],
    "retail": ["좋은가게", "행복한쇼핑", "믿음상점"],
    "service": ["친절한서비스", "믿음가게", "행복한공간"],
    # ... other industries
}

def get_fallback_names(industry: str) -> List[Dict[str, Any]]:
    """
    Get fallback names when Bedrock is unavailable.
    
    Returns baseline names with default scores.
    """
    names = FALLBACK_NAMES.get(industry, FALLBACK_NAMES["service"])
    return [
        {
            "name": name,
            "pronunciation_score": Decimal("75.0"),
            "memorability_score": Decimal("70.0"),
            "relevance_score": Decimal("80.0"),
            "search_score": Decimal("70.0"),
            "overall_score": Decimal("73.75"),
            "reasoning": "Fallback name due to API throttling",
            "is_fallback": True
        }
        for name in names
    ]
```

## Testing Strategy

### Unit Tests (Minimal)
- `test_convert_floats_to_decimal()` - Type conversion edge cases
- `test_calculate_backoff_delay()` - Backoff algorithm

### Integration Tests (Primary)
```python
def test_reporter_agent_performance():
    """
    Test Reporter Agent completes within 60 seconds.
    
    Verifies:
    - Name generation completes
    - Scores are Decimal type
    - No throttling errors
    - Execution time < 60s
    """
    
def test_bedrock_throttling_recovery():
    """
    Test throttling recovery with exponential backoff.
    
    Simulates:
    - Bedrock throttling
    - Retry with backoff
    - Successful completion after retries
    """
    
def test_fallback_name_generation():
    """
    Test fallback names when Bedrock unavailable.
    
    Verifies:
    - Fallback names returned
    - Scores are valid Decimals
    - is_fallback flag set
    """
```

### Performance Benchmarks
```python
PERFORMANCE_TARGETS = {
    "name_generation": 60,  # seconds (max)
    "bedrock_api_call": 10,  # seconds (average)
    "throttle_recovery": 30,  # seconds (max retry time)
    "dynamodb_update": 1,    # seconds (max)
}
```

## Performance Optimization Summary

### Before Optimization
- Bedrock API calls: 4 (1 generation + 3 evaluations)
- Throttling handling: Basic retry (no backoff)
- Rate limiting: None
- Execution time: 147 seconds
- DynamoDB errors: Frequent Float type errors

### After Optimization
- Bedrock API calls: 2 (1 generation + 1 batched evaluation)
- Throttling handling: Exponential backoff with jitter
- Rate limiting: 2s delay between calls
- Execution time: <60 seconds (target)
- DynamoDB errors: None (proper Decimal conversion)

### Expected Improvements
- **60% reduction** in API calls (4 → 2)
- **60% reduction** in execution time (147s → <60s)
- **100% reduction** in DynamoDB errors
- **50% reduction** in throttling incidents (via rate limiting)
- **100% success rate** for client polling (180s timeout)

## Deployment Considerations

### Lambda Configuration
```yaml
# template.yaml
ReporterAgent:
  Type: AWS::Serverless::Function
  Properties:
    Timeout: 180  # Increased from 120s
    MemorySize: 512
    Environment:
      Variables:
        BEDROCK_RATE_LIMIT_DELAY: "2.0"  # seconds
        BEDROCK_MAX_RETRIES: "3"
        BEDROCK_BASE_DELAY: "1.0"
        BEDROCK_MAX_DELAY: "30.0"
        ENABLE_FALLBACK: "true"
```

### CloudWatch Alarms
```yaml
ReporterAgentThrottlingAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: BedrockThrottling
    Threshold: 10  # Alert if >10 throttling events/hour
    EvaluationPeriods: 1
    Period: 3600
    
ReporterAgentDurationAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: Duration
    Threshold: 60000  # Alert if >60s execution time
    EvaluationPeriods: 2
    Period: 300
```

## Monitoring and Observability

### Structured Logging
```python
logger.info(
    "Name generation performance",
    extra={
        "session_id": session_id,
        "total_duration_ms": total_duration,
        "bedrock_calls": bedrock_call_count,
        "throttled_calls": throttled_count,
        "retry_time_ms": total_retry_time,
        "fallback_used": fallback_used,
        "names_generated": len(names)
    }
)
```

### CloudWatch Metrics
- `BedrockThrottling` - Count of throttling events
- `BedrockRetryTime` - Total time spent in retries
- `NameGenerationDuration` - End-to-end execution time
- `FallbackUsage` - Count of fallback activations

### CloudWatch Insights Queries
```sql
-- Find slow name generation requests
fields @timestamp, session_id, total_duration_ms
| filter total_duration_ms > 60000
| sort total_duration_ms desc
| limit 20

-- Analyze throttling patterns
fields @timestamp, throttled_calls, retry_time_ms
| filter throttled_calls > 0
| stats sum(throttled_calls) as total_throttled, avg(retry_time_ms) as avg_retry_time by bin(5m)
```
