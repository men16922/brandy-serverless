#!/bin/bash
# Integration Test Runner for AI Branding Chatbot
# Supports both local and dev environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Branding Chatbot - Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse arguments
ENVIRONMENT=${1:-local}
TEST_FILTER=${2:-}

if [[ "$ENVIRONMENT" != "local" && "$ENVIRONMENT" != "dev" ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Usage: $0 [local|dev] [test_filter]"
    echo "Example: $0 local test_bedrock"
    exit 1
fi

echo -e "${BLUE}📋 Environment: ${ENVIRONMENT}${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found: $(docker-compose --version)${NC}"

echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv "$PROJECT_ROOT/venv"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install/upgrade test dependencies
echo ""
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q pytest pytest-asyncio boto3 requests python-dotenv
echo -e "${GREEN}✅ Test dependencies installed${NC}"

echo ""

# Environment-specific setup
if [ "$ENVIRONMENT" = "local" ]; then
    echo -e "${YELLOW}🐳 Setting up local environment...${NC}"
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        echo "Please start Docker Desktop and try again"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
    
    # Start Docker Compose services
    echo -e "${YELLOW}🚀 Starting Docker Compose services...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.local.yml up -d
    
    # Wait for services to be ready
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 5
    
    # Check service health
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
            echo -e "${GREEN}✅ Docker services are running${NC}"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}   Attempt $RETRY_COUNT/$MAX_RETRIES...${NC}"
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Services failed to start${NC}"
        docker-compose -f docker-compose.local.yml logs
        exit 1
    fi
    
    # Display service URLs
    echo ""
    echo -e "${BLUE}📍 Local Services:${NC}"
    echo -e "   DynamoDB Local:    http://localhost:8000"
    echo -e "   DynamoDB Admin UI: http://localhost:8002"
    echo -e "   MinIO Console:     http://localhost:9001 (minioadmin/minioadmin)"
    echo -e "   Chroma:            http://localhost:8001"
    
    # Load test environment variables
    export ENVIRONMENT=local
    export $(cat "$PROJECT_ROOT/.env.test" | grep -v '^#' | xargs)
    
elif [ "$ENVIRONMENT" = "dev" ]; then
    echo -e "${YELLOW}☁️  Setting up dev environment...${NC}"
    
    # Check AWS credentials
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo -e "${RED}❌ AWS credentials not found${NC}"
        echo "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        exit 1
    fi
    echo -e "${GREEN}✅ AWS credentials found${NC}"
    
    # Check Bedrock access
    echo -e "${YELLOW}🔍 Checking Bedrock access...${NC}"
    if aws bedrock list-foundation-models --region us-east-1 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Bedrock access confirmed${NC}"
    else
        echo -e "${YELLOW}⚠️  Bedrock access check failed (may still work)${NC}"
    fi
    
    # Load dev environment variables
    export ENVIRONMENT=dev
    export ENABLE_FALLBACK=false
    export BEDROCK_REGION=us-east-1
fi

echo ""

# Run integration tests
echo -e "${YELLOW}🧪 Running integration tests...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Build pytest command
PYTEST_CMD="pytest tests/integration/"

if [ -n "$TEST_FILTER" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $TEST_FILTER"
fi

PYTEST_CMD="$PYTEST_CMD -v -s --tb=short"

# Add markers for environment
if [ "$ENVIRONMENT" = "local" ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not requires_aws'"
elif [ "$ENVIRONMENT" = "dev" ]; then
    PYTEST_CMD="$PYTEST_CMD"
fi

echo -e "${BLUE}Running: $PYTEST_CMD${NC}"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    TEST_EXIT_CODE=0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ Some integration tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    TEST_EXIT_CODE=1
fi

echo ""

# Cleanup for local environment
if [ "$ENVIRONMENT" = "local" ]; then
    echo -e "${YELLOW}🧹 Cleanup options:${NC}"
    echo "   Keep services running: docker-compose -f docker-compose.local.yml ps"
    echo "   Stop services:         docker-compose -f docker-compose.local.yml down"
    echo "   Stop and clean:        docker-compose -f docker-compose.local.yml down -v"
fi

echo ""
echo -e "${BLUE}Test run completed for ${ENVIRONMENT} environment${NC}"

exit $TEST_EXIT_CODE
