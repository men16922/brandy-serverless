# Project Structure & Organization

## SAM 기반 프로젝트 구조

```
├── template.yaml                      # SAM 템플릿 (모든 AWS 리소스 정의)
├── samconfig.toml                     # SAM 배포 설정 (환경별)
├── docs/                              # 문서 및 다이어그램
│   ├── aws_architecture_diagram.png   # AWS 인프라 다이어그램
│   ├── workflow_sequence_diagram.png  # 5단계 워크플로 다이어그램
│   ├── bedrock_integration_diagram.png # Bedrock 통합 다이어그램
│   └── architecture-diagram.md        # Mermaid 다이어그램
├── src/
│   ├── lambda/
│   │   ├── agents/                    # Agent Lambda functions
│   │   │   ├── supervisor/            # Supervisor Agent
│   │   │   │   ├── index.py           # Session mgmt, error recovery, orchestration
│   │   │   │   └── requirements.txt   # Agent별 의존성
│   │   │   ├── product-insight/       # 비즈니스 분석 (Bedrock Claude)
│   │   │   ├── market-analyst/        # 시장 분석 (Bedrock Claude)
│   │   │   ├── reporter/              # 상호명 제안 (Reasoning LLM)
│   │   │   ├── signboard/             # 간판 생성 (Bedrock Titan Image Gen v2)
│   │   │   ├── interior/              # 인테리어 추천 (Bedrock Claude)
│   │   │   └── report-generator/      # HTML 보고서 (Bedrock Claude)
│   │   └── shared/                    # 공통 유틸리티 (Lambda Layer)
│   │       ├── base_agent.py          # BaseAgent 클래스
│   │       ├── bedrock_client.py      # Bedrock API 클라이언트
│   │       ├── reasoning_engine.py    # Reasoning LLM 엔진
│   │       ├── models.py              # 데이터 모델 + ReasoningStep
│   │       └── utils.py               # 공통 함수
│   └── streamlit/                     # 웹 인터페이스
│       └── app.py                     # Streamlit 앱 (localhost:8501)
├── scripts/                           # 개발/배포 스크립트
│   ├── generate_architecture_diagram.py  # 다이어그램 생성
│   └── requirements-diagram.txt       # 다이어그램 생성 의존성
├── tests/                             # AWS dev 환경 통합 테스트
│   └── integration/                   # 통합 테스트 디렉토리
│       ├── test_workflow.py           # 워크플로 통합 테스트
│       └── test_agents.py             # Agent 통신 테스트
└── .kiro/                             # Kiro IDE 설정
    └── steering/                      # 프로젝트 가이드라인
        ├── product.md                 # 제품 개요
        ├── tech.md                    # 기술 스택
        ├── structure.md               # 프로젝트 구조
        ├── hackathon.md               # 해커톤 요구사항
        ├── local-environment.md       # 로컬 환경 설정
        └── integration-testing.md     # 테스트 전략
```

**주요 특징:**
- **AWS SAM**: Infrastructure as Code로 완전 서버리스 배포
- **7개 Lambda Functions**: 6개 전문 Agent + 1개 Supervisor Agent
- **Supervisor Agent**: Session management, error recovery, orchestration
- **Bedrock Integration**: Claude 4 Sonnet, Titan Image Generator v2
- **Architecture Diagrams**: Python diagrams 라이브러리로 자동 생성
- **AWS-Only Architecture**: Streamlit만 로컬, 모든 백엔드는 AWS 직접 사용

**Hackathon 준수사항:**
- Bedrock 통합 모듈 (bedrock_client.py, reasoning_engine.py)
- Reasoning chain 저장 (DynamoDB)
- 자동 에러 복구 (Supervisor Agent)
- 시각적 아키텍처 문서화

## Code Organization Patterns

