#!/bin/bash
# 로컬 개발환경 설정

set -e

echo "🚀 로컬 개발환경 설정 중..."

# Python 가상환경 확인
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Python 가상환경이 활성화되지 않았습니다."
    echo "다음 명령어로 가상환경을 활성화하세요:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    exit 1
fi

echo "✅ Python 가상환경 활성화됨: $VIRTUAL_ENV"

# Docker 실행 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다. Docker를 시작하고 다시 시도하세요."
    exit 1
fi

# 기존 서비스 정리 (포트 충돌 방지)
echo "🧹 기존 서비스 정리..."
docker-compose -f docker-compose.local.yml down -v 2>/dev/null || true

# 로컬 서비스 시작
echo "📦 로컬 서비스 시작 (DynamoDB, MinIO, Chroma)..."
docker-compose -f docker-compose.local.yml up -d

# 서비스 헬스체크
echo "⏳ 서비스 헬스체크 중..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    
    # DynamoDB Local 체크
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "✅ DynamoDB Local 준비됨"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ DynamoDB Local 시작 실패"
        docker-compose -f docker-compose.local.yml logs dynamodb-local
        exit 1
    fi
    
    echo "⏳ DynamoDB Local 대기 중... ($attempt/$max_attempts)"
    sleep 2
done

# MinIO 헬스체크
attempt=0
while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    
    if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo "✅ MinIO 준비됨"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ MinIO 시작 실패"
        docker-compose -f docker-compose.local.yml logs minio
        exit 1
    fi
    
    echo "⏳ MinIO 대기 중... ($attempt/$max_attempts)"
    sleep 2
done

# Chroma 헬스체크
attempt=0
while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    
    if nc -z localhost 8001 2>/dev/null; then
        echo "✅ Chroma 준비됨"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Chroma 시작 실패"
        docker-compose -f docker-compose.local.yml logs chroma
        exit 1
    fi
    
    echo "⏳ Chroma 대기 중... ($attempt/$max_attempts)"
    sleep 2
done

# 데이터 디렉토리 생성
echo "📁 데이터 디렉토리 생성..."
mkdir -p data/chroma
mkdir -p data/fallbacks

# Python 의존성 설치 (가상환경에서)
echo "🐍 Python 의존성 설치 (가상환경: $VIRTUAL_ENV)..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 로컬 개발환경 설정 완료!"
echo ""
echo "🔗 서비스 URL:"
echo "  - DynamoDB Local: http://localhost:8000"
echo "  - DynamoDB Admin UI: http://localhost:8002"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  - MinIO API: http://localhost:9000"
echo "  - Chroma: http://localhost:8001"
echo ""
echo "🧪 통합 테스트 실행:"
echo "  python -m pytest tests/integration/ -v"
echo ""
echo "🚀 Streamlit 앱 실행:"
echo "  cd src/streamlit && streamlit run app.py"
echo ""
echo "📊 서비스 상태 확인:"
echo "  docker-compose -f docker-compose.local.yml ps"