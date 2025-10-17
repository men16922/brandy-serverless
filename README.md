# AI 브랜딩 챗봇 🤖

업종, 지역, 규모만 입력하면 AI가 **상호명, 간판 디자인, 인테리어, PDF 보고서**를 자동으로 만들어주는 서버리스 시스템입니다.

## 🎯 무엇을 하는 프로젝트인가요?

```
입력: "서울 강남에서 소규모 카페 운영 예정"
↓
AI가 자동 생성:
✅ 상호명 3개 후보 (발음/검색 점수 포함)
✅ 간판 디자인 3개 (DALL-E, SDXL, Gemini)
✅ 인테리어 추천 3개 (간판 스타일 맞춤)
✅ 종합 브랜딩 PDF 보고서
```

## 🏗️ 시스템 구조

### 6개 AI 에이전트가 순서대로 작업
1. **Supervisor** - 전체 작업 관리
2. **Product Insight** - 비즈니스 분석  
3. **Market Analyst** - 시장 동향 분석
4. **Reporter** - 상호명 생성
5. **Signboard** - 간판 디자인 (3개 AI 동시 사용)
6. **Interior** - 인테리어 추천

### 기술 스택
- **AWS SAM** - 서버리스 배포
- **Lambda + API Gateway** - 백엔드
- **DynamoDB + S3** - 데이터 저장
- **Step Functions** - 워크플로 관리

## 🚀 5분 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론 & 가상환경 생성
git clone <repository>
cd brandy-serverless
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. AWS 배포
```bash
# AWS 자격증명 설정
aws configure

# OpenAI API 키를 Secrets Manager에 저장
aws secretsmanager create-secret \
    --name openai-api-key \
    --secret-string '{"api_key":"sk-your-key-here"}' \
    --region us-east-1

# AWS dev 환경 배포 (5-10분 소요)
./deploy_to_dev.sh
```

### 3. Streamlit 앱 실행
```bash
# Streamlit 시작
streamlit run src/streamlit/app.py

# 브라우저 자동 오픈: http://localhost:8501
```

### 4. 확인
- **웹 앱**: http://localhost:8501 (Streamlit UI)
- **AWS Console**: CloudFormation, Lambda, DynamoDB, S3
- **로그 확인**: `sam logs --stack-name ai-branding-chatbot-dev --tail`

## 🎨 웹 앱 사용법

### 1. 서버 시작 (2개 터미널 필요)
```bash
# 터미널 1: API 서버
./scripts/dev.sh api

# 터미널 2: Streamlit 앱  
./scripts/dev.sh app
```

### 2. 브라우저에서 접속
- **웹 앱**: http://localhost:8501
- 업종/지역/규모 선택 → 분석 시작 → 5단계 자동 진행

### 3. 문제 해결

#### API 연결 오류 (`HTTPConnectionPool timeout`)
```bash
# 1. 환경 점검
./scripts/dev.sh validate

# 2. API 서버 상태 확인
curl http://localhost:3000/

# 3. API 서버 재시작 (코드 변경 후 필수)
./scripts/dev.sh api

# 4. 전체 환경 재설정
./scripts/dev.sh setup

# 5. API 연결 테스트
python test_streamlit_api_connection.py
```

#### 세션 생성 오류 (`Session ID is required`)
```bash
# SAM Local 재시작 (코드 변경사항 반영)
# 터미널에서 Ctrl+C로 중지 후 다시 시작
./scripts/dev.sh api
```

#### 의존성 오류
```bash
# 개발환경 재설정
./scripts/activate-dev.sh

# 수동 설치
source venv/bin/activate
pip install -r src/streamlit/requirements.txt
```

#### 포트 충돌
```bash
# 포트 사용 확인
lsof -i :3000,8501,8000,9000

# 프로세스 종료 후 재시작
./scripts/dev.sh cleanup
./scripts/dev.sh setup
```

## 🧪 테스트 (실제 DB 사용)

```bash
./scripts/dev.sh test      # 통합 테스트 실행 (Bedrock 검증 포함)
./scripts/dev.sh validate  # 환경 및 Bedrock 검증
```

**특징**: Mock 사용 안함. 실제 DynamoDB, MinIO, Chroma 사용하여 신뢰할 수 있는 테스트

### Bedrock 로컬 테스트

AWS Bedrock을 로컬에서 테스트하려면:

```bash
# 1. AWS 자격증명 설정
aws configure
# 또는 환경 변수 설정
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# 2. Bedrock 설정 검증
./scripts/verify-bedrock-setup.sh

# 3. 환경 변수 설정 (.env 파일)
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
ENABLE_FALLBACK=true  # 로컬 개발 시 true, 제출 시 false

# 4. Bedrock 통합 테스트 실행
python -m pytest tests/integration/test_bedrock_integration.py -v
```

