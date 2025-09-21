# 구현 계획

## 개요

이 구현 계획은 AI 브랜딩 챗봇의 에이전트 기반 아키텍처 설계를 바탕으로 단계별 코딩 태스크를 정의합니다. 각 태스크는 테스트 주도 개발 방식으로 진행되며, Supervisor Agent를 중심으로 한 6개 전문 Agent를 점진적으로 구축하여 최종적으로 완전한 서버리스 에이전트 시스템을 완성합니다.

## 구현 태스크

- [x] 1. 프로젝트 구조 및 기본 설정
  - 프로젝트 디렉토리 구조 생성
  - AWS CDK 또는 SAM 템플릿 초기화
  - 환경별 설정 파일 구성 (local/dev)
  - _요구사항: 1.1, 7.1_

- [x] 2. 데이터 모델 및 DynamoDB 설정
  - [x] 2.1 DynamoDB 테이블 스키마 정의
    - WorkflowSessions 테이블 CDK 리소스 생성
    - TTL 설정 및 인덱스 구성
    - 로컬 개발용 DynamoDB Local 설정
    - _요구사항: 1.1, 7.1_

  - [x] 2.2 세션 데이터 모델 구현
    - TypeScript/Python 데이터 모델 클래스 작성
    - 세션 상태 검증 로직 구현
    - 단위 테스트 작성 (세션 생성, 업데이트, 만료)
    - _요구사항: 1.2, 1.3_

- [x] 3. S3 버킷 및 저장소 설정
  - [x] 3.1 S3 버킷 구조 구현
    - 세션별 디렉토리 구조 생성
    - 폴백 이미지 저장소 설정
    - 로컬 개발용 MinIO 설정
    - _요구사항: 4.3, 5.3, 6.3_

  - [x] 3.2 파일 업로드/다운로드 유틸리티
    - 이미지 업로드 처리 함수 구현
    - presigned URL 생성 로직
    - 파일 검증 및 보안 처리
    - _요구사항: 2.3, 6.4_

- [x] 4. Supervisor Agent 및 에이전트 기반 구조
  - [x] 4.1 공통 Agent 레이어 구현
    - 에이전트 단위 로깅 (agent, tool, latency_ms)
    - Agent 간 통신 인터페이스
    - AWS SDK 클라이언트 초기화
    - 환경 변수 관리 헬퍼
    - _요구사항: 8.1, 9.1, 10.1_

  - [x] 4.2 Supervisor Agent Lambda 함수
    - 전체 워크플로 상태 감시 로직
    - Step Functions 실행 상태 추적
    - GET /status/{id} 엔드포인트 구현
    - 실패 시 재시도/폴백 트리거 메커니즘
    - 에이전트 간 조정 및 통제 로직
    - _요구사항: 1.1, 1.2, 1.4, Supervisor 역할_

  - [x] 4.3 기본 세션 관리 기능
    - POST /sessions 엔드포인트 구현
    - GET /sessions/{id} 엔드포인트 구현
    - 세션 상태 업데이트 로직
    - 단위 테스트 및 통합 테스트
    - _요구사항: 1.1, 1.2, 1.4_

- [x] 5. Product Insight & Market Analyst Agent 구현
  - [x] 5.1 Product Insight Agent Lambda 함수
    - 업종/지역/규모 기반 비즈니스 분석 로직
    - Bedrock Knowledge Base 조회 구현
    - KB 지연/실패 시 캐시 데이터 활용
    - 5초 내 응답 최적화
    - 에이전트 단위 로그 기록
    - _요구사항: 2.1, 2.2, 2.6, 2.7_

  - [x] 5.2 Market Analyst Agent Lambda 함수
    - 시장 동향 및 경쟁사 분석 로직
    - Bedrock KB에서 관련 데이터 검색
    - Product Insight와 협력하여 종합 분석
    - 에이전트 단위 로그 기록
    - _요구사항: 2.1, 2.6, 2.7_

  - [x] 5.3 Knowledge Base 추상화 구현
    - KnowledgeBase 인터페이스 정의
    - BedrockKnowledgeBase 구현체 (개발용)
    - ChromaKnowledgeBase 구현체 (로컬용)
    - KB 지연/실패 시 폴백 처리
    - 환경별 자동 전환 로직
    - _요구사항: 7.1, 7.2, 2.6, 2.7_

- [x] 6. Reporter Agent 구현
  - [x] 6.1 Reporter Agent Lambda 함수
    - 3개 상호명 후보 생성 로직
    - 중복 회피 알고리즘 구현
    - 발음/검색 점수 산출 로직
    - 에이전트 단위 로그 기록
    - _요구사항: 3.1, 3.2, 3.3_

  - [x] 6.2 재생성 제한 및 상태 관리
    - 재생성 횟수 추적 및 제한 (최대 3회)
    - 세션 상태 업데이트
    - Supervisor Agent와 상태 동기화
    - 오류 처리 및 사용자 메시지
    - _요구사항: 3.4, 3.5_

