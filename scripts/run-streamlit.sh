#!/bin/bash

# Streamlit 앱 실행 스크립트
# AWS API Gateway 엔드포인트를 사용하여 Streamlit 앱 실행

set -e

echo "🚀 Starting Streamlit Application..."

# 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

source venv/bin/activate

# Streamlit 의존성 설치
echo "📦 Installing Streamlit dependencies..."
pip install -q -r src/streamlit/requirements.txt

# API Gateway 엔드포인트 가져오기
echo "🔍 Getting API Gateway endpoint..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$API_ENDPOINT" ]; then
    echo "⚠️  Could not find API Gateway endpoint. Using default localhost:3000"
    API_ENDPOINT="http://localhost:3000"
else
    echo "✅ API Endpoint: $API_ENDPOINT"
fi

# 환경 변수 설정
export API_BASE_URL="$API_ENDPOINT"

# Streamlit 앱 실행
echo ""
echo "🎨 Starting Streamlit app..."
echo "📍 API Base URL: $API_BASE_URL"
echo "🌐 Streamlit will be available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run src/streamlit/app.py --server.port 8501 --server.address localhost
