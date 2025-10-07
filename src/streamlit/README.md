# AI 브랜딩 챗봇 - Streamlit Frontend

5단계 자동 워크플로로 완전한 브랜딩 패키지를 생성하는 웹 인터페이스입니다.

## 주요 기능

### 🎯 5단계 워크플로 UI
- **1단계**: 비즈니스 정보 입력 (업종/지역/규모)
- **2단계**: AI 상호명 제안 및 선택
- **3단계**: 다중 AI 간판 디자인 생성
- **4단계**: 맞춤형 인테리어 추천
- **5단계**: 종합 브랜딩 보고서 다운로드

### 📊 실시간 상태 모니터링
- 워크플로 진행률 표시
- 에이전트별 실행 상태 추적
- Supervisor Agent를 통한 전체 상태 조회
- 자동 새로고침 및 폴링

### 🎨 인터랙티브 선택 인터페이스
- 상호명 후보 카드 UI (점수 표시)
- 이미지 갤러리 (간판/인테리어)
- 색상 팔레트 시각화
- 재생성 및 선택 기능

## 기술 스택

- **Frontend**: Streamlit 1.28.0
- **HTTP Client**: Requests 2.31.0
- **Image Processing**: Pillow 10.0.0
- **Data Visualization**: Plotly 5.17.0
- **Cloud Integration**: Boto3 1.29.0

## 설치 및 실행

### 1. 의존성 설치
```bash
# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r src/streamlit/requirements.txt
```

### 2. 환경 변수 설정
```bash
# API 엔드포인트 설정 (기본값: http://localhost:3000)
export API_BASE_URL="http://localhost:3000"

# Streamlit 포트 설정 (기본값: 8501)
export STREAMLIT_SERVER_PORT=8501
```

### 3. 앱 실행
```bash
# 간편 실행 스크립트
./scripts/run-streamlit.sh

# 또는 직접 실행
cd src/streamlit
streamlit run app.py
```

### 4. 브라우저 접속
```
http://localhost:8501
```

## API 연동

### 필수 API 엔드포인트
- `POST /sessions` - 새 세션 생성
- `GET /status/{id}` - Supervisor Agent 상태 조회
- `POST /names/select` - 상호명 선택
- `POST /names/regenerate` - 상호명 재생성
- `POST /signboards/select` - 간판 선택
- `POST /interiors/select` - 인테리어 선택
- `GET /report/url` - 보고서 다운로드 링크

### SAM Local API 연동
```bash
# SAM Local API 시작
sam build
sam local start-api --port 3000

# Streamlit 앱 시작 (별도 터미널)
./scripts/run-streamlit.sh
```

## 주요 컴포넌트

### 세션 관리
```python
# 세션 상태 초기화
init_session_state()

# 세션 생성
session_id = create_session(business_info)

# 상태 폴링
poll_session_status()
```

### UI 컴포넌트
```python
# 진행률 표시
display_progress_bar()

# 에이전트 상태
display_agent_status()

# 결과 표시
display_business_names()
display_signboard_gallery()
display_interior_options()
display_report_download()
```

### 사용자 상호작용
```python
# 선택 액션
select_business_name(name)
select_signboard_image(url)
select_interior_option(url)

# 재생성
regenerate_business_names()
```

## 개발 가이드

### 디렉토리 구조
```
src/streamlit/
├── app.py              # 메인 애플리케이션
├── requirements.txt    # Python 의존성
└── README.md          # 이 파일
```

### 주요 함수 구조
```python
# 메인 애플리케이션
main()
├── init_session_state()
├── display_progress_bar()
├── display_agent_status()
├── poll_session_status()
└── step_content_functions()

# 단계별 컨텐츠
step1_business_analysis()
display_analysis_results()
display_business_names()
display_signboard_gallery()
display_interior_options()
display_report_download()

# API 통신
create_session()
get_session_status()
select_*()
regenerate_*()
download_report()
```

### 상태 관리
```python
# Streamlit 세션 상태
st.session_state.session_id      # 현재 세션 ID
st.session_state.current_step    # 현재 워크플로 단계
st.session_state.session_data    # 전체 세션 데이터
st.session_state.business_info   # 입력된 비즈니스 정보
st.session_state.polling_active  # 자동 새로고침 활성화
st.session_state.agent_status    # 에이전트별 실행 상태
```

## 환경별 설정

### 로컬 개발
```bash
API_BASE_URL=http://localhost:3000
STREAMLIT_SERVER_PORT=8501
```

### AWS 배포 (App Runner)
```bash
API_BASE_URL=https://your-api-gateway-url.amazonaws.com
STREAMLIT_SERVER_PORT=8080
```

## 트러블슈팅

### 일반적인 문제

1. **API 연결 실패**
   ```bash
   # SAM Local API 상태 확인
   curl http://localhost:3000/health
   
   # SAM Local 재시작
   sam local start-api --port 3000
   ```

2. **의존성 오류**
   ```bash
   # 가상환경 확인
   which python
   
   # 의존성 재설치
   pip install -r src/streamlit/requirements.txt
   ```

3. **포트 충돌**
   ```bash
   # 포트 사용 확인
   lsof -i :8501
   
   # 다른 포트 사용
   export STREAMLIT_SERVER_PORT=8502
   ```

4. **세션 상태 문제**
   - 브라우저 새로고침으로 세션 상태 초기화
   - "새 세션 시작" 버튼 클릭

### 디버깅 팁

1. **개발자 도구 활용**
   - 사이드바의 "개발 정보" 섹션 확인
   - API 연결 상태 모니터링
   - 세션 데이터 JSON 확인

2. **로그 확인**
   ```bash
   # Streamlit 로그
   streamlit run app.py --logger.level debug
   
   # SAM Local 로그
   sam local start-api --debug
   ```

3. **네트워크 디버깅**
   ```bash
   # API 엔드포인트 테스트
   curl -X POST http://localhost:3000/sessions \
     -H "Content-Type: application/json" \
     -d '{"industry":"restaurant","region":"seoul","size":"small"}'
   ```

## 성능 최적화

### 응답 시간 목표
- 텍스트 응답: ≤ 5초
- 이미지 생성: ≤ 30초
- 전체 워크플로: ≤ 5분

### 최적화 기법
- 자동 폴링 간격 조정 (2초)
- 이미지 썸네일 사용
- 세션 데이터 캐싱
- 에러 상태 즉시 표시

## 배포

### AWS App Runner 배포
```dockerfile
# Dockerfile (예시)
FROM python:3.11-slim

WORKDIR /app
COPY src/streamlit/ .
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
```

### 환경 변수 설정
```bash
API_BASE_URL=https://your-api-gateway.amazonaws.com
STREAMLIT_SERVER_PORT=8080
```

이 Streamlit 앱은 AI 브랜딩 챗봇의 완전한 사용자 인터페이스를 제공하며, 5단계 워크플로를 통해 사용자가 쉽게 브랜딩 패키지를 생성할 수 있도록 설계되었습니다.