**참고**: AWS 자격증명 없이도 로컬 개발 가능 (Fallback 모드)

## 🛠️ 개발 명령어

### 통합 개발 스크립트 (권장)
```bash
./scripts/dev.sh setup     # 로컬 환경 설정
./scripts/dev.sh validate  # 환경 검증
./scripts/dev.sh test      # 통합 테스트 실행
./scripts/dev.sh build     # SAM 애플리케이션 빌드
./scripts/dev.sh api       # 로컬 API 서버 시작
./scripts/dev.sh app       # Streamlit 앱 시작
./scripts/dev.sh cleanup   # 환경 정리
./scripts/dev.sh help      # 도움말
```

### 개별 스크립트
```bash
# 환경 관리
./scripts/activate-dev.sh               # 개발환경 활성화
./scripts/setup-local.sh                # Docker 서비스 시작
python scripts/validate-environment.py  # 환경 전체 검증

# SAM 개발 워크플로
./scripts/sam-build.sh                  # SAM 애플리케이션 빌드
./scripts/sam-local.sh                  # 로컬 API Gateway + Lambda
./scripts/sam-deploy.sh dev             # AWS 개발 환경 배포
sam logs --stack-name ai-branding-chatbot-dev --tail  # 실시간 로그

# Docker 서비스 관리
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
docker-compose -f docker-compose.local.yml down -v  # 서비스 중지 + 볼륨 삭제
```

### 로컬 서비스 접근
- **DynamoDB Admin UI**: http://localhost:8002 (테이블 관리)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Chroma API**: http://localhost:8001 (벡터 DB)

## ⚙️ 환경 변수 설정

### 필수 환경 변수 (.env 파일)

```bash
# OpenAI API (로컬 개발용 - Fallback)
OPENAI_API_KEY=sk-...

# AWS Bedrock 설정 (프로덕션)
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1

# Bedrock AgentCore (선택사항)
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-agent-alias-id
BEDROCK_KB_ID=your-knowledge-base-id

# Fallback 설정
ENABLE_FALLBACK=true   # 로컬 개발: true, 해커톤 제출: false
DEV_PROFILE=true       # 로컬 개발: true, 프로덕션: false
ENVIRONMENT=local      # local/dev/prod

# AWS 자격증명 (Bedrock 사용 시)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

### 환경별 설정

**로컬 개발 (.env.local)**
```bash
ENABLE_FALLBACK=true
DEV_PROFILE=true
ENVIRONMENT=local
# OpenAI API 키만 필요 (Bedrock 선택사항)
```

**해커톤 제출 (.env.prod)**
```bash
ENABLE_FALLBACK=false  # Bedrock Only!
DEV_PROFILE=false
ENVIRONMENT=prod
BEDROCK_REGION=us-east-1
# AWS 자격증명 필수
```

### 환경 변수 검증

```bash
# 전체 환경 검증
./scripts/dev.sh validate

# Bedrock 설정만 검증
./scripts/verify-bedrock-setup.sh
```

## 📁 프로젝트 구조

```
├── template.yaml                      # SAM 템플릿 (모든 AWS 리소스)
├── samconfig.toml                     # SAM 배포 설정
├── src/lambda/agents/                 # Agent Lambda 함수들
│   ├── supervisor/                    # 워크플로 감시 & 제어
│   ├── product-insight/               # 비즈니스 분석
│   ├── market-analyst/                # 시장 동향 분석
│   ├── reporter/                      # 상호명 제안
│   ├── signboard/                     # 간판 디자인 생성
│   ├── interior/                      # 인테리어 추천
│   └── report-generator/              # PDF 보고서 생성
├── src/lambda/shared/                 # 공통 유틸리티 (Lambda Layer)
├── statemachine/                      # Step Functions 정의
├── scripts/                           # SAM 빌드/배포 스크립트
│   ├── dev.sh                         # 통합 개발 스크립트
│   ├── verify-bedrock-setup.sh        # Bedrock 검증 스크립트
│   └── validate-environment.py        # 환경 검증 스크립트
├── tests/integration/                 # Docker 기반 통합 테스트
└── docker-compose.local.yml           # 로컬 개발 서비스
```

## 📚 추가 문서

- **빠른 시작**: `QUICK_START.md` - 5분 빠른 시작 가이드
- **AWS 배포**: `DEPLOY_TO_AWS_DEV.md` - AWS dev 환경 배포 상세 가이드
- **프로젝트 정리**: `PROJECT_CLEANUP_SUMMARY.md` - 정리 내역 및 구조

## 🗑️ 환경 정리

```bash
# CloudFormation 스택 삭제
aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev

# S3 버킷 비우기
aws s3 rm s3://ai-branding-chatbot-assets-dev/ --recursive
```

## 라이선스

MIT License