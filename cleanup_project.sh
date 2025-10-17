#!/bin/bash
# 프로젝트 정리 스크립트
# 불필요한 파일 및 중복 문서 제거

set -e

echo "🧹 프로젝트 정리 시작..."
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 삭제할 파일 목록
FILES_TO_DELETE=(
    # 테스트 응답 파일들 (중복)
    "response-bedrock-success.json"
    "response-bedrock-test.json"
    "response-complete.json"
    "response-debug.json"
    "response-final-bedrock.json"
    "response-final-test.json"
    "response-final.json"
    "response-fixed.json"
    "response-interior-bedrock.json"
    "response-interior-debug.json"
    "response-interior.json"
    "response-reporter-debug.json"
    "response-reporter.json"
    "response-success-final.json"
    "response-success.json"
    "response-v2.json"
    "response-with-permissions.json"
    "test-layer-check.json"
    "test-payload-interior.json"
    
    # 중복 환경 파일들
    ".env.dev"
    ".env.local"
    ".env.test"
    
    # 임시 로그 파일
    "mock_api.log"
    
    # 중복 가이드 문서들
    "CLEANUP_SUMMARY.md"
    "FINAL_STATUS.md"
    "STREAMLIT_GUIDE.md"
    "TESTING_GUIDE.md"
    "TEST_RESULTS.md"
    "TASK_15_COMPLETION_SUMMARY.md"
    
    # 임시 zip 파일
    "interior-agent-update.zip"
    
    # Mock API 서버 (실제 AWS 사용)
    "mock_api_server.py"
    "start_api_server.sh"
    
    # 중복 테스트 가이드
    "API_SERVER_SOLUTION.md"
    "LOCAL_TEST_RESULTS.md"
    "START_LOCAL_TEST.md"
)

# 삭제할 디렉토리 목록
DIRS_TO_DELETE=(
    "venv-test"
    "generated_images"
    "generated-diagrams"
)

# 파일 삭제
echo -e "${BLUE}📄 불필요한 파일 삭제 중...${NC}"
for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✓ 삭제: $file"
    fi
done

# 디렉토리 삭제
echo ""
echo -e "${BLUE}📁 불필요한 디렉토리 삭제 중...${NC}"
for dir in "${DIRS_TO_DELETE[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "  ✓ 삭제: $dir/"
    fi
done

# .DS_Store 파일 삭제 (macOS)
echo ""
echo -e "${BLUE}🍎 macOS 임시 파일 삭제 중...${NC}"
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
echo "  ✓ .DS_Store 파일 삭제 완료"

# Python 캐시 삭제
echo ""
echo -e "${BLUE}🐍 Python 캐시 삭제 중...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "  ✓ Python 캐시 삭제 완료"

# pytest 캐시 삭제
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo "  ✓ pytest 캐시 삭제 완료"
fi

# SAM 빌드 캐시 정리 (선택사항)
echo ""
echo -e "${YELLOW}⚠️  SAM 빌드 캐시를 삭제하시겠습니까? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    if [ -d ".aws-sam" ]; then
        rm -rf .aws-sam
        echo "  ✓ SAM 빌드 캐시 삭제 완료"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ 프로젝트 정리 완료!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 정리 후 프로젝트 구조 표시
echo -e "${BLUE}📊 정리된 프로젝트 구조:${NC}"
echo ""
tree -L 1 -I 'venv|.git|.aws-sam|node_modules' . 2>/dev/null || ls -la

echo ""
echo -e "${GREEN}🎉 다음 단계:${NC}"
echo "  1. 변경사항 확인: git status"
echo "  2. 커밋: git add . && git commit -m 'chore: cleanup unnecessary files'"
echo ""
