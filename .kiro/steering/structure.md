# Project Structure & Organization

## SAM 기반 프로젝트 구조

```
├── template.yaml                      # SAM 템플릿 (모든 AWS 리소스 정의)
├── samconfig.toml                     # SAM 배포 설정 (환경별)
├── src/
│   ├── lambda/
│   │   ├── agents/                    # Agent Lambda functions (핵심)
│   │   │   ├── supervisor/            # 워크플로 감시
│   │   │   │   ├── index.py           # Lambda handler
│   │   │   │   └── requirements.txt   # Agent별 의존성
│   │   │   ├── product-insight/       # 비즈니스 분석
│   │   │   ├── market-analyst/        # 시장 분석
│   │   │   └── reporter/              # 상호명 제안
│   │   └── shared/                    # 공통 유틸리티 (Lambda Layer)
│   │       ├── base_agent.py          # BaseAgent 클래스
│   │       ├── models.py              # 데이터 모델
│   │       └── utils.py               # 공통 함수
│   └── streamlit/                     # 웹 인터페이스
│       └── app.py                     # Streamlit 앱
├── statemachine/                      # Step Functions 정의
│   ├── branding-workflow.asl.json     # 워크플로 상태머신
│   └── parallel-image-gen.asl.json    # 병렬 이미지 생성
├── config/                            # 환경 설정
│   ├── dev.json                       # 개발 환경
│   └── local.json                     # 로컬 환경
├── scripts/                           # 개발/배포 스크립트
│   ├── setup-local.sh                 # 로컬 환경 설정
│   └── deploy.sh                      # SAM 배포 스크립트
├── tests/                             # Docker 기반 통합 테스트만
│   └── integration/                   # 통합 테스트 디렉토리
│       ├── test_workflow.py           # 워크플로 통합 테스트
│       ├── test_agents.py             # Agent 통신 테스트
│       └── conftest.py                # pytest fixtures
├── docker-compose.local.yml           # 로컬 개발 서비스
└── data/                              # 로컬 개발 데이터
```

**주요 변경사항:**
- AWS CDK → AWS SAM 전환으로 완전 서버리스 배포
- template.yaml 하나로 모든 AWS 리소스 정의
- 단위 테스트 제거, Docker Compose 기반 통합 테스트만 유지
- DynamoDB Admin UI 추가로 로컬 데이터 시각화
- Agent 기반 아키텍처로 통일

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
- **Data models**: `src/lambda/shared/models.py`
- **Communication**: `src/lambda/shared/agent_communication.py`
- **Vector store**: `src/lambda/shared/knowledge_base.py`
- **Common utils**: `src/lambda/shared/utils.py`

### Configuration Management
- Environment-specific configs in `config/{env}.json`
- Agent configurations include timeouts, AI providers, and feature flags
- Local development uses Docker Compose services
- Production uses AWS managed services

### Infrastructure as Code
- **SAM template** (template.yaml) defines all AWS resources in one file
- **Environment parameters**: samconfig.toml for environment-specific settings
- **Resource naming**: `branding-chatbot-{resource}-{environment}`
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