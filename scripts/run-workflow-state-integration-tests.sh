#!/bin/bash
# Run integration tests for Task 23: Workflow State Management
# Tests in both local and dev environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "  Task 23: Workflow State Management Integration Tests"
echo "  Requirements: 4.4, 4.6"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_info "Virtual environment not activated. Activating..."
    if [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please run: python3 -m venv venv"
        exit 1
    fi
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Installing..."
    pip install pytest boto3
fi

# Test 1: Local Environment
echo ""
echo "============================================================"
echo "  Test 1: Local Environment"
echo "============================================================"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_success "Docker is running"

# Check if DynamoDB Local is running
if ! curl -s http://localhost:8000 &> /dev/null; then
    print_info "DynamoDB Local not running. Starting Docker Compose..."
    
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.local.yml up -d dynamodb-local
    
    # Wait for DynamoDB to be ready
    echo "Waiting for DynamoDB Local to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000 &> /dev/null; then
            print_success "DynamoDB Local is ready"
            break
        fi
        sleep 1
    done
    
    if ! curl -s http://localhost:8000 &> /dev/null; then
        print_error "DynamoDB Local failed to start"
        exit 1
    fi
else
    print_success "DynamoDB Local is already running"
fi

# Set environment variables for local testing
export ENVIRONMENT=local
export AWS_REGION=us-east-1
export SESSIONS_TABLE=WorkflowSessions-local
export S3_BUCKET=test-bucket-local

print_info "Running local environment tests..."
cd "$PROJECT_ROOT"

if pytest tests/integration/test_workflow_state_management.py -v -s --tb=short; then
    print_success "Local environment tests passed"
    LOCAL_TESTS_PASSED=true
else
    print_error "Local environment tests failed"
    LOCAL_TESTS_PASSED=false
fi

# Test 2: Dev Environment (if AWS credentials available)
echo ""
echo "============================================================"
echo "  Test 2: Dev Environment (AWS)"
echo "============================================================"
echo ""

# Check if AWS credentials are configured
if aws sts get-caller-identity &> /dev/null; then
    print_success "AWS credentials configured"
    
    # Set environment variables for dev testing
    export ENVIRONMENT=dev
    export AWS_REGION=${AWS_REGION:-us-east-1}
    export SESSIONS_TABLE=${SESSIONS_TABLE:-branding-chatbot-sessions-dev}
    export S3_BUCKET=${S3_BUCKET:-branding-chatbot-bucket-dev}
    
    print_info "Running dev environment tests..."
    
    if pytest tests/integration/test_workflow_state_management.py -v -s --tb=short; then
        print_success "Dev environment tests passed"
        DEV_TESTS_PASSED=true
    else
        print_error "Dev environment tests failed"
        DEV_TESTS_PASSED=false
    fi
else
    print_info "AWS credentials not configured. Skipping dev environment tests."
    print_info "To run dev tests, configure AWS credentials with: aws configure"
    DEV_TESTS_PASSED="skipped"
fi

# Summary
echo ""
echo "============================================================"
echo "  Test Summary"
echo "============================================================"
echo ""

if [[ "$LOCAL_TESTS_PASSED" == true ]]; then
    print_success "Local Environment: PASSED"
else
    print_error "Local Environment: FAILED"
fi

if [[ "$DEV_TESTS_PASSED" == true ]]; then
    print_success "Dev Environment: PASSED"
elif [[ "$DEV_TESTS_PASSED" == "skipped" ]]; then
    print_info "Dev Environment: SKIPPED"
else
    print_error "Dev Environment: FAILED"
fi

echo ""
echo "============================================================"

# Exit with appropriate code
if [[ "$LOCAL_TESTS_PASSED" == true ]] && ([[ "$DEV_TESTS_PASSED" == true ]] || [[ "$DEV_TESTS_PASSED" == "skipped" ]]); then
    print_success "All integration tests completed successfully!"
    echo ""
    echo "Task 23 Integration Tests Complete:"
    echo "  ✓ Pause/resume workflow with DynamoDB"
    echo "  ✓ Intermediate result storage and retrieval"
    echo "  ✓ Multiple pause/resume cycles"
    echo "  ✓ State preservation across pause/resume"
    echo "  ✓ Error handling for invalid states"
    echo ""
    exit 0
else
    print_error "Some integration tests failed"
    exit 1
fi
