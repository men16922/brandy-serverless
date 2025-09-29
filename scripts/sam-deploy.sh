#!/bin/bash

# SAM Deploy Script for AI Branding Chatbot
# Usage: ./scripts/sam-deploy.sh [dev|prod]

set -e  # Exit on any error

ENVIRONMENT=${1:-dev}

echo "🚀 Starting SAM deployment to $ENVIRONMENT environment..."

# Validate environment parameter
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI is not installed. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "template.yaml" ]; then
    echo "❌ template.yaml not found. Please run this script from the project root."
    exit 1
fi

# Check AWS credentials for dev/prod deployment
if [ "$ENVIRONMENT" != "local" ]; then
    echo "🔐 Checking AWS credentials..."
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    echo "✅ AWS credentials verified"
    aws sts get-caller-identity --query 'Account' --output text | xargs echo "Deploying to AWS Account:"
fi

# Check if build artifacts exist
if [ ! -d ".aws-sam" ]; then
    echo "🔨 Build artifacts not found. Running sam build first..."
    ./scripts/sam-build.sh
fi

# Deploy based on environment
if [ "$ENVIRONMENT" = "dev" ]; then
    echo "🚀 Deploying to development environment..."
    echo "📋 Using samconfig.toml dev environment"
    sam deploy --config-env dev --no-confirm-changeset
elif [ "$ENVIRONMENT" = "prod" ]; then
    echo "🚀 Deploying to production environment..."
    echo "⚠️  Production deployment requires manual confirmation."
    echo "📋 Using samconfig.toml prod environment"
    sam deploy --config-env prod
fi

# Get stack outputs
echo "📋 Getting stack outputs..."
STACK_NAME="ai-branding-chatbot-$ENVIRONMENT"
aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs' --output table

echo "✅ Deployment to $ENVIRONMENT completed successfully!"
echo ""
echo "🔗 Useful commands:"
echo "  - View logs: sam logs --stack-name $STACK_NAME --tail"
echo "  - Delete stack: sam delete --stack-name $STACK_NAME"
echo "  - Sync changes: sam sync --config-env $ENVIRONMENT --watch"
echo ""

# Show API endpoint if available
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text 2>/dev/null || echo "")
if [ ! -z "$API_ENDPOINT" ]; then
    echo "🌐 API Endpoint: $API_ENDPOINT"
    echo ""
fi