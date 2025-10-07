# Implementation Plan

이 문서는 AWS AI Agent Global Hackathon 요구사항을 충족하기 위한 구현 작업 목록입니다. 각 작업은 코드 작성, 수정, 테스트에 초점을 맞추고 있으며, 요구사항 문서의 각 항목과 연결되어 있습니다.

## Task Overview

- **Total Tasks**: 15개 주요 작업
- **Estimated Timeline**: 2-3주
- **Priority**: Bedrock 통합 → AgentCore → Reasoning → Documentation

## Tasks

- [ ] 1. Bedrock 통합 기반 구조 구축
  - Bedrock 클라이언트 모듈 생성 및 기본 API 호출 구현
  - 환경 설정 및 IAM 권한 구성
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 1.1 Bedrock 클라이언트 모듈 구현
  - `src/lambda/shared/bedrock_client.py` 파일 생성
  - `BedrockClient` 클래스 구현 (Claude, SDXL, KB 쿼리 메서드)
  - Exponential backoff를 사용한 재시도 로직 구현
  - 오류 처리 및 로깅 추가
  - _Requirements: 1.1, 1.2, 1.7_

- [ ] 1.2 Bedrock 환경 설정 및 IAM 정책 추가
  - `template.yaml`에 Bedrock IAM 정책 추가
  - 환경 변수 설정 (모델 ID, 리전, Agent ID 등)
  - `config/bedrock_config.py` 생성 및 설정 관리
  - _Requirements: 1.1, 6.5_

- [ ] 1.3 Bedrock 모델 가용성 검증 스크립트 작성
  - `scripts/verify-bedrock-setup.sh` 생성
  - 모델 목록 조회 및 IAM 권한 확인
  - 배포 전 자동 검증 로직 추가
  - _Requirements: 1.1, 7.2_

- [ ]* 1.4 Bedrock 통합 테스트 작성
  - `tests/integration/test_bedrock_integration.py` 생성
  - Claude 호출, SDXL 이미지 생성, KB 쿼리 테스트
  - 오류 처리 및 재시도 로직 테스트
  - _Requirements: 1.7, 10.2_

- [ ] 2. Bedrock AgentCore 통합
  - Supervisor Agent에 AgentCore 오케스트레이션 추가
  - Tool Use, Memory primitive 구현
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 2.1 AgentCore Orchestrator 클래스 구현
  - `src/lambda/agents/supervisor/agentcore_orchestrator.py` 생성
  - `AgentCoreOrchestrator` 클래스 구현
  - Bedrock Agent Runtime API 통합
  - _Requirements: 2.1, 2.2_

- [ ] 2.2 Tool Use primitive 구현
  - Agent 간 통신을 위한 Tool Use 스키마 정의
  - `invoke_agent_with_tool()` 메서드 구현
  - Tool 실행 결과 파싱 및 오류 처리
  - _Requirements: 2.2, 2.3_

- [ ] 2.3 Memory primitive 구현
  - 워크플로 상태 저장을 위한 Memory 스키마 정의
  - `store_workflow_memory()` 메서드 구현
  - DynamoDB와 AgentCore Memory 동기화
  - _Requirements: 2.3, 2.5_

- [ ] 2.4 Supervisor Agent에 AgentCore 통합
  - `src/lambda/agents/supervisor/index.py` 수정
  - 기존 Step Functions 오케스트레이션을 AgentCore로 전환
  - Fallback 메커니즘 구현 (AgentCore 실패 시 Step Functions 사용)
  - _Requirements: 2.1, 2.6_

- [ ]* 2.5 AgentCore 통합 테스트 작성
  - `tests/integration/test_agentcore.py` 생성
  - Tool Use, Memory primitive 테스트
  - 오케스트레이션 전체 플로우 테스트
  - _Requirements: 2.7, 10.3_

