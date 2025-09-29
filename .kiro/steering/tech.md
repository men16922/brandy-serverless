# Technology Stack & Build System

## Core Technologies

### Backend Infrastructure
- **AWS SAM (Serverless Application Model)** - Infrastructure as Code (template.yaml)
- **AWS Lambda** - Serverless compute with Python 3.11
- **API Gateway HTTP API** - REST endpoints (cost-optimized vs REST API)
- **Step Functions** - Workflow orchestration (Express + Standard)
- **DynamoDB** - Session storage with TTL
- **S3** - Image and report storage

### Frontend
- **Streamlit** - Web interface deployed on AWS App Runner
- **Pause/Resume capability** for cost optimization

### AI & ML
- **Production**: AWS Bedrock (SDXL, Knowledge Base)
- **Development**: OpenAI DALL-E, Google Gemini, Chroma vector DB
- **Local**: Chroma for vector storage

### Development Environment
- **Docker Compose** - Local services (DynamoDB Local + Admin UI, MinIO, Chroma)
- **SAM CLI** - Local API Gateway + Lambda testing (sam local start-api)
- **Python 3.11+** - Runtime and development
- **pytest** - Integration testing framework (통합 테스트만 사용)
- **black, flake8, isort** - Code formatting and linting

## Environment Configuration

### Local Development
```bash
# Services: DynamoDB Local (8000), DynamoDB Admin (8002), MinIO (9000/9001), Chroma (8001)
./scripts/setup-local.sh        # Initial setup
docker-compose -f docker-compose.local.yml up -d    # Start services
sam build && sam local start-api --port 3000        # Local API Gateway + Lambda
cd src/streamlit && streamlit run app.py            # Run Streamlit app
```

### SAM Deployment
```bash
sam build                       # Build SAM application
sam deploy --guided             # Interactive deployment setup
sam deploy                      # Deploy to configured environment
sam logs --stack-name branding-chatbot --tail  # Real-time logs
```

### Essential Commands
```bash
# 환경 설정
python3 -m venv venv                    # 가상환경 생성
source venv/bin/activate                # 가상환경 활성화
pip install -r requirements.txt        # 의존성 설치

# SAM 개발 워크플로
sam build                               # SAM 애플리케이션 빌드
sam local start-api --port 3000         # 로컬 API Gateway + Lambda
sam deploy --guided                     # 대화형 AWS 배포
sam logs --stack-name branding-chatbot --tail  # 실시간 로그

# 통합 테스트 (Docker Compose 기반)
./scripts/setup-local.sh               # 로컬 환경 설정
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
python -m pytest tests/integration/    # 통합 테스트 실행
cd src/streamlit && streamlit run app.py  # 앱 실행

# Docker 서비스 관리
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
docker-compose -f docker-compose.local.yml down -v  # 서비스 중지 + 볼륨 삭제

# 로컬 서비스 접근
# DynamoDB Admin UI: http://localhost:8002
# MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
# Chroma API: http://localhost:8001
```

## Architecture Patterns

### Agent-Based Design
- **BaseAgent** class for all agents with common functionality
- **Agent Communication** interface for inter-agent messaging
- **Structured logging** with agent, tool, latency_ms, session_id
- **Environment abstraction** for local/dev/prod configurations

### Error Handling
- **Graceful degradation** with fallback results
- **Automatic retries** via Step Functions
- **Dead Letter Queues** for failed messages
- **Supervisor monitoring** of all agent executions

### Performance Requirements
- Text responses: ≤ 5 seconds
- Image generation: ≤ 30 seconds
- Full workflow: ≤ 5 minutes
- Session TTL: 24 hours

## Dependencies

### Core Python Packages
- `boto3` - AWS SDK
- `aws-sam-cli` - SAM CLI for local development and deployment
- `pydantic` - Data validation
- `streamlit` - Web interface
- `structlog` - Structured logging

### AI/ML Packages
- `openai` - DALL-E integration
- `google-generativeai` - Gemini integration
- `chromadb` - Vector database (local)

### Development Tools
- `pytest` - Testing (통합 테스트만 사용)
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

## 테스트 정책

**Docker Compose 기반 통합 테스트만 사용합니다:**
- 단위 테스트는 복잡성만 증가시키므로 사용하지 않음
- Docker Compose로 실제 환경 시뮬레이션하여 end-to-end 테스트
- `tests/integration/` - Docker 기반 워크플로 전체 테스트
- DynamoDB Admin UI (http://localhost:8002)로 데이터 시각적 검증
- MinIO Console (http://localhost:9001)로 파일 업로드/다운로드 확인
- pytest fixture로 Docker 서비스 라이프사이클 자동 관리