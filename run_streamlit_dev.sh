#!/bin/bash

# Streamlit 앱 실행 스크립트 (AWS Dev 환경)
# AWS API Gateway를 사용하여 Streamlit 앱 실행

set -e

echo "🚀 Starting Streamlit Application with AWS Dev API..."

# 가상환경 활성화 확인
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Streamlit 의존성 확인
echo "📦 Checking Streamlit dependencies..."
pip install -q streamlit requests pillow plotly boto3

# AWS Dev API Gateway 엔드포인트 설정
export API_BASE_URL="https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev"

# Docker 서비스 상태 확인 (로컬 리소스용)
echo "🐳 Checking Docker services..."
if docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
    echo "✅ Docker services are running"
else
    echo "⚠️  Docker services not running. Starting..."
    docker-compose -f docker-compose.local.yml up -d
    sleep 5
fi

# Streamlit 앱 실행
echo ""
echo "🎨 Starting Streamlit app with logging..."
echo "📍 API Base URL: $API_BASE_URL"
echo "🌐 Streamlit will be available at: http://localhost:8501"
echo "📋 Logs will be displayed below"
echo ""
echo "✨ Features:"
echo "  - 5-step AI branding workflow"
echo "  - Real-time status monitoring"
echo "  - Interactive selection interface"
echo "  - PDF report generation"
echo "  - Debug logging enabled"
echo ""
echo "🛠️  Local development services:"
echo "  - DynamoDB Admin: http://localhost:8002"
echo "  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""
echo "=== Streamlit Logs ==="
echo ""

# Run with logging to both console and file
streamlit run src/streamlit/app.py --server.port 8501 --server.address localhost 2>&1 | tee streamlit.log
