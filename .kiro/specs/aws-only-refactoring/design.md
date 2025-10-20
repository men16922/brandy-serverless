# Design Document

## Overview

This design document outlines the refactoring of the AI Branding Chatbot from a hybrid local/AWS environment to an **AWS-only architecture**. The goal is to simplify the development workflow by running only Streamlit locally while all backend services (DynamoDB, S3, Lambda, API Gateway) use AWS directly.

### Current State
- Mixed local (Docker Compose) and AWS environments
- Complex environment switching logic in code
- DynamoDB Local, MinIO, Chroma for local development
- Conditional endpoint configuration based on ENVIRONMENT variable

### Target State
- **Streamlit**: Runs locally on localhost:8501
- **All Backend Services**: AWS only (DynamoDB, S3, Lambda, API Gateway, Step Functions)
- **Single Environment**: 'dev' environment for development
- **Simplified Code**: No local endpoint logic or environment conditionals

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Machine                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Streamlit App (localhost:8501)               │  │
│  │                                                            │  │
│  │  - Business Info Input                                    │  │
│  │  - Workflow Progress Display                              │  │
│  │  - Results Visualization                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ HTTPS                             │
│                              ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                              │            AWS Cloud              │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         API Gateway (HTTP API)                            │  │
│  │         https://xxx.execute-api.us-west-2.amazonaws.com  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Supervisor Agent (Lambda)                    │  │
│  │              - Workflow Orchestration                     │  │
│  │              - Agent Coordination                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         6 Specialized Agents (Lambda Functions)           │  │
│  │                                                            │  │
│  │  - Product Insight Agent                                  │  │
│  │  - Market Analyst Agent                                   │  │
│  │  - Reporter Agent                                         │  │
│  │  - Signboard Agent                                        │  │
│  │  - Interior Agent                                         │  │
│  │  - Report Generator Agent                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AWS Services                                 │  │
│  │                                                            │  │
│  │  - DynamoDB: Session storage                              │  │
│  │  - S3: Image and report storage                           │  │
│  │  - Step Functions: Workflow orchestration                 │  │
│  │  - Bedrock: AI/ML services                                │  │
│  │  - Secrets Manager: API keys                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Streamlit (localhost:8501)
2. **API Request** → API Gateway (AWS)
3. **Workflow Start** → Supervisor Agent (Lambda)
4. **Agent Execution** → Specialized Agents (Lambda)
5. **Data Storage** → DynamoDB (AWS)
6. **File Storage** → S3 (AWS)
7. **Results** → Streamlit via API Gateway

## Components and Interfaces

### 1. Streamlit Application (Local)

**Location**: `src/streamlit/app.py`

**Responsibilities**:
- Run on localhost:8501
- Provide UI for business info input
- Display workflow progress
- Visualize results (images, reports)
- Poll API Gateway for session status

**Configuration**:
```python
# .env file
API_BASE_URL=https://vd9s16odtc.execute-api.us-west-2.amazonaws.com/dev
AWS_REGION=us-west-2
```

**Key Changes**:
- Remove all local endpoint references
- Always use API_BASE_URL from .env
- No environment switching logic

### 2. Base Agent (Lambda Layer)

**Location**: `src/lambda/shared/base_agent.py`

**Responsibilities**:
- Initialize AWS clients (DynamoDB, S3, Lambda)
- Provide common agent functionality
- Handle errors and logging
- Manage session data

**Key Changes**:
```python
# REMOVE: Local endpoint logic
# BEFORE:
if self.environment == 'local':
    dynamodb_endpoint = 'http://localhost:8000'
    s3_endpoint = 'http://localhost:9000'
else:
    dynamodb_endpoint = None
    s3_endpoint = None

# AFTER:
# Always use AWS SDK defaults (no endpoint override)
self.aws_clients = get_aws_clients()
```

**Simplified Initialization**:
```python
def __init__(self, agent_type: AgentType):
    self.agent_type = agent_type
    self.agent_name = agent_type.value
    
    # Always use 'dev' environment
    self.environment = 'dev'
    self.region = os.getenv('AWS_REGION', 'us-west-2')
    
    # Setup logging
    self.logger = setup_logging(self.agent_name)
    
    # Initialize AWS clients (no local endpoints)
    self.aws_clients = get_aws_clients()
    
    # Load configuration
    self.config = self._load_config()
```

### 3. AWS Utilities

**Location**: `src/lambda/shared/utils.py`

**Responsibilities**:
- Initialize AWS service clients
- Provide logging utilities
- Create Lambda responses

**Key Changes**:
```python
# REMOVE: Local endpoint parameters
# BEFORE:
def get_aws_clients(environment='dev', dynamodb_endpoint=None, s3_endpoint=None):
    if dynamodb_endpoint:
        dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
    else:
        dynamodb = boto3.resource('dynamodb')
    # ...

# AFTER:
def get_aws_clients():
    """Initialize AWS service clients (always uses AWS)"""
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    stepfunctions = boto3.client('stepfunctions')
    lambda_client = boto3.client('lambda')
    
    return {
        'dynamodb': dynamodb,
        's3': s3,
        'stepfunctions': stepfunctions,
        'lambda': lambda_client
    }
```

