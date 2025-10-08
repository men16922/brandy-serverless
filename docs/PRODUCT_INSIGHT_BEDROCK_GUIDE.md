# Product Insight Agent - Bedrock Integration Guide

## Quick Start

### Local Development (Fallback Mode)

```bash
# Set environment variables
export ENABLE_FALLBACK=true
export ENVIRONMENT=local

# Run validation
python3 scripts/validate-product-insight-bedrock.py

# Expected output: All tests passing with baseline_fallback provider
```

### Production Deployment (Bedrock Mode)

```bash
# Set environment variables in template.yaml or samconfig.toml
ENABLE_FALLBACK=false
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Deploy with SAM
sam build
sam deploy --guided
```

## API Usage

### Request Format

```json
{
  "body": {
    "sessionId": "session-123",
    "businessInfo": {
      "industry": "restaurant",
      "region": "seoul",
      "size": "small"
    }
  }
}
```

### Response Format (Bedrock Mode)

```json
{
  "sessionId": "session-123",
  "analysis": {
    "summary": "seoul 지역의 small 규모 restaurant 사업 분석 결과, 종합 점수 85점으로 평가됩니다.",
    "score": 85,
    "insights": [
      "restaurant 업종은 안정적인 성장이 예상되며...",
      "seoul 지역은 대규모 시장과 높은 구매력...",
      "small 규모는 1천만원 - 5천만원의 투자로..."
    ],
    "recommendations": [
      "맛과 서비스 품질의 일관성",
      "효율적인 재고 관리와 원가 절감",
      "고객 재방문율 향상 전략"
    ],
    "market_trends": [...],
    "bedrock_reasoning": "종합 평가: 이 비즈니스는...",
    "confidence": 0.85
  },
  "metadata": {
    "analyzed_at": "2025-10-09T12:00:00Z",
    "agent": "product_insight",
    "version": "2.1.0",
    "analysis_provider": "bedrock",
    "bedrock_enabled": true
  }
}
```

### Response Format (Fallback Mode)

```json
{
  "sessionId": "session-123",
  "analysis": {
    "summary": "seoul 지역의 small 규모 restaurant 사업 분석 결과, 종합 점수 80점으로 평가됩니다.",
    "score": 80,
    "insights": [...],
    "recommendations": [...]
  },
  "metadata": {
    "analyzed_at": "2025-10-09T12:00:00Z",
    "agent": "product_insight",
    "version": "2.1.0",
    "analysis_provider": "baseline_fallback",
    "bedrock_enabled": false
  }
}
```

## Supported Industries

1. restaurant (음식점)
2. retail (소매업)
3. service (서비스업)
4. healthcare (의료)
5. education (교육)
6. technology (기술)
7. manufacturing (제조업)
8. construction (건설)
9. finance (금융)
10. beauty (뷰티)
11. fitness (피트니스)
12. entertainment (엔터테인먼트)
13. automotive (자동차)
14. agriculture (농업)
15. logistics (물류)
16. other (기타)

## Supported Regions

1. seoul (서울)
2. busan (부산)
3. daegu (대구)
4. incheon (인천)
5. gwangju (광주)
6. daejeon (대전)
7. ulsan (울산)
8. gyeonggi (경기)
9. gangwon (강원)
10. chungbuk (충북)
11. chungnam (충남)
12. jeonbuk (전북)
13. jeonnam (전남)
14. gyeongbuk (경북)
15. gyeongnam (경남)
16. jeju (제주)

## Supported Sizes

1. small (소규모: 1-5명, 1천만원-5천만원)
2. medium (중규모: 6-30명, 5천만원-3억원)
3. large (대규모: 30명 이상, 3억원 이상)

## Environment Variables

### Required
- `SESSIONS_TABLE`: DynamoDB table name for sessions
- `S3_BUCKET`: S3 bucket for file storage

### Optional (Bedrock)
- `ENABLE_FALLBACK`: Enable/disable fallback mode (default: true)
- `BEDROCK_REGION`: AWS region for Bedrock (default: us-east-1)
- `CLAUDE_MODEL_ID`: Claude model ID (default: us.anthropic.claude-sonnet-4-20250514-v1:0)
- `BEDROCK_MAX_RETRIES`: Max retry attempts (default: 3)
- `BEDROCK_TIMEOUT`: API timeout in seconds (default: 30)

