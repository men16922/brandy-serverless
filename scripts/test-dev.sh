#!/bin/bash
# Dev 환경 테스트 실행 스크립트 (AWS)

set -e

echo "☁️  Running tests in DEV environment (AWS)"
echo "=================================================="

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS credentials not configured"
    echo "Please run: aws configure"
    echo "Or set AWS_PROFILE environment variable"
    exit 1
fi

# Show AWS account info
echo "🔐 AWS Account:"
aws sts get-caller-identity --query 'Account' --output text

# Check if SAM stack is deployed
STACK_NAME="branding-chatbot"
echo ""
echo "🔍 Checking SAM stack deployment..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region us-east-1 > /dev/null 2>&1; then
    echo "✅ Stack '$STACK_NAME' is deployed"
    
    # Get stack outputs
    echo ""
    echo "📋 Stack Outputs:"
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region us-east-1 \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
else
    echo "⚠️  Warning: Stack '$STACK_NAME' not found"
    echo "Deploy the stack first: sam deploy --guided"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load dev environment variables
export ENV_FILE=.env.dev
echo ""
echo "📝 Using environment: $ENV_FILE"

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "❌ Error: .env.dev file not found"
    echo "Please create .env.dev with your AWS configuration"
    exit 1
fi

# Source .env.dev
set -a
source .env.dev
set +a

# Verify required environment variables
REQUIRED_VARS=(
    "ENVIRONMENT"
    "SESSIONS_TABLE"
    "AWS_DEFAULT_REGION"
)

echo ""
echo "🔍 Verifying environment variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        exit 1
    else
        echo "✅ $var=${!var}"
    fi
done

# Run tests
echo ""
echo "🧪 Running AgentCore integration tests..."
echo "=================================================="

if [ "$1" == "verbose" ]; then
    ./venv/bin/python -m pytest tests/integration/test_agentcore.py -v -s
elif [ "$1" == "coverage" ]; then
    ./venv/bin/python -m pytest tests/integration/test_agentcore.py -v --cov=src/lambda/agents/supervisor --cov-report=html
else
    ./venv/bin/python -m pytest tests/integration/test_agentcore.py -v
fi

TEST_EXIT_CODE=$?

echo ""
echo "=================================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed in DEV environment!"
    echo ""
    echo "📊 View AWS resources:"
    echo "   - DynamoDB: https://console.aws.amazon.com/dynamodb"
    echo "   - Lambda: https://console.aws.amazon.com/lambda"
    echo "   - CloudWatch Logs: https://console.aws.amazon.com/cloudwatch"
else
    echo "❌ Some tests failed"
    echo ""
    echo "🔍 Debug resources:"
    echo "   - CloudWatch Logs: aws logs tail /aws/lambda/branding-chatbot-supervisor-dev --follow"
    echo "   - DynamoDB: aws dynamodb scan --table-name $SESSIONS_TABLE"
fi

exit $TEST_EXIT_CODE
