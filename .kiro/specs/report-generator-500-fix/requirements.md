# Requirements Document

## Introduction

The report generation workflow is failing with a 500 error after users select their interior option. The root cause is a method signature mismatch in the `DataCollector.collect_comprehensive_session_data()` method. The method requires three parameters (`session_id`, `s3_client`, `sanitizer`), but it's being called with only one parameter (`session_id`) in the report generator's `_collect_comprehensive_session_data()` method.

This issue prevents users from completing the final step of the branding workflow, blocking them from receiving their comprehensive branding report.

## Requirements

### Requirement 1: Fix Method Signature Mismatch

**User Story:** As a user who has completed the interior selection step, I want the report generation to succeed, so that I can receive my comprehensive branding report.

#### Acceptance Criteria

1. WHEN the report generator calls `DataCollector.collect_comprehensive_session_data()` THEN it SHALL pass all required parameters (`session_id`, `s3_client`, `sanitizer`)
2. WHEN the data collector receives all required parameters THEN it SHALL successfully collect session data, images, and metadata
3. WHEN the data collection completes THEN the report generator SHALL proceed to generate the HTML report without errors
4. WHEN a 500 error previously occurred THEN it SHALL no longer occur after the fix

### Requirement 2: Ensure S3 Client Availability

**User Story:** As a developer, I want the S3 client to be properly initialized and accessible, so that image collection works correctly.

#### Acceptance Criteria

1. WHEN the report generator initializes THEN it SHALL ensure an S3 client is available
2. IF the S3 client is not initialized THEN the report generator SHALL initialize it before calling data collection
3. WHEN the S3 client is passed to the data collector THEN it SHALL support `list_objects()` and `generate_presigned_url()` methods
4. WHEN S3 operations fail THEN the system SHALL log the error and continue with empty image lists

### Requirement 3: Maintain Backward Compatibility

**User Story:** As a developer, I want the fix to maintain backward compatibility, so that existing functionality is not broken.

#### Acceptance Criteria

1. WHEN the fix is applied THEN all existing report generation features SHALL continue to work
2. WHEN the data sanitizer is used THEN it SHALL properly sanitize session data as before
3. WHEN images are collected THEN presigned URLs SHALL be generated with 10-minute expiration
4. WHEN the report is generated THEN it SHALL include all components (business analysis, names, signboards, interiors, color palette, budget guide)

### Requirement 4: Improve Error Handling

**User Story:** As a user, I want clear error messages when report generation fails, so that I understand what went wrong.

#### Acceptance Criteria

1. WHEN data collection fails THEN the system SHALL log the specific error with context
2. WHEN S3 operations fail THEN the system SHALL continue with graceful degradation
3. WHEN the report generator encounters an error THEN it SHALL return a 500 response with a descriptive error message
4. WHEN errors occur THEN they SHALL be logged with session ID, agent name, and error details
