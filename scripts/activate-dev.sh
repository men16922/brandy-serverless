#!/bin/bash
# 개발환경 활성화

echo "🚀 개발환경 활성화 중..."

# 가상환경 활성화
source venv/bin/activate

# 환경변수 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src/lambda"

echo "✅ 개발환경 활성화 완료!"
echo ""
echo "🔧 주요 명령어:"
echo "  ./scripts/setup-local.sh    - 로컬 환경 설정"
echo "  ./scripts/deploy-dev.sh     - 개발 환경 배포"
echo "  python scripts/test-models.py - 모델 테스트"
echo "  cd src/streamlit && streamlit run app.py - 앱 실행"