# AI 브랜딩 챗봇 구현 계획

## 개요

현재 **인프라와 기본 구조는 70% 완성**되어 있으며, **핵심 AI 에이전트 비즈니스 로직 구현**에 집중해야 합니다. 

**완성된 부분**:
- ✅ AWS SAM 템플릿 및 인프라 (template.yaml)
- ✅ 데이터 모델 및 검증 로직 (models.py)
- ✅ BaseAgent 클래스 및 공통 유틸리티
- ✅ Docker Compose 로컬 환경
- ✅ NO MOCKS 통합 테스트 (29개 테스트)
- ✅ Supervisor Agent 기본 구현
- ✅ **HTML 브랜딩 보고서 생성 시스템** (PDF 폰트 문제 완전 해결)

**구현 필요 부분**:
- ❌ AI 에이전트 비즈니스 로직 (현재 Mock 응답만)
- ❌ AI 모델 연동 (OpenAI, Stability AI, Google Gemini)
- ❌ Streamlit 웹 인터페이스
- ✅ **Report Generator Agent 완료** (HTML/JSON/텍스트 다중 형식)

## 우선순위별 구현 태스크

### 🎯 Phase 1: 핵심 AI 에이전트 구현 (2-3주) - **즉시 시작 가능**

- [x] 1. Product Insight Agent 비즈니스 로직 구현
  - [x] 1.1 업종별 분석 로직 구현
    - 16개 업종별 특성 분석 데이터 하드코딩
    - 지역별 시장 환경 분석 로직
    - 규모별 전략 추천 알고리즘
    - _요구사항: 3.1, 3.2, 3.3_

  - [x] 1.2 실제 인사이트 생성 로직
    - Mock 응답을 실제 분석 로직으로 교체
    - 종합 점수 계산 알고리즘 (0-100)
    - 핵심 인사이트 3개 생성 로직
    - 5초 내 응답 최적화
    - _요구사항: 3.4, 3.5, 3.6_

- [ ] 2. Reporter Agent 상호명 생성 구현
  - [x] 2.1 상호명 생성 알고리즘
    - 업종 + 지역 + 키워드 조합 로직
    - 발음 점수 계산 (음성학 기반)
    - 검색 점수 계산 (SEO 친화성)
    - 중복 회피 알고리즘
    - _요구사항: 4.1, 4.2, 4.3_

  - [x] 2.2 재생성 및 점수 시스템
    - 최대 3회 재생성 제한 로직
    - 종합 점수 계산 (발음 + 검색)
    - 3개 후보 생성 및 순위 매기기
    - _요구사항: 4.4, 4.5_

- [x] 3. OpenAI DALL-E 연동 (Signboard Agent)
  - [x] 3.1 OpenAI API 클라이언트 설정
    - API 키 관리 (AWS Secrets Manager)
    - 요청/응답 처리 로직
    - 오류 처리 및 재시도 메커니즘
    - _요구사항: 5.1, 5.2_

  - [x] 3.2 간판 이미지 생성 로직
    - 상호명 + 업종 기반 프롬프트 생성
    - DALL-E API 호출 및 이미지 생성
    - S3 업로드 및 URL 반환
    - 30초 타임아웃 처리
    - _요구사항: 5.3, 5.4, 5.5_

- [x] 4. Interior Agent 기본 구현
  - [x] 4.1 간판 스타일 분석 로직
    - 간판 이미지 색상 추출
    - 스타일 분류 (모던, 클래식, 미니멀 등)
    - 분위기 분석 (따뜻함, 차가움, 활기참 등)
    - _요구사항: 6.1, 6.2_

  - [x] 4.2 인테리어 추천 생성
    - 간판 스타일 기반 인테리어 매칭
    - 예산 범위 계산 로직
    - 색상 팔레트 생성
    - 기본 인테리어 이미지 생성
    - _요구사항: 6.3, 6.4, 6.5_

