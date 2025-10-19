# Implementation Plan

- [x] 1. Interior Agent - DynamoDB 저장 로직 추가
  - Add `_save_interior_to_dynamodb()` method to save recommendations as Map type
  - Call method after image generation completes in `_generate_interior_recommendations_with_bedrock()`
  - Set status fields: `interiorGenerationStatus`, `interiorGenerationStartedAt`, `interiorGenerationCompletedAt`
  - Log DynamoDB item structure for debugging
  - _Requirements: 1.1, 1.2, 1.3, 4.1_

- [x] 2. Interior Agent - 필드명 통일
  - Use `interiors` field name (not `interior_recommendations`)
  - Ensure each recommendation dict contains `imageUrl`, `isGenerated`, `provider` fields
  - Maintain backward compatibility by keeping old field if exists
  - _Requirements: 1.3, 1.4_

- [x] 3. Streamlit - Polling 로직 개선
  - [x] 3.1 Backward compatibility 추가
    - Check both `interiors` (new) and `interior_recommendations` (old) fields
    - Parse JSON string if old format detected
    - Extract imageUrl from nested structures
    - _Requirements: 2.1, 2.2, 4.2_
  
  - [x] 3.2 진행률 표시 개선
    - Count images with valid URLs
    - Display "X/3 images generated" with accurate count
    - Update progress bar in real-time
    - _Requirements: 2.3_
  
  - [x] 3.3 Polling 완료 조건 수정
    - Stop polling when all 3 images have URLs
    - Check `interiorGenerationStatus == "completed"` as primary signal
    - Fallback to image count if status field missing
    - _Requirements: 2.4_
  
  - [x] 3.4 Timeout 처리 개선
    - Show timeout message after 60 seconds
    - Display manual refresh button on timeout
    - Add exponential backoff after 30 seconds
    - _Requirements: 2.5_

- [x] 4. Streamlit - 수동 새로고침 버튼 추가
  - [x] 4.1 버튼 컴포넌트 구현
    - Create `render_manual_refresh_button()` function
    - Display button only during interior generation
    - Hide button when generation completes
    - _Requirements: 3.1, 3.5_
  
  - [x] 4.2 새로고침 로직 구현
    - Query DynamoDB on button click
    - Update st.session_state with latest data
    - Display toast notification with result
    - _Requirements: 3.2, 3.3_
  
  - [x] 4.3 Rate limiting 추가
    - Track last refresh time in session state
    - Disable button for 2 seconds after click
    - Show countdown timer on button
    - _Requirements: 3.4_

- [x] 5. 에러 처리 및 로깅 강화
  - [x] 5.1 Interior Agent 로깅
    - Log DynamoDB save success/failure
    - Log item structure after save
    - Add custom CloudWatch metrics
    - _Requirements: 4.1_
  
  - [x] 5.2 Streamlit 에러 처리
    - Catch JSON parsing errors with graceful fallback
    - Log unexpected data formats
    - Display user-friendly error messages
    - Handle missing imageUrl fields
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 5.3 필드명 불일치 로깅
    - Log when expected fields are missing
    - Log field name mismatches
    - Suggest correct field names in logs
    - _Requirements: 4.5_

- [ ] 6. Integration testing
  - [ ] 6.1 DynamoDB 저장 형식 검증
    - Verify `interiors` field is Map type (not string)
    - Verify each recommendation has required fields
    - Check status fields are set correctly
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 6.2 Streamlit polling 검증
    - Test polling with real AWS data
    - Verify progress display accuracy
    - Test timeout behavior
    - Verify manual refresh works
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 3.3_
  
  - [ ] 6.3 Backward compatibility 검증
    - Test with old JSON string format
    - Verify parsing succeeds
    - Verify images display correctly
    - _Requirements: 2.1, 2.2_

- [x] 7. 배포 및 검증
  - Deploy Interior Agent Lambda function
  - Deploy Streamlit app
  - Monitor CloudWatch logs for errors
  - Verify DynamoDB data structure in AWS Console
  - Test end-to-end workflow in production
  - _Requirements: All_
