# Technology Stack & Build System

## Core Technologies

### Backend Infrastructure
- **AWS CDK** - Infrastructure as Code (Python)
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
- **Docker Compose** - Local services (DynamoDB Local, MinIO, Chroma)
- **Python 3.11+** - Runtime and development
- **pytest** - Testing framework
- **black, flake8, isort** - Code formatting and linting

## Environment Configuration

### Local Development
```bash
# Services: DynamoDB Local (8000), MinIO (9000/9001), Chroma (8001)
./scripts/setup-local.sh        # Initial setup
docker-compose -f docker-compose.local.yml up -d    # Start services
cd src/streamlit && streamlit run app.py            # Run Streamlit app
```

### Development Deployment
```bash
./scripts/deploy-dev.sh         # Deploy to AWS dev environment
```

### Essential Commands
```bash
# 환경 설정
python3 -m venv venv                    # 가상환경 생성
source venv/bin/activate                # 가상환경 활성화
pip install -r requirements.txt        # 의존성 설치

# 개발 워크플로
./scripts/setup-local.sh               # 로컬 환경 설정
./scripts/deploy-dev.sh                # AWS 배포
python -m pytest tests/                # 통합 테스트 실행
cd src/streamlit && streamlit run app.py  # 앱 실행

# Docker 서비스
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
docker-compose -f docker-compose.local.yml down     # 서비스 중지
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
- `aws-cdk-lib` - CDK constructs
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

**통합 테스트만 사용합니다:**
- 단위 테스트는 복잡성만 증가시키므로 사용하지 않음
- 전체 워크플로를 테스트하는 통합 테스트로 충분
- `tests/test_integration.py` - 워크플로 전체 테스트
- `tests/test_models.py` - 데이터 모델 검증