#!/bin/bash
# Agent 테스트 실행

echo "🧪 Agent 테스트 실행 중..."

# 가상환경 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경을 먼저 활성화하세요: source venv/bin/activate"
    exit 1
fi

# 로컬 서비스 시작
echo "🐳 로컬 서비스 시작..."
docker-compose -f docker-compose.local.yml up -d
sleep 5

# 테스트 실행
echo "🧪 테스트 실행..."
python -m pytest tests/ -v

echo "✅ 테스트 완료!"