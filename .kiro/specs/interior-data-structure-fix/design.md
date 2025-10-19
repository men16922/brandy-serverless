# Design Document

## Overview

인테리어 이미지 생성은 성공하지만 Streamlit UI에서 표시되지 않는 문제를 해결합니다. 근본 원인은 Interior Agent가 DynamoDB에 데이터를 저장하지 않거나 잘못된 형식으로 저장하기 때문입니다.

## Architecture

### Current State (Broken)
```
Interior Agent → Generate Images (✅ Success)
                ↓
                DynamoDB Save (❌ Missing or Wrong Format)
                ↓
                Streamlit Poll (❌ No Data Found)
```

### Target State (Fixed)
```
Interior Agent → Generate Images (✅)
                ↓
                DynamoDB Save as Map Type (✅ New)
                ↓
                Streamlit Poll with Fallback (✅ Enhanced)
                ↓
                Manual Refresh Button (✅ New)
```

## Components and Interfaces

### 1. Interior Agent - DynamoDB Save Logic

**New Method: `_save_interior_to_dynamodb()`**

```python
def _save_interior_to_dynamodb(
    self, 
    session_id: str, 
    recommendations: List[Dict[str, Any]]
) -> None:
    """
    Save interior recommendations to DynamoDB as Map type
    
    Args:
        session_id: Session identifier
        recommendations: List of recommendation dicts with imageUrl
    
    DynamoDB Structure:
        {
            "sessionId": "xxx",
            "interiors": [  # Map type, not JSON string
                {
                    "style": "cozy",
                    "description": "...",
                    "imageUrl": "https://s3.../xxx.png",
                    "isGenerated": true,
                    "provider": "bedrock-titan",
                    "colorScheme": ["color1", "color2"],
                    "materials": ["material1", "material2"],
                    "furniture": ["furniture1", "furniture2"],
                    "estimatedCost": "중간",
                    "suitabilityScore": 92.0,
                    "pros": ["pro1", "pro2"],
                    "cons": ["con1", "con2"],
                    "generatedAt": "2025-10-19T12:24:02.974885"
                }
            ],
            "interiorGenerationStatus": "completed",
            "interiorGenerationStartedAt": "2025-10-19T12:23:40.862Z",
            "interiorGenerationCompletedAt": "2025-10-19T12:24:37.863Z"
        }
    """
```

**Integration Points:**
- Called after image generation completes
- Updates session with proper Map structure
- Sets status flags for polling detection

### 2. Streamlit - Enhanced Polling Logic

**Modified Method: `poll_for_interior_images()`**

```python
def poll_for_interior_images(
    session_id: str, 
    max_attempts: int = 60,
    interval: int = 2
) -> Dict[str, Any]:
    """
    Poll for interior image generation with enhanced error handling
    
    Returns:
        {
            "status": "completed" | "in_progress" | "timeout",
            "images": [
                {
                    "style": "cozy",
                    "imageUrl": "https://...",
                    "description": "...",
                    "provider": "bedrock-titan"
                }
            ],
            "progress": {
                "current": 3,
                "total": 3
            }
        }
    
    Backward Compatibility:
        - Checks both 'interiors' (new) and 'interior_recommendations' (old)
        - Parses JSON string if found (old format)
        - Extracts imageUrl from nested structures
    """
```

**Polling Strategy:**
1. Check `interiorGenerationStatus` field first
2. If "completed", extract `interiors` array
3. Fallback: check `interior_recommendations` (JSON string)
4. Parse JSON string and extract imageUrl fields
5. Count images with valid URLs
6. Display progress: "X/3 images generated"

### 3. Streamlit - Manual Refresh Button

**New Component: `render_manual_refresh_button()`**

```python
def render_manual_refresh_button(session_id: str) -> None:
    """
    Render manual refresh button during interior generation
    
    UI Layout:
        [🔄 상태 새로고침] button
        
    Behavior:
        - Visible only during interior generation
        - On click: immediate DynamoDB query
        - Updates st.session_state with latest data
        - Resets polling timer
        - Shows toast notification with result
    """
```

