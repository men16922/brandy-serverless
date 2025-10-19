# Requirements Document

## Introduction

The Reporter Agent is experiencing severe performance issues causing 120+ second execution times, primarily due to Bedrock API throttling and inefficient retry logic. This feature will optimize the Reporter Agent's performance to meet the target of <30 seconds for name generation.

## Requirements

### Requirement 1: Bedrock Throttling Mitigation

**User Story:** As a system operator, I want the Reporter Agent to handle Bedrock throttling gracefully, so that name generation completes within acceptable timeframes.

#### Acceptance Criteria

1. WHEN Bedrock API returns ThrottlingException THEN the system SHALL implement exponential backoff with jitter
2. WHEN multiple Bedrock API calls are needed THEN the system SHALL add delays between calls to prevent throttling
3. WHEN throttling occurs repeatedly THEN the system SHALL fall back to cached/baseline results after 3 retries
4. IF Bedrock throttling exceeds 60 seconds THEN the system SHALL use fallback name generation
5. THE system SHALL log all throttling events with latency metrics

### Requirement 2: API Call Optimization

**User Story:** As a developer, I want to minimize the number of Bedrock API calls, so that the Reporter Agent executes faster and costs less.

#### Acceptance Criteria

1. WHEN generating business names THEN the system SHALL batch API calls where possible
2. WHEN evaluating names THEN the system SHALL use a single API call for all 3 names instead of 3 separate calls
3. THE system SHALL cache Bedrock responses for identical inputs within a session
4. THE system SHALL implement request deduplication to avoid redundant API calls
5. WHEN baseline mode is enabled THEN the system SHALL skip Bedrock calls entirely

### Requirement 3: DynamoDB Float Conversion Fix

**User Story:** As a developer, I want all numeric scores to be stored as Decimal in DynamoDB, so that session updates succeed without Float type errors.

#### Acceptance Criteria

1. WHEN storing name scores THEN the system SHALL convert all float values to Decimal
2. WHEN updating session data THEN the system SHALL recursively convert nested float values
3. THE system SHALL handle None values without conversion errors
4. THE system SHALL preserve integer values as integers
5. WHEN conversion fails THEN the system SHALL log the error and use default Decimal values

### Requirement 4: Timeout Configuration

**User Story:** As a user, I want the Streamlit client to wait long enough for name generation, so that I don't see timeout errors when the Lambda is still processing.

#### Acceptance Criteria

1. WHEN polling for name generation status THEN the client SHALL wait up to 180 seconds
2. WHEN Lambda execution exceeds 180 seconds THEN the client SHALL display a helpful error message
3. THE client SHALL show progress updates every 3 seconds during polling
4. THE client SHALL display estimated time remaining based on average execution time
5. WHEN timeout occurs THEN the client SHALL suggest checking CloudWatch logs

### Requirement 5: Performance Monitoring

**User Story:** As a system operator, I want detailed performance metrics for the Reporter Agent, so that I can identify and resolve bottlenecks.

#### Acceptance Criteria

1. THE system SHALL log execution time for each Bedrock API call
2. THE system SHALL log total execution time for name generation
3. THE system SHALL track throttling frequency and retry counts
4. THE system SHALL emit CloudWatch metrics for performance monitoring
5. WHEN execution exceeds 60 seconds THEN the system SHALL log a warning with breakdown of time spent