- [ ] 7. AI Provider 추상화 계층
  - [ ] 7.1 AI Provider 인터페이스 구현
    - 공통 AI Provider 인터페이스 정의
    - 이미지 생성 메서드 표준화
    - 오류 처리 및 재시도 로직
    - _요구사항: 4.1, 5.1, 8.4_

  - [ ] 7.2 개별 AI Provider 구현
    - DALLEProvider (OpenAI API 연동)
    - SDXLProvider (Bedrock 연동)
    - GeminiProvider (Google API 연동)
    - 각 Provider별 단위 테스트
    - _요구사항: 4.1, 5.1_

- [ ] 8. Signboard & Interior Agent 구현
  - [ ] 8.1 Signboard Agent Lambda 함수
    - DALL-E, SDXL, Gemini 병렬 호출 로직
    - Step Functions Express 트리거 구현
    - 30초 타임아웃 처리
    - 폴백 이미지 처리 로직
    - 에이전트 단위 로그 기록
    - _요구사항: 4.1, 4.2, 4.3, 4.5_

  - [ ] 8.2 Interior Agent Lambda 함수
    - 간판 스타일 기반 인테리어 생성
    - 병렬 AI 모델 호출 구현
    - 예산/팔레트 메타데이터 포함
    - 에이전트 단위 로그 기록
    - _요구사항: 5.1, 5.2, 5.3, 5.5_

- [ ] 9. Step Functions 워크플로 + Supervisor 통합
  - [ ] 9.1 Express Workflow with Supervisor 감시
    - 병렬 이미지 생성 상태머신 작성
    - Supervisor Agent 실행 상태 모니터링 통합
    - 3개 AI Provider 병렬 실행 구성
    - 실패 시 Supervisor 폴백 트리거
    - 타임아웃 및 오류 처리 설정
    - _요구사항: 4.1, 4.2, 5.1, 5.2, Supervisor 감시_

  - [ ] 9.2 Standard Workflow with Supervisor 제어
    - 사용자 선택 대기 상태머신 작성
    - Supervisor Agent 대기 상태 추적
    - 상태 유지 및 재개 로직
    - 워크플로 제어 메커니즘
    - _요구사항: 4.4, 5.4, Supervisor 제어_

- [ ] 10. Report Generator Agent 구현
  - [ ] 10.1 Report Generator Agent Lambda 함수
    - Lambda 컨테이너 이미지 설정
    - PDF 템플릿 및 생성 로직
    - 모든 선택 사항 포함 로직
    - 에이전트 단위 로그 기록
    - _요구사항: 6.1, 6.2_

  - [ ] 10.2 보고서 다운로드 API
    - GET /report/url 엔드포인트 구현
    - presigned URL 생성 (10분 제한)
    - 보고서 상태 확인 로직
    - _요구사항: 6.4, 6.5_

- [ ] 11. Agent 간 통신 및 조정 시스템
  - [ ] 11.1 Agent Communication 인터페이스
    - Agent 간 메시지 전송 프로토콜
    - Supervisor Agent 상태 브로드캐스트
    - 에이전트 요청/응답 처리
    - 통신 로그 및 추적
    - _요구사항: Agent 간 통신_

  - [ ] 11.2 Workflow 상태 동기화
    - 전체 워크플로 상태 관리
    - Agent별 실행 상태 추적
    - 실패 시 복구 메커니즘
    - 상태 일관성 보장
    - _요구사항: Supervisor 제어_

- [ ] 12. API Gateway 설정 및 Agent 통합
  - [ ] 12.1 HTTP API 구성
    - 모든 Agent 엔드포인트 라우팅 설정
    - /status/{id} Supervisor Agent 엔드포인트 추가
    - CORS 설정 및 보안 헤더
    - 요청/응답 변환 설정
    - _요구사항: 모든 API 엔드포인트, /status/{id}_

  - [ ] 12.2 Agent별 인증 및 권한 설정
    - 선택적 Cognito 인증 구성
    - Agent별 IAM 역할 및 정책 설정
    - 에이전트별 Lambda 분리 배포 권한
    - 최소 권한 원칙 적용
    - _요구사항: 9.1, 9.2, 9.4, 에이전트별 분리 배포_

