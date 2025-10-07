# Design Document

## Overview

이 설계 문서는 기존 AI 브랜딩 챗봇을 AWS AI Agent Global Hackathon 요구사항에 맞춰 수정하는 방법을 정의합니다. 핵심 변경사항은 Amazon Bedrock 통합, Bedrock AgentCore 구현, 그리고 Reasoning LLM 기반 자율 의사결정 시스템 추가입니다.

### Design Principles

1. **Minimal Disruption**: 기존 Agent-Based Architecture 유지하면서 Bedrock 통합
2. **Backward Compatibility**: 로컬 개발 환경은 기존 방식 지원 (OpenAI fallback)
3. **Hackathon Compliance**: 모든 필수 요구사항 충족 (Bedrock, AgentCore, Reasoning LLM)
4. **Production Ready**: 해커톤 이후에도 실제 서비스로 운영 가능한 구조
5. **Well-Architected**: AWS Well-Architected Framework 원칙 준수

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Web UI                          │
│                     (AWS App Runner)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway (HTTP API)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                              │
│              (Bedrock AgentCore Orchestrator)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Bedrock AgentCore - Reasoning & Orchestration           │  │
│  │  - Claude 3.5 Sonnet for reasoning                       │  │
│  │  - Tool Use primitive for agent coordination             │  │
│  │  - Memory primitive for workflow state                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Product     │ │   Market     │ │   Reporter   │
│  Insight     │ │   Analyst    │ │    Agent     │
│  Agent       │ │   Agent      │ │              │
│ (Bedrock)    │ │  (Bedrock)   │ │  (Bedrock)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
         ┌──────────────────────────────┐
         │                              │
         ▼                              ▼
┌──────────────┐              ┌──────────────┐
│  Signboard   │              │  Interior    │
│   Agent      │              │   Agent      │
│ (Bedrock     │              │  (Bedrock)   │
│   SDXL)      │              │              │
└──────┬───────┘              └──────┬───────┘
       │                             │
       └──────────────┬──────────────┘
                      ▼
              ┌──────────────┐
              │   Report     │
              │  Generator   │
              │   Agent      │
              │  (Bedrock)   │
              └──────┬───────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Services Layer                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  DynamoDB    │  │      S3      │  │   Bedrock    │         │
│  │  (Sessions)  │  │   (Assets)   │  │  Knowledge   │         │
│  │              │  │              │  │     Base     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Changes

1. **Bedrock Integration Layer**: 모든 Agent에 Bedrock 클라이언트 추가
2. **AgentCore Orchestrator**: Supervisor Agent에 AgentCore 통합
3. **Reasoning Engine**: 각 Agent에 Claude 3.5 Sonnet 기반 reasoning 추가
4. **Fallback System**: Bedrock 실패 시 기존 OpenAI/Gemini로 fallback

## Components and Interfaces

### 1. Bedrock Integration Module

**Location**: `src/lambda/shared/bedrock_client.py`

**Purpose**: Amazon Bedrock API와의 통합을 위한 공통 클라이언트

**Key Methods**:

```python
class BedrockClient:
    """Amazon Bedrock 통합 클라이언트"""
    
    def __init__(self, region: str = "us-east-1"):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
    
    def invoke_claude(self, prompt: str, system_prompt: str = None, 
                     max_tokens: int = 2048, temperature: float = 0.7) -> dict:
        """Claude 3.5 Sonnet 호출 (reasoning 및 text generation)"""
        
    def invoke_sdxl(self, prompt: str, negative_prompt: str = None,
                   width: int = 1024, height: int = 1024) -> bytes:
        """Stable Diffusion XL 호출 (image generation)"""
    
    def query_knowledge_base(self, query: str, kb_id: str) -> list:
        """Bedrock Knowledge Base 쿼리 (vector search)"""
    
    def invoke_with_retry(self, func, max_retries: int = 3) -> Any:
        """Exponential backoff를 사용한 재시도 로직"""
```

**Error Handling**:
- `ThrottlingException`: Exponential backoff으로 재시도
- `ValidationException`: 입력 파라미터 검증 및 로깅
- `ServiceUnavailableException`: Fallback provider로 전환

