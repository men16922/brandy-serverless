# Implementation Plan - AWS Hackathon Compliance

이 문서는 **기존 AI 브랜딩 챗봇 프로젝트**를 AWS AI Agent Global Hackathon 요구사항에 맞춰 수정하는 통합 구현 계획입니다.

## 📊 현재 프로젝트 상태 (2025-10-07 분석)

### ✅ 완료된 부분 (기존 프로젝트)
- ✅ AWS SAM 인프라 (template.yaml, DynamoDB, S3, Lambda, API Gateway)
- ✅ 데이터 모델 및 검증 로직 (models.py - 완성)
- ✅ BaseAgent 클래스 및 공통 유틸리티 (완전 구현)
- ✅ Docker Compose 로컬 환경 (DynamoDB Local, MinIO, Chroma)
- ✅ 통합 테스트 환경 (Docker 기반)
- ✅ Supervisor Agent 기본 구현 (세션 관리, Agent 통신)
- ✅ Product Insight Agent 완료 (업종/지역/규모 분석)
- ✅ Reporter Agent 완료 (상호명 생성 알고리즘)
- ✅ Market Analyst Agent 완료 (시장 분석)
- ✅ Signboard Agent 완료 (DALL-E, Gemini 병렬 처리)
- ✅ Interior Agent 완료 (인테리어 추천)
- ✅ Report Generator Agent 완료 (HTML/JSON/텍스트 보고서)
- ✅ Streamlit 웹 인터페이스 완료
- ✅ Agent 간 통신 인터페이스 (agent_communication.py)
- ✅ 구조화된 로깅 시스템 (agent, tool, latency_ms)

### ❌ 해커톤 요구사항 미충족 부분 (구현 필요)
- ❌ Amazon Bedrock 통합 (BedrockClient 모듈 없음)
- ❌ Bedrock AgentCore 통합 (AgentCoreOrchestrator 없음)
- ❌ Reasoning LLM 시스템 (ReasoningEngine 없음)
- ❌ ReasoningStep 데이터 모델 (models.py에 없음)
- ❌ Bedrock IAM 정책 (template.yaml에 없음)
- ❌ Fallback 거버넌스 시스템 (환경 변수 기반)
- ❌ 해커톤 제출 문서 (아키텍처 다이어그램, 데모 비디오)

## Task Overview

- **Total Tasks**: 11개 주요 작업 (Phase 1-10)
- **Estimated Timeline**: 2-3주
- **Priority**: Bedrock 통합 → AgentCore → Reasoning → Agent 전환 → Documentation
- **Strategy**: 기존 완성된 Agent 코드 유지하면서 Bedrock 레이어 추가
- **Current Status**: 0/11 phases completed (0% → 100% target)

## Tasks

### 🎯 Phase 1: Bedrock 통합 기반 구축 (Week 1)

- [x] 1. Bedrock 클라이언트 모듈 구현
  - `src/lambda/shared/bedrock_client.py` 파일 생성
  - `BedrockClient` 클래스 구현:
    - `invoke_claude()` - Claude 4 Sonnet 호출 (reasoning, text generation)
    - `invoke_sdxl()` - SDXL 이미지 생성
    - `query_knowledge_base()` - Bedrock KB 벡터 검색
    - `invoke_with_retry()` - Exponential backoff 재시도 로직
  - 오류 처리: ThrottlingException, ValidationException, ServiceUnavailableException
  - 구조화된 로깅 추가 (bedrock_api_call, model_id, latency_ms)
  - _Requirements: 1.1, 1.2, 1.7_
  - _기존 코드: BaseAgent 클래스 패턴 참고_

- [x] 2. Bedrock IAM 정책 및 환경 설정
  - `template.yaml`에 Bedrock IAM 정책 추가:
    - bedrock:InvokeModel (Claude, SDXL)
    - bedrock:Retrieve (Knowledge Base)
    - bedrock-agent-runtime:InvokeAgent (AgentCore)
  - 환경 변수 추가:
    - BEDROCK_REGION (default: us-east-1)
    - CLAUDE_MODEL_ID (us.anthropic.claude-sonnet-4-20250514-v1:0)
    - SDXL_MODEL_ID (stability.stable-diffusion-xl-v1)
    - BEDROCK_KB_ID (Knowledge Base ID)
    - ENABLE_FALLBACK (true/false)
  - `config/bedrock_config.py` 생성 (BedrockConfig dataclass)
  - _Requirements: 1.1, 6.5_
  - _기존 코드: template.yaml Globals 섹션 확장_

