#!/bin/bash
# 개발환경 활성화 및 검증

echo "🚀 개발환경 활성화 중..."

# 가상환경 확인 및 활성화
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -d "venv" ]]; then
        echo "📦 가상환경 활성화 중..."
        source venv/bin/activate
    else
        echo "❌ 가상환경이 없습니다. 다음 명령어로 생성하세요:"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
else
    echo "✅ 가상환경이 이미 활성화되어 있습니다: $VIRTUAL_ENV"
fi

# 환경변수 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src/lambda"

# 의존성 확인
echo "🔍 의존성 확인 중..."
if ! python -c "import boto3, requests, pytest" 2>/dev/null; then
    echo "⚠️  일부 의존성이 누락되었습니다. 설치 중..."
    pip install -r requirements.txt
fi

echo "✅ 개발환경 활성화 완료!"
echo ""
echo "🔧 주요 명령어:"
echo "  ./scripts/setup-local.sh              - 로컬 환경 설정 (Docker 서비스 시작)"
echo "  python scripts/validate-environment.py - 환경 검증"
echo "  python -m pytest tests/integration/ -v - 통합 테스트 실행"
echo "  ./scripts/sam-build.sh                - SAM 애플리케이션 빌드"
echo "  ./scripts/sam-local.sh                - 로컬 API 서버 시작"
echo "  cd src/streamlit && streamlit run app.py - Streamlit 앱 실행"
echo ""
echo "🌐 로컬 서비스 URL:"
echo "  - DynamoDB Admin: http://localhost:8002"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Chroma API: http://localhost:8001"