### 2. Bedrock AgentCore Integration

**Location**: `src/lambda/agents/supervisor/agentcore_orchestrator.py`

**Purpose**: Bedrock AgentCore를 사용한 Agent 오케스트레이션

**AgentCore Primitives Used**:
1. **Tool Use**: Agent 간 통신 및 작업 위임
2. **Memory**: 워크플로 상태 및 컨텍스트 유지
3. **Planning**: 다음 실행할 Agent 결정

**Implementation**:
```python
class AgentCoreOrchestrator:
    """Bedrock AgentCore 기반 Supervisor"""
    
    def __init__(self):
        self.bedrock_client = BedrockClient()
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
    
    def orchestrate_workflow(self, session_id: str, business_info: dict) -> dict:
        """AgentCore를 사용한 워크플로 오케스트레이션"""
        # 1. Reasoning: 워크플로 계획 수립
        # 2. Tool Use: 각 Agent 호출
        # 3. Memory: 진행 상태 저장
        # 4. Decision: 다음 단계 결정
        
    def invoke_agent_with_tool(self, agent_name: str, input_data: dict) -> dict:
        """AgentCore Tool Use primitive로 Agent 호출"""

    def store_workflow_memory(self, session_id: str, step: int, data: dict):
        """AgentCore Memory primitive로 상태 저장"""
    
    def reason_next_step(self, current_state: dict) -> str:
        """Reasoning LLM으로 다음 단계 결정"""
```

### 3. Reasoning Engine

**Location**: `src/lambda/shared/reasoning_engine.py`

**Purpose**: Claude 3.5 Sonnet을 사용한 자율적 의사결정

**Key Features**:
- Chain-of-Thought reasoning
- Multi-step planning
- Confidence scoring
- Explanation generation

**Implementation**:
```python
class ReasoningEngine:
    """Bedrock Claude 기반 Reasoning Engine"""
    
    def __init__(self):
        self.bedrock_client = BedrockClient()
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def reason_and_decide(self, context: dict, options: list, 
                         decision_criteria: str) -> dict:
        """
        Returns:
        {
            "decision": "selected_option",
            "reasoning": "step-by-step explanation",
            "confidence": 0.85,
            "alternatives": [...]
        }
        """
    
    def evaluate_business_name(self, name: str, business_info: dict) -> dict:
        """상호명 평가 및 점수 산정"""
    
    def rank_designs(self, designs: list, criteria: dict) -> list:
        """디자인 옵션 순위 결정"""
    
    def synthesize_insights(self, agent_outputs: dict) -> str:
        """여러 Agent 결과를 종합하여 인사이트 생성"""
```

### 4. Modified Agent Structure

각 Agent는 다음 구조로 수정됩니다:

```python
class ModernAgent(BaseAgent):
    """Bedrock 통합 Agent 기본 클래스"""
    
    def __init__(self, agent_type: AgentType):
        super().__init__(agent_type)
        self.bedrock_client = BedrockClient()
        self.reasoning_engine = ReasoningEngine()
        self.fallback_enabled = os.getenv('ENABLE_FALLBACK', 'true') == 'true'
    
    def execute_with_reasoning(self, input_data: dict) -> dict:
        """Reasoning LLM을 사용한 작업 실행"""
        try:
            # 1. Analyze input with reasoning
            analysis = self.reasoning_engine.reason_and_decide(
                context=input_data,
                options=self.get_execution_options(),
                decision_criteria=self.get_criteria()
            )
            
            # 2. Execute based on reasoning
            result = self.execute_task(analysis['decision'])
            
            # 3. Store reasoning chain
            self.store_reasoning(analysis)
            
            return result
        except Exception as e:
            if self.fallback_enabled:
                return self.execute_with_fallback(input_data)
            raise
```

## Data Models

### 1. Workflow Session (Enhanced)