- [x] 3. Bedrock 검증 스크립트 작성
  - `scripts/verify-bedrock-setup.sh` 생성:
    - `aws bedrock list-foundation-models --region us-east-1` 실행
    - Claude, SDXL 모델 가용성 확인
    - IAM 권한 검증 (bedrock:InvokeModel)
    - Knowledge Base ID 존재 확인
  - 배포 전 자동 검증 로직
  - 실패 시 명확한 오류 메시지 출력
  - _Requirements: 1.1, 7.2_
  - _기존 코드: scripts/setup-local.sh 패턴 참고_

- [x] 4. Bedrock 통합 테스트 작성
  - `tests/integration/test_bedrock_integration.py` 생성:
    - `test_bedrock_claude_invocation()` - Claude 호출 및 응답 파싱
    - `test_bedrock_sdxl_image_generation()` - SDXL 이미지 생성
    - `test_bedrock_knowledge_base_query()` - KB 쿼리
    - `test_bedrock_error_handling()` - 오류 처리 및 재시도
    - `test_bedrock_response_parsing()` - API 응답 파싱
  - Docker Compose 환경 활용 (DynamoDB, S3)
  - _Requirements: 1.7, 10.2_
  - _기존 코드: tests/integration/conftest.py 활용_

### 🤖 Phase 2: Bedrock AgentCore 통합 (Week 1-2)

- [x] 5. AgentCore Orchestrator 클래스 구현
  - `src/lambda/agents/supervisor/agentcore_orchestrator.py` 생성
  - `AgentCoreOrchestrator` 클래스 구현:
    - `__init__()` - BedrockClient 초기화, Agent ID/Alias 설정
    - `orchestrate_workflow()` - 5단계 워크플로 오케스트레이션
    - `invoke_agent_with_tool()` - Tool Use primitive로 Agent 호출
    - `store_workflow_memory()` - Memory primitive로 상태 저장
    - `reason_next_step()` - Reasoning LLM으로 다음 단계 결정
  - Bedrock Agent Runtime API 통합 (boto3 bedrock-agent-runtime)
  - _Requirements: 2.1, 2.2_
  - _기존 코드: BaseAgent 패턴, agent_communication.py 참고_

- [x] 6. Tool Use primitive 구현
  - Agent 간 통신을 위한 Tool Use 스키마 정의:
    - Tool name: "invoke_agent"
    - Input schema: {agent_name, input_data, session_id}
    - Output schema: {result, status, latency_ms}
  - `invoke_agent_with_tool()` 메서드 구현
  - Tool 실행 결과 파싱 및 오류 처리
  - 기존 `AgentCommunication` 인터페이스와 통합
  - _Requirements: 2.2, 2.3_
  - _기존 코드: src/lambda/shared/agent_communication.py 확장_

- [x] 7. Memory primitive 구현
  - 워크플로 상태 저장을 위한 Memory 스키마 정의:
    - Memory key: session_id
    - Memory value: {current_step, agent_outputs, reasoning_chain}
  - `store_workflow_memory()` 메서드 구현
  - `retrieve_workflow_memory()` 메서드 구현
  - 기존 DynamoDB 세션 관리와 AgentCore Memory 동기화
  - _Requirements: 2.3, 2.5_
  - _기존 코드: BaseAgent.update_session_data() 활용_

- [x] 8. Supervisor Agent에 AgentCore 통합
  - `src/lambda/agents/supervisor/index.py` 수정:
    - AgentCoreOrchestrator 인스턴스 생성
    - 환경 변수 `USE_AGENTCORE` 확인 (true/false)
    - AgentCore 사용 시: orchestrate_workflow() 호출
    - Fallback 시: 기존 Step Functions 로직 사용
  - 기존 세션 관리 로직 유지
  - 구조화된 로깅 추가 (orchestration_mode: agentcore/stepfunctions)
  - _Requirements: 2.1, 2.6_
  - _기존 코드: 기존 Supervisor 로직 100% 유지_

