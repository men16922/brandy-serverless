# Implementation Plan

- [x] 1. Enhance Bedrock Client with throttle protection
  - Add `invoke_with_throttle_protection()` method with exponential backoff and jitter
  - Implement `calculate_backoff_delay()` helper function
  - Add `add_rate_limit_delay()` method for inter-call delays
  - Add structured logging for throttling events
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 2. Implement batched name evaluation
  - [x] 2.1 Add `batch_evaluate_names()` method to BedrockClient
    - Create batched evaluation prompt template
    - Parse JSON array response from Bedrock
    - Handle partial failures gracefully
    - _Requirements: 2.2, 2.3_
  
  - [x] 2.2 Update Reporter Agent to use batched evaluation
    - Replace 3 separate API calls with 1 batched call
    - Add 2s delay between generation and evaluation calls
    - Convert all scores to Decimal immediately after parsing
    - _Requirements: 2.1, 2.2_

- [x] 3. Fix DynamoDB Float conversion
  - [x] 3.1 Enhance `convert_floats_to_decimal()` in base_agent.py
    - Add recursive conversion for nested dicts and lists
    - Handle None values without errors
    - Preserve integer values
    - Add unit test for edge cases
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 3.2 Apply conversion in Reporter Agent
    - Convert name evaluation results before DynamoDB update
    - Add logging for conversion errors
    - Use default Decimal values on conversion failure
    - _Requirements: 3.1, 3.5_

- [x] 4. Implement fallback name generation
  - Create `FALLBACK_NAMES` dictionary with industry-specific names
  - Add `get_fallback_names()` function
  - Integrate fallback into Reporter Agent after 60s of retries
  - Set `is_fallback` flag in results
  - _Requirements: 1.4, 1.5_

- [x] 5. Update Streamlit client timeout
  - Change `max_attempts` from 40 to 60 (120s → 180s)
  - Update timeout error message
  - Add CloudWatch logs suggestion in error message
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 6. Add performance monitoring
  - [x] 6.1 Add structured logging for performance metrics
    - Log total execution time
    - Log Bedrock API call count and latency
    - Log throttling events and retry time
    - Log fallback usage
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [ ]* 6.2 Add CloudWatch metrics emission
    - Emit `BedrockThrottling` metric
    - Emit `BedrockRetryTime` metric
    - Emit `NameGenerationDuration` metric
    - Emit `FallbackUsage` metric
    - _Requirements: 5.4_
  
  - [ ]* 6.3 Create CloudWatch alarms
    - Alarm for excessive throttling (>10/hour)
    - Alarm for slow execution (>60s)
    - Update template.yaml with alarm definitions
    - _Requirements: 5.4_

- [x] 7. Update Lambda configuration
  - Increase Reporter Agent timeout to 180s in template.yaml
  - Add environment variables for throttle protection config
  - Add environment variable for rate limit delay
  - Deploy updated configuration
  - _Requirements: 1.1, 1.2, 2.1_

- [ ]* 8. Integration testing
  - [ ]* 8.1 Test Reporter Agent performance
    - Verify execution time <60s
    - Verify scores are Decimal type
    - Verify no DynamoDB errors
    - _Requirements: All_
  
  - [ ]* 8.2 Test throttling recovery
    - Simulate Bedrock throttling
    - Verify exponential backoff behavior
    - Verify successful completion after retries
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 8.3 Test fallback mechanism
    - Simulate prolonged Bedrock unavailability
    - Verify fallback names returned
    - Verify `is_fallback` flag set
    - _Requirements: 1.4_
  
  - [ ]* 8.4 Test end-to-end workflow
    - Run full workflow from Streamlit
    - Verify no client timeouts
    - Verify name generation completes successfully
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
