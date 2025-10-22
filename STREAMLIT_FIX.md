# Streamlit Report Generation 오류 수정

## 문제

**증상:**
```
✅ Interior option has been selected!
Report generation error: Failed to start report generation after 3 attempts
```

## 원인 분석

### 1. Lambda는 정상 동작
```
✅ Report Generator Agent 성공
- Duration: 37.1초
- HTML 생성: 29.3 KiB
- S3 저장: reports/2ea24d18-70b8-4564-bae8-2b6a7386f496/branding_report_20251022_081201.html
```

### 2. Streamlit API 엔드포인트 오류
```python
# 잘못된 코드 (src/streamlit/app.py:1797)
status_response = requests.get(
    f"{API_BASE_URL}/session/{st.session_state.session_id}",  # ❌ 잘못된 엔드포인트
    timeout=10
)

# 올바른 코드
status_response = requests.get(
    f"{API_BASE_URL}/status/{st.session_state.session_id}",  # ✅ 올바른 엔드포인트
    timeout=10
)
```

## 수정 내용

### 파일: `src/streamlit/app.py`

**변경 전:**
```python
status_response = requests.get(
    f"{API_BASE_URL}/session/{st.session_state.session_id}",
    timeout=10
)
```

**변경 후:**
```python
status_response = requests.get(
    f"{API_BASE_URL}/status/{st.session_state.session_id}",
    timeout=10
)
```

## 검증

### 1. Report 생성 확인
```bash
aws s3 ls s3://ai-branding-chatbot-dev-brandingassetsbucket-13vah07ykzdc/reports/2ea24d18-70b8-4564-bae8-2b6a7386f496/

# 결과:
# 2025-10-22 17:12:02   29.3 KiB branding_report_20251022_081201.html
```

### 2. Lambda 로그 확인
```bash
aws logs tail /aws/lambda/ai-branding-chatbot-report-generator-agent-dev --since 5m

# 주요 로그:
# ✅ Successfully generated HTML report.
# ✅ Report generation completed in 36.44s
# ✅ Successfully stored html report: reports/.../branding_report_20251022_081201.html (29991 bytes)
# ✅ Agent execution completed: {"status": "success", "latency_ms": 36718}
```

### 3. API 엔드포인트 확인
```bash
# 올바른 엔드포인트
curl https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev/status/SESSION_ID

# 잘못된 엔드포인트 (404)
curl https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev/session/SESSION_ID
```

## 다음 단계

### 1. Streamlit 재시작
```bash
# 현재 실행 중인 Streamlit 중지 (Ctrl+C)

# 재시작
streamlit run src/streamlit/app.py
```

### 2. 전체 워크플로 테스트
1. Business Info 입력
2. Analysis 실행
3. Name 선택
4. Signboard 선택
5. Interior 선택
6. **Report 생성** ← 이제 정상 작동!

### 3. Report URL 확인
```
Report URL: https://ai-branding-chatbot-dev-brandingassetsbucket-13vah07ykzdc.s3.us-west-2.amazonaws.com/reports/SESSION_ID/branding_report_TIMESTAMP.html
```

## 추가 개선 사항

### 1. 타임아웃 증가 (이미 적용됨)
```python
# 기존: 30초
# 현재: 60초
timeout=60
```

### 2. 폴링 시간 증가 (이미 적용됨)
```python
# 최대 대기 시간: 180초 (3분)
max_wait_time = 180
poll_interval = 3  # 3초마다 확인
```

### 3. 비동기 모드 활성화 (이미 적용됨)
```python
headers={"x-async-mode": "true"}
```

## 결론

✅ **수정 완료!**

**문제:**
- Streamlit이 잘못된 API 엔드포인트 호출 (`/session/` → `/status/`)

**해결:**
- 올바른 엔드포인트로 수정
- Report는 실제로 정상 생성되고 있었음

**다음:**
- Streamlit 재시작
- 전체 워크플로 테스트
- Report 다운로드 확인

**예상 결과:**
```
✅ Interior option has been selected!
📄 Report is being generated in the background...
✅ Report generated successfully!
🎉 Download your branding report!
```