- [x] 9. AgentCore 통합 테스트 작성
  - `tests/integration/test_agentcore.py` 생성:
    - `test_agentcore_orchestration()` - 전체 오케스트레이션
    - `test_agentcore_tool_use()` - Tool Use primitive
    - `test_agentcore_memory()` - Memory primitive
    - `test_agentcore_inter_agent_communication()` - Agent 간 통신
    - `test_agentcore_fallback()` - Step Functions fallback
  - Docker Compose 환경 활용
  - _Requirements: 2.7, 10.3_
  - _기존 코드: tests/integration/test_workflow.py 패턴 참고_

### 🧠 Phase 3: Reasoning Engine 구현 (Week 2)

- [x] 10. Reasoning Engine 클래스 구현
  - `src/lambda/shared/reasoning_engine.py` 생성
  - `ReasoningEngine` 클래스 구현:
    - `__init__()` - BedrockClient 초기화, Claude 4 Sonnet 설정
    - `reason_and_decide()` - Chain-of-Thought reasoning 실행
    - `evaluate_business_name()` - 상호명 평가 및 점수 산정
    - `rank_designs()` - 디자인 옵션 순위 결정
    - `synthesize_insights()` - 여러 Agent 결과 종합
  - Confidence scoring 메커니즘 (0.0-1.0 scale)
  - Reasoning chain 생성 (step-by-step explanation)
  - _Requirements: 3.1, 3.2, 3.6_
  - _기존 코드: BedrockClient.invoke_claude() 활용_

- [x] 11. Reasoning 데이터 모델 추가
  - `src/lambda/shared/models.py`에 `ReasoningStep` dataclass 추가:
    - stepNumber: int
    - agentName: str
    - timestamp: str
    - input: dict
    - reasoning: str (Chain-of-Thought explanation)
    - decision: str
    - confidence: float (0.0-1.0)
    - alternatives: List[dict]
    - executionTime: float
  - `WorkflowSession`에 `reasoning_chain: List[ReasoningStep]` 필드 추가
  - `WorkflowSession.to_dict()` 및 `from_dict()` 메서드 업데이트
  - _Requirements: 3.6_
  - _기존 코드: models.py의 기존 dataclass 패턴 따르기_

- [x] 12. BaseAgent에 Reasoning 메서드 추가
  - `src/lambda/shared/base_agent.py`에 메서드 추가:
    - `execute_with_reasoning()` - Reasoning LLM 사용한 작업 실행
    - `store_reasoning()` - Reasoning chain DynamoDB 저장
    - `autonomous_error_recovery()` - 자율적 오류 복구
  - ReasoningEngine 인스턴스 생성 (self.reasoning_engine)
  - 기존 execute() 메서드는 유지 (하위 호환성)
  - _Requirements: 3.1, 3.2, 4.2_
  - _기존 코드: BaseAgent 클래스 확장_

- [x] 13. Reasoning Engine 테스트 작성
  - `tests/integration/test_reasoning.py` 생성:
    - `test_reasoning_decision_making()` - 의사결정 테스트
    - `test_reasoning_confidence_scoring()` - 신뢰도 점수 테스트
    - `test_reasoning_chain_storage()` - DynamoDB 저장 테스트
    - `test_low_confidence_handling()` - 낮은 신뢰도 처리
  - Docker Compose 환경 활용 (DynamoDB Local)
  - _Requirements: 3.7, 10.4_
  - _기존 코드: tests/integration/conftest.py 활용_

### 🔄 Phase 4: 각 Agent Bedrock 전환 (Week 2) - 병렬 작업 가능

**참고**: 이 작업들은 독립적으로 진행 가능하며, 기존 완료된 Agent 로직을 100% 유지하면서 Bedrock을 Primary로 추가합니다.

