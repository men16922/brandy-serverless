#!/bin/bash
# Bedrock 설정 검증 스크립트
# AWS Bedrock 서비스 가용성 및 IAM 권한 확인

set -e

echo "🔍 Amazon Bedrock 설정 검증 중..."
echo ""

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 오류 카운터
error_count=0
warning_count=0

# AWS CLI 설치 확인
echo "📦 AWS CLI 확인..."
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI가 설치되지 않았습니다.${NC}"
    echo "다음 명령어로 AWS CLI를 설치하세요:"
    echo "  macOS: brew install awscli"
    echo "  Linux: pip install awscli"
    echo "  Windows: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI 설치됨: $(aws --version)${NC}"
echo ""

# AWS 자격증명 확인
echo "🔑 AWS 자격증명 확인..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 자격증명이 설정되지 않았습니다.${NC}"
    echo "다음 명령어로 AWS 자격증명을 설정하세요:"
    echo "  aws configure"
    echo "또는 환경 변수를 설정하세요:"
    echo "  export AWS_ACCESS_KEY_ID=your_key"
    echo "  export AWS_SECRET_ACCESS_KEY=your_secret"
    echo "  export AWS_DEFAULT_REGION=us-east-1"
    exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity)
ACCOUNT_ID=$(echo $CALLER_IDENTITY | jq -r '.Account')
USER_ARN=$(echo $CALLER_IDENTITY | jq -r '.Arn')
echo -e "${GREEN}✅ AWS 자격증명 확인됨${NC}"
echo "   Account ID: $ACCOUNT_ID"
echo "   User/Role: $USER_ARN"
echo ""

# 환경 변수 로드
echo "⚙️  환경 변수 확인..."
BEDROCK_REGION=${BEDROCK_REGION:-us-east-1}
CLAUDE_MODEL_ID=${CLAUDE_MODEL_ID:-us.anthropic.claude-sonnet-4-20250514-v1:0}
SDXL_MODEL_ID=${SDXL_MODEL_ID:-stability.stable-diffusion-xl-v1}
BEDROCK_KB_ID=${BEDROCK_KB_ID:-}
BEDROCK_AGENT_ID=${BEDROCK_AGENT_ID:-}
BEDROCK_AGENT_ALIAS_ID=${BEDROCK_AGENT_ALIAS_ID:-}
ENABLE_FALLBACK=${ENABLE_FALLBACK:-false}

echo "   BEDROCK_REGION: $BEDROCK_REGION"
echo "   CLAUDE_MODEL_ID: $CLAUDE_MODEL_ID"
echo "   SDXL_MODEL_ID: $SDXL_MODEL_ID"
echo "   BEDROCK_KB_ID: ${BEDROCK_KB_ID:-'Not configured'}"
echo "   BEDROCK_AGENT_ID: ${BEDROCK_AGENT_ID:-'Not configured'}"
echo "   ENABLE_FALLBACK: $ENABLE_FALLBACK"
echo ""

# Bedrock 서비스 가용성 확인
echo "🌐 Bedrock 서비스 가용성 확인 (Region: $BEDROCK_REGION)..."
if ! aws bedrock list-foundation-models --region $BEDROCK_REGION &> /dev/null; then
    echo -e "${RED}❌ Bedrock 서비스에 접근할 수 없습니다.${NC}"
    echo "다음을 확인하세요:"
    echo "  1. Region이 Bedrock을 지원하는지 확인 (us-east-1, us-west-2 등)"
    echo "  2. AWS 계정에서 Bedrock 서비스가 활성화되었는지 확인"
    echo "  3. IAM 권한에 bedrock:ListFoundationModels가 포함되어 있는지 확인"
    error_count=$((error_count + 1))
else
    echo -e "${GREEN}✅ Bedrock 서비스 접근 가능${NC}"
fi
echo ""

# Claude 모델 가용성 확인
echo "🤖 Claude 4.0 Sonnet 모델 확인..."
CLAUDE_AVAILABLE=$(aws bedrock list-foundation-models \
    --region $BEDROCK_REGION \
    --by-provider anthropic \
    --query "modelSummaries[?modelId=='$CLAUDE_MODEL_ID'].modelId" \
    --output text 2>/dev/null || echo "")

if [ -z "$CLAUDE_AVAILABLE" ]; then
    echo -e "${RED}❌ Claude 모델을 찾을 수 없습니다: $CLAUDE_MODEL_ID${NC}"
    echo "사용 가능한 Claude 모델 목록:"
    aws bedrock list-foundation-models \
        --region $BEDROCK_REGION \
        --by-provider anthropic \
        --query "modelSummaries[*].[modelId,modelName]" \
        --output table 2>/dev/null || echo "  (모델 목록을 가져올 수 없습니다)"
    error_count=$((error_count + 1))
