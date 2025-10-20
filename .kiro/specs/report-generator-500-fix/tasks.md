# Implementation Plan

- [x] 1. Fix DataCollector method call in ReportGeneratorAgent
  - Update `_collect_comprehensive_session_data()` method in `src/lambda/agents/report-generator/index.py`
  - Pass all three required parameters: `session_id`, `s3_client`, `sanitizer`
  - Access S3 client from `self.storage_manager.s3_client`
  - Pass `self.sanitizer` instance
  - Add error handling for None values
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Add defensive checks for dependencies
  - Verify `self.storage_manager.s3_client` is not None before passing
  - Verify `self.sanitizer` is not None before passing
  - Add fallback behavior if S3 client is unavailable (empty image lists)
  - Log warnings when dependencies are missing
  - _Requirements: 2.3, 2.4, 4.1, 4.2_

- [x] 3. Improve error logging
  - Add structured logging with session_id context
  - Log specific error details when data collection fails
  - Include agent name and operation in log messages
  - Add debug logging for successful operations
  - _Requirements: 4.1, 4.3, 4.4_

- [x] 4. Deploy and verify fix
  - Build SAM application with updated code
  - Deploy to AWS dev environment
  - Monitor CloudWatch logs during deployment
  - Verify Lambda function updated successfully
  - _Requirements: 1.4, 3.1_

- [x] 5. Test report generation workflow
  - Create test session via Streamlit UI
  - Complete workflow steps 1-4 (analysis, name, signboard, interior)
  - Select interior option
  - Trigger report generation
  - Verify 200 response (not 500 error)
  - Download and verify report content
  - _Requirements: 1.3, 1.4, 3.2, 3.3, 3.4_

- [x] 6. Verify data integrity
  - Check DynamoDB for session data with selected_interior
  - Verify S3 report file exists and is accessible
  - Verify presigned URLs are generated correctly
  - Verify report includes all components (business info, names, signboards, interiors)
  - Check CloudWatch logs for any warnings or errors
  - _Requirements: 3.2, 3.3, 3.4_
