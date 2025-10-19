# Requirements Document

## Introduction

The AI Branding Chatbot's signboard generation feature is currently failing to generate actual AI images and instead returning fallback placeholder images. Users see "⚠️ 폴백 이미지 (AI 생성 실패 시 대체)" messages for all three signboard styles (classic, vibrant, modern), indicating that the AI image generation pipeline is not working correctly.

This feature is critical for the AWS AI Agent Global Hackathon submission, as it demonstrates the integration of Amazon Bedrock SDXL for image generation. The current failure prevents the project from meeting hackathon requirements and delivering value to users.

## Requirements

### Requirement 1: Diagnose Signboard Generation Failure

**User Story:** As a developer, I want to understand why the signboard generation is failing, so that I can implement the correct fix.

#### Acceptance Criteria

1. WHEN the signboard agent is invoked THEN the system SHALL log detailed error messages including provider name, error type, and failure reason
2. WHEN Bedrock SDXL initialization fails THEN the system SHALL log the specific AWS error code and message
3. WHEN image generation fails THEN the system SHALL capture and log the full exception stack trace
4. IF Bedrock credentials are missing THEN the system SHALL log "Bedrock credentials not configured"
5. IF Bedrock API returns an error THEN the system SHALL log the HTTP status code and response body

### Requirement 2: Fix Bedrock SDXL Integration

**User Story:** As a user, I want the signboard agent to generate actual AI images using Amazon Bedrock SDXL, so that I receive unique, high-quality signboard designs.

#### Acceptance Criteria

1. WHEN the signboard agent initializes THEN it SHALL successfully connect to Amazon Bedrock SDXL service
2. WHEN generating a signboard image THEN the system SHALL use the correct Bedrock SDXL model ID: `stability.stable-diffusion-xl-v1`
3. WHEN calling Bedrock SDXL THEN the system SHALL include required parameters: prompt, seed, cfg_scale, steps
4. IF Bedrock SDXL is unavailable THEN the system SHALL retry up to 3 times with exponential backoff
5. WHEN Bedrock SDXL succeeds THEN the system SHALL return a valid image URL or base64 data

### Requirement 3: Implement Proper Error Handling

**User Story:** As a developer, I want clear error messages and graceful degradation, so that I can quickly identify and fix issues.

#### Acceptance Criteria

1. WHEN any AI provider fails THEN the system SHALL log the error with context (provider, style, session_id)
2. WHEN Bedrock SDXL fails THEN the system SHALL attempt fallback providers (DALL-E, Gemini) if enabled
3. WHEN all providers fail THEN the system SHALL return fallback images with clear error messages
4. IF the environment is 'local' or 'dev' THEN fallback providers SHALL be enabled by default
5. IF the environment is 'prod' and ENABLE_FALLBACK=false THEN the system SHALL only use Bedrock SDXL

### Requirement 4: Verify AWS Credentials and Permissions

**User Story:** As a developer, I want to ensure AWS credentials and IAM permissions are correctly configured, so that Bedrock SDXL can be accessed.

#### Acceptance Criteria

1. WHEN the signboard agent starts THEN it SHALL verify AWS credentials are configured
2. WHEN accessing Bedrock SDXL THEN the Lambda function SHALL have IAM permission `bedrock:InvokeModel`
3. WHEN accessing Bedrock SDXL THEN the Lambda function SHALL have IAM permission `bedrock:InvokeModelWithResponseStream`
4. IF credentials are missing THEN the system SHALL log "AWS credentials not found" and fail gracefully
5. IF IAM permissions are insufficient THEN the system SHALL log "Access denied to Bedrock SDXL" with the specific permission error

### Requirement 5: Add Comprehensive Logging

**User Story:** As a developer, I want detailed logs for the image generation process, so that I can monitor and debug issues in production.

#### Acceptance Criteria

1. WHEN image generation starts THEN the system SHALL log: session_id, selected_name, style, provider
2. WHEN calling an AI provider THEN the system SHALL log: provider_name, prompt (truncated), parameters
3. WHEN image generation succeeds THEN the system SHALL log: provider_name, style, generation_time_ms, image_size
4. WHEN image generation fails THEN the system SHALL log: provider_name, error_type, error_message, retry_count
5. WHEN using fallback images THEN the system SHALL log: "Using fallback image for style={style}, reason={error_message}"

### Requirement 6: Test Signboard Generation End-to-End

**User Story:** As a QA engineer, I want to verify that signboard generation works correctly in all environments, so that users receive reliable service.

#### Acceptance Criteria

1. WHEN running integration tests THEN the system SHALL test signboard generation with Bedrock SDXL
2. WHEN testing in local environment THEN the system SHALL use mock Bedrock responses or fallback providers
3. WHEN testing in dev environment THEN the system SHALL use actual AWS Bedrock SDXL service
4. IF Bedrock SDXL succeeds THEN the test SHALL verify the image URL is valid and accessible
5. IF Bedrock SDXL fails THEN the test SHALL verify fallback images are returned with appropriate error messages

### Requirement 7: Update Environment Configuration

**User Story:** As a developer, I want clear environment configuration for AI providers, so that I can control which providers are used in different environments.

#### Acceptance Criteria

1. WHEN ENVIRONMENT=local THEN the system SHALL enable fallback providers (DALL-E, Gemini)
2. WHEN ENVIRONMENT=dev THEN the system SHALL use Bedrock SDXL as primary with fallback enabled
3. WHEN ENVIRONMENT=prod AND ENABLE_FALLBACK=false THEN the system SHALL only use Bedrock SDXL
4. WHEN DEV_PROFILE=true THEN the system SHALL enable fallback providers regardless of environment
5. WHEN ENABLE_FALLBACK=false AND DEV_PROFILE=false THEN the system SHALL fail if Bedrock SDXL is unavailable