- [ ] 13. Streamlit 프론트엔드 + Agent 통합
  - [ ] 13.1 Agent 기반 UI 구조 구현
    - 5단계 워크플로 UI 레이아웃
    - Supervisor Agent를 통한 전체 워크플로 상태 조회
    - 에이전트별 실행 상태 표시
    - 진행률 표시 컴포넌트
    - _요구사항: 모든 사용자 인터페이스, Agent 상태 표시_

  - [ ] 13.2 Supervisor Agent API 연동
    - Supervisor Agent API 호출 로직
    - /status/{id} 엔드포인트 활용
    - 세션 폴링 및 실시간 업데이트
    - 에이전트별 오류 처리 및 사용자 피드백
    - _요구사항: 8.5, Supervisor 통합_

- [ ] 14. 에이전트 단위 모니터링 및 로깅 구현
  - [ ] 14.1 에이전트 단위 구조화 로깅 설정
    - 모든 Agent Lambda 함수에 로깅 추가
    - agent, tool, latency_ms 포함 로그 구조
    - trace_id, session_id 추가
    - CloudWatch Logs 그룹 설정
    - _요구사항: 10.1, 10.5, 에이전트 단위 로그_

  - [ ] 14.2 Agent 단위 메트릭 및 알람 구성
    - CloudWatch 대시보드에서 Agent 단위 성능/실패율 추적
    - 에이전트별 응답 시간 및 오류율 알람
    - Supervisor Agent 감시 현황 대시보드
    - Knowledge Base 조회 성능 추적
    - SNS 알림 설정
    - _요구사항: 10.2, 10.4, Agent 단위 추적_

- [ ] 15. 환경별 Agent 배포 및 테스트
  - [ ] 15.1 로컬 개발 환경 Agent 설정
    - DynamoDB Local 및 MinIO 설정
    - Chroma Knowledge Base 구성
    - 로컬 Agent 테스트 스크립트 작성
    - Agent 간 통신 로컬 테스트
    - _요구사항: 7.1, 7.4_

  - [ ] 15.2 개발 환경 Agent 분리 배포
    - 에이전트별 Lambda 분리 배포 스크립트
    - Bedrock Knowledge Base 설정
    - Supervisor Agent 우선 배포
    - 환경별 Agent 설정 검증
    - _요구사항: 7.2, 7.4, 에이전트별 분리 배포_

- [ ] 16. Docker Compose 기반 통합 테스트 구현
  - [x] 16.1 Docker Compose Manager 구현
    - docker-compose.local.yml 서비스 자동 시작/중지 클래스 작성
    - DynamoDB Local, MinIO, Chroma 헬스체크 로직 구현
    - Docker 가용성 확인 및 graceful skip 처리
    - 포트 충돌 감지 및 해결 가이드 제공
    - pytest fixture로 서비스 라이프사이클 관리
    - _요구사항: 통합 테스트 1, 7_

  - [ ] 16.2 Test Environment Setup 구현
    - DynamoDB Local에 실제 테이블 자동 생성 로직
    - MinIO에 버킷 및 폴더 구조 자동 설정
    - Chroma에 테스트용 벡터 컬렉션 생성
    - 테스트 데이터 팩토리 및 클린업 로직
    - 환경별 설정 자동 전환 (local 환경 강제)
    - _요구사항: 통합 테스트 2, 3_

  - [ ] 16.3 전체 워크플로 통합 테스트 구현
    - 실제 BusinessInfo로 세션 생성부터 PDF 생성까지 end-to-end 테스트
    - 각 단계별 DynamoDB 세션 상태 검증
    - MinIO 파일 업로드/다운로드 실제 동작 확인
    - Agent 실행 로그 (agent, tool, latency_ms) 검증
    - Supervisor Agent 워크플로 모니터링 테스트
    - _요구사항: 통합 테스트 2, 3_

  - [ ] 16.4 Agent 통신 및 오류 처리 테스트
    - Agent 간 통신 및 Supervisor 조정 실제 동작 테스트
    - AI Provider 실패 시 폴백 이미지 사용 검증
    - 네트워크 타임아웃 및 서비스 장애 시나리오 테스트
    - 데이터 일관성 및 세션 TTL 동작 확인
    - 동시 세션 처리 시 데이터 격리 검증
    - _요구사항: 통합 테스트 4, 6_

  - [ ] 16.5 CI/CD 통합 및 성능 최적화
    - GitHub Actions에서 Docker-in-Docker 환경 설정
    - 테스트 병렬 실행을 위한 독립적 세션 ID 사용
    - 전체 테스트 5분 내 완료 최적화
    - 실패 시 로그 및 데이터 아티팩트 수집
    - 메모리/CPU 제약 환경에서의 안정성 확보
    - _요구사항: 통합 테스트 4, 5_

