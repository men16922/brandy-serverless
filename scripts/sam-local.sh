#!/bin/bash

# SAM Local Development Script
# This script starts the local API Gateway and Lambda functions

set -e  # Exit on any error

PORT=${1:-3000}

echo "🚀 Starting SAM local development environment..."

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI is not installed. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if build artifacts exist
if [ ! -d ".aws-sam" ]; then
    echo "🔨 Build artifacts not found. Running sam build first..."
    ./scripts/sam-build.sh
fi

# Start Docker Compose services for local development
echo "🐳 Starting local services (DynamoDB + Admin UI, MinIO, Chroma)..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check for local services
echo "🔍 Checking local services health..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ DynamoDB Local is ready"
else
    echo "⚠️  DynamoDB Local might not be ready yet"
fi

if curl -s http://localhost:8002/ > /dev/null; then
    echo "✅ DynamoDB Admin UI is ready"
else
    echo "⚠️  DynamoDB Admin UI might not be ready yet"
fi

# Start SAM local API with local configuration
echo "🌐 Starting SAM local API on http://localhost:$PORT"
echo "📋 Using samconfig.toml local environment"
echo ""
echo "🔗 Available endpoints:"
echo "  - POST   http://localhost:$PORT/sessions"
echo "  - GET    http://localhost:$PORT/sessions/{id}"
echo "  - GET    http://localhost:$PORT/status/{id}"
echo "  - POST   http://localhost:$PORT/analysis"
echo "  - POST   http://localhost:$PORT/names/suggest"
echo "  - POST   http://localhost:$PORT/signboards/generate"
echo "  - POST   http://localhost:$PORT/interiors/generate"
echo "  - POST   http://localhost:$PORT/report/generate"
echo "  - GET    http://localhost:$PORT/report/url"
echo ""
echo "🛠️  Local development services:"
echo "  - DynamoDB Admin: http://localhost:8002"
echo "  - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Chroma API:     http://localhost:8001"
echo ""
echo "💡 Tips:"
echo "  - Use DynamoDB Admin UI to view/edit session data"
echo "  - Check MinIO Console for uploaded files"
echo "  - Press Ctrl+C to stop all services"
echo ""

sam local start-api --config-env local --port "$PORT"