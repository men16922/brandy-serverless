# Interior Data Structure - Testing Guide

## ✅ Code Verification Complete

### Float to Decimal Conversion Logic

**1. Data Generation (`_recommendation_to_dict`)**
```python
{
    "suitabilityScore": recommendation.suitability_score,  # float (e.g., 92.0)
    ...
}
```

**2. DynamoDB Save (`_save_interior_to_dynamodb`)**
```python
def float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))  # ✅ Converts 92.0 → Decimal('92.0')
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(item) for item in obj]
    return obj

recommendations_clean = float_to_decimal(recommendations)  # ✅ All floats → Decimals
```

**3. DynamoDB Storage**
```json
{
  "interiors": {
    "L": [
      {
        "M": {
          "suitabilityScore": {"N": "92.0"},  // ✅ Stored as Number (Decimal)
          "style": {"S": "cozy"},
          "imageUrl": {"S": "https://..."}
        }
      }
    ]
  }
}
```

## 🧪 Testing Steps

### Step 1: Start New Session

**Important:** Must use a NEW session to test the fixed code!

```bash
# Open Streamlit
streamlit run src/streamlit/app.py --server.port 8501

# Open browser
http://localhost:8501
```

### Step 2: Complete Workflow

1. **Step 1: Business Analysis**
   - Industry: restaurant
   - Region: seoul
   - Size: small
   - Click "분석 시작"

2. **Step 2: Name Generation**
   - Wait for 3 name suggestions
   - Select any name

3. **Step 3: Signboard Design**
   - Wait for 3 signboard images
   - Select any signboard

4. **Step 4: Interior Generation**
   - Click "인테리어 추천 생성"
   - Watch polling progress
   - Should see: "1/3 images generated" → "2/3" → "3/3"
   - Should complete in ~60 seconds

### Step 3: Verify DynamoDB Structure

```bash
# Get your session ID from Streamlit UI (shown at top)
SESSION_ID="your-session-id-here"

# Query DynamoDB
aws dynamodb get-item \
  --table-name ai-branding-chatbot-sessions \
  --key "{\"sessionId\":{\"S\":\"$SESSION_ID\"}}" \
  --region us-east-1 \
  --query 'Item.{interiors:interiors,status:interiorGenerationStatus}' \
  > interior_data.json

# Check the structure
cat interior_data.json
```

**Expected Output:**
```json
{
  "interiors": {
    "L": [
      {
        "M": {
          "style": {"S": "cozy"},
          "description": {"S": "..."},
          "imageUrl": {"S": "https://ai-branding-chatbot-assets-908601828278.s3.amazonaws.com/interiors/..."},
          "isGenerated": {"BOOL": true},
          "provider": {"S": "bedrock-titan"},
          "colorScheme": {"L": [{"S": "색상1"}, {"S": "색상2"}]},
          "materials": {"L": [{"S": "소재1"}, {"S": "소재2"}]},
          "furniture": {"L": [{"S": "가구1"}, {"S": "가구2"}]},
          "estimatedCost": {"S": "중간"},
          "suitabilityScore": {"N": "92.0"},  // ✅ Number type (Decimal)
          "pros": {"L": [{"S": "장점1"}]},
          "cons": {"L": [{"S": "단점1"}]},
          "generatedAt": {"S": "2025-10-19T..."}
        }
      }
    ]
  },
  "status": {"S": "completed"}
}
```

### Step 4: Verify CloudWatch Logs

```bash
# Watch Interior Agent logs
aws logs tail /aws/lambda/ai-branding-chatbot-interior-agent-dev --follow

# Look for these success messages:
# ✅ [cozy] ✅ Bedrock Titan succeeded: https://...
# ✅ [modern] ✅ Bedrock Titan succeeded: https://...
# ✅ [industrial] ✅ Bedrock Titan succeeded: https://...
# ✅ Saving interior data to DynamoDB: 3 recommendations
# ✅ Successfully saved 3 interiors to DynamoDB as Map type

# Should NOT see:
# ❌ Float types are not supported
# ❌ Failed to save interior data to DynamoDB
```

### Step 5: Verify Streamlit Display

**Expected UI:**
- ✅ Progress bar shows "3/3 images generated"
- ✅ Three interior options displayed with images
- ✅ Each option shows:
  - Style name (cozy, modern, industrial)
  - Interior image
  - Provider badge (🎨 Amazon Bedrock Titan)
  - Description
  - Suitability score progress bar
  - Color scheme, materials, furniture
  - Pros and cons
  - Selection button

## 🔍 Troubleshooting

