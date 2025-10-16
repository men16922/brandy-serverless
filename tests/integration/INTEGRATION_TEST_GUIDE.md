# Integration Test Guide
## 로컬 및 AWS Dev 환경 통합 테스트

이 가이드는 AI 브랜딩 챗봇의 통합 테스트를 로컬 환경과 AWS Dev 환경에서 실행하는 방법을 설명합니다.

---

## 📋 목차

1. [테스트 개요](#테스트-개요)
2. [로컬 환경 테스트](#로컬-환경-테스트)
3. [AWS Dev 환경 테스트](#aws-dev-환경-테스트)
4. [테스트 실행 방법](#테스트-실행-방법)
5. [문제 해결](#문제-해결)

---

## 테스트 개요

### 테스트 파일
- **메인 테스트**: `tests/integration/test_hackathon_workflow.py`
- **테스트 러너 (Bash)**: `scripts/run-integration-tests.sh`
- **테스트 러너 (Python)**: `scripts/run_integration_tests.py`

### 테스트 클래스 (6개)

| 테스트 클래스 | 설명 | 요구사항 |
|------------|------|---------|
| `TestFullWorkflowWithBedrock` | 전체 5단계 워크플로 | 10.4, 10.7 |
| `TestAutonomousExecution` | 자율 실행 테스트 | 4.1 |
| `TestFallbackMechanism` | Fallback 메커니즘 | 1.6, 5.6 |
| `TestPDFReportGeneration` | PDF 보고서 생성 | 1.5, 5.5 |
| `TestConcurrentSessions` | 동시 세션 처리 | 9.4 |
| `TestWorkflowStateManagement` | 워크플로 상태 관리 | 4.4 |

---

## 로컬 환경 테스트

### 사전 요구사항

1. **Docker 설치 및 실행**
   ```bash
   docker --version
   docker info
   ```

2. **Python 가상환경**
   ```bash
   source venv/bin/activate
   ```

3. **Docker Compose 서비스**
   - DynamoDB Local (포트 8000)
   - MinIO (포트 9000, 9001)
   - Chroma (포트 8001)
   - DynamoDB Admin UI (포트 8002)

### 로컬 테스트 실행

#### 방법 1: Python 스크립트 사용 (권장)

```bash
# 모든 로컬 테스트 실행
./venv/bin/python scripts/run_integration_tests.py local

# 사용 가능한 테스트 목록 보기
./venv/bin/python scripts/run_integration_tests.py list

# 특정 테스트만 실행
./venv/bin/python scripts/run_integration_tests.py specific TestFullWorkflowWithBedrock
```

#### 방법 2: Bash 스크립트 사용

```bash
# 모든 로컬 테스트 실행
./scripts/run-integration-tests.sh local

# 도움말 보기
./scripts/run-integration-tests.sh help
```

#### 방법 3: 직접 pytest 실행

```bash
# Docker 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 환경 변수 설정
export ENVIRONMENT=local
export DYNAMODB_ENDPOINT=http://localhost:8000
export S3_ENDPOINT=http://localhost:9000
export SESSIONS_TABLE=branding-chatbot-sessions-test

# 테스트 실행
./venv/bin/python -m pytest tests/integration/test_hackathon_workflow.py -v
```

### 로컬 테스트 결과 확인

테스트 실행 후 다음 URL에서 데이터를 확인할 수 있습니다:

- **DynamoDB Admin UI**: http://localhost:8002
  - 세션 데이터 확인
  - Agent 로그 검증
  
- **MinIO Console**: http://localhost:9001
  - 사용자명: `minioadmin`
  - 비밀번호: `minioadmin`
  - PDF 보고서 확인
  
- **Chroma API**: http://localhost:8001
  - 벡터 데이터베이스 상태 확인

### 로컬 환경 정리

```bash
# Docker 서비스 중지 및 데이터 삭제
docker-compose -f docker-compose.local.yml down -v

# 또는 서비스만 중지 (데이터 유지)
docker-compose -f docker-compose.local.yml down
```

---

## AWS Dev 환경 테스트

### 사전 요구사항

1. **AWS 자격 증명 설정**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

2. **SAM 스택 배포 확인**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name branding-chatbot \
     --region us-east-1
   ```

3. **AWS 리소스 확인**
   - DynamoDB 테이블: `ai-branding-chatbot-sessions`
   - S3 버킷: `ai-branding-chatbot-assets`
   - Bedrock 모델 접근 권한

### AWS Dev 테스트 실행

#### 방법 1: Python 스크립트 사용 (권장)

```bash
# AWS Dev 환경 테스트 실행
./venv/bin/python scripts/run_integration_tests.py dev
```

#### 방법 2: Bash 스크립트 사용

```bash
# AWS Dev 환경 테스트 실행
./scripts/run-integration-tests.sh dev
```

### AWS Dev 테스트 특징

- **실제 Bedrock API 사용**: Claude 4 Sonnet, SDXL
- **실제 DynamoDB 테이블**: 프로덕션 스키마
- **실제 S3 버킷**: 파일 저장 및 검색
- **Fallback 비활성화**: Bedrock만 사용 (`ENABLE_FALLBACK=false`)

### AWS Dev 환경 리소스 확인

```bash
# DynamoDB 테이블 확인
aws dynamodb describe-table \
  --table-name ai-branding-chatbot-sessions \
  --region us-east-1

# S3 버킷 확인
aws s3 ls s3://ai-branding-chatbot-assets/ --recursive

# Bedrock 모델 목록
aws bedrock list-foundation-models --region us-east-1
```

---

## 테스트 실행 방법

### 전체 테스트 실행

```bash
# 로컬 환경
./venv/bin/python scripts/run_integration_tests.py local

# AWS Dev 환경
./venv/bin/python scripts/run_integration_tests.py dev
```

### 개별 테스트 실행

```bash
# 특정 테스트 클래스 실행
./venv/bin/python scripts/run_integration_tests.py specific TestFullWorkflowWithBedrock

# 특정 테스트 메서드 실행
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py::TestFullWorkflowWithBedrock::test_full_workflow_with_bedrock \
  -v -s
```

### 상세 출력으로 실행

```bash
# 상세 로그 출력
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  -v -s --tb=long
```

### 특정 마커로 실행

```bash
# 로컬 전용 테스트만 실행
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  -m "local_only"

# 느린 테스트 제외
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  -m "not slow"
```

---

## 문제 해결

### Docker 서비스 문제

#### 문제: Docker 서비스가 시작되지 않음

```bash
# Docker 상태 확인
docker info

# Docker 재시작 (macOS)
killall Docker && open /Applications/Docker.app

# 서비스 로그 확인
docker-compose -f docker-compose.local.yml logs
```

#### 문제: 포트 충돌

```bash
# 포트 사용 확인
lsof -i :8000,8001,8002,9000,9001

# 충돌하는 프로세스 종료
sudo lsof -ti:8000 | xargs kill -9

# 서비스 재시작
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

### 테스트 실패 문제

#### 문제: DynamoDB 연결 실패

```bash
# DynamoDB Local 상태 확인
curl http://localhost:8000

# 서비스 재시작
docker-compose -f docker-compose.local.yml restart dynamodb-local

# 테이블 목록 확인
aws dynamodb list-tables \
  --endpoint-url http://localhost:8000 \
  --region us-east-1
```

#### 문제: MinIO 연결 실패

```bash
# MinIO 상태 확인
curl http://localhost:9000/minio/health/live

# MinIO 콘솔 접속
open http://localhost:9001

# 서비스 재시작
docker-compose -f docker-compose.local.yml restart minio
```

#### 문제: 테스트 데이터 정리 안됨

```bash
# 모든 Docker 볼륨 삭제
docker-compose -f docker-compose.local.yml down -v

# 특정 볼륨만 삭제
docker volume rm brandy-serverless_minio_data
docker volume rm brandy-serverless_chroma_data
```

### AWS Dev 환경 문제

#### 문제: AWS 자격 증명 오류

```bash
# AWS 자격 증명 확인
aws sts get-caller-identity

# 자격 증명 재설정
aws configure

# 환경 변수로 설정
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

#### 문제: Bedrock 접근 권한 없음

```bash
# Bedrock 모델 목록 확인
aws bedrock list-foundation-models --region us-east-1

# IAM 권한 확인
aws iam get-user

# 필요한 권한:
# - bedrock:InvokeModel
# - bedrock:ListFoundationModels
# - bedrock-agent-runtime:Retrieve
```

#### 문제: SAM 스택 배포 안됨

```bash
# 스택 상태 확인
aws cloudformation describe-stacks \
  --stack-name branding-chatbot \
  --region us-east-1

# 스택 재배포
sam build
sam deploy --guided
```

### 성능 문제

#### 문제: 테스트 실행이 너무 느림

```bash
# 병렬 실행 (주의: 리소스 경합 가능)
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  -n auto

# 느린 테스트 제외
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  -m "not slow"

# 특정 테스트만 실행
./venv/bin/python scripts/run_integration_tests.py specific TestFullWorkflowWithBedrock
```

---

## 테스트 결과 예시

### 성공적인 로컬 테스트

```
============================================================
Running LOCAL Integration Tests
============================================================

✓ Docker is available
✓ DynamoDB Local is running (port 8000)
✓ MinIO is running (port 9000)
✓ Chroma is running (port 8001)
✓ DynamoDB Admin UI is running (port 8002)

✓ All Docker services are healthy

✓ Local environment configured

======================== 6 passed in 7.96s ========================

✓ All local tests passed!

Verification URLs:
  • DynamoDB Admin: http://localhost:8002
  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
  • Chroma API: http://localhost:8001
```

### 성공적인 AWS Dev 테스트

```
============================================================
Running AWS DEV Integration Tests
============================================================

✓ AWS credentials found
✓ SAM stack 'branding-chatbot' is deployed
✓ API Gateway URL: https://xxx.execute-api.us-east-1.amazonaws.com/dev

======================== 6 passed in 45.23s ========================

✓ All AWS dev tests passed!

AWS Resources:
  • DynamoDB Table: ai-branding-chatbot-sessions
  • S3 Bucket: ai-branding-chatbot-assets
  • Region: us-east-1
```

---

## 추가 리소스

### 관련 문서
- [HACKATHON_WORKFLOW_TEST_SUMMARY.md](./HACKATHON_WORKFLOW_TEST_SUMMARY.md) - 테스트 상세 설명
- [RUN_HACKATHON_TESTS.md](./RUN_HACKATHON_TESTS.md) - 빠른 참조 가이드
- [../README.md](../../README.md) - 프로젝트 전체 문서

### 유용한 명령어

```bash
# 테스트 커버리지 확인
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  --cov=src/lambda/shared \
  --cov-report=html

# 테스트 실행 시간 측정
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  --durations=10

# 실패한 테스트만 재실행
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  --lf

# 디버그 모드로 실행
./venv/bin/python -m pytest \
  tests/integration/test_hackathon_workflow.py \
  --pdb
```

---

## 요약

### 로컬 테스트 (빠른 시작)
```bash
# 1. Docker 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 2. 테스트 실행
./venv/bin/python scripts/run_integration_tests.py local

# 3. 결과 확인
open http://localhost:8002  # DynamoDB Admin
```

### AWS Dev 테스트 (빠른 시작)
```bash
# 1. AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 2. 테스트 실행
./venv/bin/python scripts/run_integration_tests.py dev

# 3. AWS 콘솔에서 결과 확인
```

---

**마지막 업데이트**: 2025년 10월 16일  
**테스트 상태**: ✅ 모든 테스트 통과  
**총 테스트**: 6개 클래스, 6개 메서드  
**실행 시간**: ~8초 (로컬), ~45초 (AWS Dev)
