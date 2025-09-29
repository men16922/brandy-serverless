# AI 브랜딩 챗봇 🤖

업종, 지역, 규모만 입력하면 AI가 **상호명, 간판 디자인, 인테리어, PDF 보고서**를 자동으로 만들어주는 서버리스 시스템입니다.

## 🎯 무엇을 하는 프로젝트인가요?

```
입력: "서울 강남에서 소규모 카페 운영 예정"
↓
AI가 자동 생성:
✅ 상호명 3개 후보 (발음/검색 점수 포함)
✅ 간판 디자인 3개 (DALL-E, SDXL, Gemini)
✅ 인테리어 추천 3개 (간판 스타일 맞춤)
✅ 종합 브랜딩 PDF 보고서
```

## 🏗️ 시스템 구조

### 6개 AI 에이전트가 순서대로 작업
1. **Supervisor** - 전체 작업 관리
2. **Product Insight** - 비즈니스 분석  
3. **Market Analyst** - 시장 동향 분석
4. **Reporter** - 상호명 생성
5. **Signboard** - 간판 디자인 (3개 AI 동시 사용)
6. **Interior** - 인테리어 추천

### 기술 스택
- **AWS SAM** - 서버리스 배포
- **Lambda + API Gateway** - 백엔드
- **DynamoDB + S3** - 데이터 저장
- **Step Functions** - 워크플로 관리

## 🚀 5분 빠른 시작

### 1. 환경 설정
```bash
# 저장소 클론 & 가상환경 생성
git clone <repository>
cd brandy-serverless
python3 -m venv venv
source venv/bin/activate

# 개발환경 자동 설정 (의존성 설치)
./scripts/activate-dev.sh
```

### 2. 로컬 개발 시작
```bash
./scripts/dev.sh setup     # Docker 서비스 시작
./scripts/dev.sh validate  # 환경 검증
./scripts/dev.sh test      # 테스트 실행 (29개 모두 통과)
./scripts/dev.sh api       # API 서버 시작
```

### 3. 확인
- **API 테스트**: http://localhost:3000
- **데이터 확인**: http://localhost:8002 (DynamoDB Admin)
- **파일 확인**: http://localhost:9001 (MinIO Console)

## 🧪 테스트 (실제 DB 사용)

```bash
./scripts/dev.sh test      # 29개 통합 테스트 실행
./scripts/dev.sh validate  # 환경 검증
```

**특징**: Mock 사용 안함. 실제 DynamoDB, MinIO, Chroma 사용하여 신뢰할 수 있는 테스트

## 🛠️ 개발 명령어

### 통합 개발 스크립트 (권장)
```bash
./scripts/dev.sh setup     # 로컬 환경 설정
./scripts/dev.sh validate  # 환경 검증
./scripts/dev.sh test      # 통합 테스트 실행
./scripts/dev.sh build     # SAM 애플리케이션 빌드
./scripts/dev.sh api       # 로컬 API 서버 시작
./scripts/dev.sh app       # Streamlit 앱 시작
./scripts/dev.sh cleanup   # 환경 정리
./scripts/dev.sh help      # 도움말
```

### 개별 스크립트
```bash
# 환경 관리
./scripts/activate-dev.sh               # 개발환경 활성화
./scripts/setup-local.sh                # Docker 서비스 시작
python scripts/validate-environment.py  # 환경 전체 검증

# SAM 개발 워크플로
./scripts/sam-build.sh                  # SAM 애플리케이션 빌드
./scripts/sam-local.sh                  # 로컬 API Gateway + Lambda
./scripts/sam-deploy.sh dev             # AWS 개발 환경 배포
sam logs --stack-name ai-branding-chatbot-dev --tail  # 실시간 로그

# Docker 서비스 관리
docker-compose -f docker-compose.local.yml up -d    # 서비스 시작
docker-compose -f docker-compose.local.yml down -v  # 서비스 중지 + 볼륨 삭제
```

### 로컬 서비스 접근
- **DynamoDB Admin UI**: http://localhost:8002 (테이블 관리)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Chroma API**: http://localhost:8001 (벡터 DB)

## 📁 프로젝트 구조

```
├── template.yaml                      # SAM 템플릿 (모든 AWS 리소스)
├── samconfig.toml                     # SAM 배포 설정
├── src/lambda/agents/                 # Agent Lambda 함수들
│   ├── supervisor/                    # 워크플로 감시 & 제어
│   ├── product-insight/               # 비즈니스 분석
│   ├── market-analyst/                # 시장 동향 분석
│   ├── reporter/                      # 상호명 제안
│   ├── signboard/                     # 간판 디자인 생성
│   ├── interior/                      # 인테리어 추천
│   └── report-generator/              # PDF 보고서 생성
├── src/lambda/shared/                 # 공통 유틸리티 (Lambda Layer)
├── statemachine/                      # Step Functions 정의
├── scripts/                           # SAM 빌드/배포 스크립트
├── tests/integration/                 # Docker 기반 통합 테스트
└── docker-compose.local.yml           # 로컬 개발 서비스
```

## 라이선스

MIT License