# Project Structure & Organization

## 간소화된 프로젝트 구조

```
├── src/
│   ├── lambda/
│   │   ├── agents/                    # Agent Lambda functions (핵심)
│   │   │   ├── supervisor/            # 워크플로 감시
│   │   │   ├── product-insight/       # 비즈니스 분석
│   │   │   ├── market-analyst/        # 시장 분석
│   │   │   └── reporter/              # 상호명 제안
│   │   └── shared/                    # 공통 유틸리티
│   │       ├── base_agent.py          # BaseAgent 클래스
│   │       ├── models.py              # 데이터 모델
│   │       └── utils.py               # 공통 함수
│   └── streamlit/                     # 웹 인터페이스
│       └── app.py                     # Streamlit 앱
├── infrastructure/                    # AWS CDK 코드
│   ├── app.py                         # CDK 앱
│   └── stacks/                        # CDK 스택들
├── config/                            # 환경 설정
│   ├── dev.json                       # 개발 환경
│   └── local.json                     # 로컬 환경
├── scripts/                           # 개발/배포 스크립트
├── tests/                             # 통합 테스트만
│   ├── test_integration.py            # 워크플로 통합 테스트
│   └── test_models.py                 # 모델 테스트
└── data/                              # 로컬 개발 데이터
```

**주요 변경사항:**
- 레거시 Lambda 함수들 제거 (business-analyzer, file-handler 등)
- 단위 테스트 제거, 통합 테스트만 유지
- 복잡한 설정 파일들 간소화
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
- **CDK stacks** are modular and environment-aware
- **Stack dependencies**: Storage → API → Workflow → Frontend
- **Resource naming**: `branding-chatbot-{resource}-{environment}`
- **IAM permissions**: Least privilege with stack-specific roles

## File Naming Conventions

### Lambda Functions
- Agent functions: `{agent-name}/index.py`
- Shared utilities: `shared/{module_name}.py`
- Handler function: Always `lambda_handler`

### CDK Infrastructure
- Stack files: `{purpose}_stack.py`
- Stack classes: `{Purpose}Stack`
- Resource IDs: PascalCase with environment suffix

### Configuration Files
- Environment configs: `{environment}.json`
- Docker compose: `docker-compose.{environment}.yml`
- Scripts: `{action}-{target}.sh`

### Test Files
- Integration tests: `test_integration.py` (워크플로 전체 테스트)
- Model tests: `test_models.py` (데이터 모델 테스트)
- **단위 테스트는 사용하지 않음** - 통합 테스트로 충분

## Import Patterns

### Agent Imports
```python
# Always import from shared utilities
from src.lambda.shared.base_agent import BaseAgent
from src.lambda.shared.models import WorkflowSession, AgentType
from src.lambda.shared.utils import setup_logging, get_aws_clients
```

### CDK Imports
```python
# Standard CDK pattern
from aws_cdk import Stack, Duration
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
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