- [x] 14. Product Insight Agent Bedrock 통합
  - `src/lambda/agents/product-insight/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 분석 로직 유지
    - Bedrock Claude로 업종/지역/규모 분석 수행
    - execute_with_reasoning() 메서드 사용
    - Fallback: 기존 로직 (ENABLE_FALLBACK=true 시)
  - _Requirements: 1.2, 3.1_
  - _기존 코드: 완료된 Product Insight Agent 확장_

- [x] 15. Reporter Agent Bedrock 통합
  - `src/lambda/agents/reporter/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 상호명 생성 알고리즘 유지
    - Bedrock Claude로 상호명 생성 및 평가
    - ReasoningEngine.evaluate_business_name() 사용
    - Fallback: 기존 로직
  - _Requirements: 1.2, 3.3_
  - _기존 코드: 완료된 Reporter Agent 확장_

- [x] 16. Market Analyst Agent Bedrock 통합
  - `src/lambda/agents/market-analyst/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 시장 분석 로직 유지
    - Bedrock Claude + Knowledge Base로 시장 트렌드 분석
    - query_knowledge_base() 메서드 사용
    - Fallback: 기존 로직 + Chroma (로컬)
  - _Requirements: 1.3, 3.2, 5.2_
  - _기존 코드: 완료된 Market Analyst Agent 확장_

- [x] 17. Signboard Agent Bedrock SDXL 통합
  - `src/lambda/agents/signboard/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 DALL-E, Gemini 병렬 처리 유지
    - Bedrock SDXL을 3번째 병렬 옵션으로 추가
    - 이미지 생성 파라미터 최적화 (1024x1024)
    - Fallback: DALL-E, Gemini 유지
  - _Requirements: 1.4, 5.3_
  - _기존 코드: 완료된 Signboard Agent 확장_

