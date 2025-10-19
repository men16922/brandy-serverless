#!/bin/bash
# 안전한 AWS 배포 스크립트
# 스택 상태 확인 및 자동 정리 후 재배포

set -e

echo "🚀 안전한 AWS 배포 시작"
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STACK_NAME="ai-branding-chatbot-dev"

# 1. AWS 자격증명 확인
echo -e "${BLUE}🔑 AWS 자격증명 확인...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 자격증명이 설정되지 않았습니다.${NC}"
    echo "다음 명령어로 설정하세요:"
    echo "  aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: $ACCOUNT_ID${NC}"
echo ""

# 2. 스택 상태 확인
echo -e "${BLUE}📦 스택 상태 확인...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "NOT_FOUND")

echo "현재 스택 상태: $STACK_STATUS"
echo ""

# 3. 문제 있는 스택 삭제
if [ "$STACK_STATUS" != "NOT_FOUND" ] && [ "$STACK_STATUS" != "CREATE_COMPLETE" ] && [ "$STACK_STATUS" != "UPDATE_COMPLETE" ]; then
    echo -e "${YELLOW}⚠️  스택이 비정상 상태입니다: $STACK_STATUS${NC}"
    echo "스택을 삭제하고 다시 배포합니다."
    echo ""
    
    echo -e "${BLUE}🗑️  스택 삭제 중...${NC}"
    aws cloudformation delete-stack --stack-name $STACK_NAME
    
    echo "스택 삭제 대기 중..."
    WAIT_COUNT=0
    MAX_WAIT=60  # 최대 10분 대기
    
    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        STATUS=$(aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null || echo "DELETE_COMPLETE")
        
        if [ "$STATUS" = "DELETE_COMPLETE" ]; then
            echo -e "${GREEN}✅ 스택 삭제 완료${NC}"
            break
        fi
        
        echo "  대기 중... ($((WAIT_COUNT * 10))초 경과, 상태: $STATUS)"
        sleep 10
        WAIT_COUNT=$((WAIT_COUNT + 1))
    done
    
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo -e "${RED}❌ 스택 삭제 타임아웃${NC}"
        echo "수동으로 확인하세요:"
        echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME"
        exit 1
    fi
    echo ""
fi

# 4. OpenAI API 키 확인
echo -e "${BLUE}🔑 OpenAI API 키 확인...${NC}"
SECRET_EXISTS=$(aws secretsmanager describe-secret \
    --secret-id openai-api-key \
    --query 'Name' \
    --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$SECRET_EXISTS" = "NOT_FOUND" ]; then
    echo -e "${YELLOW}⚠️  OpenAI API 키가 Secrets Manager에 없습니다.${NC}"
    echo ""
    echo "다음 명령어로 추가하세요:"
    echo "  aws secretsmanager create-secret \\"
    echo "    --name openai-api-key \\"
    echo "    --secret-string '{\"api_key\":\"sk-your-key-here\"}' \\"
    echo "    --region us-east-1"
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ OpenAI API 키 확인됨${NC}"
fi
echo ""

# 5. SAM 빌드
echo -e "${BLUE}🔨 SAM 빌드 중...${NC}"
echo "이 작업은 2-3분 소요됩니다..."
echo "Docker 컨테이너를 사용하여 빌드합니다..."
echo ""

if sam build --config-env dev --use-container; then
    echo -e "${GREEN}✅ SAM 빌드 완료${NC}"
else
    echo -e "${RED}❌ SAM 빌드 실패${NC}"
    echo "빌드 로그를 확인하세요."
    echo ""
    echo "문제 해결:"
    echo "1. Docker가 실행 중인지 확인: docker info"
    echo "2. Python 버전 확인: python3 --version"
    echo "3. SAM CLI 버전 확인: sam --version"
    exit 1
fi
echo ""

# 6. SAM 배포
echo -e "${BLUE}🚀 SAM 배포 중...${NC}"
echo "이 작업은 5-10분 소요됩니다..."
echo ""

if sam deploy --config-env dev --no-confirm-changeset --no-fail-on-empty-changeset; then
    echo -e "${GREEN}✅ SAM 배포 완료${NC}"
else
    echo -e "${RED}❌ SAM 배포 실패${NC}"
    echo ""
    echo "실패 원인 확인:"
    aws cloudformation describe-stack-events \
        --stack-name $STACK_NAME \
        --max-items 20 \
        --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].[Timestamp,LogicalResourceId,ResourceStatusReason]' \
        --output table
    exit 1
fi
echo ""

# 7. API Gateway URL 확인
echo -e "${BLUE}🌐 API Gateway URL 확인...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
    echo -e "${GREEN}✅ API Gateway URL:${NC}"
    echo "   $API_URL"
    echo ""
    
    # .env 파일 업데이트
    if [ -f .env ]; then
        sed -i.bak '/^API_BASE_URL=/d' .env 2>/dev/null || true
        rm -f .env.bak
    fi
    echo "API_BASE_URL=$API_URL" >> .env
    echo -e "${GREEN}✅ .env 파일 업데이트 완료${NC}"
    echo ""
    
    # API 테스트
    echo -e "${BLUE}🧪 API 연결 테스트...${NC}"
    sleep 5  # Cold Start 대기
    if curl -s -f "$API_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API 정상 동작${NC}"
    else
        echo -e "${YELLOW}⚠️  API 응답 없음 (Cold Start 가능)${NC}"
        echo "잠시 후 다시 시도하세요."
    fi
else
    echo -e "${YELLOW}⚠️  API URL을 자동으로 가져올 수 없습니다.${NC}"
    echo "AWS Console에서 확인하세요:"
    echo "  https://console.aws.amazon.com/cloudformation/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}🎉 다음 단계:${NC}"
echo ""
echo "1. Streamlit 앱 시작:"
echo "   streamlit run src/streamlit/app.py"
echo ""
echo "2. 브라우저 접속:"
echo "   http://localhost:8501"
echo ""
if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
    echo "3. API URL:"
    echo "   $API_URL"
    echo ""
fi
echo "4. 로그 확인:"
echo "   sam logs --stack-name $STACK_NAME --tail"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
