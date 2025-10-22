# Streamlit E2E Testing Guide

## 개요

Streamlit 전체 워크플로를 자동으로 테스트할 수 있는 2가지 방법을 제공합니다:

1. **API 기반 테스트** - AWS API를 직접 호출하여 백엔드 로직 테스트
2. **UI 기반 테스트** - Playwright로 실제 Streamlit UI 상호작용 테스트

---

## 빠른 시작

### 1. API 테스트 (추천)

```bash
# 간단하고 빠름!
python tests/e2e/test_streamlit_workflow.py
```

**장점:**
- ✅ 빠른 실행 (2-5분)
- ✅ CI/CD 통합 쉬움
- ✅ 브라우저 불필요
- ✅ 백엔드 로직 직접 테스트

### 2. UI 테스트

```bash
# Terminal 1: Streamlit 실행
streamlit run src/streamlit/app.py

# Terminal 2: UI 테스트 실행
python tests/e2e/test_streamlit_ui.py
```

**장점:**
- ✅ 실제 사용자 경험 테스트
- ✅ UI 버그 발견
- ✅ 실패 시 스크린샷 저장
- ✅ 시각적 확인 가능

### 3. 통합 스크립트

```bash
# API 테스트만
./run_e2e_tests.sh --api-only

# UI 테스트만
./run_e2e_tests.sh --ui-only

# 모두 실행
./run_e2e_tests.sh --all
```

---

## 테스트 내용

### API 테스트가 검증하는 것:

1. **Step 1: Business Analysis**
   - ✅ 세션 생성
   - ✅ 비즈니스 정보 제출
   - ✅ 분석 결과 수신
   - ✅ Score 및 Summary 확인

2. **Step 2: Name Generation**
   - ✅ 비동기 요청 시작 (202 응답)
   - ✅ 폴링으로 결과 대기
   - ✅ 3개 이상 이름 생성 확인
   - ✅ 첫 번째 이름 자동 선택

3. **Step 3: Signboard Generation**
   - ✅ 비동기 요청 시작
   - ✅ 폴링으로 이미지 대기
   - ✅ 3개 이미지 생성 확인
   - ✅ 첫 번째 디자인 선택

4. **Step 4: Interior Generation**
   - ✅ 비동기 요청 시작
   - ✅ 폴링으로 추천 대기
   - ✅ 3개 추천 생성 확인

5. **Step 5: Report Generation**
   - ✅ 보고서 생성 요청
   - ✅ 보고서 URL 수신

### UI 테스트가 검증하는 것:

1. **Form Interaction**
   - ✅ Country 선택 → City 자동 업데이트
   - ✅ Industry, Size 선택
   - ✅ Description 입력
   - ✅ Submit 버튼 클릭

2. **Navigation**
   - ✅ Step 간 자동 이동
   - ✅ "Next Step" 버튼 작동
   - ✅ Progress bar 업데이트

3. **Async Feedback**
   - ✅ "Generation started" 메시지
   - ✅ Progress bar 표시
   - ✅ "Complete" 메시지
   - ✅ 디버그 정보 표시

4. **Selection**
   - ✅ "Select This Name" 버튼
   - ✅ "Select This Design" 버튼
   - ✅ 선택 후 다음 단계 시작

---

## 설치

### API 테스트 의존성

```bash
pip install requests
```

### UI 테스트 의존성

```bash
pip install playwright pytest-playwright
playwright install chromium
```

---

## 실행 예시

### API 테스트 출력:

```
================================================================================
Starting Full Workflow Test
================================================================================

================================================================================
STEP 1: Business Analysis
================================================================================
Creating session...
✅ Session created: cd38bd1e-ef15-4fb1-936f-8695adf1baff
Starting business analysis...
✅ Analysis complete!
   Score: 85
   Summary: Strong market potential for Korean fusion restaurant in New York...

================================================================================
STEP 2: Business Name Generation
================================================================================
Starting name generation (async)...
✅ Name generation started, polling for results...
   Polling... (30s elapsed)
✅ Name generation complete! (3 names)
   1. Seoul Fusion (score: 0.92)
   2. Hanbok Kitchen (score: 0.88)
   3. K-Town Table (score: 0.85)
✅ Selected name: Seoul Fusion

================================================================================
STEP 3: Signboard Design Generation
================================================================================
Starting signboard generation (async)...
✅ Signboard generation started, polling for results...
   Polling... (60s elapsed)
✅ Signboard generation complete! (3 images)
   1. Style: modern, Provider: bedrock_sdxl
   2. Style: classic, Provider: bedrock_sdxl
   3. Style: vibrant, Provider: dalle
✅ Selected signboard: s3://ai-branding-chatbot-assets.../signboard_1.png
✅ Signboard selected successfully

================================================================================
STEP 4: Interior Recommendations Generation
================================================================================
Starting interior generation (async)...
✅ Interior generation started, polling for results...
   Polling... (30s elapsed)
✅ Interior generation complete! (3 recommendations)
   1. Style: modern
   2. Style: traditional
   3. Style: minimalist

================================================================================
STEP 5: Final Report Generation
================================================================================
Starting report generation...
✅ Report generation complete!
   Report URL: s3://ai-branding-chatbot-assets.../report.html

================================================================================
✅ ALL TESTS PASSED!
================================================================================

================================================================================
📊 FINAL SESSION SUMMARY
================================================================================
Session ID: cd38bd1e-ef15-4fb1-936f-8695adf1baff
Business Name: Seoul Fusion
Current Step: 5
Status: completed
================================================================================
```

