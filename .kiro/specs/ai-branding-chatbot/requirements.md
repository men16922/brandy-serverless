# AI 브랜딩 챗봇 요구사항 문서

## 개요

**목표**: 사업자가 업종/지역/규모만 입력하면 AI가 자동으로 상호명, 간판 디자인, 인테리어 추천, HTML 브랜딩 보고서까지 생성하는 완전 자동화 브랜딩 시스템

**핵심 워크플로**: 5단계 자동 생성 (분석 → 상호명 → 간판 → 인테리어 → 보고서)

**아키텍처**:
- **프론트엔드**: Streamlit (AWS App Runner)
- **API**: API Gateway HTTP API + 7개 Lambda Functions
- **오케스트레이션**: Step Functions (Express + Standard) + Supervisor Agent
- **데이터**: DynamoDB (세션 관리), S3 (이미지/보고서 저장)
- **AI**: OpenAI DALL-E, Stability AI SDXL, Google Gemini, AWS Bedrock
- **로컬 개발**: Docker Compose (DynamoDB Local, MinIO, Chroma)
- **에이전트 아키텍처**: 6개 전문 AI 에이전트 + 1개 감독 에이전트

## 핵심 기능 요구사항

### 1. 자동 브랜딩 생성 워크플로

**사용자 스토리:** 사업자로서, 업종/지역/규모만 입력하면 AI가 자동으로 완전한 브랜딩 패키지를 생성해주기를 원합니다.

#### 승인 기준
1. WHEN 사용자가 "서울 강남 소규모 카페" 입력 THEN 시스템은 5분 내에 완전한 브랜딩 패키지를 생성해야 함
2. WHEN 워크플로 실행 THEN 시스템은 상호명 3개, 간판 디자인 3개, 인테리어 추천 3개, HTML 브랜딩 보고서를 자동 생성해야 함
3. WHEN 각 단계 완료 THEN 시스템은 사용자에게 진행 상황을 실시간으로 알려야 함
4. WHEN AI 모델 실패 THEN 시스템은 폴백 결과로 서비스 중단 없이 계속 진행해야 함
5. WHEN 워크플로 완료 THEN 사용자는 HTML 보고서 다운로드 링크를 받아야 함

### 2. 세션 관리 및 상태 추적

**사용자 스토리:** 사용자로서, 워크플로 진행 상황을 실시간으로 확인하고 중단 후 이어서 진행할 수 있기를 원합니다.

#### 승인 기준
1. WHEN 새 세션 생성 THEN 시스템은 고유 세션 ID를 발급하고 DynamoDB에 저장해야 함
2. WHEN 세션 상태 조회 THEN 시스템은 현재 단계, 진행률, 각 에이전트 상태를 반환해야 함
3. WHEN 24시간 경과 THEN 시스템은 세션을 자동 만료(TTL)시켜야 함
4. WHEN 각 단계 완료 THEN 시스템은 세션 데이터를 실시간 업데이트해야 함
5. WHEN 만료된 세션 접근 THEN 시스템은 적절한 오류 메시지를 반환해야 함

### 3. AI 에이전트 기반 비즈니스 분석

**사용자 스토리:** 사업자로서, 입력한 업종/지역/규모를 바탕으로 전문적인 비즈니스 분석과 시장 인사이트를 받고 싶습니다.

#### 승인 기준
1. WHEN Product Insight Agent 실행 THEN 업종별 특성, 지역별 시장 환경, 규모별 전략을 분석해야 함
2. WHEN Market Analyst Agent 실행 THEN 경쟁사 현황, 시장 트렌드, 성장 잠재력을 분석해야 함
3. WHEN 분석 완료 THEN 시스템은 종합 점수(0-100)와 핵심 인사이트 3개를 제공해야 함
4. WHEN 분석 요청 THEN 시스템은 5초 이내에 응답을 완료해야 함
5. WHEN AI 분석 실패 THEN 시스템은 업종별 기본 분석 결과를 폴백으로 제공해야 함
6. WHEN 이미지 업로드 THEN 시스템은 S3에 저장하고 분석에 반영해야 함