- [x] 5. Report Generator Agent HTML 보고서 생성
  - [x] 5.1 HTML 템플릿 구현
    - 반응형 브랜딩 보고서 레이아웃 디자인
    - 색상 팔레트 시각화 및 이미지 정보 표시
    - CSS 스타일링 및 인쇄 최적화
    - 한글 폰트 완벽 지원
    - _요구사항: 7.1, 7.2, 7.6_

  - [x] 5.2 종합 보고서 생성 로직
    - 모든 선택 사항 통합
    - HTML/JSON/텍스트 다중 형식 지원
    - S3 저장 및 presigned URL 생성 (10분 유효)
    - 5초 내 완료 최적화 (99.99% 성능 개선)
    - 폴백 시스템: HTML → JSON → 텍스트
    - _요구사항: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

### 🚀 Phase 2: AI 모델 확장 (1-2주)

- [ ] 6. 다중 AI 모델 지원 (Signboard Agent 확장)
  - [ ] 6.1 Stability AI SDXL 연동
    - AWS Bedrock SDXL 모델 호출
    - 프롬프트 최적화 (SDXL 특화)
    - 이미지 품질 향상 로직
    - _요구사항: 5.1, 5.2_

  - [ ] 6.2 Google Gemini 연동
    - Google AI API 클라이언트 설정
    - Gemini 이미지 생성 호출
    - 응답 형식 표준화
    - _요구사항: 5.1, 5.2_

  - [ ] 6.3 병렬 처리 구현
    - Step Functions Express 워크플로
    - 3개 AI 모델 동시 실행
    - 결과 병합 및 폴백 처리
    - _요구사항: 5.1, 5.5_

- [ ] 7. Market Analyst Agent 구현
  - [ ] 7.1 시장 분석 로직
    - 업종별 시장 규모 데이터
    - 경쟁사 현황 분석
    - 성장 잠재력 평가
    - _요구사항: 3.1, 3.2_

  - [ ] 7.2 트렌드 분석 기능
    - 최신 시장 트렌드 데이터
    - 소비자 선호도 변화
    - 기회 요소 발굴
    - _요구사항: 3.3, 3.6_

### 🎨 Phase 3: 웹 인터페이스 (1-2주)

- [ ] 8. Streamlit 앱 구현
  - [ ] 8.1 5단계 워크플로 UI
    - 단계별 진행 표시
    - 실시간 상태 업데이트
    - 에이전트별 실행 상태 표시
    - _요구사항: 모든 UI 요구사항_

  - [ ] 8.2 결과 표시 및 선택 인터페이스
    - 상호명 후보 카드 UI
    - 이미지 갤러리 및 선택
    - PDF 다운로드 링크
    - _요구사항: UI 상호작용_

### 🔧 Phase 4: 고도화 (1-2주)

- [ ] 9. 지식 베이스 구축
  - [ ] 9.1 업종별 상세 데이터
    - 16개 업종별 심화 분석 데이터
    - 지역별 시장 특성 데이터
    - 성공 사례 및 실패 요인
    - _요구사항: 데이터 고도화_

  - [ ] 9.2 AWS Bedrock Knowledge Base 연동
    - 벡터 검색 최적화
    - 캐시 전략 구현
    - 폴백 데이터 관리
    - _요구사항: 9.1, 9.2_

- [ ] 10. 모니터링 및 운영
  - [ ] 10.1 CloudWatch 대시보드
    - 에이전트별 성능 메트릭
    - 오류율 및 응답 시간 추적
    - 비용 모니터링
    - _요구사항: 8.1, 8.2_

  - [ ] 10.2 알람 및 알림 설정
    - 임계값 초과 시 SNS 알림
    - 에이전트 실패 시 자동 복구
    - 성능 저하 감지
    - _요구사항: 8.3, 8.4_

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