### 4. Configuration Management

**Location**: `config/`

**Changes**:
- **REMOVE**: `config/local.json`
- **KEEP**: `config/bedrock_config.py`, `config/fallback_config.py`
- **UPDATE**: Remove local environment references

**Environment Variables** (`.env`):
```bash
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Environment (dev only)
ENVIRONMENT=dev

# API Gateway
API_BASE_URL=https://vd9s16odtc.execute-api.us-west-2.amazonaws.com/dev

# DynamoDB
SESSIONS_TABLE=ai-branding-chatbot-sessions

# S3
S3_BUCKET=ai-branding-chatbot-assets-908601828278

# Bedrock
BEDROCK_REGION=us-west-2
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
ENABLE_FALLBACK=true
DEV_PROFILE=true
```

### 5. SAM Template

**Location**: `template.yaml`

**Changes**:
- **REMOVE**: Local environment parameter
- **UPDATE**: Default environment to 'dev'
- **SIMPLIFY**: Remove local-specific configurations

```yaml
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]  # Remove 'local'
    Description: Deployment environment
```

## Data Models

### Session Data (DynamoDB)

**Table**: `ai-branding-chatbot-sessions`

**Schema**:
```json
{
  "sessionId": "uuid",
  "currentStep": 1,
  "status": "in_progress",
  "businessInfo": {
    "industry": "restaurant",
    "region": "seoul",
    "size": "small",
    "description": "..."
  },
  "analysisResult": {...},
  "nameOptions": [...],
  "signboardImages": [...],
  "interiorRecommendations": [...],
  "reportUrl": "s3://...",
  "reasoning_chain": [...],
  "agent_logs": [...],
  "createdAt": "2025-10-18T...",
  "updatedAt": "2025-10-18T...",
  "ttl": 1729296000
}
```

**Access Pattern**:
- Streamlit → API Gateway → Lambda → DynamoDB
- No local DynamoDB access

### File Storage (S3)

**Bucket**: `ai-branding-chatbot-assets-908601828278`

**Structure**:
```
s3://ai-branding-chatbot-assets-908601828278/
├── sessions/
│   └── {session_id}/
│       ├── signboard_1.png
│       ├── signboard_2.png
│       ├── signboard_3.png
│       └── report.html
└── fallbacks/
    └── default_signboard.png
```

**Access Pattern**:
- Lambda → S3 (upload)
- Streamlit → S3 presigned URL (download/display)

## Error Handling

### Simplified Error Flow

1. **Lambda Execution Error**:
   - Log to CloudWatch
   - Return error response to API Gateway
   - Streamlit displays error message

2. **AWS Service Error**:
   - Retry with exponential backoff (boto3 default)
   - Log error details
   - Return graceful error response

3. **Bedrock API Error**:
   - Use fallback provider (if enabled)
   - Log fallback usage
   - Continue workflow

### Removed Error Scenarios

- ❌ Docker service unavailable
- ❌ Local endpoint connection failed
- ❌ Port conflicts
- ❌ Local data cleanup errors

## Testing Strategy

### Integration Testing

**Approach**: Use AWS dev environment directly

**Test Flow**:
1. Deploy to AWS dev environment
2. Run Streamlit locally
3. Execute end-to-end workflow tests
4. Verify data in AWS Console (DynamoDB, S3)
5. Check CloudWatch logs

**Test Script**:
```bash
#!/bin/bash
# test-aws-integration.sh

# 1. Deploy to AWS
sam build
sam deploy --config-env dev

# 2. Run Streamlit
streamlit run src/streamlit/app.py &
STREAMLIT_PID=$!

# 3. Run integration tests
pytest tests/integration/test_aws_workflow.py -v

# 4. Cleanup
kill $STREAMLIT_PID
```

### Removed Testing Components

- ❌ Docker Compose fixtures
- ❌ DynamoDB Local setup
- ❌ MinIO setup
- ❌ Chroma setup
- ❌ Local service health checks

## Deployment

### Development Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Deploy to AWS
./safe_deploy.sh

# 3. Run Streamlit locally
streamlit run src/streamlit/app.py

