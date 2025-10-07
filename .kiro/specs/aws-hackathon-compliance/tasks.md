# Implementation Plan - AWS Hackathon Compliance

이 문서는 **기존 AI 브랜딩 챗봇 프로젝트**를 AWS AI Agent Global Hackathon 요구사항에 맞춰 수정하는 통합 구현 계획입니다.

## 📊 현재 프로젝트 상태

### ✅ 완료된 부분 (기존 프로젝트)
- ✅ AWS SAM 인프라 (template.yaml, DynamoDB, S3, Lambda, API Gateway)
- ✅ 데이터 모델 및 검증 로직 (models.py - 95% 완성)
- ✅ BaseAgent 클래스 및 공통 유틸리티
- ✅ Docker Compose 로컬 환경 (DynamoDB Local, MinIO, Chroma)
- ✅ NO MOCKS 통합 테스트 (29개 테스트 통과)
- ✅ Supervisor Agent 기본 구현 (세션 관리)
- ✅ Product Insight Agent 완료 (업종/지역/규모 분석)
- ✅ Reporter Agent 완료 (상호명 생성 알고리즘)
- ✅ Market Analyst Agent 완료 (시장 분석)
- ✅ Signboard Agent 완료 (DALL-E, SDXL, Gemini 병렬 처리)
- ✅ Interior Agent 완료 (인테리어 추천)
- ✅ Report Generator Agent 완료 (HTML/JSON/텍스트 보고서)
- ✅ Streamlit 웹 인터페이스 완료

### ❌ 해커톤 요구사항 미충족 부분
- ❌ Amazon Bedrock을 주요 LLM으로 사용 (현재: OpenAI, Gemini)
- ❌ Bedrock AgentCore 통합 (필수)
- ❌ Reasoning LLM 기반 자율 의사결정 시스템
- ❌ 해커톤 제출 문서 (아키텍처 다이어그램, 데모 비디오)

## Task Overview

- **Total Tasks**: 12개 주요 작업 (기존 완료 작업 제외)
- **Estimated Timeline**: 2-3주
- **Priority**: Bedrock 통합 → AgentCore → Reasoning → Documentation
- **Strategy**: 기존 코드 유지하면서 Bedrock 레이어 추가

## Tasks

### 🎯 Phase 1: Bedrock 통합 기반 구축 (Week 1)

- [ ] 1. Bedrock 통합 기반 구조 구축
  - 기존 AI Provider 구조에 Bedrock 추가
  - Fallback 메커니즘 유지 (개발 환경용)
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 1.1 Bedrock 클라이언트 모듈 구현
  - `src/lambda/shared/bedrock_client.py` 파일 생성
  - `BedrockClient` 클래스 구현 (Claude, SDXL, KB 쿼리 메서드)
  - Exponential backoff를 사용한 재시도 로직 구현
  - 오류 처리 및 로깅 추가
  - 기존 `BaseAgent` 클래스와 통합
  - _Requirements: 1.1, 1.2, 1.7_
  - _기존 코드: src/lambda/shared/base_agent.py 활용_

- [ ] 1.2 Bedrock 환경 설정 및 IAM 정책 추가
  - `template.yaml`에 Bedrock IAM 정책 추가
  - 환경 변수 설정 (모델 ID, 리전, Agent ID 등)
  - `config/bedrock_config.py` 생성 및 설정 관리
  - 기존 환경 설정 파일과 통합 (.env, samconfig.toml)
  - _Requirements: 1.1, 6.5_
  - _기존 코드: template.yaml 수정_

- [ ] 1.3 Bedrock 모델 가용성 검증 스크립트 작성
  - `scripts/verify-bedrock-setup.sh` 생성
  - 모델 목록 조회 및 IAM 권한 확인
  - 배포 전 자동 검증 로직 추가
  - 기존 `scripts/dev.sh`에 통합
  - _Requirements: 1.1, 7.2_
  - _기존 코드: scripts/dev.sh 확장_

- [ ]* 1.4 Bedrock 통합 테스트 작성
  - `tests/integration/test_bedrock_integration.py` 생성
  - Claude 호출, SDXL 이미지 생성, KB 쿼리 테스트
  - 오류 처리 및 재시도 로직 테스트
  - 기존 Docker Compose 환경 활용
  - _Requirements: 1.7, 10.2_
  - _기존 코드: tests/integration/ 구조 활용_

### 🤖 Phase 2: Bedrock AgentCore 통합 (Week 1-2)

