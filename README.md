# AI 브랜딩 챗봇 (Agent-Based Architecture)

5단계 워크플로를 통해 비즈니스 브랜딩을 자동 생성하는 에이전트 기반 서버리스 시스템입니다.

## 에이전트 기반 아키텍처

- **Supervisor Agent**: 전체 워크플로 감시, Step Functions 실행 상태 추적, 에이전트 간 조정
- **Product Insight Agent**: 업종/지역/규모 기반 비즈니스 분석, Bedrock KB 조회
- **Market Analyst Agent**: 시장 동향 및 경쟁사 분석, KB 데이터 검색
- **Reporter Agent**: 3개 상호명 후보 생성, 중복 회피, 발음/검색 점수 산출
- **Signboard Agent**: DALL-E, SDXL, Gemini 병렬 간판 이미지 생성
- **Interior Agent**: 간판 스타일 기반 인테리어 추천 생성
- **Report Generator Agent**: PDF 보고서 생성

## 기술 스택

- **프론트엔드**: Streamlit (AWS App Runner)
- **API**: API Gateway HTTP API + Agent Lambda Functions
- **오케스트레이션**: Step Functions (Express + Standard) + Supervisor Agent
- **데이터**: DynamoDB (세션) + S3 (이미지/보고서) + Bedrock Knowledge Base
- **AI**: Bedrock (SDXL + KB) + OpenAI (DALL-E) + Google Gemini
- **모니터링**: CloudWatch (에이전트 단위) + X-Ray (분산 추적)

## 프로젝트 구조

```
├── src/
│   ├── lambda/
│   │   ├── agents/                    # Agent Lambda 함수들
│   │   │   ├── supervisor/            # Supervisor Agent (워크플로 감시/제어)
│   │   │   ├── product-insight/       # Product Insight Agent (비즈니스 분석)
│   │   │   ├── market-analyst/        # Market Analyst Agent (시장 분석)
│   │   │   ├── reporter/              # Reporter Agent (상호명 제안)
│   │   │   ├── signboard-agent/       # Signboard Agent (간판 생성)
│   │   │   ├── interior-agent/        # Interior Agent (인테리어 생성)
│   │   │   └── report-generator-agent/ # Report Generator Agent (PDF 생성)
│   │   └── shared/                    # 공통 Agent 유틸리티
│   │       ├── utils.py               # Agent-aware 로깅, AWS 클라이언트
│   │       ├── agent_communication.py # Agent 간 통신 인터페이스
│   │       └── knowledge_base.py      # KB 추상화 (Bedrock/Chroma)
│   └── streamlit/                     # Streamlit 앱 (Agent 통합)
├── infrastructure/                    # AWS CDK 인프라 코드
│   └── stacks/                       # CDK 스택들 (Agent 기반)
├── config/                           # 환경별 Agent 설정
├── scripts/                          # Agent 배포/설정 스크립트
└── data/                             # 로컬 개발용 데이터
```

## 환경 설정

### 로컬 개발 환경

1. **필수 요구사항**
   - Docker & Docker Compose
   - Python 3.11+
   - AWS CLI
   - Node.js (CDK용)

2. **로컬 환경 설정**
   ```bash
   # 로컬 서비스 시작 (DynamoDB Local, MinIO, Chroma)
   ./scripts/setup-local.sh
   
   # Streamlit 앱 실행
   cd src/streamlit
   streamlit run app.py
   ```

3. **로컬 서비스 URL**
   - DynamoDB Local: http://localhost:8000
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - Chroma: http://localhost:8001

### 개발 환경 (AWS)

1. **AWS 설정**
   ```bash
   # AWS CLI 설정
   aws configure
   
   # CDK 설치
   npm install -g aws-cdk
   ```

2. **배포**
   ```bash
   # 개발 환경 배포
   ./scripts/deploy-dev.sh
   ```

## 5단계 Agent 워크플로

1. **비즈니스 분석**: Product Insight + Market Analyst Agent → Bedrock KB 조회 → 종합 분석
2. **상호명 제안**: Reporter Agent → 3개 후보 생성 (최대 3회 재생성) → 발음/검색 점수
3. **간판 디자인**: Signboard Agent → DALL-E, SDXL, Gemini 병렬 생성 → Supervisor 감시
4. **인테리어 추천**: Interior Agent → 간판 스타일 기반 3개 옵션 → 병렬 AI 모델
5. **PDF 보고서**: Report Generator Agent → 모든 선택사항 포함 보고서 생성

**Supervisor Agent**: 전 단계에서 워크플로 상태 감시, 실패 시 재시도/폴백 트리거

## 환경별 구성

### Local 환경
- **저장소**: DynamoDB Local + MinIO
- **벡터 저장소**: Chroma
- **AI 모델**: OpenAI DALL-E + Google Gemini

### Dev 환경  
- **저장소**: AWS DynamoDB + S3
- **벡터 저장소**: Bedrock Knowledge Base
- **AI 모델**: Bedrock SDXL + OpenAI DALL-E + Google Gemini

## API 엔드포인트

- `POST /sessions` - 새 세션 생성
- `GET /sessions/{id}` - 세션 상태 조회
- `POST /analysis` - 비즈니스 분석
- `POST /names/suggest` - 상호명 제안
- `POST /signboards/generate` - 간판 생성
- `POST /interiors/generate` - 인테리어 생성
- `POST /report/generate` - PDF 생성
- `GET /report/url` - 다운로드 링크

## 개발 가이드

### 환경 변수

로컬 개발시 `.env` 파일 생성:
```bash
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ENVIRONMENT=local
```

### 테스트

```bash
# 단위 테스트
python -m pytest tests/

# 통합 테스트
python -m pytest tests/integration/
```

### 로그 확인

```bash
# 로컬 개발
tail -f logs/app.log

# AWS 환경
aws logs tail /aws/lambda/branding-chatbot-session-manager-dev --follow
```

## 모니터링

- **CloudWatch**: 로그 및 메트릭
- **X-Ray**: 분산 추적
- **구조화된 로그**: trace_id, session_id, latency_ms 포함

## 확장 기능 (선택사항)

- **Strands Agents**: 분석/네이밍 단계를 Agent 패턴으로 대체
- **Slack 인터페이스**: `/brand` 명령어로 워크플로 실행

## 라이선스

MIT License