### Agent Structure
Each agent follows a consistent pattern:
```python
# agents/{agent-name}/index.py
from src.lambda.shared.base_agent import BaseAgent
from src.lambda.shared.models import AgentType

class SpecificAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentType.SPECIFIC)
    
    def execute(self, event, context):
        # Agent-specific logic
        pass

def lambda_handler(event, context):
    agent = SpecificAgent()
    return agent.lambda_handler(event, context)
```

### Shared Utilities Location
- **Base classes**: `src/lambda/shared/base_agent.py`
- **Bedrock integration**: `src/lambda/shared/bedrock_client.py`
- **Reasoning engine**: `src/lambda/shared/reasoning_engine.py`
- **Data models**: `src/lambda/shared/models.py` (+ ReasoningStep)
- **Common utils**: `src/lambda/shared/utils.py`

### Configuration Management
- Environment variables in `template.yaml`
- Agent configurations include timeouts, Bedrock model IDs, and feature flags
- All environments use AWS managed services
- `.env` file for Streamlit API endpoint configuration

### Infrastructure as Code
- **SAM template** (template.yaml) defines all AWS resources in one file
- **Environment parameters**: samconfig.toml for environment-specific settings
- **Resource naming**: `ai-branding-chatbot-{resource}-{environment}`
- **IAM permissions**: Least privilege with SAM-generated roles

### Architecture Documentation
- **Python diagrams**: `scripts/generate_architecture_diagram.py`
- **Generated diagrams**: `docs/*.png` (3 diagrams)
- **Mermaid diagrams**: `docs/architecture-diagram.md`
- **README integration**: Diagrams embedded in README.md
- **IAM permissions**: Least privilege with SAM-generated roles
- **Local testing**: sam local start-api for API Gateway + Lambda testing

## File Naming Conventions

### Lambda Functions
- Agent functions: `{agent-name}/index.py`
- Shared utilities: `shared/{module_name}.py`
- Handler function: Always `lambda_handler`

### SAM Infrastructure
- SAM template: `template.yaml`
- State machines: `statemachine/{workflow-name}.asl.json`
- Resource IDs: PascalCase with environment suffix

### Configuration Files
- Environment configs: `{environment}.json`
- Docker compose: `docker-compose.{environment}.yml`
- Scripts: `{action}-{target}.sh`

### Test Files
- Integration tests: `tests/integration/test_workflow.py` (Docker 기반 워크플로 전체 테스트)
- Agent tests: `tests/integration/test_agents.py` (Agent 통신 테스트)
- Test fixtures: `tests/integration/conftest.py` (Docker Compose 관리)
- **단위 테스트는 사용하지 않음** - Docker 기반 통합 테스트로 충분

## Import Patterns

### Agent Imports
```python
# Always import from shared utilities
from src.lambda.shared.base_agent import BaseAgent
from src.lambda.shared.models import WorkflowSession, AgentType
from src.lambda.shared.utils import setup_logging, get_aws_clients
```

### SAM Template Pattern
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: dev

Globals:
  Function:
    Runtime: python3.11
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment

Resources:
  SupervisorAgent:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/lambda/agents/supervisor/
      Handler: index.lambda_handler
```

### Environment-Specific Logic
```python
# Environment detection pattern
environment = os.getenv('ENVIRONMENT', 'local')
if environment == 'local':
    # Local development configuration
elif environment == 'dev':
    # Development environment configuration
```

## Data Flow Architecture

### Session Management
1. **Creation**: POST /sessions → Supervisor Agent → DynamoDB
2. **Updates**: Each agent updates session state via BaseAgent methods
3. **Retrieval**: GET /sessions/{id} → Supervisor Agent → DynamoDB

### Agent Communication
1. **Direct**: Agent → Agent via communication interface
2. **Supervised**: Agent → Supervisor → Target Agent
3. **Async**: Agent → SQS → Target Agent (for long-running tasks)

### Error Handling Flow
1. **Agent Level**: BaseAgent.handle_error() → structured logging
2. **Supervisor Level**: Monitor agent status → retry/fallback
3. **API Level**: HTTP error responses with agent context