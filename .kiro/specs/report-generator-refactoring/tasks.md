# Implementation Plan

- [x] 1. Create BusinessUtils module
  - Create business_utils.py with BusinessUtils class
  - Implement generate_color_palette() method with industry-specific colors
  - Implement generate_budget_guide() method with size/region-based estimates
  - Implement generate_recommendations() method
  - _Requirements: 1, 4_

- [x] 2. Create StorageManager module
  - Create storage_manager.py with StorageManager class
  - Implement store_report() method for S3 uploads
  - Implement add_presigned_urls_to_images() method
  - Implement get_download_url() method
  - Handle storage errors with retry logic
  - _Requirements: 1, 3_

- [x] 3. Create BedrockIntegration module
  - Create bedrock_integration.py with BedrockIntegration class
  - Implement synthesize_insights() method using ReasoningEngine
  - Implement enhance_report_content() method
  - Implement is_enabled() check method
  - Handle Bedrock initialization with fallback
  - Respect ENABLE_FALLBACK environment variable
  - _Requirements: 1, 5_

- [x] 4. Create ReportGenerator module
  - Create report_generator.py with ReportGenerator class
  - Implement generate_report() orchestration method
  - Implement generate_pdf_report() method
  - Implement generate_html_report() method
  - Implement generate_json_report() method
  - Implement generate_text_report() method
  - Integrate with BedrockIntegration for AI enhancements
  - Integrate with BusinessUtils for business logic
  - Delegate to alternative_report_generator for complex formats
  - Implement fallback chain (PDF → HTML → JSON → text)
  - _Requirements: 1, 2_

- [x] 5. Refactor index.py to use new modules
  - Import all new modules (report_generator, storage_manager, business_utils, bedrock_integration)
  - Initialize module instances in __init__
  - Refactor execute() to delegate to modules
  - Refactor _generate_pdf_report() to use ReportGenerator
  - Remove old methods that are now in modules
  - Keep lambda_handler unchanged
  - Ensure index.py is under 200 lines
  - _Requirements: 6, 7_

- [x] 6. Update imports and handle Lambda Layer paths
  - Ensure all modules use try/except for shared imports
  - Test imports work in Lambda Layer structure
  - Test imports work in local development
  - Verify no circular dependencies
  - _Requirements: 8_

- [x] 7. Deploy and test in AWS dev environment
  - Run sam build to verify no syntax errors
  - Deploy to AWS dev environment
  - Test report generation with different formats
  - Test with Bedrock enabled and disabled
  - Verify presigned URLs work
  - Check CloudWatch logs for errors
  - _Requirements: 7_

- [x] 8. Verify backward compatibility
  - Test existing API endpoints work identically
  - Verify report output formats are unchanged
  - Verify error responses maintain same structure
  - Test with real session data from Streamlit
  - _Requirements: 7_
