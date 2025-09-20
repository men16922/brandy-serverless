#!/bin/bash
# Development environment deployment script

set -e

echo "🚀 Deploying AI Branding Chatbot to AWS development environment..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Please install it first:"
    echo "npm install -g aws-cdk"
    exit 1
fi

# Set environment variables
export ENVIRONMENT=dev
export AWS_REGION=${AWS_REGION:-us-east-1}

# Install CDK dependencies
echo "📦 Installing CDK dependencies..."
cd infrastructure
pip install -r requirements.txt

# Bootstrap CDK (if not already done)
echo "🏗️ Bootstrapping CDK..."
cdk bootstrap --context environment=dev

# Deploy stacks in order
echo "🚀 Deploying storage stack..."
cdk deploy BrandingChatbot-Storage-dev --context environment=dev --require-approval never

echo "🚀 Deploying API stack..."
cdk deploy BrandingChatbot-Api-dev --context environment=dev --require-approval never

echo "🚀 Deploying workflow stack..."
cdk deploy BrandingChatbot-Workflow-dev --context environment=dev --require-approval never

echo "🚀 Deploying frontend stack..."
cdk deploy BrandingChatbot-Frontend-dev --context environment=dev --require-approval never

# Get stack outputs
echo "📋 Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name BrandingChatbot-Api-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo "✅ Deployment complete!"
echo ""
echo "🔗 API URL: $API_URL"
echo ""
echo "📝 Next steps:"
echo "1. Update config/dev.json with actual resource ARNs"
echo "2. Configure Bedrock Knowledge Base"
echo "3. Set up environment variables for API keys"

cd ..