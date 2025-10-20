# Design Document

## Overview

This design addresses the 500 error occurring during report generation after interior selection. The root cause is a method signature mismatch where `DataCollector.collect_comprehensive_session_data()` expects three parameters but is called with only one.

The fix involves:
1. Updating the report generator to pass all required parameters to the data collector
2. Ensuring S3 client and sanitizer instances are available
3. Maintaining backward compatibility with existing functionality
4. Improving error handling and logging

## Architecture

### Current Architecture

```
ReportGeneratorAgent
├── DataCollector (initialized with base_agent, logger)
├── DataSanitizer (initialized with logger)
├── StorageManager (initialized with logger, s3_client)
├── BedrockIntegration
└── ReportGenerator
```

### Problem

```python
# In index.py _collect_comprehensive_session_data()
session_data = self.collector.collect_comprehensive_session_data(session_id)
# ❌ Missing s3_client and sanitizer parameters

# In data_collector.py
def collect_comprehensive_session_data(self, session_id: str, s3_client, sanitizer) -> Dict[str, Any]:
# ✓ Expects 3 parameters
```

### Solution Architecture

```
ReportGeneratorAgent
├── self.collector (DataCollector)
├── self.sanitizer (DataSanitizer)
├── self.storage_manager (StorageManager)
│   └── self.storage_manager.s3_client (S3Client)
└── Pass all required dependencies to data collector
```

## Components and Interfaces

### 1. ReportGeneratorAgent (Modified)

**File:** `src/lambda/agents/report-generator/index.py`

**Changes:**
- Update `_collect_comprehensive_session_data()` method to pass all required parameters
- Access S3 client from `self.storage_manager.s3_client`
- Pass `self.sanitizer` to data collector

**Method Signature:**
```python
def _collect_comprehensive_session_data(self, session_id: str) -> Dict[str, Any]:
    """Collect comprehensive session data with all assets"""
    try:
        # Pass all required parameters to data collector
        session_data = self.collector.collect_comprehensive_session_data(
            session_id=session_id,
            s3_client=self.storage_manager.s3_client,
            sanitizer=self.sanitizer
        )
        
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        # Continue with existing logic...
```

### 2. DataCollector (No Changes Required)

**File:** `src/lambda/agents/report-generator/data_collector.py`

**Current Interface:**
```python
def collect_comprehensive_session_data(
    self, 
    session_id: str, 
    s3_client, 
    sanitizer
) -> Dict[str, Any]:
    """종합 세션 데이터 수집 - 모든 선택 사항 통합"""
```

**Responsibilities:**
- Retrieve session data from DynamoDB via `base_agent.get_session_data()`
- Sanitize session data using provided `sanitizer`
- Collect images from S3 using provided `s3_client`
- Parse and structure all session data
- Return comprehensive data dictionary

**No changes needed** - the interface is correct, we just need to call it properly.

### 3. DataSanitizer (No Changes Required)

**File:** `src/lambda/agents/report-generator/data_sanitizer.py`

**Interface:**
```python
def sanitize_session_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """세션 데이터 정제 - DynamoDB 형식 및 Decimal 타입 제거"""
```

**Responsibilities:**
- Convert DynamoDB format to standard Python types
- Handle Decimal types from DynamoDB
- Parse JSON strings
- Ensure data structure consistency

**No changes needed** - already properly initialized in `ReportGeneratorAgent.__init__()`.

### 4. StorageManager (No Changes Required)

**File:** `src/lambda/agents/report-generator/storage_manager.py`

**Interface:**
```python
def __init__(self, logger=None, s3_client=None):
    self.logger = logger or logging.getLogger(__name__)
    self.s3_client = s3_client or self._get_s3_client()
```

**S3 Client Access:**
- `self.storage_manager.s3_client` provides access to initialized S3 client
- Supports `list_objects()`, `generate_presigned_url()`, `upload_file()` methods

**No changes needed** - already properly initialized with S3 client.

## Data Models

### Session Data Structure

```python
{
    "session_id": str,
    "session": Dict[str, Any],  # Raw session data
    "business_info": {
        "industry": str,
        "region": str,
        "size": str,
        # ... other fields
    },
    "analysis_result": Dict[str, Any],
    "business_names": List[str],
    "selected_name": str,
    "selected_signboard": str,
    "selected_interior": str,  # ✓ This should be populated after interior selection
    "signboard_images": List[Dict],
    "interior_images": List[Dict],
    "uploaded_images": List[Dict],
    "generated_at": str  # ISO format timestamp
}
```

### Image Data Structure

```python
{
    "key": str,  # S3 key
    "size": int,  # File size in bytes
    "last_modified": str,  # ISO format timestamp
    "presigned_url": str,  # 10-minute expiry URL
    "url": str  # Same as presigned_url
}
```

## Error Handling

### Error Scenarios and Handling

