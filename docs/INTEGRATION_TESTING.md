# Integration Testing Guide

## Overview

This guide explains how to run integration tests for the AI Branding Chatbot project in both **local** and **dev** environments.

## Test Philosophy

**NO MOCKS**: All integration tests use real services (Docker Compose for local, AWS services for dev) to ensure end-to-end functionality.

## Prerequisites

### Common Requirements
- Python 3.11+
- Docker Desktop (for local environment)
- Virtual environment activated

### Local Environment
- Docker Compose services running
- No AWS credentials required

### Dev Environment
- AWS credentials configured
- Bedrock access enabled in us-east-1
- DynamoDB and S3 access

## Quick Start

### 1. Local Environment Testing

```bash
# Start Docker services and run tests
./scripts/run-integration-tests.sh local

# Run specific test file
./scripts/run-integration-tests.sh local test_bedrock

# Run specific test function
./scripts/run-integration-tests.sh local test_bedrock_claude_invocation
```

### 2. Dev Environment Testing

```bash
# Ensure AWS credentials are set
export AWS_PROFILE=your-profile
# OR
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

# Run tests against AWS services
./scripts/run-integration-tests.sh dev

# Run specific tests
./scripts/run-integration-tests.sh dev test_agentcore
```

## Test Structure

```
tests/integration/
├── conftest.py                      # Shared fixtures and setup
├── test_bedrock_integration.py      # Bedrock API tests (Tasks 4)
├── test_agentcore.py                # AgentCore orchestration tests (Task 9)
├── test_agentcore_orchestrator.py   # AgentCore primitives tests
├── test_reasoning_engine.py         # Reasoning Engine tests (Task 13)
├── test_reporter_bedrock.py         # Reporter Agent Bedrock tests
├── test_interior_bedrock.py         # Interior Agent Bedrock tests
└── test_hackathon_workflow.py       # Full workflow tests (Task 25)
```

## Environment Configuration

### Local Environment (.env.test)
```bash
ENVIRONMENT=local
BEDROCK_REGION=us-east-1
ENABLE_FALLBACK=true
DYNAMODB_ENDPOINT=http://localhost:8000
S3_ENDPOINT=http://localhost:9000
CHROMA_ENDPOINT=http://localhost:8001
```

### Dev Environment
```bash
ENVIRONMENT=dev
BEDROCK_REGION=us-east-1
ENABLE_FALLBACK=false
# Uses real AWS services (no endpoints)
```

## Docker Services (Local Only)

### Starting Services
```bash
docker-compose -f docker-compose.local.yml up -d
```

### Checking Service Status
```bash
docker-compose -f docker-compose.local.yml ps
```

### Service URLs
- **DynamoDB Local**: http://localhost:8000
- **DynamoDB Admin UI**: http://localhost:8002
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Chroma**: http://localhost:8001

### Stopping Services
```bash
# Stop services (keep data)
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.local.yml down -v
```

## Test Categories

### 1. Bedrock Integration Tests (Task 4)
Tests Amazon Bedrock API integration:
- Claude 4 Sonnet invocation
- SDXL image generation
- Knowledge Base queries
- Error handling and retries
- Response parsing

**Run**: `./scripts/run-integration-tests.sh local test_bedrock_integration`

### 2. AgentCore Tests (Task 9)
Tests Bedrock AgentCore orchestration:
- Orchestrator initialization
- Tool Use primitive
- Memory primitive
- Inter-agent communication
- Workflow orchestration

**Run**: `./scripts/run-integration-tests.sh local test_agentcore`

### 3. Reasoning Engine Tests (Task 13)
Tests Reasoning LLM capabilities:
- Chain-of-Thought reasoning
- Business name evaluation
- Design ranking
- Confidence scoring
- Reasoning chain storage

**Run**: `./scripts/run-integration-tests.sh local test_reasoning`

### 4. Agent Bedrock Integration Tests
Tests individual agents with Bedrock:
- Reporter Agent (name generation)
- Interior Agent (recommendations)
- Market Analyst Agent (KB queries)
- Signboard Agent (SDXL images)

**Run**: `./scripts/run-integration-tests.sh local test_reporter_bedrock`

### 5. Full Workflow Tests (Task 25)
Tests complete 5-step branding workflow:
- End-to-end execution
- Autonomous decision-making
- Fallback mechanisms
- PDF report generation
- Concurrent sessions

**Run**: `./scripts/run-integration-tests.sh local test_hackathon_workflow`

## Manual Testing

### Running pytest directly
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/integration/ -v

# Run with detailed output
pytest tests/integration/ -v -s

# Run specific test file
pytest tests/integration/test_bedrock_integration.py -v

# Run specific test function
pytest tests/integration/test_bedrock_integration.py::test_bedrock_claude_invocation -v

# Run tests matching pattern
pytest tests/integration/ -k "bedrock" -v
```

## Troubleshooting

### Docker Services Not Starting
```bash
# Check Docker daemon
docker info

# Check service logs
docker-compose -f docker-compose.local.yml logs

# Restart services
docker-compose -f docker-compose.local.yml restart
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000,8001,8002,9000,9001

# Kill processes if needed
sudo lsof -ti:8000 | xargs kill -9
```

### AWS Credentials Issues (Dev)
```bash
# Verify credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Set credentials
export AWS_PROFILE=your-profile
```

### Test Failures
```bash
# Run with more verbose output
pytest tests/integration/ -v -s --tb=long

# Run single test for debugging
pytest tests/integration/test_bedrock_integration.py::test_bedrock_claude_invocation -v -s

# Check Docker service logs
docker-compose -f docker-compose.local.yml logs dynamodb-local
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test-local:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run Local Integration Tests
        run: ./scripts/run-integration-tests.sh local

  test-dev:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Run Dev Integration Tests
        run: ./scripts/run-integration-tests.sh dev
```

## Performance Expectations

### Local Environment
- Test setup: < 30 seconds
- Individual test: < 10 seconds
- Full test suite: < 5 minutes

### Dev Environment
- Test setup: < 10 seconds
- Individual test: < 15 seconds (includes AWS API calls)
- Full test suite: < 10 minutes

## Best Practices

1. **Always run local tests first** before dev tests
2. **Keep Docker services running** during development for faster test iterations
3. **Use test filters** to run specific tests during development
4. **Check service health** before running tests
5. **Clean up test data** after test runs
6. **Monitor AWS costs** when running dev tests frequently

## Test Coverage Goals

- **Bedrock Integration**: 100% of API methods
- **AgentCore**: 100% of primitives (Tool Use, Memory)
- **Reasoning Engine**: 100% of decision-making methods
- **Agent Integration**: 80%+ of agent methods
- **Full Workflow**: 100% of 5-step workflow

## Next Steps

After successful integration tests:
1. Review test results and logs
2. Fix any failing tests
3. Update task status in `.kiro/specs/aws-hackathon-compliance/tasks.md`
4. Proceed to next phase (documentation, demo video, deployment)

## Support

For issues or questions:
1. Check Docker service logs
2. Review test output with `-v -s` flags
3. Verify environment variables
4. Check AWS credentials and permissions
5. Consult the main README.md for project setup
