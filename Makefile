# AI 브랜딩 챗봇 개발 도구

.PHONY: help setup-local start-local stop-local deploy-dev clean test lint

help: ## 사용 가능한 명령어 표시
	@echo "AI 브랜딩 챗봇 개발 도구"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup-local: ## 로컬 개발 환경 설정
	@echo "🚀 로컬 개발 환경 설정 중..."
	./scripts/setup-local.sh

start-local: ## 로컬 서비스 시작
	@echo "📦 로컬 서비스 시작 중..."
	docker-compose -f docker-compose.local.yml up -d
	@echo "✅ 서비스가 시작되었습니다."
	@echo "  - DynamoDB Local: http://localhost:8000"
	@echo "  - MinIO Console: http://localhost:9001"
	@echo "  - Chroma: http://localhost:8001"

stop-local: ## 로컬 서비스 중지
	@echo "🛑 로컬 서비스 중지 중..."
	docker-compose -f docker-compose.local.yml down

streamlit: ## Streamlit 앱 실행
	@echo "🎨 Streamlit 앱 시작 중..."
	cd src/streamlit && streamlit run app.py

deploy-dev: ## 개발 환경 배포
	@echo "🚀 개발 환경 배포 중..."
	./scripts/deploy-dev.sh

clean: ## 임시 파일 및 캐시 정리
	@echo "🧹 정리 중..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf cdk.out/
	docker system prune -f

test: ## 테스트 실행
	@echo "🧪 테스트 실행 중..."
	python -m pytest tests/ -v

lint: ## 코드 린팅
	@echo "🔍 코드 린팅 중..."
	flake8 src/
	black --check src/

format: ## 코드 포맷팅
	@echo "✨ 코드 포맷팅 중..."
	black src/
	isort src/

install-deps: ## Python 의존성 설치
	@echo "📦 Python 의존성 설치 중..."
	pip install -r src/streamlit/requirements.txt
	pip install -r infrastructure/requirements.txt
	pip install pytest flake8 black isort

logs-local: ## 로컬 서비스 로그 확인
	docker-compose -f docker-compose.local.yml logs -f

status: ## 서비스 상태 확인
	@echo "📊 서비스 상태:"
	@docker-compose -f docker-compose.local.yml ps