## IAM Permissions

### Bedrock Permissions (Production)

```yaml
- Effect: Allow
  Action:
    - bedrock:InvokeModel
    - bedrock:InvokeModelWithResponseStream
  Resource:
    - arn:aws:bedrock:*::foundation-model/anthropic.claude-*
```

### DynamoDB Permissions

```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:PutItem
    - dynamodb:UpdateItem
  Resource:
    - arn:aws:dynamodb:*:*:table/${SessionsTable}
```

## Monitoring

### CloudWatch Metrics

Monitor these metrics:
- `bedrock_api_call`: Bedrock API invocations
- `latency_ms`: Response time
- `analysis_provider`: Provider used (bedrock/baseline_fallback)
- `confidence`: Analysis confidence score

### CloudWatch Logs

Search for:
- `"Bedrock analysis complete"`: Successful Bedrock calls
- `"Bedrock analysis failed"`: Failed Bedrock calls
- `"Fallback enabled"`: Fallback mode active
- `"Business analysis completed"`: Overall completion

### Example Log Query

```
fields @timestamp, agent, analysis_provider, latency_ms, confidence
| filter agent = "product_insight"
| stats avg(latency_ms) as avg_latency, avg(confidence) as avg_confidence by analysis_provider
```

## Troubleshooting

### Issue: Bedrock Not Available

**Symptoms**: `analysis_provider` is "baseline_no_bedrock"

**Solutions**:
1. Check IAM permissions for Bedrock
2. Verify `BEDROCK_REGION` is correct
3. Ensure Claude model is available in region
4. Check CloudWatch logs for initialization errors

### Issue: High Latency

**Symptoms**: `latency_ms` > 5000ms

**Solutions**:
1. Check Bedrock API throttling
2. Verify network connectivity
3. Consider increasing timeout
4. Monitor Bedrock service status

### Issue: Low Confidence Scores

**Symptoms**: `confidence` < 0.7

**Solutions**:
1. Review input data quality
2. Check if industry/region/size are valid
3. Refine Claude prompts
4. Adjust temperature parameter

### Issue: Fallback Always Used

**Symptoms**: `analysis_provider` always "baseline_fallback"

**Solutions**:
1. Check `ENABLE_FALLBACK` environment variable
2. Verify Bedrock client initialization
3. Review CloudWatch logs for errors
4. Test Bedrock connectivity

## Performance Optimization

### Reduce Latency
1. Use regional Bedrock endpoints
2. Implement response caching
3. Optimize prompt length
4. Use lower temperature for faster responses

### Reduce Costs
1. Enable fallback for non-critical requests
2. Cache frequent analysis results
3. Use batch processing when possible
4. Monitor token usage

### Improve Quality
1. Refine system prompts
2. Add industry-specific context
3. Increase temperature for creativity
4. Validate confidence scores

## Testing

### Unit Tests
```bash
# Run validation script
python3 scripts/validate-product-insight-bedrock.py
```

### Integration Tests
```bash
# Start Docker services
docker-compose -f docker-compose.local.yml up -d

# Run integration tests
pytest tests/integration/test_product_insight.py -v
```

### Load Tests
```bash
# Use artillery or similar tool
artillery quick --count 10 --num 100 https://api.example.com/analyze
```

## Best Practices

### Development
1. Always use `ENABLE_FALLBACK=true` locally
2. Test both Bedrock and fallback modes
3. Validate response structure
4. Monitor logs for errors

### Production
1. Set `ENABLE_FALLBACK=false` for Bedrock-only
2. Monitor Bedrock API costs
3. Set up CloudWatch alarms
4. Implement circuit breakers

### Prompt Engineering
1. Keep prompts concise and clear
2. Use structured JSON responses
3. Include specific examples
4. Test with various inputs

## Support

### Documentation
- Implementation: `docs/implementation/TASK_14_PRODUCT_INSIGHT_BEDROCK.md`
- Summary: `TASK_14_SUMMARY.md`
- Tasks: `.kiro/specs/aws-hackathon-compliance/tasks.md`

### Validation
- Script: `scripts/validate-product-insight-bedrock.py`
- Expected: All tests passing

### Contact
- GitHub Issues: [Project Repository]
- AWS Support: For Bedrock-specific issues

---

**Last Updated**: 2025-10-09  
**Version**: 2.1.0  
**Status**: Production Ready ✅