else
    echo -e "${GREEN}✅ Claude 모델 사용 가능: $CLAUDE_MODEL_ID${NC}"
fi
echo ""

# SDXL 모델 가용성 확인
echo "🎨 Stable Diffusion XL 모델 확인..."
SDXL_AVAILABLE=$(aws bedrock list-foundation-models \
    --region $BEDROCK_REGION \
    --by-provider stability \
    --query "modelSummaries[?modelId=='$SDXL_MODEL_ID'].modelId" \
    --output text 2>/dev/null || echo "")

if [ -z "$SDXL_AVAILABLE" ]; then
    echo -e "${RED}❌ SDXL 모델을 찾을 수 없습니다: $SDXL_MODEL_ID${NC}"
    echo "사용 가능한 Stability AI 모델 목록:"
    aws bedrock list-foundation-models \
        --region $BEDROCK_REGION \
        --by-provider stability \
        --query "modelSummaries[*].[modelId,modelName]" \
        --output table 2>/dev/null || echo "  (모델 목록을 가져올 수 없습니다)"
    error_count=$((error_count + 1))
else
    echo -e "${GREEN}✅ SDXL 모델 사용 가능: $SDXL_MODEL_ID${NC}"
fi
echo ""

# IAM 권한 확인 - bedrock:InvokeModel
echo "🔐 IAM 권한 확인..."
echo "   bedrock:InvokeModel 권한 테스트 중..."

# Claude 모델 호출 테스트 (실제 호출하지 않고 권한만 확인)
INVOKE_TEST=$(aws bedrock-runtime invoke-model \
    --region $BEDROCK_REGION \
    --model-id $CLAUDE_MODEL_ID \
    --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1,"messages":[{"role":"user","content":"test"}]}' \
    /dev/stdout 2>&1 || echo "PERMISSION_ERROR")

if echo "$INVOKE_TEST" | grep -q "AccessDeniedException\|UnauthorizedException"; then
    echo -e "${RED}❌ bedrock:InvokeModel 권한이 없습니다.${NC}"
    echo "IAM 정책에 다음 권한을 추가하세요:"
    echo '  {
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ],
    "Resource": "arn:aws:bedrock:*::foundation-model/*"
  }'
    error_count=$((error_count + 1))
elif echo "$INVOKE_TEST" | grep -q "PERMISSION_ERROR"; then
    echo -e "${YELLOW}⚠️  bedrock:InvokeModel 권한 확인 실패 (네트워크 오류 가능)${NC}"
    warning_count=$((warning_count + 1))
else
    echo -e "${GREEN}✅ bedrock:InvokeModel 권한 확인됨${NC}"
fi
echo ""