```python
@dataclass
class WorkflowSession:
    sessionId: str
    businessInfo: BusinessInfo
    currentStep: int
    status: str  # 'active', 'paused', 'completed', 'failed'
    createdAt: str
    updatedAt: str
    ttl: int
    
    # New fields for Bedrock integration
    bedrockAgentId: Optional[str] = None
    reasoningChain: List[ReasoningStep] = field(default_factory=list)
    agentCoreMemory: Dict[str, Any] = field(default_factory=dict)
    confidenceScores: Dict[str, float] = field(default_factory=dict)
    
    # Existing fields
    productInsight: Optional[dict] = None
    marketAnalysis: Optional[dict] = None
    nameOptions: Optional[List[dict]] = None
    signboardDesigns: Optional[List[dict]] = None
    interiorOptions: Optional[List[dict]] = None
    reportUrl: Optional[str] = None
```

### 2. Reasoning Step

```python
@dataclass
class ReasoningStep:
    """Reasoning LLM의 의사결정 단계"""
    stepNumber: int
    agentName: str
    timestamp: str
    input: dict
    reasoning: str  # Chain-of-thought explanation
    decision: str
    confidence: float
    alternatives: List[dict]
    executionTime: float
```

### 3. Bedrock Configuration

```python
@dataclass
class BedrockConfig:
    """Bedrock 서비스 설정"""
    region: str = "us-east-1"
    claude_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    sdxl_model_id: str = "stability.stable-diffusion-xl-v1"
    agent_id: Optional[str] = None
    agent_alias_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30
    enable_fallback: bool = True
```

## Error Handling

### Bedrock-Specific Error Handling

```python
class BedrockErrorHandler:
    """Bedrock API 오류 처리"""
    
    @staticmethod
    def handle_bedrock_error(error: Exception, context: dict) -> dict:
        """
        Bedrock 오류 유형별 처리:
        - ThrottlingException: Exponential backoff 재시도
        - ValidationException: 입력 검증 및 수정
        - ModelTimeoutException: 타임아웃 증가 또는 fallback
        - ServiceUnavailableException: Fallback provider 사용
        - AccessDeniedException: IAM 권한 확인 메시지
        """
        
        if isinstance(error, ThrottlingException):
            return retry_with_backoff(context)
        elif isinstance(error, ValidationException):
            return validate_and_retry(context)
        elif isinstance(error, ServiceUnavailableException):
            return use_fallback_provider(context)
        else:
            return create_error_response(error, context)
```

### Fallback Strategy

1. **Primary**: Amazon Bedrock (Claude, SDXL)
2. **Secondary**: OpenAI (GPT-4, DALL-E) - 로컬 개발용
3. **Tertiary**: Google Gemini - 추가 fallback
4. **Final**: Static fallback responses

## Testing Strategy

### 1. Bedrock Integration Tests

**Location**: `tests/integration/test_bedrock_integration.py`

```python
def test_bedrock_claude_invocation():
    """Claude 3.5 Sonnet 호출 테스트"""
    
def test_bedrock_sdxl_image_generation():
    """SDXL 이미지 생성 테스트"""
    
def test_bedrock_knowledge_base_query():
    """Knowledge Base 쿼리 테스트"""
    
def test_bedrock_error_handling():
    """Bedrock 오류 처리 테스트"""
```

### 2. AgentCore Tests

**Location**: `tests/integration/test_agentcore.py`

```python
def test_agentcore_orchestration():
    """AgentCore 오케스트레이션 테스트"""
    
def test_agentcore_tool_use():
    """Tool Use primitive 테스트"""
    
def test_agentcore_memory():
    """Memory primitive 테스트"""
```

### 3. Reasoning Engine Tests

**Location**: `tests/integration/test_reasoning.py`

```python
def test_reasoning_decision_making():
    """Reasoning LLM 의사결정 테스트"""
    
def test_reasoning_confidence_scoring():
    """신뢰도 점수 산정 테스트"""
    
def test_reasoning_chain_storage():
    """Reasoning chain 저장 테스트"""
```

### 4. End-to-End Workflow Tests

**Location**: `tests/integration/test_hackathon_workflow.py`

```python
def test_full_workflow_with_bedrock():
    """Bedrock을 사용한 전체 워크플로 테스트"""
    
def test_autonomous_execution():
    """자율적 작업 실행 테스트"""
    
def test_fallback_mechanism():
    """Fallback 메커니즘 테스트"""
```

## Deployment Strategy

### Phase 1: Bedrock Integration (Week 1)

