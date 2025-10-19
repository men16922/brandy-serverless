# Interior Data Structure Fix - Implementation Summary

## Problem Statement

인테리어 이미지 생성은 성공적으로 완료되지만 (3/3 images, S3 업로드 완료), Streamlit UI에서 "0/3 images generated"로 표시되는 문제가 발생했습니다.

### Root Cause

1. **DynamoDB 저장 형식 문제**: Interior Agent가 데이터를 JSON 문자열로 저장하거나 저장하지 않음
2. **필드명 불일치**: `interior_recommendations` (snake_case) vs `interiors` (camelCase)
3. **Streamlit Polling 로직**: JSON 문자열 파싱 미지원, backward compatibility 부족
4. **수동 새로고침 기능 부재**: Timeout 발생 시 사용자가 상태를 확인할 방법 없음

## Solution Overview

### 1. Interior Agent - DynamoDB 저장 로직 추가

**New Method: `_save_interior_to_dynamodb()`**

```python
def _save_interior_to_dynamodb(self, session_id: str, 
                               recommendations: List[Dict[str, Any]]) -> None:
    """
    Save interior recommendations to DynamoDB as Map type (not JSON string)
    
    DynamoDB Structure:
        {
            "interiors": [  # List of Maps (not JSON string!)
                {
                    "style": "cozy",
                    "description": "...",
                    "imageUrl": "https://s3.../xxx.png",
                    "isGenerated": true,
                    "provider": "bedrock-titan",
                    ...
                }
            ],
            "interiorGenerationStatus": "completed",
            "interiorGenerationCompletedAt": "2025-10-19T12:24:37.863Z"
        }
    """
```