**Button States:**
- **Visible**: When `interiorGenerationStatus == "in_progress"`
- **Hidden**: When `interiorGenerationStatus == "completed"`
- **Disabled**: During active refresh (prevent double-click)

## Data Models

### DynamoDB Session Schema (Updated)

```python
{
    "sessionId": "string (PK)",
    "currentStep": 4,
    "status": "active",
    
    # Interior-specific fields (NEW)
    "interiors": [  # Map type (not string!)
        {
            "style": "string",
            "description": "string",
            "imageUrl": "string",  # S3 URL
            "isGenerated": "boolean",
            "provider": "string",  # "bedrock-titan" | "openai-dalle3"
            "colorScheme": ["string"],
            "materials": ["string"],
            "furniture": ["string"],
            "estimatedCost": "string",
            "suitabilityScore": "number",
            "pros": ["string"],
            "cons": ["string"],
            "generatedAt": "string (ISO 8601)"
        }
    ],
    "interiorGenerationStatus": "in_progress" | "completed" | "failed",
    "interiorGenerationStartedAt": "string (ISO 8601)",
    "interiorGenerationCompletedAt": "string (ISO 8601)",
    
    # Legacy field (for backward compatibility)
    "interior_recommendations": "string (JSON)"  # Deprecated
}
```

### Streamlit Session State (Updated)

```python
st.session_state = {
    "session_id": "string",
    "current_step": 4,
    "interior_data": {
        "recommendations": [
            {
                "style": "string",
                "imageUrl": "string",
                "description": "string",
                "provider": "string"
            }
        ],
        "progress": {
            "current": 3,
            "total": 3
        },
        "status": "completed"
    },
    "polling_active": False,
    "last_refresh_time": "timestamp"
}
```

## Error Handling

### 1. DynamoDB Save Failures

**Scenario**: Interior Agent fails to save to DynamoDB

**Handling**:
```python
try:
    self._save_interior_to_dynamodb(session_id, recommendations)
except Exception as e:
    self.logger.error(f"DynamoDB save failed: {str(e)}")
    # Continue execution - data is in Lambda response
    # Streamlit can still display from API response
```

### 2. JSON Parsing Failures

**Scenario**: Streamlit receives malformed JSON string

**Handling**:
```python
try:
    data = json.loads(interior_recommendations_str)
except json.JSONDecodeError as e:
    logger.error(f"JSON parse failed: {str(e)}")
    logger.error(f"Raw data: {interior_recommendations_str[:200]}")
    st.error("데이터 형식 오류가 발생했습니다. 새로고침을 시도해주세요.")
    return None
```

### 3. Missing Image URLs

**Scenario**: Image generation succeeded but URL is missing

**Handling**:
```python
for rec in recommendations:
    if not rec.get('imageUrl'):
        logger.warning(f"Missing imageUrl for style: {rec.get('style')}")
        rec['imageUrl'] = PLACEHOLDER_IMAGE_URL
        rec['isGenerated'] = False
```

### 4. Polling Timeout

**Scenario**: 60 seconds elapsed without completion

**Handling**:
```python
if attempts >= max_attempts:
    st.warning("⏱️ 인테리어 이미지 생성이 예상보다 오래 걸리고 있습니다.")
    st.info("잠시 후 '상태 새로고침' 버튼을 눌러 확인해주세요.")
    # Show manual refresh button
    render_manual_refresh_button(session_id)
```

## Testing Strategy

### Unit Tests (Not Required per project policy)

Skip unit tests - use integration tests only.

### Integration Tests

