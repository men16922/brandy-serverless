# 다음 단계: Market Analyst Agent 코드 리팩토링

## 현재 상태

✅ **완료된 작업**:
1. JSON 파일 7개 생성 (정적 데이터)
2. DynamoDB 테이블 설계 (동적 데이터)
3. JSON 데이터 로더 구현
4. DynamoDB 데이터 로더 구현
5. 초기 데이터 시딩 스크립트 작성
6. SAM template 업데이트

⏳ **다음 작업**:
- Market Analyst Agent 코드에서 하드코딩 제거
- JSON/DynamoDB 로더 통합
- 통합 테스트 실행

---

## 코드 리팩토링 계획

### 수정이 필요한 메서드 (index.py)

1. **`_analyze_consumer_preferences()`**
   - 현재: 하드코딩된 `generational_preferences`, `regional_preferences`, `behavioral_changes`
   - 변경: JSON 로더 + DynamoDB 로더 사용

2. **`_analyze_trend_risks()`**
   - 현재: 하드코딩된 `trend_risks`, `industry_specific_risks`
   - 변경: JSON 로더 + DynamoDB 로더 사용

3. **`_analyze_entry_barriers()`**
   - 현재: 하드코딩된 `barriers_data`
   - 변경: JSON 로더 사용

4. **`_get_differentiation_factors()`**
   - 현재: 하드코딩된 `factors`
   - 변경: JSON 로더 사용

5. **`_get_benchmark_metrics()`**
   - 현재: 하드코딩된 `metrics`
   - 변경: DynamoDB 로더 사용

6. **`_identify_market_gaps()`**
   - 현재: 하드코딩된 `gaps`
   - 변경: DynamoDB 로더 사용

7. **`_identify_new_segments()`**
   - 현재: 하드코딩된 `segments`
   - 변경: DynamoDB 로더 사용

8. **`_identify_tech_opportunities()`**
   - 현재: 하드코딩된 `opportunities`
   - 변경: DynamoDB 로더 사용

9. **`_identify_partnership_opportunities()`**
   - 현재: 하드코딩된 `partnerships`
   - 변경: JSON 로더 사용

10. **`_identify_expansion_opportunities()`**
    - 현재: 하드코딩된 `opportunities`
    - 변경: JSON 로더 사용

11. **`_extract_preference_insights()`**
    - 현재: 하드코딩된 `insights`
    - 변경: DynamoDB 로더 사용

12. **`_project_future_preferences()`**
    - 현재: 하드코딩된 전망 데이터
    - 변경: DynamoDB 로더 사용

---

## 리팩토링 예시

### Before (하드코딩)
```python
def _analyze_entry_barriers(self, industry: str) -> List[Dict[str, str]]:
    """진입 장벽 분석"""
    barriers_data = {
        "restaurant": [
            {"barrier": "초기 투자비", "level": "중간", "description": "인테리어, 장비 비용"},
            ...
        ],
        ...
    }
    return barriers_data.get(industry, barriers_data["service"])
```

### After (JSON 로더)
```python
def _analyze_entry_barriers(self, industry: str) -> List[Dict[str, str]]:
    """진입 장벽 분석"""
    from data_loader import get_data_loader
    
    loader = get_data_loader()
    barriers_data = loader.get_entry_barriers()
    
    return barriers_data.get(industry, barriers_data.get("service", []))
```

### Before (하드코딩)
```python
def _get_benchmark_metrics(self, industry: str) -> Dict[str, str]:
    """벤치마크 지표"""
    metrics = {
        "restaurant": {
            "고객 재방문율": "60-70%",
            ...
        },
        ...
    }
    return metrics.get(industry, {"고객 만족도": "85%", "재이용률": "70%"})
```

### After (DynamoDB 로더)
```python
def _get_benchmark_metrics(self, industry: str) -> Dict[str, str]:
    """벤치마크 지표"""
    from dynamodb_loader import get_dynamodb_loader
    
    loader = get_dynamodb_loader()
    metrics = loader.get_benchmark_metrics(industry, region="GLOBAL")
    
    # Fallback
    if not metrics:
        metrics = {"고객 만족도": "85%", "재이용률": "70%"}
    
    return metrics
```

---

## 실행 순서

### 1. 테이블 배포
```bash
# SAM 빌드 및 배포
sam build
sam deploy --guided

# 배포 확인
aws dynamodb describe-table \
  --table-name ai-branding-chatbot-market-analysis-dev
```

### 2. 초기 데이터 로드
```bash
# 환경 변수 설정
export ENVIRONMENT=dev
export AWS_PROFILE=your-profile

# 데이터 시딩
python3 scripts/seed-market-analysis-data.py
```

### 3. 코드 리팩토링
```bash
# index.py 수정 (12개 메서드)
# - JSON 로더 통합 (7개 메서드)
# - DynamoDB 로더 통합 (5개 메서드)
```

### 4. 로컬 테스트
```bash
# Docker Compose 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 통합 테스트 실행
pytest tests/integration/test_market_analyst.py -v
```

### 5. 배포 및 검증
```bash
# Lambda 재배포
sam build
sam deploy

# API 테스트
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/dev/market-analysis \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test-123","businessInfo":{"industry":"restaurant","region":"seoul"}}'
```

---

## 예상 소요 시간

- 코드 리팩토링: 2-3시간
- 테스트 및 디버깅: 1-2시간
- 문서화: 30분

**총 예상 시간**: 4-6시간

---

## 체크리스트

### 배포 전
- [ ] SAM template 검증
- [ ] 환경 변수 설정 확인
- [ ] IAM 권한 확인 (DynamoDB 읽기/쓰기)

### 배포 후
- [ ] DynamoDB 테이블 생성 확인
- [ ] 초기 데이터 로드 성공 확인
- [ ] 데이터 조회 테스트

### 리팩토링 후
- [ ] 12개 메서드 수정 완료
- [ ] 로컬 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 (응답 시간)
- [ ] 에러 핸들링 검증

### 문서화
- [ ] 코드 주석 업데이트
- [ ] README 업데이트
- [ ] API 문서 업데이트

---

## 진행하시겠습니까?

다음 중 선택하세요:

1. **코드 리팩토링 시작** - index.py 수정 시작
2. **테이블 먼저 배포** - SAM deploy 실행
3. **테스트 환경 구성** - Docker Compose 설정
4. **일시 중지** - 나중에 계속

---

**현재 위치**: 데이터 분리 완료, 코드 리팩토링 대기 중
**다음 작업**: Market Analyst Agent index.py 리팩토링
