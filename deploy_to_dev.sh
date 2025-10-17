#!/bin/bash
# AWS dev 환경 배포 스크립트

set -e

echo "🚀 AWS dev 환경 배포 시작..."
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# AWS 자격증명 확인
echo -e "${BLUE}🔑 AWS 자격증명 확인...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 자격증명이 설정되지 않았습니다.${NC}"
    echo "다음 명령어로 AWS 자격증명을 설정하세요:"
    echo "  aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: $ACCOUNT_ID${NC}"
echo ""

# SAM 빌드
echo -e "${BLUE}🔨 SAM 빌드 중...${NC}"
sam build --config-env dev

echo -e "${GREEN}✅ SAM 빌드 완료${NC}"
echo ""

# SAM 배포
echo -e "${BLUE}🚀 SAM 배포 중...${NC}"
sam deploy --config-env dev --no-confirm-changeset

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# API Gateway URL 가져오기
echo -e "${BLUE}🔍 API Gateway URL 확인 중...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$API_URL" ]; then
    echo -e "${YELLOW}⚠️  API URL을 자동으로 가져올 수 없습니다.${NC}"
    echo "AWS Console에서 확인하세요:"
    echo "  https://console.aws.amazon.com/cloudformation/"
else
    echo -e "${GREEN}✅ API Gateway URL:${NC}"
    echo "   $API_URL"
    echo ""
    
    # .env 파일 업데이트
    if [ -f .env ]; then
        # 기존 API_BASE_URL 제거
        sed -i.bak '/^API_BASE_URL=/d' .env
    fi
    
    # 새 API_BASE_URL 추가
    echo "API_BASE_URL=$API_URL" >> .env
    echo -e "${GREEN}✅ .env 파일 업데이트 완료${NC}"
    echo ""
    
    # API 테스트
    echo -e "${BLUE}🧪 API 테스트 중...${NC}"
    if curl -s -f "$API_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API 정상 동작${NC}"
    else
        echo -e "${YELLOW}⚠️  API 응답 없음 (배포 직후 Cold Start 가능)${NC}"
        echo "잠시 후 다시 시도하세요."
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 다음 단계:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Streamlit 앱 시작:"
echo "   streamlit run src/streamlit/app.py"
echo ""
echo "2. 브라우저에서 접속:"
echo "   http://localhost:8501"
echo ""
echo "3. API URL 확인:"
if [ -n "$API_URL" ]; then
    echo "   $API_URL"
else
    echo "   AWS Console에서 확인"
fi
echo ""
echo "4. 로그 확인:"
echo "   sam logs --stack-name ai-branding-chatbot-dev --tail"
echo ""