**Key Changes:**
- ✅ Save as DynamoDB Map type (not JSON string)
- ✅ Use `interiors` field name (standardized)
- ✅ Set status fields: `interiorGenerationStatus`, `interiorGenerationStartedAt`, `interiorGenerationCompletedAt`
- ✅ Log DynamoDB item structure for debugging
- ✅ Graceful error handling (don't fail Lambda if DynamoDB save fails)

**Integration:**
- Called after image generation completes in `_generate_interior_recommendations_with_bedrock()`
- Set initial status when execution starts

### 2. Streamlit - Enhanced Polling Logic

**Backward Compatibility:**
```python
# Try new format first: 'interiors' field (Map type)
if 'interiors' in status_data:
    interior_data = status_data['interiors']
    if isinstance(interior_data, list):
        recommendations = interior_data
        generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))

# Fallback: old format 'interior_recommendations' (JSON string)
elif 'interior_recommendations' in status_data:
    interior_str = status_data['interior_recommendations']
    if isinstance(interior_str, str):
        interior_parsed = json.loads(interior_str)
        recommendations = interior_parsed.get('recommendations', [])
        generated_images = sum(1 for rec in recommendations if rec.get('imageUrl'))
```

**Key Changes:**
- ✅ Check both `interiors` (new) and `interior_recommendations` (old) fields
- ✅ Parse JSON string if old format detected
- ✅ Count images with valid URLs (accurate progress)
- ✅ Check `interiorGenerationStatus` field as primary completion signal
- ✅ Display accurate progress: "X/3 images generated"

### 3. Manual Refresh Button

**New Function: `manual_refresh_interior_status()`**

```python
def manual_refresh_interior_status():
    """Manually refresh interior generation status"""
    # Rate limiting: max 1 refresh per 2 seconds
    # Query DynamoDB via API
    # Parse data with backward compatibility
    # Update session state
    # Show result with toast notification
```

**UI Integration:**
```python
# Show button if timeout occurred or in progress
if show_refresh and not interior_data:
    st.info("🎨 인테리어 이미지를 생성하고 있습니다...")
    if st.button("🔄 상태 새로고침"):
        manual_refresh_interior_status()
```

**Key Features:**
- ✅ Rate limiting (2-second cooldown)
- ✅ Visible only during generation or timeout
- ✅ Immediate DynamoDB query
- ✅ Updates UI with latest data
- ✅ Toast notifications for user feedback

### 4. Enhanced Error Handling & Logging

**Interior Agent:**
```python
# Log DynamoDB structure
self.logger.info(f"Saving interior data to DynamoDB: {len(recommendations)} recommendations")
self.logger.info(f"Sample structure: {json.dumps(recommendations[0], indent=2)}")
self.logger.info(f"Interior recommendation fields: {list(recommendations[0].keys())}")

# Graceful error handling
try:
    self._save_interior_to_dynamodb(session_id, recommendations)
except Exception as save_error:
    self.logger.error(f"DynamoDB save failed but continuing: {str(save_error)}")
    # Don't raise - Lambda can still return response
```

**Streamlit:**
```python
# JSON parsing with error handling
try:
    interior_parsed = json.loads(interior_str)
except json.JSONDecodeError as e:
    logger.error(f"JSON parse error: {str(e)}")
    logger.error(f"Raw data: {interior_str[:200]}")
    st.error("❌ 데이터 형식 오류가 발생했습니다.")
```

## Testing Strategy

### Manual Testing Steps

1. **Start Interior Generation**
   ```bash
   # Run Streamlit
   streamlit run src/streamlit/app.py
   
   # Complete workflow up to Step 3 (Signboard)
   # Select a signboard design
   # Click "인테리어 추천 생성"
   ```

2. **Verify DynamoDB Structure**
   ```bash
   # Query session data
   aws dynamodb get-item \
     --table-name ai-branding-chatbot-sessions \
     --key '{"sessionId":{"S":"YOUR_SESSION_ID"}}' \
     --region us-east-1
   
   # Verify:
   # - "interiors" field exists (not "interior_recommendations")
   # - "interiors" is List type (L), not String (S)
   # - Each item has "imageUrl" field
   # - "interiorGenerationStatus" is "completed"
   ```

3. **Verify Streamlit Polling**
   ```bash
   # Watch Streamlit logs
   # Should see:
   # - "Polling attempt X: Y/3 images generated"
   # - Progress bar updates
   # - "✅ 인테리어 추천 완료! (3개 이미지 생성)"
   ```

4. **Test Manual Refresh Button**
   ```bash
   # If timeout occurs:
   # - "🔄 상태 새로고침" button should appear
   # - Click button
   # - Should see updated status
   # - Rate limiting should prevent rapid clicks
   ```

5. **Test Backward Compatibility**
   ```bash
   # Manually insert old format data
   aws dynamodb update-item \
     --table-name ai-branding-chatbot-sessions \
     --key '{"sessionId":{"S":"TEST_SESSION"}}' \
     --update-expression "SET interior_recommendations = :val" \
     --expression-attribute-values '{":val":{"S":"{\"recommendations\":[...]}"}}'
   
   # Verify Streamlit can parse and display
   ```

### Integration Test (AWS Dev Environment)

```python
def test_interior_data_structure():
    """Test interior data is saved correctly to DynamoDB"""
    # 1. Create session
    session_id = create_test_session()
    
    # 2. Generate interior recommendations
    response = requests.post(
        f"{API_BASE_URL}/interiors/generate",
        json={"sessionId": session_id, "businessInfo": {...}}
    )
    assert response.status_code == 200
    
    # 3. Query DynamoDB
    item = dynamodb.get_item(
        TableName="ai-branding-chatbot-sessions",
        Key={"sessionId": {"S": session_id}}
    )
    
    # 4. Verify structure
    assert "interiors" in item["Item"]
    assert item["Item"]["interiors"]["L"]  # List type
    assert item["Item"]["interiors"]["L"][0]["M"]  # Map type
    assert "imageUrl" in item["Item"]["interiors"]["L"][0]["M"]
    assert item["Item"]["interiorGenerationStatus"]["S"] == "completed"
```

## Deployment Steps

### 1. Deploy Interior Agent Lambda

```bash
# Build SAM application
sam build

# Deploy to dev environment
sam deploy --config-env dev

# Verify deployment
aws lambda get-function \
  --function-name ai-branding-chatbot-interior-agent-dev \
  --query 'Configuration.LastModified'
```

### 2. Restart Streamlit

```bash
# Stop current Streamlit process
pkill -f streamlit

# Start Streamlit
streamlit run src/streamlit/app.py --server.port 8501
```

### 3. Verify CloudWatch Logs

```bash
# Watch Interior Agent logs
aws logs tail /aws/lambda/ai-branding-chatbot-interior-agent-dev --follow

# Look for:
# - "Saving interior data to DynamoDB: 3 recommendations"
# - "Sample structure: {...}"
# - "✅ Successfully saved 3 interiors to DynamoDB as Map type"
```

### 4. Test End-to-End Workflow

```bash
# 1. Open Streamlit: http://localhost:8501
# 2. Complete Steps 1-3 (Analysis, Names, Signboard)
# 3. Click "인테리어 추천 생성"
# 4. Watch polling progress
# 5. Verify 3 images display correctly
# 6. Check DynamoDB data structure
```

## Monitoring

### CloudWatch Metrics

Monitor these custom metrics:
- `InteriorAgent.DynamoDBSaveSuccess`
- `InteriorAgent.DynamoDBSaveFailure`
- `StreamlitPolling.Timeout`

### CloudWatch Logs

**Interior Agent:**
```
✅ Successfully saved 3 interiors to DynamoDB as Map type
Interior recommendation fields: ['style', 'description', 'imageUrl', 'isGenerated', 'provider', ...]
```

**Streamlit:**
```
Polling attempt 15: 3/3 images generated, status=completed
Interior generation complete! 3 images generated
```

### Alerts

Set up CloudWatch Alarms:
- Alert if DynamoDB save failure rate > 5%
- Alert if Streamlit polling timeout rate > 10%

## Rollback Plan

If issues occur:

1. **Interior Agent**: Revert Lambda deployment
   ```bash
   # Deploy previous version
   sam deploy --config-env dev --parameter-overrides Version=previous
   ```

2. **Streamlit**: No rollback needed (backward compatible)
   - New code supports both old and new formats
   - No breaking changes

3. **DynamoDB**: No schema changes needed
   - New fields are additive only
   - Old data still works

## Success Criteria

✅ **DynamoDB Structure**
- `interiors` field is Map type (not JSON string)
- Each recommendation has `imageUrl`, `isGenerated`, `provider` fields
- Status fields are set correctly

✅ **Streamlit Polling**
- Accurate progress display: "X/3 images generated"
- Polling completes when all images ready
- Backward compatibility with old format

✅ **Manual Refresh**
- Button appears on timeout
- Rate limiting works (2-second cooldown)
- Updates UI with latest data

✅ **Error Handling**
- Graceful degradation on DynamoDB save failure
- JSON parsing errors handled gracefully
- User-friendly error messages

## Files Modified

1. `src/lambda/agents/interior/index.py`
   - Added `_save_interior_to_dynamodb()` method
   - Modified `_generate_interior_recommendations_with_bedrock()` to call save method
   - Added status field updates

2. `src/streamlit/app.py`
   - Enhanced `start_interior_generation()` polling logic
   - Added `manual_refresh_interior_status()` function
   - Modified `display_interior_options()` to show refresh button
   - Added backward compatibility for JSON string parsing

3. `docs/INTERIOR_DATA_STRUCTURE_FIX.md` (this file)
   - Implementation summary and deployment guide

## Related Issues

- Original issue: "0/3 images generated" despite successful image generation
- CloudWatch logs showed images were created and uploaded to S3
- DynamoDB data was either missing or in wrong format (JSON string)
- Streamlit polling couldn't detect completion

## Next Steps

1. ✅ Deploy to dev environment
2. ✅ Test end-to-end workflow
3. ✅ Monitor CloudWatch logs
4. ✅ Verify DynamoDB structure
5. ⏳ Deploy to production (after validation)

## Contact

For questions or issues, check:
- CloudWatch Logs: `/aws/lambda/ai-branding-chatbot-interior-agent-dev`
- DynamoDB Console: `ai-branding-chatbot-sessions` table
- Streamlit logs: Local terminal output
