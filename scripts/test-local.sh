#!/bin/bash
# Local 환경 테스트 실행 스크립트

set -e

echo "🏠 Running tests in LOCAL environment (Docker Compose)"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Start Docker Compose services
echo "🐳 Starting Docker Compose services..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.local.yml ps

# Load test environment variables
export ENV_FILE=.env.test
echo "📝 Using environment: $ENV_FILE"

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
    echo "✅ All tests passed!"
    echo ""
    echo "📊 View test data:"
    echo "   - DynamoDB Admin: http://localhost:8002"
    echo "   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
else
    echo "❌ Some tests failed"
    echo ""
    echo "🔍 Debug resources:"
    echo "   - DynamoDB Admin: http://localhost:8002"
    echo "   - Docker logs: docker-compose -f docker-compose.local.yml logs"
fi

exit $TEST_EXIT_CODE