- [x] 18. Interior Agent Bedrock 통합
  - `src/lambda/agents/interior/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 인테리어 추천 로직 유지
    - Bedrock Claude로 인테리어 스타일 추천
    - execute_with_reasoning() 메서드 사용
    - Fallback: 기존 로직
  - _Requirements: 1.5, 3.4_
  - _기존 코드: 완료된 Interior Agent 확장_

- [x] 19. Report Generator Agent Bedrock 통합
  - `src/lambda/agents/report-generator/index.py` 수정:
    - BedrockClient 인스턴스 생성
    - 기존 HTML/JSON/텍스트 생성 로직 유지
    - Bedrock Claude로 인사이트 종합 개선
    - ReasoningEngine.synthesize_insights() 사용
    - Fallback: 기존 로직
  - _Requirements: 1.5, 3.5_
  - _기존 코드: 완료된 Report Generator Agent 확장_

### ⚙️ Phase 5: Fallback 거버넌스 및 자율 실행 (Week 2)

- [x] 20. Fallback 설정 모듈 구현
  - `config/fallback_config.py` 생성:
    - `FallbackConfig` 클래스 구현
    - `is_fallback_enabled()` - 환경 변수 확인 (ENABLE_FALLBACK, DEV_PROFILE)
    - `get_fallback_provider()` - OpenAI/Gemini 선택 로직
  - 환경 변수 추가:
    - ENABLE_FALLBACK (true/false)
    - DEV_PROFILE (true/false)
    - FALLBACK_PROVIDER (openai/gemini)
  - _Requirements: 1.6_
  - _기존 코드: .env, samconfig.toml 활용_

- [x] 21. BaseAgent에 Fallback 메서드 추가
  - `src/lambda/shared/base_agent.py`에 메서드 추가:
    - `execute_with_fallback()` - Bedrock 실패 시 fallback 실행
    - `_should_use_fallback()` - Fallback 사용 여부 결정
    - `_log_fallback_usage()` - Fallback 사용 로깅
  - Circuit breaker 패턴 구현 (연속 실패 시 fallback 자동 전환)
  - Fallback 사용 시 메트릭 기록 (CloudWatch)
  - _Requirements: 1.6, 5.6_
  - _기존 코드: BaseAgent 클래스 확장_

- [x] 22. Supervisor Agent 자율 의사결정 로직 구현
  - `src/lambda/agents/supervisor/index.py` 수정:
    - `autonomous_error_recovery()` 메서드 추가
    - Reasoning Engine으로 복구 전략 결정 (retry/fallback/human)
    - 재시도 로직 (exponential backoff)
    - 휴먼 개입 요청 로직 (낮은 신뢰도 시)
  - 기존 세션 관리 로직과 통합
  - _Requirements: 4.2, 4.5_
  - _기존 코드: 기존 Supervisor 로직 확장_

- [x] 23. 워크플로 상태 관리 개선
  - 세션 일시 중지 및 재개 기능:
    - `pause_workflow()` - 현재 상태 저장
    - `resume_workflow()` - 저장된 상태에서 재개
  - 중간 결과 저장 및 복원 로직
  - DynamoDB 세션 데이터 확장 (pause_reason, resume_count)
  - _Requirements: 4.4, 4.6_
  - _기존 코드: BaseAgent.update_session_data() 활용_

- [ ] 24. Streamlit UI 상태 업데이트 개선
  - `src/streamlit/app.py` 수정:
    - Polling 간격 최적화 (5초 → 2초)
    - 진행 상황 표시 강화 (progress bar, step indicator)
    - Reasoning chain 표시 (expandable section)
    - 오류 발생 시 복구 전략 표시
  - _Requirements: 4.7_
  - _기존 코드: 기존 Streamlit UI 확장_

### 🧪 Phase 6: 통합 테스트 (Week 2-3)

- [ ] 25. 전체 워크플로 통합 테스트 작성
  - `tests/integration/test_hackathon_workflow.py` 생성:
    - `test_full_workflow_with_bedrock()` - Bedrock 사용한 5단계 워크플로
    - `test_autonomous_execution()` - 자율적 작업 실행 (Requirement 4.1)
    - `test_fallback_mechanism()` - Fallback 메커니즘 테스트
    - `test_pdf_report_generation()` - 최종 PDF 보고서 생성
    - `test_concurrent_sessions()` - 동시 세션 처리 (Requirement 9.4)
  - Docker Compose 환경 활용 (DynamoDB, S3, Chroma)
  - _Requirements: 10.4, 10.7_
  - _기존 코드: tests/integration/test_workflow.py 패턴 참고_

- [ ] 26. Docker Compose 환경 및 스크립트 업데이트
  - `docker-compose.local.yml` 유지 (변경 없음)
  - `scripts/dev.sh` 업데이트:
    - Bedrock 검증 스크립트 호출 추가
    - 통합 테스트 실행 명령 추가
  - `README.md` 업데이트:
    - Bedrock 로컬 테스트 가이드 추가
    - 환경 변수 설정 가이드 추가
  - _Requirements: 10.1_
  - _기존 코드: docker-compose.local.yml, scripts/dev.sh 확장_

### 📚 Phase 7: 문서화 (Week 3)

- [ ] 27. 아키텍처 다이어그램 생성
  - `docs/architecture.md` 생성:
    - High-level architecture diagram (Bedrock 통합 강조)
    - 5-step workflow diagram (Reasoning LLM 결정 포인트 표시)
    - Bedrock integration detail diagram (Claude, SDXL, KB, AgentCore)
    - Sequence diagram (Happy Path & Error Recovery Path)
  - Mermaid 또는 draw.io 사용
  - 기존 다이어그램 업데이트 (.kiro/specs/aws-hackathon-compliance/*.png)
  - _Requirements: 6.1, 6.2, 6.7_
  - _기존 코드: 기존 다이어그램 참고_

- [ ] 28. Agent 문서 작성
  - `docs/agents.md` 생성:
    - 각 Agent의 책임 및 역할
    - I/O 계약 (input schema, output schema)
    - Bedrock 모델 사용 (Claude, SDXL, KB)
    - Reasoning 예시 (Chain-of-Thought)
    - Tool 스키마 (AgentCore Tool Use)
    - 프롬프트 템플릿
  - _Requirements: 6.3, 6.5_

- [ ] 29. README.md 업데이트 (영어)
  - 기존 README.md 업데이트:
    - Project overview (Bedrock 통합 강조)
    - Architecture diagram 링크
    - Bedrock 설정 가이드 (IAM, 모델 가용성)
    - 배포 가이드 (sam build && sam deploy --guided)
    - 환경 변수 설정 가이드
    - 해커톤 제출 체크리스트
  - 영어로 작성 (해커톤 제출용)
  - _Requirements: 6.4, 7.2, 7.3, 7.5_
  - _기존 코드: README.md 확장_

### 🎥 Phase 8: 데모 비디오 제작 (Week 3)

- [ ] 30. 데모 스크립트 작성
  - `docs/demo_script.md` 생성:
    - 0:00-0:30 - 문제 소개 (브랜딩 비용, 시간 문제)
    - 0:30-2:00 - 솔루션 시연 (Streamlit UI, 5단계 워크플로)
    - 2:00-2:30 - 기술 설명 (Bedrock, AgentCore, Reasoning LLM)
    - 2:30-3:00 - 결과 및 영향 (생성된 브랜딩 자료, 비용/시간 절감)
  - 주요 토킹 포인트 및 화면 녹화 가이드
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 31. 데모 비디오 녹화 및 편집
  - 화면 녹화:
    - Streamlit UI 시연 (업종/지역/규모 입력)
    - 5단계 워크플로 진행 상황 표시
    - Reasoning chain 표시 (expandable section)
    - 생성된 결과물 (상호명, 간판, 인테리어, PDF)
  - 아키텍처 다이어그램 추가 (Bedrock 통합 강조)
  - 자막 추가 (영어)
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 32. 데모 비디오 업로드
  - YouTube에 공개 업로드:
    - 제목: "AI Branding Chatbot - AWS Bedrock AgentCore Implementation"
    - 설명: 프로젝트 개요, GitHub 링크, 기술 스택
    - 태그: AWS, Bedrock, AgentCore, AI Agent, Hackathon
  - 비디오 URL을 README.md 및 Devpost 제출 양식에 추가
  - _Requirements: 8.7_

### ⚡ Phase 9: 성능 최적화 및 모니터링 (Week 3)

- [ ] 33. CloudWatch 대시보드 생성
  - `template.yaml`에 CloudWatch Dashboard 리소스 추가:
    - Bedrock API 호출 횟수 (Claude, SDXL, KB)
    - Bedrock API 응답 시간 (P50, P95, P99)
    - Bedrock API 오류율
    - AgentCore 오케스트레이션 성공률
    - Reasoning confidence 평균 점수
    - 워크플로 완료 시간
    - 동시 세션 수
  - 대시보드 JSON 정의
  - _Requirements: 7.7, 9.6_
  - _기존 코드: template.yaml 확장_

- [ ] 34. 비용 제한 및 알람 설정
  - `config/cost_limits.py` 생성:
    - 이미지 생성 횟수 제한 (3개/세션)
    - 이미지 해상도 제한 (1024x1024)
    - 토큰 수 제한 (max_tokens: 2048)
  - CloudWatch 알람 설정:
    - Lambda 오류율 > 5%
    - Bedrock API 지연 > 10초
    - DynamoDB throttling 이벤트
  - _Requirements: 9.7_

- [ ] 35. 성능 최적화
  - Lambda 함수 메모리 조정:
    - Signboard Agent: 1024MB → 1536MB
    - Report Generator Agent: 2048MB (유지)
    - 기타 Agent: 512MB → 768MB
  - Lambda 타임아웃 조정:
    - Signboard Agent: 60초 (유지)
    - Report Generator Agent: 120초 (유지)
  - Bedrock API 호출 병렬화 (Signboard Agent)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

### 🚀 Phase 10: 최종 배포 및 제출 (Week 3)

- [ ] 36. 프로덕션 배포
  - 환경 변수 설정 확인:
    - ENABLE_FALLBACK=false (Bedrock Only)
    - USE_AGENTCORE=true
    - BEDROCK_REGION=us-east-1
  - SAM 배포 실행:
    - `sam build`
    - `sam deploy --guided` (첫 배포)
    - `sam deploy` (이후 배포)
  - API Gateway 엔드포인트 테스트:
    - POST /sessions (세션 생성)
    - GET /sessions/{id} (세션 조회)
    - GET /status/{id} (상태 확인)
  - _Requirements: 7.2, 7.3_
  - _기존 코드: scripts/sam-deploy.sh 활용_

- [ ] 37. 공개 GitHub 저장소 준비
  - GitHub public 저장소 생성 또는 전환
  - 모든 코드 푸시:
    - src/ (Lambda 코드)
    - template.yaml (SAM 템플릿)
    - docs/ (문서)
    - tests/ (통합 테스트)
  - README.md 최종 검토 (영어)
  - LICENSE 파일 확인 (MIT)
  - .gitignore 확인 (.env, venv/, .aws-sam/)
  - _Requirements: 7.1, 7.4_

- [ ] 38. 해커톤 제출
  - Devpost 제출 양식 작성:
    - Project Title: "AI Branding Chatbot - Bedrock AgentCore Implementation"
    - GitHub URL: https://github.com/{username}/ai-branding-chatbot
    - Demo Video URL: https://youtube.com/watch?v={video_id}
    - Deployed URL: https://{api-id}.execute-api.us-east-1.amazonaws.com/dev
    - Architecture Diagram: docs/architecture.md
    - Project Description (영어, 500자)
    - Technologies Used: AWS Bedrock, AgentCore, Claude 4 Sonnet, SDXL, Lambda, DynamoDB, S3
  - 제출 체크리스트 최종 확인:
    - [ ] ENABLE_FALLBACK=false
    - [ ] Bedrock 모델 가용성 확인
    - [ ] AgentCore Agent ID 설정
    - [ ] IAM 권한 확인
    - [ ] 통합 테스트 통과
    - [ ] 아키텍처 다이어그램 완성
    - [ ] 데모 비디오 업로드
    - [ ] README.md 영어 번역
    - [ ] GitHub 저장소 public
    - [ ] API 엔드포인트 테스트
  - _Requirements: 7.1, 7.4, 7.5, 7.6, 7.7_

## Implementation Notes

### 🎯 통합 전략

**핵심 원칙**: 기존 완성된 Agent 코드를 100% 유지하면서 Bedrock 레이어를 추가합니다.

```
기존 완료된 Agent 구조 (100% 완성)
    ↓