**Test 1: DynamoDB Save Format**
```python
def test_interior_dynamodb_save_format():
    """Verify interior data is saved as Map type"""
    # Generate interior recommendations
    response = requests.post(f"{API_BASE_URL}/interiors/generate", ...)
    
    # Query DynamoDB directly
    item = dynamodb.get_item(TableName="sessions", Key={"sessionId": session_id})
    
    # Verify structure
    assert "interiors" in item["Item"]
    assert item["Item"]["interiors"]["L"]  # List type
    assert item["Item"]["interiors"]["L"][0]["M"]  # Map type
    assert "imageUrl" in item["Item"]["interiors"]["L"][0]["M"]
```

**Test 2: Streamlit Polling**
```python
def test_streamlit_polling_with_real_data():
    """Verify Streamlit can poll and display interior images"""
    # Start interior generation
    session_id = create_test_session()
    
    # Poll until complete
    result = poll_for_interior_images(session_id, max_attempts=60)
    
    # Verify result
    assert result["status"] == "completed"
    assert len(result["images"]) == 3
    assert all(img["imageUrl"] for img in result["images"])
```

**Test 3: Manual Refresh Button**
```python
def test_manual_refresh_button():
    """Verify manual refresh updates UI correctly"""
    # Setup: interior generation in progress
    session_id = create_test_session_with_partial_images()
    
    # Simulate button click
    refresh_result = manual_refresh(session_id)
    
    # Verify UI updates
    assert refresh_result["progress"]["current"] >= 0
    assert refresh_result["progress"]["total"] == 3
```

**Test 4: Backward Compatibility**
```python
def test_backward_compatibility_with_json_string():
    """Verify Streamlit can handle old JSON string format"""
    # Setup: session with old format (JSON string)
    session_id = create_legacy_session_with_json_string()
    
    # Poll
    result = poll_for_interior_images(session_id)
    
    # Verify parsing succeeds
    assert result["status"] == "completed"
    assert len(result["images"]) > 0
```

## Performance Considerations

### DynamoDB Write Latency
- **Target**: < 100ms for save operation
- **Optimization**: Use batch write if multiple updates needed

### Streamlit Polling Overhead
- **Current**: 2-second intervals for 60 seconds = 30 requests
- **Optimization**: Exponential backoff after 30 seconds
  - 0-30s: 2-second intervals
  - 30-60s: 5-second intervals

### Manual Refresh Rate Limiting
- **Constraint**: Max 1 refresh per 2 seconds
- **Implementation**: Check `last_refresh_time` in session state
- **UI Feedback**: Disable button for 2 seconds after click

## Deployment Plan

### Phase 1: Interior Agent Fix
1. Add `_save_interior_to_dynamodb()` method
2. Call after image generation completes
3. Deploy Lambda function
4. Verify DynamoDB structure in AWS Console

### Phase 2: Streamlit Polling Enhancement
1. Update `poll_for_interior_images()` with fallback logic
2. Add JSON string parsing for backward compatibility
3. Test locally with real AWS data
4. Deploy to production

### Phase 3: Manual Refresh Button
1. Add `render_manual_refresh_button()` component
2. Integrate with polling logic
3. Add rate limiting
4. Test user experience

### Phase 4: Validation
1. Run integration tests against AWS dev environment
2. Monitor CloudWatch logs for errors
3. Verify DynamoDB data structure
4. Confirm Streamlit UI displays correctly

## Rollback Plan

If issues occur:
1. **Interior Agent**: Revert Lambda deployment
2. **Streamlit**: Keep backward compatibility code (no breaking changes)
3. **DynamoDB**: No schema changes needed (additive only)

## Monitoring

### CloudWatch Metrics
- `InteriorAgent.DynamoDBSaveSuccess` (custom metric)
- `InteriorAgent.DynamoDBSaveFailure` (custom metric)
- `StreamlitPolling.Timeout` (custom metric)

### CloudWatch Logs
- Interior Agent: Log DynamoDB item structure after save
- Streamlit: Log polling attempts and results
- Manual Refresh: Log button clicks and outcomes

### Alerts
- Alert if DynamoDB save failure rate > 5%
- Alert if Streamlit polling timeout rate > 10%
