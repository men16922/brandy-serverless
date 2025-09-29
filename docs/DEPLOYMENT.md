# 배포 가이드

AI 브랜딩 챗봇의 환경별 배포 및 실행 가이드입니다.

## 🏗️ 환경 구성

### Local 환경 (로컬 개발)
- **목적**: 로컬 개발 및 테스트
- **인프라**: Docker Compose (DynamoDB Local, MinIO, Chroma)
- **설정**: `samconfig.toml` local 환경
- **특징**: 
  - AWS 계정 불필요
  - 실제 AWS 서비스 대신 로컬 에뮬레이터 사용
  - DynamoDB Admin UI로 데이터 시각화
  - NO MOCKS 정책 - 실제 서비스 사용

### Dev 환경 (AWS 개발)
- **목적**: AWS 클라우드 개발 및 통합 테스트
- **인프라**: 실제 AWS 서비스 (DynamoDB, S3, Lambda, API Gateway)
- **설정**: `samconfig.toml` dev 환경
- **특징**:
  - AWS 계정 및 자격증명 필요
  - 실제 AWS 서비스 사용
  - Bedrock, OpenAI, Google API 연동

## 🚀 배포 명령어

### 로컬 개발 환경 시작

```bash
# 통합 개발 스크립트 사용 (권장)
./scripts/dev.sh setup    # 환경 설정
./scripts/dev.sh api      # API 서버 시작

# 또는 개별 스크립트 사용
./scripts/setup-local.sh  # Docker 서비스 시작
./scripts/sam-local.sh    # SAM Local API 시작
```

**접속 URL:**
- API Gateway: http://localhost:3000
- DynamoDB Admin: http://localhost:8002
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### AWS Dev 환경 배포

```bash
# 1. AWS 자격증명 설정 (최초 1회)
aws configure

# 2. Dev 환경에 배포
./scripts/sam-deploy.sh dev
```

### 빌드만 실행

```bash
# SAM 애플리케이션 빌드
./scripts/sam-build.sh
```

## 📁 설정 파일 구조

### samconfig.toml
모든 환경 설정이 `samconfig.toml` 파일에 통합되어 있습니다:

```toml
# Local 환경 설정
[local.local_start_api.parameters]
env_vars = """
ENVIRONMENT=local
DYNAMODB_ENDPOINT=http://host.docker.internal:8000
S3_ENDPOINT=http://host.docker.internal:9000
CHROMA_ENDPOINT=http://host.docker.internal:8001
LOG_LEVEL=DEBUG
"""

# Dev 환경 설정
[dev.deploy.parameters]
parameter_overrides = "Environment=dev ProjectName=ai-branding-chatbot"
```

## 🔧 환경별 차이점

| 항목 | Local | Dev |
|------|-------|-----|
| DynamoDB | DynamoDB Local (Docker) | AWS DynamoDB |
| S3 | MinIO (Docker) | AWS S3 |
| Vector DB | Chroma (Docker) | AWS Bedrock Knowledge Base |
| API Gateway | SAM Local | AWS API Gateway |
| Lambda | SAM Local (Docker) | AWS Lambda |
| 비용 | 무료 | AWS 사용량 기반 |
| 인터넷 | 불필요 | 필요 |
| AWS 계정 | 불필요 | 필요 |

## 🛠️ 개발 워크플로

### 1. 로컬 개발
```bash
# 로컬 환경 시작
./scripts/sam-local.sh

# 코드 수정 후 재빌드
./scripts/sam-build.sh

# 로컬 테스트
curl -X POST http://localhost:3000/sessions \
  -H "Content-Type: application/json" \
  -d '{"businessInfo": {"industry": "카페", "region": "강남", "size": "소규모"}}'
```

### 2. AWS 배포
```bash
# Dev 환경에 배포
./scripts/sam-deploy.sh dev

# 배포된 API 테스트
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/sessions \
  -H "Content-Type: application/json" \
  -d '{"businessInfo": {"industry": "카페", "region": "강남", "size": "소규모"}}'
```

## 🔍 디버깅 및 모니터링

### 로컬 환경
- **DynamoDB**: http://localhost:8002에서 테이블 및 데이터 확인
- **파일 저장소**: http://localhost:9001에서 업로드된 파일 확인
- **로그**: 터미널에서 실시간 확인

### Dev 환경
```bash
# CloudWatch 로그 실시간 확인
sam logs --stack-name ai-branding-chatbot-dev --tail

# 특정 함수 로그만 확인
sam logs --stack-name ai-branding-chatbot-dev --name SupervisorAgent --tail
```

## 🚨 주의사항

### 로컬 환경
- Docker가 실행 중이어야 함
- 포트 8000, 8001, 8002, 9000, 9001이 사용 가능해야 함
- `.aws-sam` 폴더는 Git에 커밋하지 않음

### Dev 환경
- AWS 자격증명이 올바르게 설정되어야 함
- AWS 리소스 사용에 따른 비용 발생
- API 키는 AWS Secrets Manager에 저장 권장

## 🧹 정리

### 로컬 환경 정리
```bash
# Docker 서비스 중지 및 정리
docker-compose -f docker-compose.local.yml down -v

# SAM 빌드 아티팩트 정리
rm -rf .aws-sam/
```

### Dev 환경 정리
```bash
# AWS 스택 삭제
sam delete --stack-name ai-branding-chatbot-dev
```