# Development Environment - AWS-Only Architecture

## Architecture Overview

This project uses **AWS-only architecture**:
- **Streamlit**: Runs locally on localhost:8501
- **All Backend Services**: Use AWS directly (no Docker, no local services)

### 로컬 실행
- ✅ **Streamlit UI**: localhost:8501

### AWS 서비스 (클라우드)
- ✅ **API Gateway**: https://vd9s16odtc.execute-api.us-east-1.amazonaws.com/dev
- ✅ **Lambda Functions**: 7개 Agent 함수
- ✅ **DynamoDB**: ai-branding-chatbot-sessions
- ✅ **S3**: ai-branding-chatbot-assets-908601828278
- ✅ **Step Functions**: ai-branding-chatbot-workflow-dev

## Python Virtual Environment Setup

### Initial Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Verify activation
which python  # Should show venv path

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Daily Development Workflow
```bash
# 1. Activate venv
source venv/bin/activate

# 2. Run Streamlit (connects to AWS)
streamlit run src/streamlit/app.py --server.port 8501

# OR use script
./run_streamlit_dev.sh
```

## AWS Configuration

### Required AWS Credentials
```bash
# Check credentials
aws sts get-caller-identity

# Configure if needed
aws configure
```

### Environment Variables
```bash
# .env file (already configured)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
ENVIRONMENT=dev
API_BASE_URL=https://vd9s16odtc.execute-api.us-east-1.amazonaws.com/dev
```

## Development Tools

### Streamlit App
- **URL**: http://localhost:8501
- **Purpose**: Web UI for branding workflow
- **Connects to**: AWS API Gateway

### AWS Console Access
- **DynamoDB**: https://console.aws.amazon.com/dynamodb
- **S3**: https://console.aws.amazon.com/s3
- **Lambda**: https://console.aws.amazon.com/lambda
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch

## Deployment Workflow

### 1. Code Changes
```bash
# Edit Lambda function code
vim src/lambda/agents/product-insight/index.py
```

### 2. Build and Deploy
```bash
# Build SAM application
sam build

# Deploy to AWS
sam deploy --config-env dev
```

### 3. Test with Streamlit
```bash
# Run Streamlit locally
streamlit run src/streamlit/app.py
```

## Monitoring and Debugging

### Real-time Logs
```bash
# Supervisor Agent
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev --follow

# Product Insight Agent
aws logs tail /aws/lambda/ai-branding-chatbot-product-insight-agent-dev --follow

# All agents
aws logs tail /aws/lambda/ai-branding-chatbot --follow
```

### DynamoDB Data
```bash
# Get session
aws dynamodb get-item \
  --table-name ai-branding-chatbot-sessions \
  --key '{"sessionId":{"S":"YOUR_SESSION_ID"}}' \
  --region us-east-1

# Scan recent sessions
aws dynamodb scan \
  --table-name ai-branding-chatbot-sessions \
  --max-items 5 \
  --region us-east-1
```

### S3 Files
```bash
# List files
aws s3 ls s3://ai-branding-chatbot-assets-908601828278/ --recursive

# Download file
aws s3 cp s3://ai-branding-chatbot-assets-908601828278/path/to/file ./
```

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```bash
   # Check credentials
   aws sts get-caller-identity
   
   # Reconfigure
   aws configure
   ```

2. **API Gateway Connection Error**
   ```bash
   # Test API endpoint
   curl https://vd9s16odtc.execute-api.us-east-1.amazonaws.com/dev/
   
   # Check CloudFormation outputs
   aws cloudformation describe-stacks \
     --stack-name ai-branding-chatbot-dev \
     --query 'Stacks[0].Outputs'
   ```

3. **DynamoDB Access Denied**
   ```bash
   # Check Lambda IAM role
   aws lambda get-function \
     --function-name ai-branding-chatbot-supervisor-agent-dev \
     --query 'Configuration.Role'
   ```

4. **Streamlit Connection Timeout**
   - Check .env file has correct API_BASE_URL
   - Verify AWS credentials are valid
   - Check Lambda functions are deployed

## Performance Expectations

- Streamlit startup: < 5 seconds
- API Gateway response: < 5 seconds
- Lambda cold start: < 3 seconds
- Lambda warm: < 1 second
- DynamoDB operations: < 100ms
- S3 operations: < 500ms

## Cost Optimization

### Free Tier Usage
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- DynamoDB: 25GB storage free
- S3: 5GB storage free

### Development Best Practices
- Delete old sessions regularly
- Clean up S3 files after testing
- Use DynamoDB TTL (already configured)
- Monitor CloudWatch costs

## Removed Components

The following components are **NO LONGER USED**:

- ❌ Docker Compose services
- ❌ DynamoDB Local
- ❌ DynamoDB Admin UI
- ❌ MinIO (S3 mock)
- ❌ Chroma (Vector DB mock)
- ❌ SAM Local API
- ❌ Local endpoint configurations
- ❌ Mock testing infrastructure

All testing and development now uses **real AWS services**.
