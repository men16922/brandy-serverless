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

### AI & ML (Hackathon Compliant)
- **Primary (Production)**: 
  - Amazon Bedrock Claude 4 Sonnet (`us.anthropic.claude-sonnet-4-20250514-v1:0`) - Text generation and reasoning
  - Amazon Bedrock Titan Image Generator v2 (`amazon.titan-image-generator-v2:0`) - Image generation
  - Reasoning Engine - Chain-of-Thought for autonomous decision-making
- **Development Tools**:
  - BedrockClient - Shared module for all Bedrock API calls
  - ReasoningEngine - Shared module for autonomous decisions

### Development Environment
- **AWS-Only Architecture** - Streamlit runs locally, all backend uses AWS directly
- **SAM CLI** - Build and deploy serverless applications
- **Python 3.11+** - Runtime and development
- **pytest** - Integration testing framework
- **diagrams** - Python library for generating architecture diagrams
- **black, flake8, isort** - Code formatting and linting

## Environment Configuration

### Local Development
```bash
# Streamlit runs locally, connects to AWS services
source venv/bin/activate                # Activate virtual environment
streamlit run src/streamlit/app.py      # Run Streamlit UI (localhost:8501)

# All backend services use AWS directly:
# - API Gateway: https://xxx.execute-api.us-west-2.amazonaws.com/dev
# - Lambda: 7 agent functions
# - DynamoDB: ai-branding-chatbot-sessions
# - S3: ai-branding-chatbot-assets-xxx
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
pip install -r requirements.txt         # 의존성 설치

# SAM 개발 워크플로
sam build                               # SAM 애플리케이션 빌드
sam deploy --guided                     # 대화형 AWS 배포 (첫 배포)
sam deploy --config-env dev             # 이후 배포
sam logs --stack-name ai-branding-chatbot-dev --tail  # 실시간 로그

# Streamlit 실행
streamlit run src/streamlit/app.py      # 웹 UI 실행 (localhost:8501)

# 통합 테스트 (AWS 환경)
python -m pytest tests/integration/ -v  # AWS dev 환경 테스트

# 아키텍처 다이어그램 생성
python3 -m venv venv-diagram
source venv-diagram/bin/activate
pip install diagrams graphviz
python3 scripts/generate_architecture_diagram.py

# AWS 리소스 모니터링
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev --follow
aws dynamodb scan --table-name ai-branding-chatbot-sessions --max-items 5
aws s3 ls s3://ai-branding-chatbot-assets-xxx/ --recursive
```

## Architecture Patterns

### Agent-Based Design (Hackathon Compliant)
- **BaseAgent** class for all agents with common functionality
- **Bedrock Integration**: BedrockClient module for all Bedrock API calls
- **AgentCore Orchestrator**: Supervisor Agent uses Bedrock AgentCore
- **Reasoning Engine**: Claude 4 Sonnet for autonomous decision-making
- **Agent Communication** interface for inter-agent messaging
- **Structured logging** with agent, tool, latency_ms, session_id, reasoning_chain
- **Environment abstraction** for local/dev/prod configurations

### Bedrock Integration Strategy
- **Primary**: Bedrock Claude 4 Sonnet + Titan Image Generator v2 for all workloads
- **Bedrock-Only Mode**: `ENABLE_FALLBACK=false` for hackathon compliance
- **Reasoning Chain**: Store all LLM decision-making steps in DynamoDB
- **Shared Modules**: BedrockClient and ReasoningEngine in src/lambda/shared/

### Error Handling
- **Autonomous Error Recovery** - Supervisor Agent uses Reasoning LLM for intelligent recovery
- **Automatic retries** with exponential backoff
- **Supervisor monitoring** of all agent executions
- **Bedrock-specific errors**: ThrottlingException, ValidationException handling
- **CloudWatch logging** for debugging and monitoring

### Performance Requirements
- Text responses: ≤ 5 seconds (Bedrock Claude)
- Image generation: ≤ 30 seconds (Bedrock Titan Image Generator v2)
- Full workflow: ≤ 5 minutes
- Session TTL: 24 hours
- Bedrock API latency: P95 < 3 seconds
- Cost per workflow: ~$0.20

## Dependencies

### Core Python Packages
- `boto3` - AWS SDK (Bedrock, DynamoDB, S3)
- `aws-sam-cli` - SAM CLI for local development and deployment
- `pydantic` - Data validation
- `streamlit` - Web interface
- `structlog` - Structured logging

### AI/ML Packages (Hackathon Compliant)
- **Primary**:
  - `boto3` with `bedrock-runtime` - Bedrock Claude 4 Sonnet, Titan Image Generator v2
  - BedrockClient module - Shared Bedrock API client
  - ReasoningEngine module - Autonomous decision-making with Chain-of-Thought

### Development Tools
- `pytest` - Integration testing with AWS dev environment
- `diagrams` - Architecture diagram generation
- `graphviz` - Diagram rendering
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

### Hackathon-Specific Dependencies
- Bedrock model IDs:
  - `us.anthropic.claude-sonnet-4-20250514-v1:0` (Claude 4 Sonnet - text and reasoning)
  - `amazon.titan-image-generator-v2:0` (Titan Image Generator v2 - image generation)
- Reasoning Engine: Chain-of-Thought prompting for autonomous decisions
- Architecture Diagrams: Python diagrams library for visual documentation

## 테스트 정책

**AWS Dev Environment 기반 통합 테스트:**
- 단위 테스트는 사용하지 않음 (복잡성 증가)
- AWS dev 환경에서 실제 서비스로 end-to-end 테스트
- `tests/integration/` - AWS 기반 워크플로 전체 테스트
- 실제 DynamoDB, S3, Lambda, Bedrock 사용
- AWS Console에서 데이터 시각적 검증
- pytest로 테스트 자동화

## 아키텍처 다이어그램 생성

**Python diagrams 라이브러리 사용:**
- `scripts/generate_architecture_diagram.py` - 다이어그램 생성 스크립트
- 3개 다이어그램 자동 생성:
  - AWS Infrastructure Architecture
  - 5-Step Workflow Sequence
  - Bedrock Integration Details
- PNG 형식으로 `docs/` 디렉토리에 저장
- README.md에 자동 임베드