---

## 커스터마이징

### 다른 비즈니스 정보로 테스트

`tests/e2e/test_streamlit_workflow.py` 수정:

```python
self.business_info = {
    "industry": "retail",  # 변경
    "country": "South Korea",  # 변경
    "city": "Seoul",  # 변경
    "region": "Seoul, South Korea",
    "size": "medium",  # 변경
    "description": "Modern fashion boutique"  # 변경
}
```

### 타임아웃 조정

```python
# 폴링 시간 증가
max_attempts = 90  # 90 * 3s = 270s (4.5분)

# 개별 요청 타임아웃 증가
timeout=120  # 2분
```

### Headless 모드 (CI/CD용)

`tests/e2e/test_streamlit_ui.py` 수정:

```python
# 브라우저 창 표시 안 함
browser = p.chromium.launch(headless=True)
```

---

## CI/CD 통합

### GitHub Actions 예시

`.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Run API tests
        run: python tests/e2e/test_streamlit_workflow.py
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
```

---

## 문제 해결

### API 테스트 실패

**증상:** Connection refused
```bash
❌ Cannot connect to API server
```

**해결:**
```bash
# API 배포 확인
sam deploy --config-env dev

# API 엔드포인트 테스트
curl https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev/
```

**증상:** Timeout during polling
```bash
❌ Name generation timeout
```

**해결:**
```bash
# CloudWatch 로그 확인
aws logs tail /aws/lambda/ai-branding-chatbot-reporter-agent-dev --follow

# Lambda 타임아웃 확인 (180s 이상이어야 함)
aws lambda get-function-configuration \
  --function-name ai-branding-chatbot-reporter-agent-dev \
  --query 'Timeout'
```

### UI 테스트 실패

**증상:** Streamlit not found
```bash
❌ Navigation timeout
```

**해결:**
```bash
# Streamlit 실행 확인
curl http://localhost:8501

# Streamlit 재시작
streamlit run src/streamlit/app.py
```

**증상:** Element not found
```bash
❌ Selector not found
```

**해결:**
1. `test_failure.png` 스크린샷 확인
2. Selector 업데이트
3. `time.sleep()` 추가

---

## 파일 구조

```
tests/
└── e2e/
    ├── README.md                      # 상세 문서
    ├── test_streamlit_workflow.py     # API 테스트
    └── test_streamlit_ui.py           # UI 테스트

run_e2e_tests.sh                       # 통합 실행 스크립트
STREAMLIT_E2E_TESTING.md              # 이 문서
```

---

## 다음 단계

### 1. 정기 실행 설정

```bash
# Cron job 추가 (매일 오전 9시)
0 9 * * * cd /path/to/project && ./run_e2e_tests.sh --api-only
```

### 2. 알림 설정

```bash
# 실패 시 Slack 알림
if ! ./run_e2e_tests.sh --api-only; then
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"E2E tests failed!"}' \
      YOUR_SLACK_WEBHOOK_URL
fi
```

### 3. 성능 모니터링

```python
# 각 단계 실행 시간 측정
start_time = time.time()
# ... test code ...
duration = time.time() - start_time
logger.info(f"Step completed in {duration:.2f}s")
```

---

## 요약

✅ **API 테스트**: 빠르고 안정적, CI/CD에 적합
✅ **UI 테스트**: 실제 사용자 경험 검증
✅ **자동화**: 수동 테스트 시간 절약
✅ **신뢰성**: 배포 전 버그 발견

**추천 워크플로:**
1. 개발 중: API 테스트로 빠른 피드백
2. PR 전: UI 테스트로 전체 검증
3. 배포 전: 두 테스트 모두 실행
4. 프로덕션: 정기적으로 API 테스트 실행

---

## 참고 자료

- [tests/e2e/README.md](tests/e2e/README.md) - 상세 문서
- [Playwright Documentation](https://playwright.dev/python/)
- [AWS API Gateway Testing](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-test-method.html)
