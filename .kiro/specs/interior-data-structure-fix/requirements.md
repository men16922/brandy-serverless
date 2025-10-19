# Requirements Document

## Introduction

인테리어 이미지 생성은 성공적으로 완료되지만 (3/3 images, S3 업로드 완료), Streamlit UI에서 "0/3 images generated"로 표시되는 문제를 해결합니다. 근본 원인은 DynamoDB에 인테리어 데이터가 JSON 문자열로 저장되어 Streamlit에서 파싱하지 못하는 구조적 불일치입니다.

## Requirements

### Requirement 1: DynamoDB 데이터 구조 정규화

**User Story:** As a developer, I want interior recommendations to be stored in DynamoDB as proper Map types, so that Streamlit can directly access the data without JSON parsing.

#### Acceptance Criteria

1. WHEN Interior Agent saves recommendations to DynamoDB THEN the data SHALL be stored as DynamoDB Map type (not JSON string)
2. WHEN Interior Agent saves image URLs THEN each recommendation SHALL contain imageUrl field with S3 URL
3. WHEN Interior Agent saves recommendations THEN the field name SHALL be `interiors` (not `interior_recommendations`)
4. WHEN Streamlit queries session data THEN it SHALL receive properly structured Map data without string parsing

### Requirement 2: Streamlit Polling 로직 개선

**User Story:** As a user, I want to see real-time progress of interior image generation, so that I know the system is working and can wait appropriately.

#### Acceptance Criteria

1. WHEN Streamlit polls for interior data THEN it SHALL check both `interiors` and `interior_recommendations` fields for backward compatibility
2. WHEN Streamlit receives JSON string data THEN it SHALL parse the string and extract image URLs
3. WHEN Streamlit detects image generation progress THEN it SHALL display "X/3 images generated" with accurate count
4. WHEN all 3 images are generated THEN Streamlit SHALL stop polling and display the results
5. WHEN polling exceeds 60 seconds THEN Streamlit SHALL show timeout message with manual refresh option

### Requirement 3: 수동 새로고침 기능

**User Story:** As a user, I want a manual refresh button during interior generation, so that I can check the status on demand without waiting for automatic polling.

#### Acceptance Criteria

1. WHEN interior generation is in progress THEN a "상태 새로고침" button SHALL be displayed
2. WHEN user clicks the refresh button THEN Streamlit SHALL immediately query DynamoDB for latest data
3. WHEN refresh succeeds THEN the UI SHALL update with current image count and display any completed images
4. WHEN refresh button is clicked THEN polling timer SHALL reset to prevent duplicate requests
5. WHEN all images are complete THEN the refresh button SHALL be hidden

### Requirement 4: 에러 처리 및 로깅

**User Story:** As a developer, I want comprehensive error logging for data structure mismatches, so that I can quickly diagnose and fix issues.

#### Acceptance Criteria

1. WHEN Interior Agent saves data THEN it SHALL log the DynamoDB item structure
2. WHEN Streamlit receives unexpected data format THEN it SHALL log the raw data and attempt graceful fallback
3. WHEN JSON parsing fails THEN Streamlit SHALL log the error and display user-friendly message
4. WHEN S3 image URL is missing THEN the system SHALL log warning and use placeholder image
5. WHEN DynamoDB field names don't match THEN the system SHALL log field name mismatch details
