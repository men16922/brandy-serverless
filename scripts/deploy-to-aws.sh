#!/bin/bash
# AWS 배포 스크립트 - Lambda + API Gateway + DynamoDB

set -e

echo "=========================================="
echo "  AI Branding Chatbot - AWS 배포"
echo "=========================================="
echo ""

# 환경 변수 확인
ENVIRONMENT=${1:-dev}
echo "📦 배포 환경: $ENVIRONMENT"
echo ""

# AWS 자격 증명 확인
echo "🔐 AWS 자격 증명 확인..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS 자격 증명이 설정되지 않았습니다."
    echo "   aws configure를 실행하여 설정하세요."
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "✓ AWS Account: $AWS_ACCOUNT_ID"
echo "✓ AWS Region: $AWS_REGION"
echo ""

# Bedrock 모델 가용성 확인
echo "🤖 Bedrock 모델 가용성 확인..."
if aws bedrock list-foundation-models --region $AWS_REGION > /dev/null 2>&1; then
    echo "✓ Bedrock 접근 가능"
    
    # Claude 모델 확인
    if aws bedrock list-foundation-models --region $AWS_REGION \
        --query "modelSummaries[?contains(modelId, 'claude')].modelId" \
        --output text | grep -q "claude"; then
        echo "✓ Claude 모델 사용 가능"
    else
        echo "⚠️  Claude 모델을 찾을 수 없습니다. 계속 진행하시겠습니까? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "⚠️  Bedrock 접근 불가 (IAM 권한 확인 필요)"
    echo "   계속 진행하시겠습니까? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# SAM 빌드
echo "🔨 SAM 애플리케이션 빌드 중..."
if sam build; then
    echo "✓ 빌드 완료"
else
    echo "❌ 빌드 실패"
    exit 1
fi
echo ""

# 배포 확인
echo "🚀 배포 준비 완료"
echo ""
echo "배포 정보:"
echo "  - 환경: $ENVIRONMENT"
echo "  - 리전: $AWS_REGION"
echo "  - 계정: $AWS_ACCOUNT_ID"
echo ""
echo "예상 리소스:"
echo "  - Lambda 함수: 7개 (Supervisor + 6 Agents)"
echo "  - API Gateway: 1개 (HTTP API)"
echo "  - DynamoDB 테이블: 1개"
echo "  - S3 버킷: 1개"
echo "  - IAM 역할: 자동 생성"
echo ""
echo "예상 비용:"
echo "  - Lambda: 프리티어 내 무료 (1M 요청/월)"
echo "  - API Gateway: 프리티어 내 무료 (1M 요청/월)"
echo "  - DynamoDB: 프리티어 내 무료 (25GB)"
echo "  - S3: 프리티어 내 무료 (5GB)"
echo "  - Bedrock: 사용량 기반 (~$0.50/10회 테스트)"
echo ""
echo "배포를 시작하시겠습니까? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "배포 취소됨"
    exit 0
fi

# SAM 배포
echo ""
echo "🚀 AWS에 배포 중..."
echo ""

if [ -f samconfig.toml ]; then
    # 기존 설정 사용
    echo "기존 samconfig.toml 사용"
    sam deploy --config-env $ENVIRONMENT
else
    # 대화형 배포
    echo "첫 배포 - 대화형 설정"
    sam deploy --guided --config-env $ENVIRONMENT
fi

# 배포 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ 배포 완료!"
    echo "=========================================="
    echo ""
    
    # 스택 정보 가져오기
    STACK_NAME="ai-branding-chatbot-$ENVIRONMENT"
    
    echo "📊 배포된 리소스:"
    echo ""
    
    # API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
        --output text 2>/dev/null || echo "N/A")
    
    if [ "$API_URL" != "N/A" ]; then
        echo "🌐 API Gateway URL:"
        echo "   $API_URL"
        echo ""
        
        echo "📝 테스트 명령어:"
        echo ""
        echo "# 세션 생성"
        echo "curl -X POST $API_URL/sessions \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"businessInfo\": {\"industry\": \"restaurant\", \"region\": \"seoul\", \"size\": \"small\"}}'"
        echo ""
        echo "# 세션 상태 조회 (세션 ID 필요)"
        echo "curl $API_URL/status/{session-id}"
        echo ""
    fi
    
    # DynamoDB 테이블
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='SessionsTableName'].OutputValue" \
        --output text 2>/dev/null || echo "N/A")
    
    if [ "$TABLE_NAME" != "N/A" ]; then
        echo "🗄️  DynamoDB 테이블: $TABLE_NAME"
        echo ""
    fi
    
    # S3 버킷
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
        --output text 2>/dev/null || echo "N/A")
    
    if [ "$BUCKET_NAME" != "N/A" ]; then
        echo "🪣 S3 버킷: $BUCKET_NAME"
        echo ""
    fi
    
    echo "=========================================="
    echo ""
    echo "💡 다음 단계:"
    echo "   1. API URL로 테스트 요청 보내기"
    echo "   2. CloudWatch Logs에서 로그 확인"
    echo "   3. DynamoDB 콘솔에서 세션 데이터 확인"
    echo ""
    echo "🔍 로그 확인:"
    echo "   sam logs --stack-name $STACK_NAME --tail"
    echo ""
    echo "🗑️  삭제 (테스트 후):"
    echo "   sam delete --stack-name $STACK_NAME"
    echo ""
    
else
    echo ""
    echo "❌ 배포 실패"
    echo ""
    echo "문제 해결:"
    echo "  1. AWS 자격 증명 확인: aws sts get-caller-identity"
    echo "  2. IAM 권한 확인: CloudFormation, Lambda, API Gateway, DynamoDB 권한 필요"
    echo "  3. 리전 확인: Bedrock 사용 가능 리전인지 확인"
    echo "  4. 로그 확인: sam logs --stack-name $STACK_NAME"
    echo ""
    exit 1
fi