# Knowledge Base 확인 (선택사항)
if [ -n "$BEDROCK_KB_ID" ]; then
    echo "📚 Knowledge Base 확인..."
    KB_EXISTS=$(aws bedrock-agent get-knowledge-base \
        --region $BEDROCK_REGION \
        --knowledge-base-id $BEDROCK_KB_ID \
        --query "knowledgeBase.knowledgeBaseId" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$KB_EXISTS" ]; then
        echo -e "${RED}❌ Knowledge Base를 찾을 수 없습니다: $BEDROCK_KB_ID${NC}"
        echo "다음을 확인하세요:"
        echo "  1. Knowledge Base ID가 올바른지 확인"
        echo "  2. Knowledge Base가 $BEDROCK_REGION 리전에 있는지 확인"
        echo "  3. IAM 권한에 bedrock:GetKnowledgeBase가 포함되어 있는지 확인"
        error_count=$((error_count + 1))
    else
        echo -e "${GREEN}✅ Knowledge Base 존재 확인: $BEDROCK_KB_ID${NC}"
        
        # Retrieve 권한 확인
        echo "   bedrock:Retrieve 권한 테스트 중..."
        RETRIEVE_TEST=$(aws bedrock-agent-runtime retrieve \
            --region $BEDROCK_REGION \
            --knowledge-base-id $BEDROCK_KB_ID \
            --retrieval-query text="test" 2>&1 || echo "PERMISSION_ERROR")
        
        if echo "$RETRIEVE_TEST" | grep -q "AccessDeniedException\|UnauthorizedException"; then
            echo -e "${RED}❌ bedrock:Retrieve 권한이 없습니다.${NC}"
            error_count=$((error_count + 1))
        elif echo "$RETRIEVE_TEST" | grep -q "PERMISSION_ERROR"; then
            echo -e "${YELLOW}⚠️  bedrock:Retrieve 권한 확인 실패${NC}"
            warning_count=$((warning_count + 1))
        else
            echo -e "${GREEN}✅ bedrock:Retrieve 권한 확인됨${NC}"
        fi
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  Knowledge Base ID가 설정되지 않았습니다 (선택사항)${NC}"
    echo "   Knowledge Base를 사용하려면 BEDROCK_KB_ID 환경 변수를 설정하세요."
    warning_count=$((warning_count + 1))
    echo ""
fi

# Bedrock Agent 확인 (선택사항)
if [ -n "$BEDROCK_AGENT_ID" ]; then
    echo "🤖 Bedrock Agent 확인..."
    AGENT_EXISTS=$(aws bedrock-agent get-agent \
        --region $BEDROCK_REGION \
        --agent-id $BEDROCK_AGENT_ID \
        --query "agent.agentId" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$AGENT_EXISTS" ]; then
        echo -e "${RED}❌ Bedrock Agent를 찾을 수 없습니다: $BEDROCK_AGENT_ID${NC}"
        error_count=$((error_count + 1))
    else
        echo -e "${GREEN}✅ Bedrock Agent 존재 확인: $BEDROCK_AGENT_ID${NC}"
        
        # Agent Alias 확인
        if [ -n "$BEDROCK_AGENT_ALIAS_ID" ]; then
            ALIAS_EXISTS=$(aws bedrock-agent get-agent-alias \
                --region $BEDROCK_REGION \
                --agent-id $BEDROCK_AGENT_ID \
                --agent-alias-id $BEDROCK_AGENT_ALIAS_ID \
                --query "agentAlias.agentAliasId" \
                --output text 2>/dev/null || echo "")
            
            if [ -z "$ALIAS_EXISTS" ]; then
                echo -e "${RED}❌ Agent Alias를 찾을 수 없습니다: $BEDROCK_AGENT_ALIAS_ID${NC}"
                error_count=$((error_count + 1))
            else
                echo -e "${GREEN}✅ Agent Alias 존재 확인: $BEDROCK_AGENT_ALIAS_ID${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Agent Alias ID가 설정되지 않았습니다${NC}"
            warning_count=$((warning_count + 1))
        fi
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  Bedrock Agent ID가 설정되지 않았습니다 (선택사항)${NC}"
    echo "   AgentCore를 사용하려면 BEDROCK_AGENT_ID와 BEDROCK_AGENT_ALIAS_ID를 설정하세요."
    warning_count=$((warning_count + 1))
    echo ""
fi

# Fallback 설정 경고
if [ "$ENABLE_FALLBACK" = "true" ]; then
    echo -e "${YELLOW}⚠️  Fallback이 활성화되어 있습니다 (ENABLE_FALLBACK=true)${NC}"
    echo "   해커톤 제출 시에는 ENABLE_FALLBACK=false로 설정하세요."
    warning_count=$((warning_count + 1))
    echo ""
fi

# 최종 결과 출력
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ $error_count -eq 0 ]; then
    echo -e "${GREEN}✅ Bedrock 설정 검증 완료!${NC}"
    echo ""
    echo "모든 필수 검증을 통과했습니다."
    if [ $warning_count -gt 0 ]; then
        echo -e "${YELLOW}경고 $warning_count개가 있습니다. 위 내용을 확인하세요.${NC}"
    fi
    echo ""
    echo "🚀 다음 단계:"
    echo "  1. SAM 빌드: sam build"
    echo "  2. SAM 배포: sam deploy --guided"
    echo "  3. 통합 테스트: python -m pytest tests/integration/"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Bedrock 설정 검증 실패!${NC}"
    echo ""
    echo -e "${RED}오류 $error_count개를 발견했습니다.${NC}"
    if [ $warning_count -gt 0 ]; then
        echo -e "${YELLOW}경고 $warning_count개도 있습니다.${NC}"
    fi
    echo ""
    echo "위의 오류를 수정한 후 다시 실행하세요:"
    echo "  ./scripts/verify-bedrock-setup.sh"
    echo ""
    echo "도움말:"
    echo "  - Bedrock 문서: https://docs.aws.amazon.com/bedrock/"
    echo "  - IAM 권한 설정: https://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html"
    echo "  - 모델 가용성: https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html"
    echo ""
    exit 1
fi