- [ ] 17. 선택 확장 기능 구현 (옵션)
  - [ ] 17.1 에이전트 기반 확장 고도화
    - Product/Market/Reporter/Sign/Interior Agent 독립 실행 강화
    - Supervisor Agent 전체 워크플로 통제 고도화
    - kb.search, name.score, image.generate 툴 구현
    - 샌드박스 모드 보안 설정
    - 기존 Lambda 워크플로와 교체 가능 구조
    - _요구사항: 에이전트 기반 확장_

  - [ ] 17.2 Slack 인터페이스 + Agent 통합
    - Slack Events API → Supervisor Agent 연동
    - /brand analyze, /brand name, /brand signboard, /brand interior, /brand report, /brand status 명령 구현
    - 에이전트 로그(agent, tool, latency) 요약을 Slack 채널로 실시간 전송
    - Supervisor Agent가 Slack에서 직접 상태 질의(/brand status)에 응답
    - 비동기 작업 결과를 DM으로 전송
    - _요구사항: Slack 인터페이스 확장, Agent 통합_

  - [ ] 17.3 환경변수 기반 Agent 기능 토글
    - ENABLE_AGENT_MODE, ENABLE_SLACK 환경변수 설정
    - Agent Lambda/App Runner/Step Functions 환경변수 주입
    - 런타임 Agent 분기 처리 로직 구현
    - 기본 Lambda와 Agent 모드 통합 코드 작성
    - _요구사항: 확장 기능 선택적 활성화_

## 구현 순서 및 우선순위

**Phase 1 (핵심 인프라 + Supervisor)**: 태스크 1-4
**Phase 2 (분석 Agent)**: 태스크 5-6  
**Phase 3 (AI Agent + 워크플로)**: 태스크 7-10
**Phase 4 (Agent 통신 + API 통합)**: 태스크 11-13
**Phase 5 (모니터링 + 배포)**: 태스크 14-15
**Phase 6 (Docker 통합 테스트)**: 태스크 16 ⭐ **핵심 검증 단계**
**Phase 7 (Agent 확장)**: 태스크 17 (선택사항)

## 통합 테스트 우선순위

Docker Compose 기반 통합 테스트(태스크 16)는 **전체 시스템 검증의 핵심**으로, 다음과 같은 이유로 중요합니다:

- **실제 환경 검증**: 단위 테스트로는 확인할 수 없는 서비스 간 실제 연동 검증
- **Agent 협업 확인**: Supervisor Agent와 각 전문 Agent 간의 실제 통신 및 조정 검증  
- **데이터 플로우 검증**: DynamoDB → MinIO → Chroma 간 실제 데이터 흐름 확인
- **오류 복구 검증**: 실제 서비스 장애 시나리오에서의 폴백 메커니즘 동작 확인
- **성능 검증**: 실제 Docker 환경에서의 응답 시간 및 리소스 사용량 측정

## 에이전트 기반 아키텍처 구현 전략

### Agent 우선순위 및 의존성

1. **Supervisor Agent** (최우선): 전체 워크플로 감시 및 제어
2. **Product Insight + Market Analyst Agent**: 비즈니스 분석 담당
3. **Reporter Agent**: 상호명 제안 담당
4. **Signboard + Interior Agent**: 이미지 생성 담당
5. **Report Generator Agent**: PDF 생성 담당

### 환경변수 기반 Agent 모드 토글 전략

에이전트 기반 확장 기능은 환경변수를 통해 런타임에 활성화/비활성화할 수 있도록 구현합니다:

```python
import os

ENABLE_AGENT_MODE = os.getenv("ENABLE_AGENT_MODE", "false").lower() == "true"
ENABLE_SLACK = os.getenv("ENABLE_SLACK", "false").lower() == "true"

def handle_request(event):
    if ENABLE_AGENT_MODE:
        return run_agent_workflow(event)
    elif ENABLE_SLACK:
        return run_slack_agent_interface(event)
    else:
        return run_default_lambda(event)

def run_agent_workflow(event):
    # Supervisor Agent가 적절한 Agent로 라우팅
    supervisor = SupervisorAgent()
    return supervisor.route_to_agent(event)
```

### Agent 통신 패턴

```python
class AgentCommunication:
    def send_to_supervisor(self, agent_id: str, status: str, result: Any):
        # Supervisor Agent로 상태 전송
        
    def request_from_agent(self, target_agent: str, request: AgentRequest):
        # 다른 Agent에게 요청
        
    def broadcast_status(self, workflow_status: WorkflowStatus):
        # 전체 워크플로 상태 브로드캐스트
```

**장점**:
- Agent별 독립적 확장 및 배포
- Supervisor를 통한 중앙 집중식 제어
- 장애 격리 및 복구 메커니즘
- 에이전트 단위 모니터링 및 로깅

**고려사항**:
- Agent 간 통신 오버헤드
- Supervisor Agent 단일 장애점 위험 (HA 구성 필요)
- 복잡한 상태 동기화

각 태스크는 이전 태스크의 완료를 전제로 하며, Agent 단위 테스트와 통합 테스트를 포함하여 안정적인 점진적 개발을 보장합니다.