1. Bedrock 클라이언트 구현
2. 기존 Agent에 Bedrock 통합
3. Fallback 메커니즘 구현
4. 통합 테스트 작성

### Phase 2: AgentCore Implementation (Week 1-2)

1. Supervisor Agent에 AgentCore 통합
2. Tool Use primitive 구현
3. Memory primitive 구현
4. AgentCore 테스트

### Phase 3: Reasoning Engine (Week 2)

1. Reasoning Engine 구현
2. 각 Agent에 reasoning 추가
3. Confidence scoring 구현
4. Reasoning chain 저장

### Phase 4: Documentation & Demo (Week 2-3)

1. 아키텍처 다이어그램 작성
2. README 업데이트
3. 데모 비디오 제작
4. 배포 가이드 작성

### Phase 5: Testing & Submission (Week 3)

1. 전체 통합 테스트
2. 성능 최적화
3. 문서 최종 검토
4. 해커톤 제출

## Performance Considerations

### Bedrock API Latency

- Claude 3.5 Sonnet: ~2-3초 (평균)
- SDXL 이미지 생성: ~10-15초 (평균)
- Knowledge Base 쿼리: ~1-2초 (평균)

### Optimization Strategies

1. **Parallel Execution**: Step Functions로 병렬 Agent 실행
2. **Caching**: DynamoDB에 자주 사용되는 결과 캐싱
3. **Batch Processing**: 여러 요청을 배치로 처리
4. **Connection Pooling**: Bedrock 클라이언트 재사용

## Security Considerations

### IAM Permissions

```yaml
BedrockAccessPolicy:
  Version: '2012-10-17'
  Statement:
    - Effect: Allow
      Action:
        - bedrock:InvokeModel
        - bedrock:InvokeModelWithResponseStream
        - bedrock-agent-runtime:InvokeAgent
        - bedrock-agent-runtime:Retrieve
      Resource:
        - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/*'
        - !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:agent/*'
        - !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:knowledge-base/*'
```

### API Key Management

- Bedrock: IAM 역할 기반 인증 (API 키 불필요)
- OpenAI (fallback): AWS Secrets Manager에 저장
- Gemini (fallback): AWS Secrets Manager에 저장

## Monitoring and Observability

### CloudWatch Metrics

- Bedrock API 호출 횟수
- Bedrock API 응답 시간
- Bedrock API 오류율
- AgentCore 오케스트레이션 성공률
- Reasoning confidence 평균 점수

### CloudWatch Logs

- 구조화된 로그 (JSON 형식)
- Reasoning chain 로깅
- Agent 간 통신 로깅
- 오류 스택 트레이스

