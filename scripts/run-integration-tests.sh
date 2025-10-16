#!/bin/bash
# Comprehensive Integration Test Runner
# Runs tests in both local (Docker) and AWS dev environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.local.yml"

# Test environment selection
TEST_ENV="${1:-local}"  # Default to local if not specified

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI Branding Chatbot Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Test Environment: ${GREEN}$TEST_ENV${NC}"
echo -e "Project Root: $PROJECT_ROOT"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker services
check_docker_services() {
    echo -e "${YELLOW}Checking Docker services...${NC}"
    
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker not found${NC}"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon not running${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Docker is available${NC}"
    return 0
}

# Function to start Docker Compose services
start_docker_services() {
    echo -e "${YELLOW}Starting Docker Compose services...${NC}"
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 10
    
    # Check DynamoDB Local
    if curl -s http://localhost:8000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ DynamoDB Local is running (port 8000)${NC}"
    else
        echo -e "${RED}❌ DynamoDB Local not responding${NC}"
        return 1
    fi
    
    # Check MinIO
    if curl -s http://localhost:9000/minio/health/live >/dev/null 2>&1; then
        echo -e "${GREEN}✓ MinIO is running (port 9000)${NC}"
    else
        echo -e "${RED}❌ MinIO not responding${NC}"
        return 1
    fi
    
    # Check Chroma
    if curl -s http://localhost:8001 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Chroma is running (port 8001)${NC}"
    else
        echo -e "${RED}❌ Chroma not responding${NC}"
        return 1
    fi
    
    # Check DynamoDB Admin UI
    if curl -s http://localhost:8002 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ DynamoDB Admin UI is running (port 8002)${NC}"
    else
        echo -e "${YELLOW}⚠️  DynamoDB Admin UI not responding (non-critical)${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ All Docker services are healthy${NC}"
    echo ""
    return 0
}

# Function to activate virtual environment
activate_venv() {
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_PATH"
    fi
    
    source "$VENV_PATH/bin/activate"
    
    # Verify pytest is installed
    if ! command_exists pytest; then
        echo -e "${YELLOW}Installing test dependencies...${NC}"
        pip install -q pytest pytest-asyncio boto3 requests
    fi
    
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    echo ""
}

