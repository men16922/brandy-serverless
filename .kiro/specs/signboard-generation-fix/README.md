# Signboard Generation Fix Spec

## Problem Statement

The AI Branding Chatbot's signboard generation feature is failing to generate actual AI images using Amazon Bedrock SDXL. Instead, users are seeing fallback placeholder images with the message "⚠️ 폴백 이미지 (AI 생성 실패 시 대체)" for all three signboard styles (classic, vibrant, modern).

This is a critical issue for the AWS AI Agent Global Hackathon submission, as Bedrock SDXL integration is a core requirement.

## Root Cause Hypothesis

Based on code analysis, the likely causes are:

1. **SDXLProvider initialization failing silently** - The provider may be failing to initialize but not logging the error
2. **Missing or incorrect AWS credentials** - Bedrock client may not have valid credentials
3. **Insufficient IAM permissions** - Lambda execution role may lack `bedrock:InvokeModel` permission
4. **Incorrect Bedrock SDXL configuration** - Model ID or API parameters may be incorrect
5. **Network or API errors** - Bedrock API calls may be timing out or returning errors

## Solution Approach

This spec implements a comprehensive fix with three phases:

### Phase 1: Diagnosis (Tasks 1-2)
- Add detailed logging throughout the image generation pipeline
- Create AIProviderFactory for centralized provider management
- Identify the exact failure point and error message

### Phase 2: Fix (Tasks 3-10)
- Enhance SDXLProvider with proper error handling
- Integrate BedrockClient for standardized API calls
- Implement retry logic with exponential backoff
- Update IAM permissions and environment configuration
- Add structured logging at each step

### Phase 3: Verification (Tasks 11-15)
- Create integration tests for SDXL provider
- Test end-to-end signboard generation workflow
- Deploy to dev environment and verify fix
- Add CloudWatch monitoring and alerts
- Document the fix and troubleshooting steps

## Key Features

- **Enhanced Error Visibility:** Detailed logging at every step to identify failures
- **Robust Retry Logic:** Exponential backoff with jitter for transient errors
- **Environment-Based Fallback:** Smart fallback behavior based on environment
- **Comprehensive Testing:** Integration tests with actual AWS Bedrock
- **Production Monitoring:** CloudWatch metrics and alarms for ongoing health

## Success Criteria

✅ Bedrock SDXL successfully generates images in dev environment  
✅ No "⚠️ 폴백 이미지" messages for successful generations  
✅ Detailed error logs available in CloudWatch  
✅ Integration tests pass with actual AWS Bedrock  
✅ Fallback behavior works correctly when Bedrock fails  
✅ Performance targets met (≤30s per image)  
✅ IAM permissions correctly configured  
✅ Manual testing checklist completed  

## Getting Started

1. **Review the requirements:** Read `requirements.md` to understand all acceptance criteria
2. **Study the design:** Read `design.md` to understand the architecture and implementation approach
3. **Start with Task 1:** Open `tasks.md` and click "Start task" on Task 1 to begin diagnosis

## Timeline

- **Phase 1 (Diagnosis):** 1-2 hours
- **Phase 2 (Fix):** 4-6 hours
- **Phase 3 (Verification):** 2-3 hours
- **Total:** 7-11 hours

## Related Documentation

- [AWS Bedrock SDXL Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion.html)
- [Hackathon Requirements](../../../docs/AWS%20Hackathon%20rules.md)
- [Project Structure](../../../.kiro/steering/structure.md)
- [Integration Testing Guide](../../../.kiro/steering/integration-testing.md)

## Notes

- This spec follows the project's NO MOCKS policy - all tests use actual AWS services
- The fix maintains backward compatibility with existing fallback behavior
- Environment variables control whether fallback providers are enabled
- The implementation prioritizes visibility (logging) before fixing the root cause