- [ ] 2. Bedrock AgentCore 통합
  - 기존 Supervisor Agent에 AgentCore 추가
  - Step Functions와 병행 운영 (Fallback)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 2.1 AgentCore Orchestrator 클래스 구현
  - `src/lambda/agents/supervisor/agentcore_orchestrator.py` 생성
  - `AgentCoreOrchestrator` 클래스 구현
  - Bedrock Agent Runtime API 통합
  - 기존 `SupervisorAgent` 클래스와 통합
  - _Requirements: 2.1, 2.2_
  - _기존 코드: src/lambda/agents/supervisor/index.py 확장_

- [ ] 2.2 Tool Use primitive 구현
  - Agent 간 통신을 위한 Tool Use 스키마 정의
  - `invoke_agent_with_tool()` 메서드 구현
  - Tool 실행 결과 파싱 및 오류 처리
  - 기존 `AgentCommunication` 인터페이스와 통합
  - _Requirements: 2.2, 2.3_
  - _기존 코드: src/lambda/shared/agent_communication.py 활용_

- [ ] 2.3 Memory primitive 구현
  - 워크플로 상태 저장을 위한 Memory 스키마 정의
  - `store_workflow_memory()` 메서드 구현
  - 기존 DynamoDB 세션 관리와 AgentCore Memory 동기화
  - _Requirements: 2.3, 2.5_
  - _기존 코드: src/lambda/shared/session_manager.py 활용_

- [ ] 2.4 Supervisor Agent에 AgentCore 통합
  - `src/lambda/agents/supervisor/index.py` 수정
  - 기존 Step Functions 오케스트레이션 유지
  - AgentCore를 Primary로, Step Functions를 Fallback으로 설정
  - 환경 변수로 모드 전환 가능하게 구현
  - _Requirements: 2.1, 2.6_
  - _기존 코드: 기존 Supervisor 로직 유지_

- [ ]* 2.5 AgentCore 통합 테스트 작성
  - `tests/integration/test_agentcore.py` 생성
  - Tool Use, Memory primitive 테스트
  - 오케스트레이션 전체 플로우 테스트
  - 기존 통합 테스트 환경 활용
  - _Requirements: 2.7, 10.3_
  - _기존 코드: tests/integration/conftest.py 활용_

### 🧠 Phase 3: Reasoning Engine 구현 (Week 2)

- [ ] 3. Reasoning Engine 구현
  - Claude 3.5 Sonnet 기반 자율 의사결정 시스템 구축
  - 기존 Agent 로직에 Reasoning 레이어 추가
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 3.1 Reasoning Engine 클래스 구현
  - `src/lambda/shared/reasoning_engine.py` 생성
  - `ReasoningEngine` 클래스 구현
  - Chain-of-Thought reasoning 로직 추가
  - Confidence scoring 메커니즘 구현
  - Bedrock Claude 3.5 Sonnet 통합
  - _Requirements: 3.1, 3.2, 3.6_
  - _기존 코드: src/lambda/shared/bedrock_client.py 활용_

- [ ] 3.2 Reasoning 데이터 모델 정의
  - `src/lambda/shared/models.py`에 `ReasoningStep` 클래스 추가
  - 기존 `WorkflowSession`에 `reasoningChain` 필드 추가
  - DynamoDB 스키마 업데이트 (기존 테이블 확장)
  - _Requirements: 3.6_
  - _기존 코드: src/lambda/shared/models.py 확장 (95% 완성)_

- [ ] 3.3 각 Agent에 Reasoning 통합
  - 기존 `BaseAgent` 클래스에 `execute_with_reasoning()` 메서드 추가
  - 완료된 Agent들에 reasoning 추가:
    - Product Insight Agent (완료됨)
    - Market Analyst Agent (완료됨)
    - Reporter Agent (완료됨)
    - Signboard Agent (완료됨)
    - Interior Agent (완료됨)
  - 기존 비즈니스 로직 유지하면서 reasoning 레이어만 추가
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - _기존 코드: 각 Agent의 index.py 수정_

- [ ]* 3.4 Reasoning Engine 테스트 작성
  - `tests/integration/test_reasoning.py` 생성
  - 의사결정, confidence scoring, chain 저장 테스트
  - 기존 29개 통합 테스트와 통합
  - _Requirements: 3.7, 10.4_
  - _기존 코드: tests/integration/ 구조 활용_

### 🔄 Phase 4: 각 Agent Bedrock 전환 (Week 2) - 병렬 작업 가능

**참고**: 이 작업들은 독립적으로 진행 가능하며, 기존 완료된 Agent 로직을 유지하면서 Bedrock을 Primary로 추가합니다.

