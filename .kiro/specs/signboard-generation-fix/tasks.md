# Implementation Plan

- [x] 1. Add diagnostic logging to identify root cause
  - Add detailed logging to SignboardAgent initialization to track provider creation
  - Add logging to SDXLProvider.__init__ to capture initialization failures
  - Add logging to AIProviderFactory (create if missing) to track provider instantiation
  - Log AWS credentials status (present/missing, not the actual values)
  - Log IAM permissions check results
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Create AIProviderFactory for centralized provider management
  - Create AIProviderFactory class in ai_providers.py
  - Implement create_provider() method with error handling
  - Implement get_available_providers() method
  - Add provider validation on creation
  - Log provider creation success/failure
  - _Requirements: 2.1, 2.2, 3.1, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 3. Enhance SDXLProvider with proper error handling
  - Add _validate_initialization() method to check AWS credentials and Bedrock client
  - Implement proper exception handling in __init__
  - Add detailed error messages for common failure scenarios
  - Implement _build_sdxl_payload() method for request construction
  - Add parameter validation (width/height must be multiple of 64)
  - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Integrate BedrockClient.invoke_sdxl() method
  - Add invoke_sdxl() method to BedrockClient class
  - Implement SDXL-specific request payload construction
  - Add retry logic with exponential backoff for throttling
  - Parse SDXL response and extract base64 image data
  - Handle Bedrock-specific exceptions (ThrottlingException, ValidationException)
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 3.2, 3.3_

- [x] 5. Update SDXLProvider to use BedrockClient
  - Refactor SDXLProvider.generate_image() to use BedrockClient.invoke_sdxl()
  - Remove direct boto3 bedrock-runtime calls
  - Add structured logging for each generation attempt
  - Implement proper error propagation
  - Add generation time tracking
  - _Requirements: 2.2, 2.3, 2.4, 2.5, 5.2, 5.3_

- [x] 6. Enhance SignboardAgent error handling and logging
  - Add _validate_providers() method to check provider availability on startup
  - Implement _log_generation_attempt() for detailed attempt logging
  - Implement _log_generation_result() for success/failure logging
  - Add _should_use_fallback() method for environment-based fallback logic
  - Update _generate_images_async() to log provider selection and results
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Implement exponential backoff retry logic
  - Create exponential_backoff() utility function
  - Add jitter to prevent thundering herd
  - Implement max delay cap (30 seconds)
  - Add retry count tracking in ImageResult metadata
  - Log each retry attempt with delay duration
  - _Requirements: 2.4, 3.2, 5.4_

- [x] 8. Update ImageResult model with error tracking
  - Add error_message field to ImageResult
  - Add generation_time_ms field to ImageResult
  - Add retry_count field to ImageResult
  - Update _image_result_to_dict() to include new fields
  - Update validation logic to handle error cases
  - _Requirements: 3.1, 3.4, 5.3, 5.4_

- [x] 9. Verify and update IAM permissions
  - Check Lambda execution role has bedrock:InvokeModel permission
  - Check Lambda execution role has bedrock:InvokeModelWithResponseStream permission
  - Update template.yaml with correct Bedrock resource ARN
  - Add S3 permissions for image upload (s3:PutObject, s3:GetObject)
  - Deploy updated SAM template to dev environment
  - _Requirements: 4.2, 4.3, 4.5_

- [x] 10. Update environment configuration
  - Add BEDROCK_REGION environment variable to template.yaml
  - Add ENABLE_FALLBACK parameter to template.yaml
  - Add SDXL_MODEL_ID environment variable with default value
  - Update .env.example with new environment variables
  - Document environment variable usage in README
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 11. Create integration tests for SDXL provider
  - Create test_sdxl_provider.py in tests/integration/
  - Test successful SDXL provider initialization
  - Test initialization failure scenarios (no credentials, no permissions)
  - Test image generation with valid prompt
  - Test retry logic on throttling errors
  - Test fallback behavior on persistent failures
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 12. Create end-to-end signboard generation tests
  - Create test_signboard_generation_fix.py in tests/integration/
  - Test complete workflow from name selection to image generation
  - Test parallel generation of 3 signboard styles
  - Test provider validation on agent startup
  - Test error handling and logging output
  - Verify CloudWatch logs contain expected structured log entries
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 13. Deploy and verify in dev environment
  - Build SAM application with updated code
  - Deploy to dev environment using safe_deploy.sh
  - Verify Lambda function has correct environment variables
  - Check CloudWatch logs for initialization messages
  - Test signboard generation via Streamlit UI
  - Verify actual images are generated (not fallback placeholders)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.3_

- [x] 13.1. **CRITICAL: Fix deprecated model ID in deployed stack**
  - Current issue: Lambda is using deprecated `stability.stable-diffusion-xl-v1` (end-of-life)
  - Correct model: `amazon.titan-image-generator-v2:0` (already in template.yaml)
  - Update CloudFormation stack parameter SdxlModelId to use correct value
  - Redeploy stack with: `sam deploy --parameter-overrides SdxlModelId=amazon.titan-image-generator-v2:0`
  - Verify Lambda environment variable SDXL_MODEL_ID is updated
  - Test image generation to confirm fix
  - _Requirements: 2.1, 2.2, 2.5, 4.2, 4.3_
  - **COMPLETED**: Stack redeployed, Lambda now using `amazon.titan-image-generator-v2:0`

- [ ] 14. Add CloudWatch monitoring and alerts
  - Create CloudWatch custom metrics for image generation
  - Add metric for ImageGenerationSuccess count
  - Add metric for ImageGenerationFailure count
  - Add metric for ImageGenerationLatency (P50, P95, P99)
  - Add metric for FallbackImageUsage count
  - _Requirements: 5.3, 5.4_

- [x] 15. Document the fix and update README
  - Document root cause analysis in SIGNBOARD_FIX.md
  - Update README with troubleshooting section
  - Add section on Bedrock SDXL configuration
  - Document environment variables for AI providers
  - Add manual testing checklist
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 16. Fix Titan Image Generator prompt length validation
  - **ROOT CAUSE**: Prompts are 522-525 characters, exceeding Titan's 512 character limit
  - Add prompt truncation logic in _create_image_prompt() method
  - Ensure prompts are ≤ 512 characters for Titan Image Generator v2
  - Add validation before calling Bedrock API
  - Log original and truncated prompt lengths
  - Test with various business info combinations
  - Verify images generate successfully without ValidationException
  - _Requirements: 2.2, 2.3, 3.3, 5.2_