### Issue: Still seeing "0/3 images generated"

**Check 1: Is it a new session?**
```bash
# Old sessions won't have the new 'interiors' field
# Must start a completely new session
```

**Check 2: Check CloudWatch logs**
```bash
aws logs tail /aws/lambda/ai-branding-chatbot-interior-agent-dev --since 5m

# Look for errors
```

**Check 3: Check DynamoDB directly**
```bash
aws dynamodb get-item \
  --table-name ai-branding-chatbot-sessions \
  --key "{\"sessionId\":{\"S\":\"$SESSION_ID\"}}" \
  --region us-east-1
```

### Issue: "Float types are not supported" error

**This means the code wasn't deployed properly.**

```bash
# Rebuild and redeploy
sam build
sam deploy --config-env dev --no-confirm-changeset

# Verify Lambda was updated
aws lambda get-function \
  --function-name ai-branding-chatbot-interior-agent-dev \
  --query 'Configuration.LastModified'
```

### Issue: Manual refresh button doesn't appear

**Check Streamlit code:**
```python
# Should see this in app.py
show_refresh = st.session_state.get('interior_timeout', False) or interior_status == "in_progress"

if show_refresh and not interior_data:
    if st.button("🔄 상태 새로고침"):
        manual_refresh_interior_status()
```

## ✅ Success Criteria

- [ ] New session created
- [ ] Interior generation completes in ~60 seconds
- [ ] Polling shows "3/3 images generated"
- [ ] DynamoDB has `interiors` field (not `interior_recommendations`)
- [ ] `interiors` is List type (L), not String (S)
- [ ] `suitabilityScore` is Number type (N), not Float
- [ ] All 3 images display in Streamlit
- [ ] No "Float types are not supported" error in logs
- [ ] CloudWatch shows "✅ Successfully saved 3 interiors to DynamoDB"

## 📊 Data Type Verification

### Correct DynamoDB Types

```python
{
  "interiors": "L",              # ✅ List
  "interiors[0]": "M",           # ✅ Map
  "style": "S",                  # ✅ String
  "imageUrl": "S",               # ✅ String
  "isGenerated": "BOOL",         # ✅ Boolean
  "suitabilityScore": "N",       # ✅ Number (Decimal)
  "colorScheme": "L",            # ✅ List
  "pros": "L",                   # ✅ List
  "cons": "L"                    # ✅ List
}
```

### Incorrect Types (Old Format)

```python
{
  "interior_recommendations": "S",  # ❌ String (JSON)
  # Contains: {"suitabilityScore": 92.0}  # ❌ Float in JSON string
}
```

## 🎯 Expected Results

### Before Fix
```
Images: ✅ Generated (3/3)
S3: ✅ Uploaded
DynamoDB: ❌ Save failed (Float error)
Streamlit: ❌ Shows "0/3 images"
```

### After Fix
```
Images: ✅ Generated (3/3)
S3: ✅ Uploaded
DynamoDB: ✅ Saved as Map with Decimals
Streamlit: ✅ Shows "3/3 images"
```

## 📝 Test Report Template

```markdown
# Interior Data Structure Test Report

**Date:** 2025-10-19
**Tester:** [Your Name]
**Session ID:** [Your Session ID]

## Test Results

- [ ] New session created successfully
- [ ] Interior generation completed
- [ ] Polling showed accurate progress
- [ ] DynamoDB structure verified
- [ ] All data types correct (Decimal, not Float)
- [ ] Streamlit displayed 3 images
- [ ] No errors in CloudWatch logs

## DynamoDB Verification

```bash
# Command used
aws dynamodb get-item --table-name ai-branding-chatbot-sessions --key '{"sessionId":{"S":"xxx"}}'

# Result
[Paste DynamoDB output here]
```

## CloudWatch Logs

```
[Paste relevant log entries here]
```

## Screenshots

[Attach Streamlit UI screenshots showing 3 images]

## Issues Found

[List any issues or unexpected behavior]

## Conclusion

✅ Test PASSED / ❌ Test FAILED

[Additional notes]
```

## 🚀 Next Steps After Successful Test

1. ✅ Verify all test criteria passed
2. ✅ Document test results
3. ✅ Update project status
4. ✅ Consider deploying to production
5. ✅ Monitor production metrics

## 📞 Support

If you encounter issues:

1. Check CloudWatch logs first
2. Verify DynamoDB structure
3. Ensure using a NEW session
4. Confirm Lambda was deployed
5. Check Streamlit console for errors

**All systems should be working correctly now!** 🎉
