#!/bin/bash

# SAM Build Script for AI Branding Chatbot
# This script builds the SAM application with proper error handling

set -e  # Exit on any error

echo "🚀 Starting SAM build process..."

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

# Clean previous build artifacts
echo "🧹 Cleaning previous build artifacts..."
rm -rf .aws-sam/

# Build the SAM application
echo "🔨 Building SAM application..."
sam build --cached --parallel

# Validate the template
echo "✅ Validating SAM template..."
sam validate --lint

echo "✅ SAM build completed successfully!"
echo ""
echo "Next steps:"
echo "  - Deploy to dev: ./scripts/sam-deploy.sh dev"
echo "  - Deploy to prod: ./scripts/sam-deploy.sh prod"
echo "  - Start local API: sam local start-api --port 3000"
echo ""