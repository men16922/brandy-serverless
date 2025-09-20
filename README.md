# AI 브랜딩 챗봇

5단계 워크플로를 통해 비즈니스 브랜딩을 자동 생성하는 AI 시스템입니다.

## 워크플로

1. **비즈니스 분석** - 업종/지역/규모 기반 분석
2. **상호명 제안** - 3개 후보 생성 (발음/검색 점수 포함)
3. **간판 디자인** - DALL-E, SDXL, Gemini 병렬 생성
4. **인테리어 추천** - 간판 스타일 기반 3개 옵션
5. **PDF 보고서** - 종합 브랜딩 보고서 생성

## 기술 스택

- **Frontend**: Streamlit (AWS App Runner)
- **Backend**: AWS Lambda + API Gateway + Step Functions
- **Storage**: DynamoDB + S3
- **AI**: AWS Bedrock + OpenAI + Google Gemini
- **Local Dev**: Docker Compose (DynamoDB Local, MinIO, Chroma)

## 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 로컬 개발환경 시작
```bash
# 로컬 서비스 시작 (DynamoDB, MinIO, Chroma)
./scripts/setup-local.sh

# Streamlit 앱 실행
cd src/streamlit && streamlit run app.py
```

### 3. AWS 배포
```bash
# 개발 환경 배포
./scripts/deploy-dev.sh
```

## 로컬 서비스

로컬 개발 시 다음 서비스들이 Docker로 실행됩니다:

- **DynamoDB Local**: http://localhost:8000
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)  
- **Chroma Vector DB**: http://localhost:8001

## 필수 요구사항

- Docker & Docker Compose
- Python 3.11+
- AWS CLI (배포용)
- Node.js (CDK용)

## 환경 변수

로컬 개발 시 `.env` 파일 생성:
```bash
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ENVIRONMENT=local
```

## 개발 명령어

```bash
# 테스트 실행
python scripts/test-models.py       # 모델 테스트
python -m pytest tests/             # 전체 테스트

# 코드 품질
black src/ && flake8 src/           # 포맷팅 + 린팅

# 서비스 관리
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
docker-compose -f docker-compose.local.yml down     # 서비스 중지
```

## 프로젝트 구조

```
├── src/
│   ├── lambda/agents/              # Agent Lambda 함수들
│   ├── lambda/shared/              # 공통 유틸리티
│   └── streamlit/                  # Streamlit 웹 앱
├── infrastructure/                 # AWS CDK 코드
├── scripts/                        # 개발/배포 스크립트
├── config/                         # 환경별 설정
└── tests/                          # 테스트 코드
```

## 라이선스

MIT License