# AWS AI Agent Global Hackathon Guidelines

## Hackathon Requirements

이 프로젝트는 AWS AI Agent Global Hackathon 제출을 위해 다음 요구사항을 충족해야 합니다.

### 필수 조건 (Must Have)

1. **Amazon Bedrock LLM 사용**
   - Primary LLM: Bedrock Claude 4 Sonnet
   - Image Generation: Bedrock SDXL
   - Knowledge Base: Bedrock KB (production)
   - ❌ OpenAI/Gemini는 개발 환경 fallback만 허용

2. **Bedrock AgentCore 통합**
   - Supervisor Agent에 AgentCore 구현
   - Tool Use primitive 사용 (agent 간 통신)
   - Memory primitive 사용 (워크플로 상태)
   - 최소 1개 primitive 필수

3. **Reasoning LLM 의사결정**
   - Claude 4 Sonnet으로 Chain-of-Thought reasoning
   - 모든 주요 결정에 reasoning chain 저장
   - Confidence scoring (0-1)
   - DynamoDB에 reasoning 기록

4. **자율적 작업 실행**
   - 사용자 입력 최소화
   - 자동 오류 복구 (재시도, fallback)
   - Supervisor Agent의 자율 의사결정

5. **외부 도구 통합**
   - DynamoDB (세션 관리)
   - S3 (파일 저장)
   - Bedrock KB (벡터 검색)
   - Agent 간 통신

### 제출 요구사항

1. **공개 GitHub 저장소**
   - 전체 소스 코드
   - README.md (배포 가이드)
   - LICENSE (MIT)

2. **아키텍처 다이어그램**
   - Bedrock 통합 명시
   - AgentCore 사용 표시
   - Reasoning LLM 결정 포인트

3. **3분 데모 비디오**
   - 문제 소개 (0:00-0:30)
   - 솔루션 시연 (0:30-2:00)
   - 기술 설명 (2:00-2:30)
   - 결과 및 영향 (2:30-3:00)

4. **배포된 프로젝트 URL**
   - 실제 동작하는 API 엔드포인트
   - Streamlit 웹 인터페이스

5. **프로젝트 설명 (영어)**
   - 문제 정의
   - 솔루션 설명
   - 기술 스택
   - 영향 및 가치

## 개발 가이드라인

### Bedrock Only 모드

제출 시 반드시 Bedrock만 사용하도록 설정:

```bash
# .env 또는 환경 변수
ENABLE_FALLBACK=false
DEV_PROFILE=false
BEDROCK_REGION=us-east-1
```

### 로컬 개발 모드

개발 중에는 fallback 허용:

```bash
# .env.local
ENABLE_FALLBACK=true
DEV_PROFILE=true
ENVIRONMENT=local
```

### Reasoning Chain 저장

모든 주요 결정에 reasoning 기록:

```python
reasoning_step = {
    "stepNumber": 1,
    "agentName": "reporter",
    "timestamp": "2025-10-07T12:00:00Z",
    "input": {"business_info": "..."},
    "reasoning": "Based on the industry analysis...",
    "decision": "Selected name: CafeBreeze",
    "confidence": 0.85,
    "alternatives": [...]
}
```

### AgentCore 사용 예시

```python
# Supervisor Agent
from agentcore_orchestrator import AgentCoreOrchestrator

orchestrator = AgentCoreOrchestrator()

# Tool Use primitive
result = orchestrator.invoke_agent_with_tool(
    agent_name="reporter",
    input_data={"business_info": business_info}
)

# Memory primitive
orchestrator.store_workflow_memory(
    session_id=session_id,
    step=2,
    data=result
)
```

## 평가 기준

### Technical Execution (50%)
- ✅ Bedrock 사용 (필수)
- ✅ AgentCore 구현 (필수)
- ✅ Reasoning LLM (필수)
- ✅ Well-architected (SAM, serverless)
- ✅ Reproducible (배포 가능)

### Potential Value/Impact (20%)
- 실제 문제 해결
- 측정 가능한 영향
- 비즈니스 가치

### Creativity (10%)
- 문제의 참신함
- 접근 방식의 독창성

### Functionality (10%)
- Agent 정상 동작
- 확장 가능성

### Demo Presentation (10%)
- End-to-end 워크플로 시연
- 명확한 설명

## 제출 체크리스트

배포 전 확인사항:

- [ ] `ENABLE_FALLBACK=false` 설정
- [ ] Bedrock 모델 가용성 확인 (`aws bedrock list-foundation-models`)
- [ ] AgentCore Agent ID 설정
- [ ] Bedrock Knowledge Base ID 설정
- [ ] IAM 권한 확인 (Bedrock, AgentCore)
- [ ] 통합 테스트 통과
- [ ] 아키텍처 다이어그램 완성
- [ ] 데모 비디오 업로드 (YouTube)
- [ ] README.md 영어 번역
- [ ] GitHub 저장소 public 설정
- [ ] API 엔드포인트 테스트
- [ ] Devpost 제출 양식 작성

## 상금 카테고리

이 프로젝트는 다음 카테고리에 지원 가능:

1. **1st/2nd/3rd Place** ($16,000/$9,000/$5,000)
   - 전체 프로젝트 평가

2. **Best Amazon Bedrock AgentCore Implementation** ($3,000)
   - AgentCore 사용 우수성
   - Tool Use, Memory primitive 활용

3. **Best Amazon Bedrock Application** ($3,000)
   - Bedrock 통합 우수성
   - Claude, SDXL, KB 활용

## 참고 자료

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock AgentCore Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Claude 4 Sonnet Model Card](https://docs.anthropic.com/claude/docs/models-overview)
- [Hackathon Rules](../../docs/AWS%20Hackathon%20rules.md)
- [Hackathon Overview](../../docs/AWS%20Hackathon%20overview.md)

## 마감일

- **제출 마감**: 2025년 10월 21일 @ 9:00am GMT+9
- **심사 기간**: 2025년 10월 21일 - 11월 12일
- **수상자 발표**: 2025년 12월 5일 @ re:invent conference

## 지원

- AWS 크레딧: $100 (선착순)
- Kiro 액세스 코드: 14일 무료 체험
- 기술 지원: Devpost 포럼
