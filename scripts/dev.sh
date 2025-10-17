#!/bin/bash
# 통합 개발 스크립트
# Usage: ./scripts/dev.sh [command]

set -e

COMMAND=${1:-help}

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_error "가상환경이 활성화되지 않았습니다."
        echo "다음 명령어로 활성화하세요:"
        echo "  source venv/bin/activate"
        exit 1
    fi
    print_success "가상환경 활성화됨: $VIRTUAL_ENV"
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker가 실행되지 않았습니다."
        exit 1
    fi
    print_success "Docker 실행 중"
}

setup_local() {
    print_status "로컬 환경 설정 중..."
    check_venv
    check_docker
    
    # Docker 서비스 시작
    docker-compose -f docker-compose.local.yml up -d
    
    # 서비스 헬스체크
    print_status "서비스 헬스체크 중..."
    sleep 5
    
    # 의존성 설치
    pip install -r requirements.txt
    
    print_success "로컬 환경 설정 완료!"
    echo ""
    echo "🔗 서비스 URL:"
    echo "  - DynamoDB Admin: http://localhost:8002"
    echo "  - MinIO Console: http://localhost:9001"
    echo "  - Chroma API: http://localhost:8001"
}

run_tests() {
    print_status "통합 테스트 실행 중..."
    check_venv
    
    # 환경 검증 먼저 실행
    python scripts/validate-environment.py
    
    # Bedrock 설정 검증 (선택사항 - AWS 자격증명이 있는 경우)
    if [ -n "$AWS_ACCESS_KEY_ID" ] || aws sts get-caller-identity &> /dev/null; then
        print_status "Bedrock 설정 검증 중..."
        ./scripts/verify-bedrock-setup.sh || print_warning "Bedrock 검증 실패 (로컬 개발은 계속 가능)"
    else
        print_warning "AWS 자격증명 없음 - Bedrock 검증 건너뜀 (로컬 개발 모드)"
    fi
    
    # 통합 테스트 실행
    python -m pytest tests/integration/ -v
    
    print_success "모든 테스트 통과!"
}

validate_env() {
    print_status "환경 검증 중..."
    check_venv
    python scripts/validate-environment.py
    
    # Bedrock 설정 검증 (선택사항)
    if [ -n "$AWS_ACCESS_KEY_ID" ] || aws sts get-caller-identity &> /dev/null; then
        print_status "Bedrock 설정 검증 중..."
        ./scripts/verify-bedrock-setup.sh
    else
        print_warning "AWS 자격증명 없음 - Bedrock 검증 건너뜀"
        echo "Bedrock 검증을 실행하려면 AWS 자격증명을 설정하세요:"
        echo "  aws configure"
    fi
}

build_sam() {
    print_status "SAM 애플리케이션 빌드 중..."
    ./scripts/sam-build.sh
}

start_local_api() {
    print_status "로컬 API 서버 시작 중..."
    check_venv
    check_docker
    ./scripts/sam-local.sh
}

start_streamlit() {
    print_status "Streamlit 앱 시작 중..."
    check_venv
    cd src/streamlit
    streamlit run app.py
}

cleanup() {
    print_status "환경 정리 중..."
    docker-compose -f docker-compose.local.yml down -v
    print_success "정리 완료!"
}

show_help() {
    echo "AI 브랜딩 챗봇 개발 스크립트"
    echo ""
    echo "사용법: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - 로컬 환경 설정 (Docker 서비스 시작)"
    echo "  test      - 통합 테스트 실행 (Bedrock 검증 포함)"
    echo "  validate  - 환경 검증 (Docker + Bedrock)"
    echo "  build     - SAM 애플리케이션 빌드"
    echo "  api       - 로컬 API 서버 시작"
    echo "  app       - Streamlit 앱 시작"
    echo "  cleanup   - 환경 정리 (Docker 서비스 중지)"
    echo "  help      - 이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 setup    # 로컬 환경 설정"
    echo "  $0 test     # 테스트 실행 (Bedrock 검증 포함)"
    echo "  $0 validate # 환경 및 Bedrock 검증"
    echo "  $0 api      # API 서버 시작"
    echo ""
    echo "Bedrock 검증:"
    echo "  AWS 자격증명이 설정된 경우 자동으로 Bedrock 설정을 검증합니다."
    echo "  로컬 개발만 하는 경우 AWS 자격증명 없이도 사용 가능합니다."
}

case $COMMAND in
    setup)
        setup_local
        ;;
    test)
        run_tests
        ;;
    validate)
        validate_env
        ;;
    build)
        build_sam
        ;;
    api)
        start_local_api
        ;;
    app)
        start_streamlit
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "알 수 없는 명령어: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac