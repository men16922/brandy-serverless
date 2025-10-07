# 프로젝트 정리 계획

## 🗑️ 제거할 파일들

### 1. 중복/임시 테스트 파일들 (루트 디렉토리)
- `test_ai_providers_simple.py` - 단순 테스트, 통합 테스트로 대체됨
- `test_alternative_report_generation.py` - 대안 구현, 불필요
- `test_complete_multi_ai_workflow.py` - 중복
- `test_complete_workflow_with_alternative_report.py` - 중복
- `test_final_report_generation.py` - 중복
- `test_full_workflow.py` - 중복
- `test_individual_ai_providers.py` - 중복
- `test_market_analyst_local.py` - 로컬 테스트, 통합 테스트로 대체
- `test_multi_ai_complete_workflow.py` - 중복
- `test_multi_ai_mock_integration.py` - Mock 테스트, 불필요
- `test_multi_ai_signboard.py` - 중복
- `test_openai_api.py` - 단순 API 테스트
- `test_real_dalle_generation.py` - 중복
- `test_real_multi_ai_integration.py` - 중복
- `test_reporter_agent.py` - 중복
- `test_reporter_only.py` - 중복
- `test_reporter_with_dynamodb.py` - 중복
- `test_simple_workflow.py` - 중복
- `test_streamlit_api_connection.py` - Streamlit 테스트
- `test_streamlit_app.py` - Streamlit 테스트

### 2. 임시 생성 파일들
- `test_report.html` - 테스트 결과물
- `test_report.json` - 테스트 결과물
- `test_report.txt` - 테스트 결과물
- `minio_test_image.png` - 테스트 이미지

### 3. 임시 디렉토리
- `test_env/` - 임시 테스트 환경
- `generated_images/` - 테스트 이미지들 (필요시 .gitignore)
- `generated-diagrams/` - 테스트 다이어그램들 (필요시 .gitignore)

## ✅ 유지할 파일들

### 핵심 테스트 파일
- `test_bedrock_image_generation.py` - Bedrock 이미지 생성 테스트
- `test_bedrock_minio_integration.py` - Bedrock + MinIO 통합 테스트
- `tests/integration/` - 통합 테스트 디렉토리

### 문서 파일
- `TASK_1_IMPLEMENTATION_SUMMARY.md` - Task 1 구현 요약
- `TASK_2_IMPLEMENTATION_SUMMARY.md` - Task 2 구현 요약
- `TASK_3_IMPLEMENTATION_SUMMARY.md` - Task 3 구현 요약
- `TASK_4_IMPLEMENTATION_SUMMARY.md` - Task 4 구현 요약
- `BEDROCK_MINIO_INTEGRATION_TEST_RESULTS.md` - 통합 테스트 결과
- `README.md` - 프로젝트 README

## 🔄 통합/리팩토링 필요 항목

### 1. 테스트 파일 통합
현재 유지할 테스트:
- `tests/integration/test_bedrock_integration.py` - Bedrock API 테스트
- `tests/integration/test_workflow.py` - 워크플로 테스트
- `tests/integration/test_models.py` - 모델 테스트
- `test_bedrock_minio_integration.py` - Bedrock + MinIO 통합

### 2. 문서 통합
- TASK 구현 요약들을 하나의 IMPLEMENTATION_SUMMARY.md로 통합 고려