- [ ] 3. Reasoning Engine 구현
  - Claude 3.5 Sonnet 기반 자율 의사결정 시스템 구축
  - Reasoning chain 저장 및 설명 생성
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 3.1 Reasoning Engine 클래스 구현
  - `src/lambda/shared/reasoning_engine.py` 생성
  - `ReasoningEngine` 클래스 구현
  - Chain-of-Thought reasoning 로직 추가
  - Confidence scoring 메커니즘 구현
  - _Requirements: 3.1, 3.2, 3.6_

- [ ] 3.2 Reasoning 데이터 모델 정의
  - `src/lambda/shared/models.py`에 `ReasoningStep` 클래스 추가
  - `WorkflowSession`에 `reasoningChain` 필드 추가
  - DynamoDB 스키마 업데이트
  - _Requirements: 3.6_

- [ ] 3.3 각 Agent에 Reasoning 통합
  - `BaseAgent` 클래스에 `execute_with_reasoning()` 메서드 추가
  - Product Insight, Market Analyst, Reporter Agent에 reasoning 추가
  - Signboard, Interior Agent에 reasoning 추가
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 3.4 Reasoning Engine 테스트 작성
  - `tests/integration/test_reasoning.py` 생성
  - 의사결정, confidence scoring, chain 저장 테스트
  - _Requirements: 3.7, 10.4_

- [ ] 4. Reporter Agent Bedrock 전환
  - OpenAI → Bedrock Claude로 상호명 생성 로직 전환
  - Reasoning LLM을 사용한 이름 평가 추가
  - _Requirements: 1.2, 3.3_

- [ ] 4.1 Reporter Agent Bedrock 통합
  - `src/lambda/agents/reporter/index.py` 수정
  - OpenAI API 호출을 Bedrock Claude로 교체
  - Reasoning Engine을 사용한 이름 평가 로직 추가
  - Fallback 메커니즘 유지 (DEV_PROFILE=true 시)
  - _Requirements: 1.2, 3.3_

- [ ] 5. Market Analyst Agent Bedrock 전환
  - Bedrock Claude + Knowledge Base 통합
  - 시장 분석 및 트렌드 분석 로직 개선
  - _Requirements: 1.3, 3.2, 5.2_

- [ ] 5.1 Market Analyst Agent Bedrock 통합
  - `src/lambda/agents/market-analyst/index.py` 수정
  - Bedrock Claude로 시장 분석 로직 전환
  - Bedrock Knowledge Base 쿼리 추가 (DynamoDB fallback 유지)
  - Reasoning Engine을 사용한 트렌드 분석
  - _Requirements: 1.3, 3.2, 5.2_

- [ ] 6. Signboard Agent Bedrock SDXL 전환
  - DALL-E, Gemini → Bedrock SDXL로 이미지 생성 전환
  - 병렬 처리 유지 (3개 이미지 동시 생성)
  - _Requirements: 1.4, 5.3_

- [ ] 6.1 Signboard Agent Bedrock SDXL 통합
  - `src/lambda/agents/signboard/index.py` 수정
  - DALL-E, Gemini API 호출을 Bedrock SDXL로 교체
  - 이미지 생성 파라미터 최적화 (1024x1024, cost limits)
  - Fallback 메커니즘 유지 (DEV_PROFILE=true 시)
  - _Requirements: 1.4, 5.3_

- [ ] 7. Interior Agent Bedrock 전환
  - Bedrock Claude를 사용한 인테리어 추천 로직 개선
  - Reasoning LLM으로 디자인 평가
  - _Requirements: 1.5, 3.4_

- [ ] 7.1 Interior Agent Bedrock 통합
  - `src/lambda/agents/interior/index.py` 수정
  - Bedrock Claude로 인테리어 추천 로직 전환
  - Reasoning Engine을 사용한 디자인 평가
  - _Requirements: 1.5, 3.4_

- [ ] 8. Report Generator Agent Bedrock 전환
  - Bedrock Claude를 사용한 리포트 생성 개선
  - Reasoning LLM으로 인사이트 종합
  - _Requirements: 1.5, 3.5_