+ Bedrock 클라이언트 모듈 (bedrock_client.py)
+ AgentCore 오케스트레이터 (agentcore_orchestrator.py)
+ Reasoning Engine (reasoning_engine.py)
+ ReasoningStep 데이터 모델
+ Fallback 거버넌스 (환경 변수 기반)
    ↓
해커톤 요구사항 충족 (100%)
```

### 작업 순서 권장사항

1. **Week 1**: Phase 1-2 (Tasks 1-9) - Bedrock 통합 + AgentCore
2. **Week 2**: Phase 3-6 (Tasks 10-26) - Reasoning Engine + Agent 전환 + Fallback + 테스트
3. **Week 3**: Phase 7-10 (Tasks 27-38) - 문서화, 데모, 최적화, 배포

### 병렬 작업 가능 항목

- **Phase 4 (Tasks 14-19)**: 각 Agent Bedrock 전환은 독립적으로 진행 가능
- **Phase 7 (Tasks 27-29)**: 문서 작성은 구현과 병행 가능
- **Phase 9 (Tasks 33-35)**: 모니터링은 배포 전에 완료 필요

### 중요 체크포인트

- **Checkpoint 1** (Week 1 종료): Bedrock 통합 및 AgentCore 동작 확인
  - BedrockClient 모듈 완성
  - AgentCoreOrchestrator 완성
  - Bedrock IAM 정책 추가
  - 통합 테스트 통과 (Tasks 4, 9)
  
- **Checkpoint 2** (Week 2 종료): 전체 워크플로 end-to-end 테스트 통과
  - Reasoning Engine 완성
  - 모든 Agent Bedrock 전환 완료
  - Fallback 거버넌스 구현
  - 통합 테스트 통과 (Task 25)
  
- **Checkpoint 3** (Week 3 중반): 데모 비디오 완성 및 문서 검토
  - 아키텍처 다이어그램 완성
  - Agent 문서 완성
  - README.md 영어 번역
  - 데모 비디오 업로드
  
- **Final Checkpoint** (제출 전): 모든 체크리스트 항목 확인
  - ENABLE_FALLBACK=false 설정
  - Bedrock 모델 가용성 확인
  - 통합 테스트 통과
  - Devpost 제출 완료

### 테스트 전략

- Docker Compose 기반 통합 테스트만 사용 (NO MOCKS)
- 각 Phase 완료 후 해당 통합 테스트 실행
- 선택사항(*) 테스트는 시간이 허용될 경우 작성
- 필수 테스트: Tasks 4, 9, 13, 25 (Bedrock, AgentCore, Reasoning, 전체 워크플로)

### Fallback 전략

- **로컬 개발**: `ENABLE_FALLBACK=true`, `DEV_PROFILE=true` 설정으로 OpenAI/Gemini fallback 활성화
- **제출용 배포**: `ENABLE_FALLBACK=false` 설정으로 Bedrock Only 모드
- **기존 코드 유지**: OpenAI/Gemini 코드는 삭제하지 않고 Fallback으로 유지

### 기존 완료 작업 활용

✅ **인프라**: template.yaml 그대로 사용 (Bedrock IAM 정책만 추가)
✅ **데이터 모델**: models.py 확장 (ReasoningStep 추가)
✅ **BaseAgent**: base_agent.py 확장 (Bedrock 메서드 추가)
✅ **Agent 통신**: agent_communication.py 그대로 사용
✅ **테스트 환경**: Docker Compose 그대로 사용
✅ **개발 스크립트**: scripts/dev.sh 확장
✅ **완료된 Agent**: 비즈니스 로직 100% 유지, Bedrock 레이어만 추가

## Success Criteria

모든 38개 작업이 완료되면:

### 필수 요구사항 (Must Have)
✅ Amazon Bedrock을 주요 LLM 제공자로 사용 (Claude 4 Sonnet, SDXL)
✅ Bedrock AgentCore 최소 2개 primitive 구현 (Tool Use, Memory)
✅ Reasoning LLM 기반 자율 의사결정 시스템 동작 (Chain-of-Thought)
✅ 외부 API, 데이터베이스, 도구 통합 시연 (DynamoDB, S3, Bedrock KB)
✅ 명확한 아키텍처 다이어그램 및 문서 제공 (4개 다이어그램)
✅ SAM을 통한 재현 가능한 배포 (template.yaml)
✅ 3분 데모 비디오 제작 및 업로드 (YouTube)
✅ 공개 GitHub 저장소에 전체 소스 코드 공개
✅ 배포된 프로젝트 URL 제공 (API Gateway)
✅ 모든 통합 테스트 통과 (Docker Compose 기반)

### 기술 실행 (Technical Execution)
✅ BedrockClient 모듈 구현 (invoke_claude, invoke_sdxl, query_knowledge_base)
✅ AgentCoreOrchestrator 구현 (orchestrate_workflow, Tool Use, Memory)
✅ ReasoningEngine 구현 (reason_and_decide, confidence scoring)
✅ ReasoningStep 데이터 모델 추가 (models.py)
✅ 6개 Agent Bedrock 전환 완료 (Product Insight, Reporter, Market Analyst, Signboard, Interior, Report Generator)
✅ Fallback 거버넌스 구현 (환경 변수 기반)
✅ 자율적 오류 복구 시스템 (autonomous_error_recovery)
✅ CloudWatch 대시보드 및 알람 설정

### 문서화 (Documentation)
✅ 아키텍처 다이어그램 4개 (High-level, Workflow, Bedrock Integration, Sequence)
✅ Agent 문서 (I/O 계약, Tool 스키마, Reasoning 예시)
✅ README.md 영어 번역 (배포 가이드, Bedrock 설정)
✅ 데모 스크립트 작성 (3분 타임라인)

### 배포 및 제출 (Deployment & Submission)
✅ ENABLE_FALLBACK=false 설정 (Bedrock Only)
✅ Bedrock 모델 가용성 확인 (Claude, SDXL)
✅ AgentCore Agent ID 설정
✅ IAM 권한 확인 (bedrock:InvokeModel, bedrock-agent-runtime:InvokeAgent)
✅ API 엔드포인트 테스트 (POST /sessions, GET /sessions/{id})
✅ Devpost 제출 완료

해커톤 제출 준비 완료! 🎉