# 4. Test in browser
# http://localhost:8501
```

### Deployment Script (`safe_deploy.sh`)

**Features**:
- Check AWS credentials
- Build SAM application
- Deploy to AWS dev environment
- Extract API Gateway URL
- Update .env file
- Test API connectivity

### Removed Deployment Components

- ❌ `docker-compose up`
- ❌ Local service initialization
- ❌ Port conflict checks
- ❌ Local data seeding

## Migration Plan

### Phase 1: Code Cleanup
1. Remove local endpoint logic from `base_agent.py`
2. Simplify `utils.py` AWS client initialization
3. Remove environment switching in agent code
4. Update configuration loading

### Phase 2: File Removal
1. Delete `docker-compose.local.yml`
2. Delete `config/local.json`
3. Delete `scripts/setup-local.sh`
4. Delete local-only scripts
5. Delete `local_api_server.py`

### Phase 3: Documentation Update
1. Update `README.md` with AWS-only setup
2. Update `.kiro/steering/local-environment.md`
3. Update `DEPLOYMENT_FIX.md`
4. Remove Docker references from all docs

### Phase 4: Testing
1. Update integration tests for AWS
2. Remove Docker fixtures
3. Test end-to-end workflow
4. Verify CloudWatch logs

### Phase 5: Validation
1. Deploy to AWS dev
2. Run Streamlit locally
3. Execute full workflow
4. Verify all 5 steps complete
5. Check data in DynamoDB and S3

## Performance Considerations

### Benefits of AWS-Only Architecture

1. **Consistency**: Dev and prod environments identical
2. **Simplicity**: No environment switching logic
3. **Reliability**: Use AWS managed services
4. **Scalability**: AWS auto-scaling
5. **Monitoring**: CloudWatch integration

### Potential Concerns

1. **AWS Costs**: Monitor usage with AWS Cost Explorer
2. **Network Latency**: Acceptable for development (< 100ms)
3. **API Rate Limits**: Use AWS service quotas

### Optimization Strategies

1. **Lambda Cold Starts**: Use provisioned concurrency if needed
2. **DynamoDB**: Use on-demand billing for dev
3. **S3**: Enable lifecycle policies for old files
4. **API Gateway**: Use HTTP API (cheaper than REST API)

## Security

### AWS IAM Roles

**Lambda Execution Role**:
```yaml
Policies:
  - DynamoDBCrudPolicy:
      TableName: !Ref WorkflowSessionsTable
  - S3CrudPolicy:
      BucketName: !Ref BrandingAssetsBucket
  - Statement:
      - Effect: Allow
        Action:
          - bedrock:InvokeModel
          - bedrock:InvokeAgent
        Resource: "*"
```

### Secrets Management

**AWS Secrets Manager**:
- OpenAI API Key: `openai-api-key`
- Gemini API Key: `gemini-api-key` (if used)

**Access**:
```python
# Lambda function
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='openai-api-key')
api_key = json.loads(secret['SecretString'])['api_key']
```

### Removed Security Concerns

- ❌ Docker container security
- ❌ Local port exposure
- ❌ MinIO access credentials
- ❌ Local database security

## Monitoring and Logging

### CloudWatch Logs

**Log Groups**:
- `/aws/lambda/ai-branding-chatbot-supervisor-agent-dev`
- `/aws/lambda/ai-branding-chatbot-product-insight-agent-dev`
- `/aws/lambda/ai-branding-chatbot-market-analyst-agent-dev`
- `/aws/lambda/ai-branding-chatbot-reporter-agent-dev`
- `/aws/lambda/ai-branding-chatbot-signboard-agent-dev`
- `/aws/lambda/ai-branding-chatbot-interior-agent-dev`
- `/aws/lambda/ai-branding-chatbot-report-generator-agent-dev`

**Log Viewing**:
```bash
# Real-time logs
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev --follow

# All agents
aws logs tail /aws/lambda/ai-branding-chatbot --follow
```

### Metrics

**CloudWatch Metrics**:
- Lambda invocations
- Lambda duration
- Lambda errors
- API Gateway requests
- DynamoDB read/write capacity
- S3 operations

### Removed Monitoring

- ❌ Docker container logs
- ❌ Local service health checks
- ❌ DynamoDB Admin UI

## Documentation Updates

### README.md

**New Structure**:
1. Project Overview
2. AWS-Only Architecture
3. Prerequisites (AWS account, credentials)
4. Setup (SAM deploy)
5. Running Streamlit Locally
6. Testing
7. Deployment
8. Troubleshooting

### local-environment.md

**New Content**:
- Streamlit runs locally
- All backend services use AWS
- No Docker required
- AWS credentials setup
- API Gateway endpoint configuration

### DEPLOYMENT_FIX.md

**Updates**:
- Remove Docker references
- Focus on SAM deployment
- AWS troubleshooting only
- CloudWatch log access

## Conclusion

This design provides a clear path to simplify the AI Branding Chatbot architecture by removing all local development infrastructure and using AWS services directly. The result is:

- **Simpler codebase**: No environment switching logic
- **Consistent environments**: Dev matches prod
- **Easier onboarding**: Just deploy to AWS and run Streamlit
- **Better monitoring**: CloudWatch integration
- **Production-ready**: Same services in dev and prod

The migration can be done incrementally following the 5-phase plan, with validation at each step.