- [ ] 8.1 Report Generator Agent Bedrock 통합
  - `src/lambda/agents/report-generator/index.py` 수정
  - Bedrock Claude로 리포트 생성 로직 전환
  - Reasoning Engine을 사용한 인사이트 종합
  - _Requirements: 1.5, 3.5_

- [ ] 9. Fallback 거버넌스 구현
  - 환경별 Fallback 제어 로직 추가
  - 제출용 Bedrock Only 모드 구현
  - _Requirements: 1.6, 5.6_

- [ ] 9.1 Fallback 설정 모듈 구현
  - `config/fallback_config.py` 생성
  - `FallbackConfig` 클래스 구현
  - 환경 변수 기반 Fallback 활성화 로직
  - _Requirements: 1.6_

- [ ] 9.2 각 Agent에 Fallback 로직 추가
  - `BaseAgent`에 `execute_with_fallback()` 메서드 추가
  - Bedrock 실패 시 OpenAI/Gemini로 fallback (DEV_PROFILE=true 시만)
  - Fallback 사용 시 로깅 및 메트릭 기록
  - _Requirements: 1.6, 5.6_

- [ ] 10. 자율적 작업 실행 능력 강화
  - Supervisor Agent의 자율 의사결정 로직 개선
  - 오류 복구 전략 구현
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 10.1 Supervisor Agent 자율 의사결정 로직 구현
  - `src/lambda/agents/supervisor/index.py` 수정
  - Reasoning Engine을 사용한 오류 복구 전략 결정
  - 재시도, 대체 모델, 휴먼 개입 요청 로직 추가
  - _Requirements: 4.2, 4.5_

- [ ] 10.2 워크플로 상태 관리 개선
  - 세션 일시 중지 및 재개 기능 구현
  - 중간 결과 저장 및 복원 로직 추가
  - _Requirements: 4.4, 4.6_

- [ ] 10.3 실시간 상태 업데이트 구현
  - WebSocket 또는 polling 기반 상태 업데이트
  - Streamlit UI에 진행 상황 표시
  - _Requirements: 4.7_

- [ ] 11. 통합 테스트 작성
  - 전체 워크플로 end-to-end 테스트
  - Bedrock 통합 검증
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 11.1 전체 워크플로 통합 테스트
  - `tests/integration/test_hackathon_workflow.py` 생성
  - Bedrock을 사용한 5단계 워크플로 테스트
  - 자율 실행 및 오류 복구 테스트
  - _Requirements: 10.4, 10.7_

- [ ] 11.2 Docker Compose 환경 업데이트
  - `docker-compose.local.yml` 수정
  - Bedrock 로컬 테스트를 위한 mock 서비스 추가 (선택사항)
  - 통합 테스트 실행 스크립트 업데이트
  - _Requirements: 10.1_

- [ ] 12. 아키텍처 문서 작성
  - 상세 아키텍처 다이어그램 생성
  - Bedrock AgentCore 통합 설명
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 12.1 아키텍처 다이어그램 생성
  - `docs/architecture.md` 생성
  - Mermaid 또는 draw.io로 다이어그램 작성
  - Bedrock 통합, AgentCore, Reasoning LLM 강조
  - 시퀀스 다이어그램 추가 (Happy Path & Error Path)
  - _Requirements: 6.1, 6.2, 6.7_

- [ ] 12.2 Agent 문서 작성
  - `docs/agents.md` 생성
  - 각 Agent의 I/O 계약, Tool 스키마, 모델 사양 문서화
  - Reasoning 예시 및 프롬프트 템플릿 포함
  - _Requirements: 6.3, 6.5_

- [ ] 12.3 배포 가이드 작성
  - README.md 업데이트
  - SAM 배포 단계별 가이드 추가
  - 환경 변수 설정 및 IAM 권한 설명
  - 해커톤 제출 체크리스트 추가
  - _Requirements: 6.4, 7.2, 7.3, 7.5_