### CloudWatch Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  AI Branding Chatbot - Hackathon Dashboard                  │
├─────────────────────────────────────────────────────────────┤
│  Bedrock API Calls (Last Hour)          │  Success Rate     │
│  ████████████████████ 1,234             │  ████████ 98.5%   │
├─────────────────────────────────────────┼───────────────────┤
│  Average Response Time                   │  Active Sessions  │
│  Claude: 2.3s  SDXL: 12.1s              │  42               │
├─────────────────────────────────────────┼───────────────────┤
│  Reasoning Confidence (Avg)              │  Fallback Rate    │
│  ████████████ 0.87                      │  ██ 2.1%          │
└─────────────────────────────────────────────────────────────┘
```

## Cost Estimation

### Bedrock Costs (per workflow execution)

- Claude 3.5 Sonnet: ~$0.015 (5 invocations)
- SDXL Image Generation: ~$0.12 (3 images)
- Knowledge Base Query: ~$0.002 (2 queries)
- **Total per workflow**: ~$0.14

### Other AWS Costs

- Lambda: ~$0.001
- DynamoDB: ~$0.0001
- S3: ~$0.0001
- API Gateway: ~$0.0001
- **Total per workflow**: ~$0.0013

### Monthly Cost Estimate (1000 workflows)

- Bedrock: $140
- Other AWS Services: $1.30
- **Total**: ~$141.30/month

## Next Steps

1. ✅ Requirements 문서 승인 완료
2. ✅ Design 문서 작성 완료
3. ⏭️ Tasks 문서 작성 (implementation plan)
4. ⏭️ 구현 시작

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock AgentCore Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Claude 3.5 Sonnet Model Card](https://docs.anthropic.com/claude/docs/models-overview)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)


## Bedrock Model/Region Matrix

| Capability | Default Model | Alt Models (if unavailable) | Default Region | Notes |
|------------|---------------|----------------------------|----------------|-------|
| Reasoning/Text | anthropic.claude-3-5-sonnet-20241022-v2:0 | claude-3-5-haiku-20241022-v1:0 | us-east-1 | Verify modelId at deploy time with list-foundation-models |
| Image Generation | stability.stable-diffusion-xl-v1 | amazon.titan-image-generator-v2 (optional) | us-east-1 | Cap: 1024x1024 for demo |
| KB Retrieve | bedrock KB (Retrieve/RetrieveAndGenerate) | — | us-east-1 | Needs KB + data source setup |
| Agent Orchestration | Bedrock Agents (AgentCore) | Step Functions fallback | us-east-1 | Use agent alias in prod |

**Important**: Run `aws bedrock list-foundation-models --region us-east-1` before deployment to verify model availability.

## Enhanced IAM Policy

```yaml
BedrockAccessPolicy:
  Type: AWS::IAM::Policy
  Properties:
    PolicyName: BedrockRuntimeAccess
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        # Bedrock Model Invocation
        - Effect: Allow
          Action:
            - bedrock:InvokeModel
            - bedrock:InvokeModelWithResponseStream
            - bedrock:ListFoundationModels
          Resource: !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/*'
        
        # Bedrock Knowledge Base
        - Effect: Allow
          Action:
            - bedrock:Retrieve
            - bedrock:RetrieveAndGenerate
          Resource: !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:knowledge-base/*'
        
        # Bedrock Agent Runtime
        - Effect: Allow
          Action:
            - bedrock-agent-runtime:InvokeAgent
          Resource: !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:agent/*'
        
        # CloudWatch Logging & Metrics
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
            - cloudwatch:PutMetricData
          Resource: '*'
        
        # S3 Asset Storage
        - Effect: Allow
          Action:
            - s3:PutObject
            - s3:GetObject
            - s3:ListBucket
          Resource:
            - !Sub 'arn:aws:s3:::${BrandingAssetsBucket}'
            - !Sub 'arn:aws:s3:::${BrandingAssetsBucket}/*'
```

## Fallback Governance

### Environment-Based Fallback Control

```python
# config/fallback_config.py
class FallbackConfig:
    """Fallback 거버넌스 설정"""
    
    @staticmethod
    def is_fallback_enabled() -> bool:
        """
        Fallback 활성화 조건:
        - ENABLE_FALLBACK=true (명시적 활성화)
        - DEV_PROFILE=true (개발 환경)
        - ENVIRONMENT=local (로컬 개발)
        
        제출용 구성: ENABLE_FALLBACK=false (Bedrock Only)
        """
        enable_fallback = os.getenv('ENABLE_FALLBACK', 'false').lower() == 'true'
        dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
        environment = os.getenv('ENVIRONMENT', 'prod')
        
        return enable_fallback or dev_profile or environment == 'local'
```

### Deployment Checklist for Hackathon Submission

**README 체크리스트 추가**:

```markdown
## Hackathon Submission Checklist

- [ ] Bedrock Only Mode: `ENABLE_FALLBACK=false` in production
- [ ] Model Availability: Verified with `aws bedrock list-foundation-models`
- [ ] AgentCore Setup: Agent ID and Alias configured
- [ ] Knowledge Base: KB ID and data source configured
- [ ] IAM Permissions: All Bedrock policies attached
- [ ] Cost Monitoring: CloudWatch dashboard configured
- [ ] Demo Video: 3-minute video uploaded to YouTube
- [ ] Architecture Diagram: Shows Bedrock AgentCore integration
- [ ] Public Repository: All code pushed to GitHub
- [ ] Deployment URL: Live API endpoint accessible
```

## Sequence Diagram

### Happy Path: Full Workflow Execution

```
User → Streamlit → API Gateway → Supervisor (AgentCore)
                                      │
                                      ├─ Reasoning: Analyze request & plan workflow
                                      │
                                      ├─ Tool Use: Invoke agents in parallel
                                      │  ├─ Product Insight Agent (Bedrock Claude)
                                      │  ├─ Market Analyst Agent (Bedrock Claude + KB)
                                      │  └─ Reporter Agent (Bedrock Claude)
                                      │
                                      ├─ Memory: Store intermediate results
                                      │
                                      ├─ Tool Use: Sequential execution
                                      │  ├─ Signboard Agent (Bedrock SDXL)
                                      │  └─ Interior Agent (Bedrock Claude)
                                      │
                                      ├─ Tool Use: Generate report
                                      │  └─ Report Generator (Bedrock Claude + S3)
                                      │
                                      └─ Memory: Store final results
                                      
                                      ↓
                                   DynamoDB (Session State)
                                   S3 (Generated Assets)
                                   
                                   ↓
User ← Streamlit ← API Gateway ← Supervisor (Success Response)
```

### Error Path: Failure & Recovery

```
Supervisor (AgentCore)
    │
    ├─ Agent Execution Fails (e.g., Bedrock Throttling)
    │
    ├─ Reasoning: Evaluate failure & decide recovery strategy
    │  ├─ Option 1: Retry with exponential backoff
    │  ├─ Option 2: Use alternative model (e.g., Haiku instead of Sonnet)
    │  ├─ Option 3: Request human intervention
    │  └─ Option 4: Use fallback provider (if DEV_PROFILE=true)
    │
    ├─ Decision: Select best recovery option based on:
    │  - Error type (throttling vs validation vs timeout)
    │  - Retry count (max 3 attempts)
    │  - Confidence score (>0.7 for auto-retry)
    │  - User preference (allow human review)
    │
    └─ Execute Recovery & Continue Workflow
```

## Risk Mitigation

| Risk | Symptom | Mitigation |
|------|---------|------------|
| **Model Availability/Region Constraints** | Deployment failure, Invoke 403 | Region Matrix + SAM parameters, pre-deployment model verification script |
| **Cost Overrun (Image Generation)** | Budget exceeded during demo | Image resolution/count limits, fallback to text preview, cost dashboard alerts |
| **Timeout/Throttling** | 429/504 errors | Exponential backoff + jitter, circuit breaker, parallel execution limits |
| **Privacy (PII in Reasoning Chain)** | Sensitive data in logs | Field masking/encryption with KMS, table separation, TTL retention policy |
| **AgentCore Unavailability** | Agent invocation fails | Step Functions fallback orchestration, direct Lambda invocation |
| **Knowledge Base Empty** | No retrieval results | Fallback to DynamoDB market data, graceful degradation with static data |

## Additional Documentation Structure

### 1. Architecture Documentation

**Location**: `docs/architecture.md`

**Contents**:
- Detailed architecture diagram with Bedrock integration
- Sequence diagrams for all workflows
- Region/Model matrix
- IAM policy details
- Cost breakdown

### 2. Agent Documentation

**Location**: `docs/agents.md`

**Contents**:
- Each agent's I/O contract
- Tool schema definitions
- Model & prompt specifications
- Reasoning examples

### 3. Demo Script

**Location**: `docs/demo_script.md`

**Contents**:
- 3-minute timeline breakdown
- Key talking points
- Demo checklist
- Screen recording guide

## Deployment Verification Script

**Location**: `scripts/verify-bedrock-setup.sh`

```bash
#!/bin/bash
# Bedrock 배포 전 검증 스크립트

echo "Verifying Bedrock setup..."

# 1. Check AWS credentials
aws sts get-caller-identity || exit 1

# 2. List available foundation models
echo "Available Bedrock models in us-east-1:"
aws bedrock list-foundation-models --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`) || contains(modelId, `stable-diffusion`)].modelId' \
  --output table

# 3. Check IAM permissions
echo "Checking IAM permissions..."
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names bedrock:InvokeModel bedrock-agent-runtime:InvokeAgent \
  --resource-arns "arn:aws:bedrock:us-east-1::foundation-model/*"

# 4. Verify environment variables
echo "Checking environment configuration..."
[ -z "$ENABLE_FALLBACK" ] && echo "⚠️  ENABLE_FALLBACK not set (defaulting to false)" || echo "✓ ENABLE_FALLBACK=$ENABLE_FALLBACK"
[ -z "$BEDROCK_AGENT_ID" ] && echo "⚠️  BEDROCK_AGENT_ID not set" || echo "✓ BEDROCK_AGENT_ID configured"

echo "Verification complete!"
```

## Cost Optimization Strategies

### Image Generation Limits

```python
# config/cost_limits.py
class CostLimits:
    """비용 제한 설정"""
    
    # Image generation limits
    MAX_IMAGES_PER_SESSION = 3
    MAX_IMAGE_RESOLUTION = 1024  # 1024x1024
    MAX_CONCURRENT_IMAGE_GENERATIONS = 2
    
    # Text generation limits
    MAX_TOKENS_PER_REQUEST = 2048
    MAX_REASONING_STEPS = 5
    
    # Session limits
    MAX_SESSIONS_PER_USER_PER_HOUR = 10
    SESSION_TTL_HOURS = 24
    
    @staticmethod
    def estimate_cost(workflow_type: str) -> float:
        """워크플로 예상 비용 계산"""
        costs = {
            'full_workflow': 0.14,  # Claude + SDXL + KB
            'text_only': 0.02,      # Claude only
            'image_only': 0.12      # SDXL only
        }
        return costs.get(workflow_type, 0.14)
```

### Cost Dashboard Configuration

```yaml
# cloudwatch-dashboard.yaml
CostDashboard:
  Type: AWS::CloudWatch::Dashboard
  Properties:
    DashboardName: !Sub '${ProjectName}-cost-monitoring'
    DashboardBody: !Sub |
      {
        "widgets": [
          {
            "type": "metric",
            "properties": {
              "metrics": [
                ["AWS/Bedrock", "InvocationCount", {"stat": "Sum"}],
                [".", "InvocationLatency", {"stat": "Average"}],
                [".", "InvocationErrors", {"stat": "Sum"}]
              ],
              "period": 300,
              "stat": "Average",
              "region": "${AWS::Region}",
              "title": "Bedrock API Metrics"
            }
          },
          {
            "type": "metric",
            "properties": {
              "metrics": [
                ["Custom/Branding", "ImageGenerationCount", {"stat": "Sum"}],
                [".", "EstimatedCost", {"stat": "Sum"}]
              ],
              "period": 3600,
              "stat": "Sum",
              "region": "${AWS::Region}",
              "title": "Cost Tracking"
            }
          }
        ]
      }
```

## Demo Video Structure (3-minute timeline)

### 0:00-0:30 - Problem Introduction
- "Small businesses struggle with branding - it's expensive and time-consuming"
- "Our AI agent system automates the entire branding process"

### 0:30-1:00 - Solution Overview
- Show Streamlit UI
- Input: "Seoul Gangnam, small cafe"
- Highlight: "6 AI agents working together using Amazon Bedrock"

### 1:00-2:00 - Technical Execution
- Show Supervisor Agent with AgentCore orchestration
- Highlight reasoning LLM decision-making
- Show parallel agent execution
- Display generated assets (names, signboards, interiors)

### 2:00-2:30 - Results & Impact
- Show final PDF report
- Metrics: "5 minutes vs 2 weeks, $0.14 vs $5,000"
- Emphasize autonomous execution

### 2:30-3:00 - Architecture & Closing
- Show architecture diagram with Bedrock integration
- Mention: "Fully serverless, scalable, reproducible"
- Call to action: "Try it yourself - deployment guide in README"

## Updated Design Approval

이제 다음 사항들이 보완되었습니다:

✅ Bedrock Model/Region Matrix 추가
✅ 강화된 IAM Policy 정의
✅ Fallback 거버넌스 및 제출 체크리스트
✅ 상세한 시퀀스 다이어그램 (Happy Path & Error Path)
✅ 리스크 완화 전략 테이블
✅ 추가 문서 구조 정의
✅ 배포 검증 스크립트
✅ 비용 최적화 전략
✅ 데모 비디오 타임라인

다음 단계로 Tasks 문서를 작성하시겠습니까?