### 4. Reporter Agent 상호명 자동 생성

**사용자 스토리:** 사업자로서, 비즈니스 특성을 반영한 기억하기 쉽고 브랜딩에 적합한 상호명 후보들을 받고 싶습니다.

#### 승인 기준
1. WHEN Reporter Agent 실행 THEN 비즈니스 분석 결과를 바탕으로 3개 상호명 후보를 생성해야 함
2. WHEN 상호명 생성 THEN 각 후보는 이름, 설명, 발음 점수, 검색 점수, 종합 점수를 포함해야 함
3. WHEN 재생성 요청 THEN 시스템은 최대 3회까지 허용하고 기존 후보와 중복을 회피해야 함
4. WHEN 상호명 선택 THEN 시스템은 선택된 이름을 세션에 저장하고 다음 단계로 진행해야 함
5. WHEN 상호명 요청 THEN 시스템은 5초 이내에 응답을 완료해야 함

### 5. Signboard Agent 다중 AI 간판 생성

**사용자 스토리:** 사업자로서, 선택한 상호명과 업종 특성을 반영한 다양한 스타일의 간판 디자인을 받아 최적의 것을 선택하고 싶습니다.

#### 승인 기준
1. WHEN Signboard Agent 실행 THEN OpenAI DALL-E, Stability AI SDXL, Google Gemini를 병렬로 호출해야 함
2. WHEN 간판 생성 THEN 각 AI 모델은 상호명과 업종을 반영한 고유한 스타일의 간판을 생성해야 함
3. WHEN 이미지 생성 완료 THEN 시스템은 S3에 저장하고 썸네일과 설명이 포함된 카드 형태로 표시해야 함
4. WHEN 30초 내 미완료 THEN 시스템은 타임아웃 처리하고 폴백 이미지를 제공해야 함
5. WHEN 일부 AI 실패 THEN 시스템은 성공한 결과와 폴백 이미지로 3개 옵션을 보장해야 함

### 6. Interior Agent 맞춤형 인테리어 추천

**사용자 스토리:** 사업자로서, 선택한 간판 디자인과 조화를 이루는 인테리어 옵션들을 받아 통일감 있는 브랜드 공간을 구성하고 싶습니다.

#### 승인 기준
1. WHEN Interior Agent 실행 THEN 선택된 간판의 색상, 스타일, 분위기를 분석해야 함
2. WHEN 인테리어 생성 THEN 간판과 조화되는 3가지 스타일의 인테리어 디자인을 생성해야 함
3. WHEN 인테리어 완료 THEN 각 옵션은 예상 예산 범위와 색상 팔레트 정보를 포함해야 함
4. WHEN 30초 내 미완료 THEN 시스템은 간판 스타일에 맞는 폴백 인테리어를 제공해야 함
5. WHEN 인테리어 선택 THEN 시스템은 선택된 디자인을 세션에 저장해야 함

### 7. Report Generator Agent 종합 브랜딩 보고서

**사용자 스토리:** 사업자로서, 모든 브랜딩 요소가 정리된 전문적인 HTML 브랜딩 보고서를 받아 실제 사업 구현에 바로 활용하고 싶습니다.

#### 승인 기준
1. WHEN Report Generator Agent 실행 THEN 모든 선택된 브랜딩 요소를 종합한 HTML 보고서를 생성해야 함
2. WHEN HTML 보고서 생성 THEN 비즈니스 분석, 최종 상호명, 간판 디자인 3개, 인테리어 옵션 3개, 색상 팔레트, 예산 가이드를 포함해야 함
3. WHEN 보고서 완료 THEN 시스템은 S3에 저장하고 10분간 유효한 다운로드 링크를 제공해야 함
4. WHEN HTML 생성 실패 THEN 시스템은 JSON 또는 텍스트 형식으로 폴백하여 보고서를 제공해야 함
5. WHEN 보고서 요청 THEN 시스템은 5초 이내에 HTML 보고서 생성을 완료해야 함
6. WHEN HTML 보고서 THEN 한글 폰트 문제 없이 완벽한 표시와 인쇄 지원을 제공해야 함