# Function to run local tests
run_local_tests() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Running LOCAL Integration Tests${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Check and start Docker services
    if ! check_docker_services; then
        echo -e "${RED}❌ Docker services check failed${NC}"
        exit 1
    fi
    
    if ! start_docker_services; then
        echo -e "${RED}❌ Failed to start Docker services${NC}"
        exit 1
    fi
    
    # Activate virtual environment
    activate_venv
    
    # Set environment variables for local testing
    export ENVIRONMENT=local
    export DYNAMODB_ENDPOINT=http://localhost:8000
    export S3_ENDPOINT=http://localhost:9000
    export CHROMA_ENDPOINT=http://localhost:8001
    export SESSIONS_TABLE=branding-chatbot-sessions-test
    export S3_BUCKET=branding-chatbot-assets-test
    export AWS_ACCESS_KEY_ID=dummy
    export AWS_SECRET_ACCESS_KEY=dummy
    export AWS_DEFAULT_REGION=us-east-1
    
    # Run tests
    echo -e "${YELLOW}Running integration tests...${NC}"
    echo ""
    
    "$VENV_PATH/bin/python" -m pytest \
        tests/integration/test_hackathon_workflow.py \
        -v \
        --tb=short \
        --color=yes
    
    TEST_EXIT_CODE=$?
    
    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All local tests passed!${NC}"
        echo ""
        echo -e "${BLUE}Verification URLs:${NC}"
        echo -e "  • DynamoDB Admin: ${GREEN}http://localhost:8002${NC}"
        echo -e "  • MinIO Console: ${GREEN}http://localhost:9001${NC} (minioadmin/minioadmin)"
        echo -e "  • Chroma API: ${GREEN}http://localhost:8001${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run AWS dev tests
run_aws_dev_tests() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Running AWS DEV Integration Tests${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Check AWS credentials
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo -e "${RED}❌ AWS credentials not found${NC}"
        echo -e "${YELLOW}Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ AWS credentials found${NC}"
    
    # Activate virtual environment
    activate_venv
    
    # Set environment variables for AWS dev testing
    export ENVIRONMENT=dev
    export AWS_DEFAULT_REGION=us-east-1
    export SESSIONS_TABLE=ai-branding-chatbot-sessions
    export S3_BUCKET=ai-branding-chatbot-assets
    export BEDROCK_REGION=us-east-1
    export ENABLE_FALLBACK=false  # Use Bedrock only in dev
    
    # Check if SAM stack is deployed
    echo -e "${YELLOW}Checking SAM stack deployment...${NC}"
    
    STACK_NAME="branding-chatbot"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region us-east-1 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ SAM stack '$STACK_NAME' is deployed${NC}"
        
        # Get API Gateway URL
        API_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region us-east-1 \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
            --output text)
        
        if [ -n "$API_URL" ]; then
            echo -e "${GREEN}✓ API Gateway URL: $API_URL${NC}"
            export API_BASE_URL="$API_URL"
        fi
    else
        echo -e "${YELLOW}⚠️  SAM stack not found. Some tests may be skipped.${NC}"
    fi
    
    echo ""
    
    # Run tests
    echo -e "${YELLOW}Running AWS dev integration tests...${NC}"
    echo ""
    
    "$VENV_PATH/bin/python" -m pytest \
        tests/integration/test_hackathon_workflow.py \
        -v \
        --tb=short \
        --color=yes \
        -m "not local_only"
    
    TEST_EXIT_CODE=$?
    
    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All AWS dev tests passed!${NC}"
        echo ""
        echo -e "${BLUE}AWS Resources:${NC}"
        echo -e "  • DynamoDB Table: ${GREEN}$SESSIONS_TABLE${NC}"
        echo -e "  • S3 Bucket: ${GREEN}$S3_BUCKET${NC}"
        echo -e "  • Region: ${GREEN}$AWS_DEFAULT_REGION${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to run specific test
run_specific_test() {
    local test_name="$1"
    
    echo -e "${BLUE}Running specific test: ${GREEN}$test_name${NC}"
    echo ""
    
    activate_venv
    
    # Set environment based on TEST_ENV
    if [ "$TEST_ENV" = "local" ]; then
        check_docker_services && start_docker_services
        export ENVIRONMENT=local
        export DYNAMODB_ENDPOINT=http://localhost:8000
        export S3_ENDPOINT=http://localhost:9000
    else
        export ENVIRONMENT=dev
    fi
    
    "$VENV_PATH/bin/python" -m pytest \
        "tests/integration/test_hackathon_workflow.py::$test_name" \
        -v \
        -s \
        --tb=short \
        --color=yes
}

# Function to show test summary
show_test_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Available test classes:"
    echo -e "  1. ${GREEN}TestFullWorkflowWithBedrock${NC} - Complete 5-step workflow"
    echo -e "  2. ${GREEN}TestAutonomousExecution${NC} - Autonomous agent execution"
    echo -e "  3. ${GREEN}TestFallbackMechanism${NC} - Fallback to alternative providers"
    echo -e "  4. ${GREEN}TestPDFReportGeneration${NC} - PDF report generation"
    echo -e "  5. ${GREEN}TestConcurrentSessions${NC} - Concurrent session handling"
    echo -e "  6. ${GREEN}TestWorkflowStateManagement${NC} - Workflow pause/resume"
    echo ""
    echo -e "Usage:"
    echo -e "  ${YELLOW}./scripts/run-integration-tests.sh${NC}              # Run all local tests"
    echo -e "  ${YELLOW}./scripts/run-integration-tests.sh local${NC}        # Run all local tests"
    echo -e "  ${YELLOW}./scripts/run-integration-tests.sh dev${NC}          # Run all AWS dev tests"
    echo -e "  ${YELLOW}./scripts/run-integration-tests.sh specific <test>${NC}  # Run specific test"
    echo ""
}

# Main execution
case "$TEST_ENV" in
    local)
        run_local_tests
        exit $?
        ;;
    dev)
        run_aws_dev_tests
        exit $?
        ;;
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify test name${NC}"
            show_test_summary
            exit 1
        fi
        run_specific_test "$2"
        exit $?
        ;;
    help|--help|-h)
        show_test_summary
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid environment: $TEST_ENV${NC}"
        echo -e "${YELLOW}Valid options: local, dev, specific, help${NC}"
        show_test_summary
        exit 1
        ;;
esac
