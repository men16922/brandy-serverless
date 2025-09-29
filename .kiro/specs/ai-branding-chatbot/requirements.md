# 요구사항 문서

## 개요

**목표**: 5단계 워크플로(분석 → 상호명 → 간판 → 인테리어 → 보고서)로 브랜딩 생성

**구성**:
- UI: Streamlit (AWS App Runner)
- API: API Gateway(HTTP API) + Lambda
- 오케스트레이션: Step Functions (Express + Standard 혼합)
- 데이터: DynamoDB (세션), S3 (이미지/보고서)
- AI: Bedrock 모델 (Dev) / Chroma (Local)
- 에이전트 기반 구성 (확장): Product Insight, Market Analyst, Reporter, Signboard, Interior, Supervisor Agent

## 기능 요구사항

### 세션 관리

**사용자 스토리:** 사용자로서, 워크플로 진행 상황을 저장하고 중단 후 이어서 진행할 수 있기를 원합니다.

#### 승인 기준

1. 새 세션 발급, 상태/결과 DynamoDB 저장
2. 24시간 후 자동 만료(TTL)
3. GET /sessions/{id}로 현재 진행 상태 조회 가능
4. 각 단계 완료 시 세션 데이터 업데이트
5. 만료된 세션 접근 시 적절한 오류 응답

### 비즈니스 분석

**사용자 스토리:** 사용자로서, 업종/지역/규모를 입력하고 분석 요약과 점수를 받아 비즈니스 특성을 이해할 수 있기를 원합니다.

#### 승인 기준

1. 업종/지역/규모 입력 → 요약/점수 생성
2. 업로드 이미지는 S3 저장
3. 5초 이내 응답 완료
4. 분석 실패 시 폴백 결과 제공
5. 결과를 세션에 저장
6. Bedrock Knowledge Base 조회로 업종/지역/규모 관련 데이터 반영
7. KB 지연/실패 시 캐시 데이터 또는 폴백 결과 제공

### 상호명 제안

**사용자 스토리:** 사용자로서, 비즈니스 정보를 기반으로 3개 상호명 후보를 받고, 최대 3회까지 재생성할 수 있기를 원합니다.

#### 승인 기준

1. 3개 후보 생성, 최대 3회 재생성
2. 각 후보는 설명과 발음/검색 점수 포함
3. 재생성 시 기존 후보와 중복 회피
4. 최종 선택 저장
5. 5초 이내 응답 완료

### 간판 이미지 생성

**사용자 스토리:** 사용자로서, 선택한 상호명과 업종 특성을 반영한 3개 간판 디자인을 받아 선택할 수 있기를 원합니다.

#### 승인 기준

1. Step Functions 병렬 분기 (DALL·E, SDXL, Gemini)
2. 30초 제한, 실패 시 폴백 이미지
3. 생성 이미지 S3 저장 후 URL 반환
4. 카드 형태(썸네일, 간단 설명)로 UI 표시
5. 실패 모델이 있어도 3개 옵션 보장

### 인테리어 추천

**사용자 스토리:** 사용자로서, 선택한 간판과 조화되는 3개 인테리어 디자인을 받아 통일감 있는 브랜드 공간을 구성할 수 있기를 원합니다.

#### 승인 기준

1. 간판 스타일 기반 3안 생성
2. 병렬 처리 (DALL·E, SDXL, Gemini)로 30초 내 완료
3. 예산/팔레트 메타데이터 포함
4. 실패 시 간판과 조화되는 폴백 이미지
5. 결과를 세션에 저장

### PDF 보고서 생성

**사용자 스토리:** 사용자로서, 모든 선택 사항이 포함된 PDF 보고서를 다운로드하여 실제 브랜딩 구현에 활용할 수 있기를 원합니다.

#### 승인 기준