### 8. Supervisor Agent 워크플로 감시 및 제어

**사용자 스토리:** 개발자로서, 전체 워크플로의 실행 상태를 실시간으로 모니터링하고 장애 시 자동 복구되기를 원합니다.

#### 승인 기준
1. WHEN Supervisor Agent 실행 THEN 모든 에이전트의 실행 상태를 실시간으로 감시해야 함
2. WHEN 에이전트 실패 THEN Supervisor는 자동으로 재시도하거나 폴백 처리를 트리거해야 함
3. WHEN 상태 조회 요청 THEN GET /status/{id}로 전체 워크플로 진행 상황을 반환해야 함
4. WHEN Step Functions 실행 THEN Supervisor는 Express/Standard 워크플로 상태를 추적해야 함
5. WHEN 에이전트 통신 THEN 구조화된 로그(agent, tool, latency_ms)를 기록해야 함

### 9. 환경별 개발 및 배포 지원

**사용자 스토리:** 개발자로서, 로컬과 클라우드 환경에서 동일한 기능을 테스트하고 배포할 수 있기를 원합니다.

#### 승인 기준
**로컬 환경**
1. WHEN 로컬 개발 THEN Docker Compose로 DynamoDB Local, MinIO, Chroma가 자동 시작되어야 함
2. WHEN SAM Local 실행 THEN 모든 Lambda 함수가 로컬에서 동작해야 함
3. WHEN 환경 검증 THEN 모든 서비스의 헬스체크가 통과해야 함

**클라우드 환경**
1. WHEN AWS 배포 THEN SAM 템플릿으로 모든 리소스가 자동 생성되어야 함
2. WHEN 프로덕션 실행 THEN AWS DynamoDB, S3, Bedrock이 연동되어야 함
3. WHEN 모니터링 THEN CloudWatch로 에이전트별 성능을 추적해야 함

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
- `POST /report/generate` → HTML 보고서 생성
- `GET /report/url` → 다운로드 링크

## Step Functions 상태머신(요지)

`Analyze(Product+Market Agent) → SuggestNames(Reporter Agent) → GenerateSigns(Parallel: Dalle|SDXL|Gemini) → GenerateInteriors(Parallel) → GeneratePDF → Done`

**Supervisor Agent 역할**: 세션 상태 및 Step Functions 실행 감시, 재시도/폴백 관리

## HTML 보고서 특징

### 기술적 장점
- **한글 폰트 완벽 지원**: PDF 폰트 문제 완전 해결
- **빠른 생성 속도**: 0.01초 (기존 120초 목표 대비 99.99% 개선)
- **반응형 디자인**: 모바일/태블릿/데스크톱 호환
- **인쇄 최적화**: CSS @media print로 깔끔한 인쇄
- **접근성**: 스크린 리더 호환 및 검색 가능

### 사용자 경험
- **즉시 열기**: 브라우저에서 바로 확인 가능
- **공유 용이**: URL로 간편 공유
- **시각적 요소**: 색상 팔레트 실제 색상 표시
- **상태 표시**: 선택된 항목 시각적 구분 (✓ 배지)
- **다중 형식**: HTML/JSON/텍스트 폴백 지원

### 포함 내용
- 비즈니스 정보 및 AI 분석 결과
- 추천 상호명 3개 (점수 및 설명 포함)
- 간판 디자인 3개 (이미지 정보 및 스타일)
- 인테리어 디자인 3개 (이미지 정보 및 스타일)
- 색상 팔레트 (시각적 색상 박스)
- 예산 가이드 (항목별 최소/권장/최대)
- 맞춤형 권장사항

## 리스크 & 완화

- 외부 모델 API 지연/실패 → 병렬/타임아웃/폴백 + 재시도 + 캐시
- 30초 제한(API GW) → 비동기 전환, 프런트 폴링/푸시
- HTML 보고서 생성으로 폰트 문제 해결 → 빠른 생성 속도와 완벽한 한글 지원

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