- [ ] 4. 모든 Agent에 Bedrock 통합
  - 기존 OpenAI/Gemini를 Fallback으로 유지
  - Bedrock을 Primary LLM으로 설정
  - 환경 변수로 Fallback 활성화/비활성화
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 3.3, 3.4, 3.5_

- [ ] 4.1 Reporter Agent Bedrock 통합
  - `src/lambda/agents/reporter/index.py` 수정
  - 기존 상호명 생성 로직 유지
  - Bedrock Claude를 Primary로 추가
  - Reasoning Engine 통합
  - _Requirements: 1.2, 3.3_
  - _기존 코드: 완료된 Reporter Agent 확장_

- [ ] 4.2 Market Analyst Agent Bedrock 통합
  - `src/lambda/agents/market-analyst/index.py` 수정
  - 기존 시장 분석 로직 유지
  - Bedrock Claude + Knowledge Base 추가
  - Reasoning Engine 통합
  - _Requirements: 1.3, 3.2, 5.2_
  - _기존 코드: 완료된 Market Analyst Agent 확장_

- [ ] 4.3 Signboard Agent Bedrock SDXL 통합
  - `src/lambda/agents/signboard/index.py` 수정
  - 기존 DALL-E, Gemini 병렬 처리 유지
  - Bedrock SDXL을 3번째 옵션으로 추가
  - 이미지 생성 파라미터 최적화
  - _Requirements: 1.4, 5.3_
  - _기존 코드: 완료된 Signboard Agent 확장_

- [ ] 4.4 Interior Agent Bedrock 통합
  - `src/lambda/agents/interior/index.py` 수정
  - 기존 인테리어 추천 로직 유지
  - Bedrock Claude를 Primary로 추가
  - Reasoning Engine 통합
  - _Requirements: 1.5, 3.4_
  - _기존 코드: 완료된 Interior Agent 확장_

- [ ] 4.5 Report Generator Agent Bedrock 통합
  - `src/lambda/agents/report-generator/index.py` 수정
  - 기존 HTML/JSON/텍스트 생성 로직 유지
  - Bedrock Claude로 인사이트 종합 개선
  - Reasoning Engine 통합
  - _Requirements: 1.5, 3.5_
  - _기존 코드: 완료된 Report Generator Agent 확장_

### ⚙️ Phase 5: Fallback 거버넌스 및 자율 실행 (Week 2)

- [ ] 5. Fallback 거버넌스 구현
  - 환경별 Fallback 제어 로직 추가
  - 제출용 Bedrock Only 모드 구현
  - _Requirements: 1.6, 5.6_

- [ ] 5.1 Fallback 설정 모듈 구현
  - `config/fallback_config.py` 생성
  - `FallbackConfig` 클래스 구현
  - 환경 변수 기반 Fallback 활성화 로직
  - 기존 환경 설정과 통합
  - _Requirements: 1.6_
  - _기존 코드: .env, samconfig.toml 활용_

- [ ] 5.2 각 Agent에 Fallback 로직 추가
  - 기존 `BaseAgent`에 `execute_with_fallback()` 메서드 추가
  - Bedrock 실패 시 OpenAI/Gemini로 fallback (DEV_PROFILE=true 시만)
  - Fallback 사용 시 로깅 및 메트릭 기록
  - _Requirements: 1.6, 5.6_
  - _기존 코드: src/lambda/shared/base_agent.py 확장_

- [ ] 6. 자율적 작업 실행 능력 강화
  - 기존 Supervisor Agent의 자율 의사결정 로직 개선
  - Reasoning Engine 기반 오류 복구 전략 구현
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 6.1 Supervisor Agent 자율 의사결정 로직 구현
  - `src/lambda/agents/supervisor/index.py` 수정
  - Reasoning Engine을 사용한 오류 복구 전략 결정
  - 재시도, 대체 모델, 휴먼 개입 요청 로직 추가
  - 기존 세션 관리 로직과 통합
  - _Requirements: 4.2, 4.5_
  - _기존 코드: 기존 Supervisor 로직 확장_

- [ ] 6.2 워크플로 상태 관리 개선
  - 세션 일시 중지 및 재개 기능 구현
  - 중간 결과 저장 및 복원 로직 추가
  - 기존 DynamoDB 세션 관리 확장
  - _Requirements: 4.4, 4.6_
  - _기존 코드: src/lambda/shared/session_manager.py 확장_

