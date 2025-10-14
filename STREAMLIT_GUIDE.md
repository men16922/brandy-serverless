# Streamlit 앱 실행 가이드

## 🚀 빠른 시작

### 1. 자동 실행 (권장)

```bash
./scripts/run-streamlit.sh
```

이 스크립트는 자동으로:
- 가상환경 활성화
- 필요한 의존성 설치
- AWS API Gateway 엔드포인트 가져오기
- Streamlit 앱 실행

### 2. 수동 실행

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. Streamlit 의존성 설치
pip install -r src/streamlit/requirements.txt

# 3. API 엔드포인트 설정
export API_BASE_URL="https://u3llaegoxc.execute-api.us-east-1.amazonaws.com/dev"

# 4. Streamlit 앱 실행
streamlit run src/streamlit/app.py --server.port 8501
```

## 📍 접속 정보

- **Streamlit UI**: http://localhost:8501
- **API Gateway**: https://u3llaegoxc.execute-api.us-east-1.amazonaws.com/dev

## 🎨 사용 방법

### Step 1: 비즈니스 정보 입력
1. **업종 (Industry)**: restaurant, retail, service 등 선택
2. **지역 (Region)**: seoul, busan 등 선택
3. **규모 (Size)**: small, medium, large 선택
4. "세션 시작" 버튼 클릭

### Step 2: 5단계 워크플로 진행
1. **비즈니스 분석** - 업종/지역/규모 분석 (Bedrock Claude)
2. **상호명 제안** - 3개 상호명 후보 생성 (Reasoning LLM)
3. **간판 디자인** - AI 간판 이미지 생성 (Bedrock SDXL)
4. **인테리어 추천** - 맞춤형 인테리어 디자인 (Bedrock Claude) ✅
5. **보고서 생성** - 종합 브랜딩 보고서 (Bedrock Claude)

### Step 3: 결과 확인
- 각 단계별 결과 실시간 확인
- Reasoning chain 확인 (expandable section)
- 최종 PDF 보고서 다운로드

## ✅ 현재 상태

### 완료된 기능
- ✅ API Gateway 엔드포인트 연결
- ✅ 세션 생성 및 관리
- ✅ Bedrock Claude 통합 (Product Insight, Reporter, Interior)
- ✅ Bedrock SDXL 통합 (Signboard)
- ✅ Reasoning Engine (Chain-of-Thought)
- ✅ Confidence Scoring
- ✅ Fallback 메커니즘

### 테스트 완료
- ✅ Interior Agent Bedrock 통합 (90% confidence, 32초 latency)
- ✅ API 세션 생성 정상 작동
- ✅ DynamoDB 세션 저장 정상

## 🔧 트러블슈팅

### 1. Streamlit이 설치되지 않음
```bash
source venv/bin/activate
pip install -r src/streamlit/requirements.txt
```

### 2. API 연결 실패
```bash
# API 엔드포인트 확인
aws cloudformation describe-stacks \
  --stack-name ai-branding-chatbot-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# 환경 변수 설정
export API_BASE_URL="<위에서 확인한 엔드포인트>"
```

### 3. 포트 충돌
```bash
# 다른 포트 사용
streamlit run src/streamlit/app.py --server.port 8502
```

## 📊 API 엔드포인트

### 세션 관리
- `POST /sessions` - 새 세션 생성
- `GET /sessions/{id}` - 세션 조회
- `GET /status/{id}` - 상태 확인

### Agent 실행
- `POST /analysis` - 비즈니스 분석 (Product Insight Agent)
- `POST /names/suggest` - 상호명 제안 (Reporter Agent)
- `POST /signboards/generate` - 간판 생성 (Signboard Agent)
- `POST /interiors/generate` - 인테리어 추천 (Interior Agent) ✅
- `POST /report/generate` - 보고서 생성 (Report Generator Agent)

## 🎯 다음 단계

1. **Task 19**: Report Generator Agent Bedrock 통합
2. **Phase 5**: Fallback 거버넌스 및 자율 실행
3. **Phase 6**: 통합 테스트
4. **Phase 7**: 문서화
5. **Phase 8**: 데모 비디오 제작

## 📝 참고사항

- Streamlit 앱은 개발 모드로 실행됩니다
- API Gateway는 AWS dev 환경을 사용합니다
- Bedrock 통합은 `ENABLE_FALLBACK=false` 설정으로 Bedrock Only 모드입니다
- 모든 Agent는 Reasoning LLM을 사용하여 자율적으로 의사결정합니다