1. Lambda 컨테이너로 PDF 생성
2. 결과 S3 저장, presigned URL 반환
3. PDF 내용: 최종 상호명, 간판 3안(선택 표시), 인테리어 3안, 색상 팔레트, 예산 범위, 분석 요약
4. 실패 시 오류 메시지 및 재시도 옵션 제공
5. GET /report/url로 다운로드 링크 제공

### 환경별 실행(Local/Dev)

**사용자 스토리:** 개발자로서, 로컬과 개발 환경에서 각각 적절한 백엔드를 사용하여 효율적으로 개발하고 테스트할 수 있기를 원합니다.

#### 승인 기준

**Local**
- 저장소: DynamoDB Local + 로컬 S3 에뮬레이터(MinIO 가능)
- 보고서/문서 벡터화: Chroma
- 헬스체크: DynamoDB Local/Chroma 상태 반환
- 앱 기동 시 data/*.json 자동 마이그레이션

**Dev**
- 저장소: AWS DynamoDB + S3
- 벡터화: Bedrock Knowledge Base
- 헬스체크: DynamoDB/Bedrock KB 상태 반환
- 앱 기동 시 data/*.json 자동 마이그레이션

## 비기능 요구사항

### 성능
- 텍스트 응답(분석/상호명): ≤ 5초
- 이미지 생성(각 모델 분기): ≤ 30초  
- 전체 워크플로(분석→보고서): ≤ 5분
- 진행 중 UI는 로딩 표시 + ETA 제공(세션에서 진행률 계산)

### 로깅/안정성
- 구조화 로그(요청/응답/오류/소요시간), CloudWatch Logs + X-Ray 추적
- 외부 호출 재시도/지수 백오프, DLQ(SQS) 연계
- 네트워크/쿼터 오류 시 사용자 메시지 표시 + 폴백 데이터/이미지 제공
- 상태 복원: 세션 데이터 기반 재시도/재실행
- 에이전트 단위 로그(agent, tool, latency_ms) 기록
- Supervisor Agent가 Step Functions 실행 상태를 감시하고 실패 시 재시도/폴백 트리거

### 보안/권한
- Cognito(선택)로 사용자 인증, 세션별 권한 검증
- Lambda 별 최소 권한 IAM(세분화된 DynamoDB/S3/KMS/Bedrock 권한)
- 비밀/키: AWS Secrets Manager/Parameter Store 관리

### 운영/배포
- IaC: **AWS SAM (Serverless Application Model)** 완전 서버리스 배포
- SAM 템플릿: template.yaml로 모든 리소스 정의 (API Gateway, Lambda Functions, Step Functions, DynamoDB, S3, IAM)
- 배포 전략: sam deploy --guided로 스테이지별 배포 (local/dev/prod)
- 환경별 파라미터: samconfig.toml로 환경별 설정 관리
- 관측: CloudWatch 대시보드(성능/오류율/재시도), 알람(SNS)
- 에이전트별 Lambda 분리 배포: SAM 템플릿에서 각 Agent별 Lambda Function 정의
- CloudWatch 대시보드에서 Agent 단위 성능/실패율 추적 가능
- SAM Local: sam local start-api로 로컬 API Gateway + Lambda 테스트

## API 엔드포인트 (예시)

- `POST /sessions` → 새 세션
- `GET /sessions/{id}` → 상태 조회
- `GET /status/{id}` → Supervisor Agent가 전체 워크플로 상태 반환
- `POST /analysis` → 분석 실행
- `POST /names/suggest` → 상호명 제안
- `POST /signboards/generate` → 간판 생성
- `POST /interiors/generate` → 인테리어 생성
- `POST /report/generate` → PDF 생성
- `GET /report/url` → 다운로드 링크

## Step Functions 상태머신(요지)

`Analyze(Product+Market Agent) → SuggestNames(Reporter Agent) → GenerateSigns(Parallel: Dalle|SDXL|Gemini) → GenerateInteriors(Parallel) → GeneratePDF → Done`

**Supervisor Agent 역할**: 세션 상태 및 Step Functions 실행 감시, 재시도/폴백 관리

## 리스크 & 완화

- 외부 모델 API 지연/실패 → 병렬/타임아웃/폴백 + 재시도 + 캐시
- 30초 제한(API GW) → 비동기 전환, 프런트 폴링/푸시
- PDF 바이너리 의존(폰트/렌더러) → Lambda 컨테이너 이미지 채택

## 용어

- **폴백 이미지**: 실패 시 표준 대체 이미지(S3 공용 디렉토리)
- **세션**: 사용자 한 번의 워크플로 실행 단위

## 선택 확장

### 에이전트 기반 확장

**사용자 스토리:** 개발자로서, 에이전트 기반 아키텍처로 더 유연하고 확장 가능한 AI 워크플로를 구현할 수 있기를 원합니다.

#### 승인 기준

1. Product/Market/Reporter/Sign/Interior Agent 독립 실행 가능
2. Supervisor Agent가 전체 워크플로 통제
3. 구조화 로그에 agent, tool, latency_ms 포함
4. Interpreter는 샌드박스 모드만 허용
5. Lambda 워크플로와 교체 가능

### Slack 인터페이스

**사용자 스토리:** 사용자로서, Slack을 통해 브랜딩 워크플로를 실행하여 팀 협업 환경에서 편리하게 사용할 수 있기를 원합니다.

#### 승인 기준

1. Slack Events API → API Gateway → Lambda 연동
2. 명령 세트 예: /brand analyze, /brand name, /brand signboard, /brand interior, /brand report, /brand status
3. 긴 작업은 결과 URL을 비동기 DM으로 회신
4. 입력 검증(정규식)으로 안전성 확보
5. 세션 관리는 기존 시스템과 동일하게 유지
6. 에이전트 로그(agent, tool, latency) 요약을 Slack 채널로 실시간 전송
7. Supervisor Agent가 Slack에서 직접 상태 질의(/brand status)에 응답 가능

### 통합 테스트

**사용자 스토리:** 개발자로서, Docker Compose 기반 로컬 환경에서 전체 워크플로를 자동으로 테스트하여 시스템의 안정성을 보장할 수 있기를 원합니다.

#### 승인 기준

1. WHEN 통합 테스트 실행 THEN 시스템은 Docker Compose 서비스(DynamoDB Local, MinIO, Chroma)를 자동으로 시작해야 함
2. WHEN Docker 서비스가 준비되면 THEN 시스템은 모든 서비스가 정상 상태인지 확인 후 테스트를 진행해야 함
3. WHEN 5단계 워크플로 테스트 실행 THEN 시스템은 세션 생성부터 PDF 생성까지 전체 프로세스를 검증해야 함
4. WHEN Agent 통신 테스트 실행 THEN 시스템은 Supervisor Agent 모니터링과 Agent 간 협업을 검증해야 함
5. WHEN 테스트 완료 THEN 시스템은 Docker 서비스를 자동으로 정리하고 테스트 결과를 리포트해야 함
6. WHEN 오류 시나리오 테스트 THEN 시스템은 폴백 메커니즘과 에러 핸들링을 검증해야 함
7. IF Docker가 실행되지 않으면 THEN 시스템은 명확한 에러 메시지와 함께 테스트를 graceful하게 skip해야 함

## 발표 포인트

- **Serverless 100% AWS**: App Runner + Lambda + Step Functions + DynamoDB + S3
- **Express/Standard 혼합 + Supervisor**: 빠른 병렬 처리 + 사용자 대기 지원 + 워크플로 감시
- **Bedrock KB + Agent 기반 확장**: 지식 기반 분석 + 유연한 에이전트 아키텍처
- **에이전트 단위 배포/관측**: 독립적인 Agent Lambda 배포 및 성능 추적
- **Docker 기반 통합 테스트**: 실제 환경과 유사한 조건에서 end-to-end 테스트
- **Slack 통합**: 팀 협업 환경에서의 브랜딩 워크플로 실행