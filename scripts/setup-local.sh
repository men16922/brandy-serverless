#!/bin/bash
# 로컬 개발환경 설정

set -e

echo "🚀 로컬 개발환경 설정 중..."

# Docker 실행 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다. Docker를 시작하고 다시 시도하세요."
    exit 1
fi

# 로컬 서비스 시작
echo "📦 로컬 서비스 시작 (DynamoDB, MinIO, Chroma)..."
docker-compose -f docker-compose.local.yml up -d

# 서비스 준비 대기
echo "⏳ 서비스 준비 중..."
sleep 10

# 데이터 디렉토리 생성
echo "📁 데이터 디렉토리 생성..."
mkdir -p data/chroma
mkdir -p data/fallbacks

# Python 의존성 설치
echo "🐍 Python 의존성 설치..."
pip install -r requirements.txt

echo "✅ 로컬 개발환경 설정 완료!"
echo ""
echo "🔗 서비스 URL:"
echo "  - DynamoDB Local: http://localhost:8000"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Chroma: http://localhost:8001"
echo ""
echo "🚀 Streamlit 앱 실행:"
echo "  cd src/streamlit && streamlit run app.py"