- [ ] 6.3 실시간 상태 업데이트 개선
  - 기존 Streamlit UI의 polling 로직 개선
  - 진행 상황 표시 강화
  - _Requirements: 4.7_
  - _기존 코드: src/streamlit/app.py 수정_

### 🧪 Phase 6: 통합 테스트 (Week 2-3)

- [ ] 7. 통합 테스트 작성
  - 기존 29개 통합 테스트 확장
  - Bedrock 통합 검증
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 7.1 전체 워크플로 통합 테스트
  - `tests/integration/test_hackathon_workflow.py` 생성
  - Bedrock을 사용한 5단계 워크플로 테스트
  - 자율 실행 및 오류 복구 테스트
  - 기존 test_workflow.py와 통합
  - _Requirements: 10.4, 10.7_
  - _기존 코드: tests/integration/test_workflow.py 확장_

- [ ] 7.2 Docker Compose 환경 업데이트
  - 기존 `docker-compose.local.yml` 유지
  - Bedrock 로컬 테스트 가이드 추가
  - 통합 테스트 실행 스크립트 업데이트
  - _Requirements: 10.1_
  - _기존 코드: docker-compose.local.yml, scripts/dev.sh 확장_

### 📚 Phase 7: 문서화 (Week 3)

- [ ] 8. 아키텍처 문서 작성
  - 기존 문서 업데이트
  - Bedrock AgentCore 통합 설명 추가
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 8.1 아키텍처 다이어그램 생성
  - `docs/architecture.md` 생성
  - Bedrock 통합, AgentCore, Reasoning LLM 강조
  - 시퀀스 다이어그램 추가 (Happy Path & Error Path)
  - 기존 다이어그램 업데이트
  - _Requirements: 6.1, 6.2, 6.7_
  - _기존 코드: .kiro/specs/ai-branding-chatbot/*.png 활용_

- [ ] 8.2 Agent 문서 작성
  - `docs/agents.md` 생성
  - 각 Agent의 I/O 계약, Tool 스키마, 모델 사양 문서화
  - Reasoning 예시 및 프롬프트 템플릿 포함
  - _Requirements: 6.3, 6.5_

- [ ] 8.3 배포 가이드 업데이트
  - 기존 README.md 업데이트
  - Bedrock 설정 가이드 추가
  - 해커톤 제출 체크리스트 추가
  - _Requirements: 6.4, 7.2, 7.3, 7.5_
  - _기존 코드: README.md 확장_

### 🎥 Phase 8: 데모 비디오 제작 (Week 3)

- [ ] 9. 데모 비디오 제작
  - 3분 데모 비디오 스크립트 작성 및 녹화
  - YouTube 업로드
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 9.1 데모 스크립트 작성
  - `docs/demo_script.md` 생성
  - 3분 타임라인 작성
  - 주요 토킹 포인트 및 화면 녹화 가이드
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 9.2 데모 비디오 녹화 및 편집
  - 기존 Streamlit UI 시연 녹화
  - Supervisor Agent 및 Reasoning LLM 동작 화면 캡처
  - 생성된 결과물 표시
  - 아키텍처 다이어그램 추가
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 9.3 데모 비디오 업로드
  - YouTube에 공개 업로드
  - 비디오 URL을 README 및 제출 양식에 추가
  - _Requirements: 8.7_

### ⚡ Phase 9: 성능 최적화 및 모니터링 (Week 3)

- [ ] 10. 성능 최적화 및 모니터링
  - 기존 CloudWatch 설정 확장
  - Bedrock 메트릭 추가
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 10.1 CloudWatch 대시보드 생성
  - 기존 `template.yaml`에 CloudWatch Dashboard 리소스 추가
  - Bedrock API 메트릭, 비용 추적, 성능 지표 표시
  - _Requirements: 7.7, 9.6_
  - _기존 코드: template.yaml 확장_

- [ ] 10.2 비용 제한 및 알람 설정
  - `config/cost_limits.py` 생성
  - 이미지 생성 횟수, 해상도, 토큰 수 제한 구현
  - CloudWatch 알람 설정
  - _Requirements: 9.7_

- [ ] 10.3 성능 최적화
  - Lambda 함수 메모리 및 타임아웃 조정
  - Bedrock API 호출 병렬화
  - 기존 DynamoDB 쿼리 최적화 유지
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

### 🚀 Phase 10: 최종 배포 및 제출 (Week 3)

- [ ] 11. 최종 배포 및 제출 준비
  - AWS 계정에 배포
  - 공개 GitHub 저장소 준비
  - 해커톤 제출
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 11.1 프로덕션 배포
  - 기존 SAM 배포 스크립트 사용
  - `sam build && sam deploy --guided` 실행
  - API Gateway 엔드포인트 테스트
  - _Requirements: 7.2, 7.3_
  - _기존 코드: scripts/sam-deploy.sh 활용_

- [ ] 11.2 공개 GitHub 저장소 준비
  - 모든 코드를 GitHub public 저장소에 푸시
  - README.md 최종 검토 및 업데이트
  - LICENSE 파일 확인 (MIT)
  - .gitignore 확인
  - _Requirements: 7.1, 7.4_

- [ ] 11.3 해커톤 제출
  - Devpost에 프로젝트 제출
  - 필수 항목 작성:
    - GitHub 저장소 URL
    - 아키텍처 다이어그램
    - 프로젝트 설명 (영어)
    - 데모 비디오 URL
    - 배포된 프로젝트 URL
  - 제출 체크리스트 최종 확인
  - _Requirements: 7.1, 7.4, 7.5, 7.6, 7.7_

## Implementation Notes

### 🎯 통합 전략

**핵심 원칙**: 기존 완료된 코드를 유지하면서 Bedrock 레이어를 추가합니다.

```
기존 완료된 Agent 구조 (70% 완성)
    ↓
+ Bedrock 클라이언트 모듈
+ AgentCore 오케스트레이터
+ Reasoning Engine
    ↓
해커톤 요구사항 충족 (100%)
```

### 작업 순서 권장사항

1. **Week 1**: Tasks 1-2 (Bedrock 통합 + AgentCore)
2. **Week 2**: Tasks 3-7 (Reasoning Engine + Agent 전환 + 테스트)
3. **Week 3**: Tasks 8-11 (문서화, 데모, 최적화, 배포)

### 병렬 작업 가능 항목

- **Task 4 (4.1-4.5)**: 각 Agent Bedrock 전환은 독립적으로 진행 가능
- **Task 8**: 문서 작성은 구현과 병행 가능
- **Task 10**: 모니터링은 배포 전에 완료 필요

### 중요 체크포인트

- **Checkpoint 1** (Week 1 종료): Bedrock 통합 및 AgentCore 동작 확인
- **Checkpoint 2** (Week 2 종료): 전체 워크플로 end-to-end 테스트 통과 (기존 29개 + 신규)
- **Checkpoint 3** (Week 3 중반): 데모 비디오 완성 및 문서 검토
- **Final Checkpoint** (제출 전): 모든 체크리스트 항목 확인

### 테스트 전략

- 기존 29개 통합 테스트 활용 (Docker Compose 기반)
- 각 주요 작업 완료 후 해당 통합 테스트 실행
- 선택사항(*) 테스트는 시간이 허용될 경우 작성
- 최소한 Task 7.1 (전체 워크플로 테스트)는 필수

### Fallback 전략

- **로컬 개발**: `DEV_PROFILE=true` 설정으로 OpenAI/Gemini fallback 활성화
- **제출용 배포**: `ENABLE_FALLBACK=false` 설정으로 Bedrock Only 모드
- **기존 코드 유지**: OpenAI/Gemini 코드는 삭제하지 않고 Fallback으로 유지

### 기존 완료 작업 활용

✅ **인프라**: template.yaml, samconfig.toml 그대로 사용 (IAM 정책만 추가)
✅ **데이터 모델**: models.py 확장 (ReasoningStep 추가)
✅ **BaseAgent**: base_agent.py 확장 (Bedrock 메서드 추가)
✅ **테스트 환경**: Docker Compose, 통합 테스트 그대로 사용
✅ **개발 스크립트**: scripts/dev.sh 확장
✅ **완료된 Agent**: 비즈니스 로직 유지, Bedrock 레이어만 추가

## Success Criteria

모든 작업이 완료되면:

✅ Amazon Bedrock을 주요 LLM 제공자로 사용
✅ Bedrock AgentCore 최소 1개 primitive 구현
✅ Reasoning LLM 기반 자율 의사결정 시스템 동작
✅ 외부 API, 데이터베이스, 도구 통합 시연
✅ 명확한 아키텍처 다이어그램 및 문서 제공
✅ SAM을 통한 재현 가능한 배포
✅ 3분 데모 비디오 제작 및 업로드
✅ 공개 GitHub 저장소에 전체 소스 코드 공개
✅ 배포된 프로젝트 URL 제공
✅ 모든 통합 테스트 통과

해커톤 제출 준비 완료! 🎉