1. **Missing Session Data**
   - **Error:** `ValueError("Session {session_id} not found")`
   - **Handling:** Return 500 with error message, log with session ID
   - **User Impact:** Clear error message indicating session not found

2. **S3 Client Not Available**
   - **Error:** S3 client is None
   - **Handling:** Continue with empty image lists, log warning
   - **User Impact:** Report generated without images (graceful degradation)

3. **Image Collection Failure**
   - **Error:** S3 operations fail (network, permissions, etc.)
   - **Handling:** Log warning, continue with empty image lists
   - **User Impact:** Report generated without images

4. **Data Sanitization Failure**
   - **Error:** Exception during sanitization
   - **Handling:** Return original data, log error with traceback
   - **User Impact:** Report may have formatting issues but still generated

5. **Presigned URL Generation Failure**
   - **Error:** Exception during URL generation
   - **Handling:** Skip URL for that image, log warning
   - **User Impact:** Some images may not have URLs but report still generated

### Error Logging Pattern

```python
try:
    session_data = self.collector.collect_comprehensive_session_data(
        session_id=session_id,
        s3_client=self.storage_manager.s3_client,
        sanitizer=self.sanitizer
    )
except Exception as e:
    self.logger.error(
        f"Failed to collect comprehensive session data: {str(e)}",
        extra={
            "session_id": session_id,
            "agent": "report-generator",
            "operation": "collect_session_data"
        }
    )
    raise
```

## Testing Strategy

### Unit Testing (Not Used - Per Project Guidelines)

This project uses integration testing only. No unit tests will be created.

### Integration Testing

**Test Scenario:** Full workflow test with interior selection

1. **Setup:**
   - Deploy to AWS dev environment
   - Create test session with business info
   - Complete steps 1-4 (analysis, name selection, signboard, interior)

2. **Test Steps:**
   - Select interior option (POST to interior agent with action='select')
   - Verify session updated with `selected_interior`
   - Trigger report generation (POST to report-generator agent)
   - Verify 200 response (not 500)
   - Verify report URL returned
   - Download report and verify content

3. **Verification:**
   - Check DynamoDB for session data
   - Check S3 for report file
   - Check CloudWatch logs for errors
   - Verify report includes selected interior information

**Test File:** `tests/integration/test_report_generator_fix.py`

```python
def test_report_generation_after_interior_selection():
    """Test that report generation succeeds after interior selection"""
    # 1. Create session and complete workflow steps 1-4
    # 2. Select interior option
    # 3. Generate report
    # 4. Verify success (200 response, not 500)
    # 5. Verify report content includes interior selection
```

### Manual Testing Checklist

- [ ] Complete full workflow in Streamlit UI
- [ ] Select interior option
- [ ] Click "Generate Report" button
- [ ] Verify no 500 error
- [ ] Verify report downloads successfully
- [ ] Verify report includes interior selection
- [ ] Check CloudWatch logs for errors
- [ ] Verify DynamoDB session data
- [ ] Verify S3 report file exists

## Implementation Notes

### Key Changes

**File:** `src/lambda/agents/report-generator/index.py`

**Method:** `_collect_comprehensive_session_data()`

**Change:**
```python
# Before (WRONG):
session_data = self.collector.collect_comprehensive_session_data(session_id)

# After (CORRECT):
session_data = self.collector.collect_comprehensive_session_data(
    session_id=session_id,
    s3_client=self.storage_manager.s3_client,
    sanitizer=self.sanitizer
)
```

### Backward Compatibility

- All existing functionality remains unchanged
- No changes to API contracts
- No changes to data models
- No changes to other agents
- Only internal method call updated

### Performance Considerations

- No performance impact expected
- S3 client already initialized (no additional overhead)
- Sanitizer already initialized (no additional overhead)
- Same number of S3 operations as before

### Security Considerations

- Presigned URLs expire after 10 minutes (existing behavior)
- S3 client uses IAM role permissions (existing behavior)
- No new security risks introduced
- No changes to authentication/authorization

## Deployment Plan

1. **Code Changes:**
   - Update `src/lambda/agents/report-generator/index.py`
   - No other files need changes

2. **Testing:**
   - Run integration tests in dev environment
   - Manual testing via Streamlit UI

3. **Deployment:**
   ```bash
   sam build
   sam deploy --config-env dev
   ```

4. **Verification:**
   - Test full workflow in dev environment
   - Monitor CloudWatch logs
   - Verify no 500 errors

5. **Rollback Plan:**
   - If issues occur, revert to previous Lambda version
   - AWS Lambda maintains previous versions automatically
   - Can rollback via AWS Console or CLI

## Success Criteria

- ✅ Report generation succeeds after interior selection (200 response)
- ✅ No 500 errors in CloudWatch logs
- ✅ Report includes all expected components
- ✅ Images are collected and included in report
- ✅ Presigned URLs are generated correctly
- ✅ Session data is properly sanitized
- ✅ All integration tests pass
- ✅ Manual testing via Streamlit UI succeeds