- [x] 10. Report Generator Agent 구현
  - [x] 10.1 Report Generator Agent Lambda 함수
    - 표준 Lambda 런타임 사용 (컨테이너 이미지 불필요)
    - HTML/JSON/텍스트 다중 형식 템플릿 및 생성 로직
    - 모든 선택 사항 포함 로직
    - 폴백 시스템 구현
    - 에이전트 단위 로그 기록
    - _요구사항: 7.1, 7.2, 7.4, 7.6_

  - [x] 10.2 보고서 다운로드 API
    - GET /report/url 엔드포인트 구현
    - presigned URL 생성 (10분 제한)
    - 보고서 상태 확인 로직
    - 다중 형식 지원
    - _요구사항: 7.3, 7.5_

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

## 🎯 즉시 시작 가능한 작업

### 1. Product Insight Agent 구현 (우선순위: 최고)
```python
# src/lambda/agents/product-insight/index.py 확장
# 현재: Mock 응답만 있음
# 목표: 실제 업종/지역/규모 분석 로직 구현
```

### 2. Reporter Agent 구현 (우선순위: 최고)  
```python
# src/lambda/agents/reporter/index.py 확장
# 현재: 기본 구조만 있음
# 목표: 상호명 생성 알고리즘 구현
```

### 3. OpenAI DALL-E 연동 (우선순위: 높음)
```python
# src/lambda/agents/signboard/index.py 확장
# 현재: 기본 구조만 있음
# 목표: 실제 이미지 생성 API 연동
```

## 📊 구현 복잡도 분석

### 높은 복잡도 (3-5일)
- **Signboard Agent**: 3개 AI 모델 병렬 처리
- **Report Generator Agent**: PDF 생성 및 레이아웃
- **지식 베이스 구축**: 데이터 수집 및 구조화

### 중간 복잡도 (2-3일)
- **Product Insight Agent**: 분석 로직 구현
- **Reporter Agent**: 상호명 생성 알고리즘
- **Interior Agent**: 스타일 매칭 로직

### 낮은 복잡도 (1-2일)
- **Market Analyst Agent**: 기본 분석 로직
- **Streamlit UI**: 기본 인터페이스
- **모니터링 설정**: CloudWatch 구성

## 💡 개발 효율성 극대화 전략

### 기존 완성된 인프라 활용
- ✅ **SAM 템플릿**: 그대로 사용, 추가 인프라 불필요
- ✅ **BaseAgent 클래스**: 모든 공통 기능 완성
- ✅ **데이터 모델**: 검증 로직까지 완벽 구현
- ✅ **Docker 환경**: 실제 DB 연동 테스트 가능

### 점진적 구현 방식
1. **Mock → 실제 로직**: 기존 Mock 응답을 실제 비즈니스 로직으로 교체
2. **단일 AI → 다중 AI**: DALL-E 먼저 구현 후 SDXL, Gemini 추가
3. **기본 → 고급**: 핵심 기능 먼저, 고도화 기능은 나중에

### NO MOCKS 테스트 활용
- 🧪 **29개 통합 테스트**: 이미 완성되어 개발 중 실시간 검증 가능
- 🔍 **실제 DB 연동**: DynamoDB Admin UI로 데이터 시각적 확인
- 📊 **성능 측정**: 실제 환경에서 응답 시간 측정

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

## 🚀 권장 개발 순서

1. **Product Insight Agent** → 분석 결과 생성 (2-3일)
2. **Reporter Agent** → 상호명 제안 (2-3일)  
3. **Signboard Agent (DALL-E만)** → 간판 1개 생성 (3-4일)
4. **Interior Agent** → 인테리어 추천 (2-3일)
5. **Report Generator Agent** → 기본 PDF (3-4일)
6. **Streamlit UI** → 사용자 인터페이스 (2-3일)
7. **다중 AI 모델 확장** → 품질 향상 (1-2주)
8. **지식 베이스 구축** → 데이터 고도화 (1-2주)

**총 예상 기간**: 6-8주 (MVP 완성까지 3-4주)

이 순서로 진행하면 **각 단계마다 동작하는 결과물을 확인**할 수 있어 개발 효율성이 높아집니다. 특히 기존에 완성된 인프라와 테스트 환경을 활용하여 **비즈니스 로직 구현에만 집중**할 수 있습니다.