- [ ] 13. 데모 비디오 제작
  - 3분 데모 비디오 스크립트 작성 및 녹화
  - YouTube 업로드
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 13.1 데모 스크립트 작성
  - `docs/demo_script.md` 생성
  - 3분 타임라인 작성 (문제 소개, 솔루션, 기술 실행, 결과, 아키텍처)
  - 주요 토킹 포인트 및 화면 녹화 가이드
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 13.2 데모 비디오 녹화 및 편집
  - Streamlit UI 시연 녹화
  - Supervisor Agent 및 Reasoning LLM 동작 화면 캡처
  - 생성된 결과물 (상호명, 간판, 인테리어, PDF) 표시
  - 아키텍처 다이어그램 및 기술 설명 추가
  - _Requirements: 8.3, 8.4, 8.5_

- [ ] 13.3 데모 비디오 업로드
  - YouTube에 공개 업로드
  - 비디오 URL을 README 및 제출 양식에 추가
  - _Requirements: 8.7_

- [ ] 14. 성능 최적화 및 모니터링
  - CloudWatch 대시보드 구성
  - 비용 모니터링 및 알람 설정
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 14.1 CloudWatch 대시보드 생성
  - `template.yaml`에 CloudWatch Dashboard 리소스 추가
  - Bedrock API 메트릭, 비용 추적, 성능 지표 표시
  - _Requirements: 7.7, 9.6_

- [ ] 14.2 비용 제한 및 알람 설정
  - `config/cost_limits.py` 생성
  - 이미지 생성 횟수, 해상도, 토큰 수 제한 구현
  - CloudWatch 알람 설정 (비용 임계값 초과 시)
  - _Requirements: 9.7_

- [ ] 14.3 성능 최적화
  - Lambda 함수 메모리 및 타임아웃 조정
  - Bedrock API 호출 병렬화
  - DynamoDB 쿼리 최적화
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 15. 최종 배포 및 제출 준비
  - AWS 계정에 배포
  - 공개 GitHub 저장소 준비
  - 해커톤 제출
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 15.1 프로덕션 배포
  - `sam build` 실행 및 빌드 검증
  - `sam deploy --guided` 실행 및 스택 생성
  - API Gateway 엔드포인트 테스트
  - _Requirements: 7.2, 7.3_

- [ ] 15.2 공개 GitHub 저장소 준비
  - 모든 코드를 GitHub public 저장소에 푸시
  - README.md 최종 검토 및 업데이트
  - LICENSE 파일 추가 (MIT)
  - .gitignore 확인 (API 키, 민감 정보 제외)
  - _Requirements: 7.1, 7.4_

- [ ] 15.3 해커톤 제출
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

### 작업 순서 권장사항

1. **Week 1**: Tasks 1-6 (Bedrock 통합 및 AgentCore)
2. **Week 2**: Tasks 7-11 (Reasoning Engine 및 통합 테스트)
3. **Week 3**: Tasks 12-15 (문서화, 데모, 배포)

### 병렬 작업 가능 항목

- Task 4, 5, 6, 7, 8 (각 Agent Bedrock 전환)은 독립적으로 진행 가능
- Task 12 (문서 작성)는 구현과 병행 가능
- Task 14 (모니터링)는 배포 전에 완료 필요

### 중요 체크포인트

- **Checkpoint 1** (Week 1 종료): Bedrock 통합 및 AgentCore 동작 확인
- **Checkpoint 2** (Week 2 종료): 전체 워크플로 end-to-end 테스트 통과
- **Checkpoint 3** (Week 3 중반): 데모 비디오 완성 및 문서 검토
- **Final Checkpoint** (제출 전): 모든 체크리스트 항목 확인

### 테스트 전략

- 각 주요 작업 완료 후 해당 통합 테스트 실행
- 선택사항(*) 테스트는 시간이 허용될 경우 작성
- 최소한 Task 11.1 (전체 워크플로 테스트)는 필수

### Fallback 전략

- 로컬 개발: `DEV_PROFILE=true` 설정으로 OpenAI/Gemini fallback 활성화
- 제출용 배포: `ENABLE_FALLBACK=false` 설정으로 Bedrock Only 모드

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
