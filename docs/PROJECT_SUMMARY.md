# AI 브랜딩 챗봇 프로젝트 종합 문서

## 프로젝트 개요

AI 브랜딩 챗봇은 Agent-Based Architecture를 사용하여 완전한 비즈니스 브랜딩을 생성하는 서버리스 시스템입니다.

### 핵심 워크플로 (5단계)
1. **Business Analysis** - Product Insight + Market Analyst Agents
2. **Name Suggestions** - Reporter Agent (3개 후보 생성)
3. **Signboard Design** - Signboard Agent (다중 AI 모델 병렬 처리)
4. **Interior Recommendations** - Interior Agent (3개 옵션)
5. **PDF Report** - Report Generator Agent (종합 브랜딩 리포트)

## 아키텍처

### Agent-Based 구조
- **Supervisor Agent**: 전체 워크플로 모니터링 및 조정
- **Product Insight Agent**: 비즈니스 분석
- **Market Analyst Agent**: 시장 분석 및 트렌드 분석 (DynamoDB 기반)
- **Reporter Agent**: 상호명 생성
- **Signboard Agent**: 간판 디자인 (DALL-E, SDXL, Gemini 병렬)
- **Interior Agent**: 인테리어 추천
- **Report Generator Agent**: PDF/HTML 리포트 생성

### 기술 스택
- **Backend**: AWS SAM, Lambda (Python 3.11), API Gateway HTTP API
- **Database**: DynamoDB (세션 관리, 시장 데이터)
- **Storage**: S3/MinIO (이미지, 리포트)
- **Vector DB**: Chroma (로컬), Bedrock KB (프로덕션)
- **AI Models**: OpenAI DALL-E, AWS Bedrock SDXL, Google Gemini
- **Frontend**: Streamlit (AWS App Runner)

## 주요 구현 완료 사항

### 1. Multi-AI 통합 (완료)
- DALL-E, SDXL, Gemini 병렬 처리
- 폴백 메커니즘 및 오류 처리
- Step Functions 기반 워크플로

### 2. Market Analyst Agent 리팩토링 (완료)
- 하드코딩 데이터 → DynamoDB 기반 관리
- JSON 파일 분리 (업종별/지역별/트렌드 데이터)
- 확장 가능한 데이터 구조
- 캐시 메커니즘 및 폴백 시스템

### 3. Report Generator 개선 (완료)
- PDF 생성 (한글 폰트 지원)
- HTML 리포트 (이미지 포함)
- MinIO 통합 (파일 저장/조회)
- 대안 리포트 생성기

### 4. 로컬 개발 환경 (완료)
- Docker Compose (DynamoDB, MinIO, Chroma)
- 통합 테스트 환경
- DynamoDB Admin UI
- 실제 데이터 저장/조회 검증

## 데이터 구조

### DynamoDB 테이블
1. **WorkflowSessions**: 세션 관리 (TTL 24시간)
2. **MarketData**: 시장 분석 기준 데이터 (28개 레코드)
   - INDUSTRY_MARKET_SIZE: 6개 업종
   - REGIONAL_MULTIPLIER: 10개 지역
   - INDUSTRY_COMPETITOR: 6개 업종
   - INDUSTRY_TREND: 6개 업종

### JSON 데이터 파일
- `data/market-data/industry-market-size.json`
- `data/market-data/regional-multipliers.json`
- `data/market-data/industry-competitors.json`
- `data/market-data/industry-trends.json`

## 성능 요구사항
- Text 응답: ≤ 5초
- Image 생성: ≤ 30초
- Full 워크플로: ≤ 5분
- Session TTL: 24시간

## 배포 및 운영

### 로컬 개발
```bash
# 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 초기 데이터 설정
python scripts/setup_market_data_tables.py

# SAM 로컬 실행
sam build && sam local start-api --port 3000

# Streamlit 앱
cd src/streamlit && streamlit run app.py
```

### AWS 배포
```bash
sam build
sam deploy --guided
```

### 모니터링
- DynamoDB Admin UI: http://localhost:8002
- MinIO Console: http://localhost:9001
- CloudWatch 대시보드 (프로덕션)

## 확장성

현재 구조는 다음과 같은 확장을 지원합니다:
- 새로운 업종/지역 추가 (JSON 파일 수정)
- 새로운 데이터 타입 추가 (DynamoDB 스키마)
- 다양한 데이터 포맷 지원
- 완전한 하위 호환성

## 테스트 전략

### 통합 테스트 (Docker 기반)
- Mock 사용 금지
- 실제 DynamoDB/MinIO/Chroma 사용
- End-to-end 워크플로 검증
- 데이터 무결성 확인

### 주요 테스트 시나리오
- Multi-AI 이미지 생성
- Market Analyst 데이터 조회
- 전체 워크플로 실행
- 리포트 생성 및 저장

## 문제 해결

### 일반적인 이슈
1. **Docker 서비스 연결 실패**
   - `docker-compose -f docker-compose.local.yml up -d`
   - 포트 충돌 확인: `lsof -i :8000,8001,8002,9000,9001`

2. **DynamoDB 데이터 없음**
   - `python scripts/setup_market_data_tables.py`
   - DynamoDB Admin UI에서 확인

3. **AI Provider 오류**
   - API 키 확인 (.env.local)
   - 폴백 이미지 사용 여부 확인

4. **PDF 생성 실패**
   - 한글 폰트 설치 확인
   - MinIO 연결 상태 확인

## 다음 단계

1. **Bedrock Knowledge Base 연동**
2. **성능 최적화 및 캐시 개선**
3. **모니터링 및 알람 설정**
4. **사용자 인터페이스 개선**
5. **추가 AI 모델 통합**