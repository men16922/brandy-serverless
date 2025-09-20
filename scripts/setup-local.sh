#!/bin/bash
# Local development environment setup script

set -e

echo "🚀 Setting up AI Branding Chatbot local development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start local services
echo "📦 Starting local services (DynamoDB, MinIO, Chroma)..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Create DynamoDB table
echo "🗄️ Creating DynamoDB table..."
aws dynamodb create-table \
    --table-name branding-chatbot-sessions-local \
    --attribute-definitions \
        AttributeName=sessionId,AttributeType=S \
    --key-schema \
        AttributeName=sessionId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1 \
    --no-cli-pager || echo "Table might already exist"

# Create MinIO bucket
echo "🪣 Creating S3 bucket in MinIO..."
aws s3 mb s3://branding-chatbot-storage-local \
    --endpoint-url http://localhost:9000 \
    --region us-east-1 || echo "Bucket might already exist"

# Create data directory for local files
echo "📁 Creating data directories..."
mkdir -p data/chroma
mkdir -p data/fallbacks/signs
mkdir -p data/fallbacks/interiors
mkdir -p data/templates

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if [ -f "src/lambda/shared/requirements.txt" ]; then
    pip install -r src/lambda/shared/requirements.txt
fi

if [ -f "src/streamlit/requirements.txt" ]; then
    pip install -r src/streamlit/requirements.txt
fi

if [ -f "infrastructure/requirements.txt" ]; then
    pip install -r infrastructure/requirements.txt
fi

echo "✅ Local development environment setup complete!"
echo ""
echo "🔗 Service URLs:"
echo "  - DynamoDB Local: http://localhost:8000"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  - Chroma: http://localhost:8001"
echo ""
echo "🚀 To start the Streamlit app:"
echo "  cd src/streamlit && streamlit run app.py"
echo ""
echo "🛑 To stop services:"
echo "  docker-compose -f docker-compose.local.yml down"