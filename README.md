# AI Branding Chatbot 🤖

A serverless system that automatically generates **business names, signboard designs, interior recommendations, and PDF reports** by simply entering industry, region, and size.

## 🎯 What Does This Project Do?

```
Input: "Planning to operate a small cafe in Gangnam, Seoul"
↓
AI automatically generates:
✅ 3 business name candidates (with pronunciation/search scores)
✅ 3 signboard designs (DALL-E, SDXL, Gemini)
✅ 3 interior recommendations (matched to signboard style)
✅ Comprehensive branding PDF report
```

## 🏗️ System Architecture

### 6 AI Agents Working Sequentially
1. **Supervisor** - Overall workflow management
2. **Product Insight** - Business analysis  
3. **Market Analyst** - Market trend analysis
4. **Reporter** - Business name generation
5. **Signboard** - Signboard design (3 AIs simultaneously)
6. **Interior** - Interior recommendations

### Technology Stack
- **AWS SAM** - Serverless deployment
- **Lambda + API Gateway** - Backend
- **DynamoDB + S3** - Data storage
- **Step Functions** - Workflow management

## 🚀 Quick Start (AWS-Only Architecture)

### Prerequisites
- AWS Account with credentials configured
- Python 3.11+
- AWS CLI installed

### 1. Setup
```bash
# Clone repository
git clone <repository>
cd brandy-serverless

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS
```bash
# Configure AWS credentials
aws configure

# Store OpenAI API key in Secrets Manager
aws secretsmanager create-secret \
    --name openai-api-key \
    --secret-string '{"api_key":"sk-your-key-here"}' \
    --region us-west-2
```

### 3. Deploy to AWS
```bash
# Deploy using safe deployment script (recommended)
./safe_deploy.sh

# This will:
# - Build SAM application
# - Deploy to AWS dev environment
# - Extract API Gateway URL
# - Update .env file
# - Test API connectivity
```

### 4. Run Streamlit Locally
```bash
# Start Streamlit (connects to AWS backend)
streamlit run src/streamlit/app.py

# Browser opens automatically: http://localhost:8501
```

### 5. Verify
- **Streamlit UI**: http://localhost:8501 (local)
- **API Gateway**: Check .env for API_BASE_URL
- **AWS Console**: CloudFormation, Lambda, DynamoDB, S3
- **Logs**: `sam logs --stack-name ai-branding-chatbot-dev --tail`

## 🎨 Using the Application

### 1. Start Streamlit
```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit (connects to AWS)
streamlit run src/streamlit/app.py
```

### 2. Access Web Interface
- **URL**: http://localhost:8501
- Select industry/region/size → Start analysis → 5-step workflow runs automatically

### 3. Troubleshooting

#### API Connection Error
```bash
# 1. Check .env file has correct API_BASE_URL
cat .env | grep API_BASE_URL

# 2. Verify AWS API Gateway is accessible
curl $(grep API_BASE_URL .env | cut -d '=' -f2)/

# 3. Check AWS credentials
aws sts get-caller-identity

# 4. Redeploy if needed
./safe_deploy.sh

# 5. Restart Streamlit with correct environment
source venv/bin/activate
```

#### Session Creation Error (`Session ID is required`)
```bash
# Restart SAM Local (to reflect code changes)
# Stop with Ctrl+C in terminal, then restart
./scripts/dev.sh api
```

#### Dependency Errors
```bash
# Reset development environment
./scripts/activate-dev.sh

# Manual installation
source venv/bin/activate
pip install -r src/streamlit/requirements.txt
```

#### Port Conflicts
```bash
# Check port usage
lsof -i :3000,8501,8000,9000

# Kill processes and restart
./scripts/dev.sh cleanup
./scripts/dev.sh setup
```

## 🧪 Testing (Using Real Database)

```bash
./scripts/dev.sh test      # Run integration tests (includes Bedrock validation)
./scripts/dev.sh validate  # Validate environment and Bedrock
```

**Feature**: No mocks used. Reliable testing with actual DynamoDB, MinIO, and Chroma

### Bedrock Local Testing

To test AWS Bedrock locally:

```bash
# 1. Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# 2. Verify Bedrock setup
./scripts/verify-bedrock-setup.sh

# 3. Configure environment variables (.env file)
BEDROCK_REGION=us-west-2
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
ENABLE_FALLBACK=true  # true for local dev, false for submission

# 4. Run Bedrock integration tests
python -m pytest tests/integration/test_bedrock_integration.py -v
```

**Note**: Local development possible without AWS credentials (Fallback mode)

## 🛠️ Development Commands

### Integrated Development Script (Recommended)
```bash
./scripts/dev.sh setup     # Setup local environment
./scripts/dev.sh validate  # Validate environment
./scripts/dev.sh test      # Run integration tests
./scripts/dev.sh build     # Build SAM application
./scripts/dev.sh api       # Start local API server
./scripts/dev.sh app       # Start Streamlit app
./scripts/dev.sh cleanup   # Clean up environment
./scripts/dev.sh help      # Show help
```

### Individual Scripts
```bash
# Environment management
./scripts/activate-dev.sh               # Activate development environment
./scripts/setup-local.sh                # Start Docker services
python scripts/validate-environment.py  # Validate entire environment

# SAM development workflow
./scripts/sam-build.sh                  # Build SAM application
./safe_deploy.sh                        # Safe AWS deployment
sam logs --stack-name ai-branding-chatbot-dev --tail  # Real-time logs
```

### AWS Console Access
- **CloudFormation**: Check stack status
- **DynamoDB**: View session data
- **S3**: View generated files
- **CloudWatch**: View logs

## ⚙️ Environment Variables

### Required Variables (.env file)

```bash
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# API Gateway (from deployment)
API_BASE_URL=https://your-api-id.execute-api.us-west-2.amazonaws.com/dev

# DynamoDB
SESSIONS_TABLE=ai-branding-chatbot-sessions

# S3
S3_BUCKET=ai-branding-chatbot-assets-908601828278

# OpenAI API (for fallback)
OPENAI_API_KEY=sk-...

# Bedrock Configuration
BEDROCK_REGION=us-west-2
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=amazon.titan-image-generator-v2:0  # Titan Image Generator v2
IMAGE_MODEL_ID=amazon.titan-image-generator-v2:0  # Alias for SDXL_MODEL_ID

# Bedrock Retry Configuration
BEDROCK_MAX_RETRIES=3        # Number of retry attempts
BEDROCK_BASE_DELAY=1.0       # Base delay for exponential backoff (seconds)
BEDROCK_MAX_DELAY=30.0       # Maximum delay cap (seconds)
BEDROCK_TIMEOUT=30           # API timeout (seconds)

# Fallback Settings
ENABLE_FALLBACK=true   # Development: true, Production: false
DEV_PROFILE=true       # Development: true, Production: false
ENVIRONMENT=dev        # Always 'dev' for development
```

### Production Settings (Hackathon Submission)

```bash
ENABLE_FALLBACK=false  # Bedrock Only!
DEV_PROFILE=false
ENVIRONMENT=prod
BEDROCK_REGION=us-west-2
# AWS credentials required
```

### Environment Variable Validation

```bash
# Validate entire environment
./scripts/dev.sh validate

# Validate Bedrock configuration only
./scripts/verify-bedrock-setup.sh
```

## 📁 Project Structure

```
├── template.yaml                      # SAM template (all AWS resources)
├── samconfig.toml                     # SAM deployment config
├── safe_deploy.sh                     # Safe deployment script
├── src/
│   ├── lambda/agents/                 # Agent Lambda functions
│   │   ├── supervisor/                # Workflow orchestration
│   │   ├── product-insight/           # Business analysis
│   │   ├── market-analyst/            # Market analysis
│   │   ├── reporter/                  # Name suggestions
│   │   ├── signboard/                 # Signboard design
│   │   ├── interior/                  # Interior recommendations
│   │   └── report-generator/          # PDF report generation
│   ├── lambda/shared/                 # Shared utilities (Lambda Layer)
│   └── streamlit/                     # Streamlit web app (runs locally)
├── statemachine/                      # Step Functions definitions
├── scripts/                           # Deployment and validation scripts
├── tests/integration/                 # AWS integration tests
└── .env                               # Environment variables
```

## 📚 Documentation

- **Deployment Guide**: `DEPLOYMENT_FIX.md` - AWS deployment guide
- **Local Environment**: `.kiro/steering/local-environment.md` - Development setup
- **Integration Testing**: `.kiro/steering/integration-testing.md` - Testing strategy

## 🗑️ Cleanup

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev

# Empty S3 bucket
aws s3 rm s3://ai-branding-chatbot-assets-908601828278/ --recursive

# Delete DynamoDB table
aws dynamodb delete-table --table-name ai-branding-chatbot-sessions
```

## 📄 License

MIT License

## 🔧 Troubleshooting

### Signboard Generation Issues

#### Problem: Fallback images appearing instead of AI-generated images

**Symptoms**:
- "⚠️ Fallback image (used when AI generation fails)" message
- Placeholder images instead of actual designs

**Solutions**:

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/ai-branding-chatbot-signboard-agent-dev --follow
   ```
   
   Look for error messages about Bedrock initialization or API calls.

2. **Verify Bedrock Access**:
   ```bash
   aws bedrock list-foundation-models --region us-west-2 \
     --query 'modelSummaries[?contains(modelId, `titan-image-generator`)].modelId'
   ```
   
   Should return: `amazon.titan-image-generator-v2:0`

3. **Check IAM Permissions**:
   ```bash
   aws lambda get-function-configuration \
     --function-name ai-branding-chatbot-signboard-agent-dev \
     --query 'Role'
   ```
   
   Verify the role has `bedrock:InvokeModel` permission.

4. **Verify Environment Variables**:
   ```bash
   aws lambda get-function-configuration \
     --function-name ai-branding-chatbot-signboard-agent-dev \
     --query 'Environment.Variables'
   ```
   
   Check:
   - `SDXL_MODEL_ID`: `amazon.titan-image-generator-v2:0`
   - `BEDROCK_REGION`: `us-west-2`
   - `ENABLE_FALLBACK`: `true` (dev) or `false` (prod)

#### Problem: Timeout errors during image generation

**Symptoms**:
- "Task timed out after 60.00 seconds"
- Incomplete image generation

**Solutions**:

1. **Increase Lambda Timeout**:
   Edit `template.yaml`:
   ```yaml
   SignboardAgent:
     Properties:
       Timeout: 90  # Increase from 60
   ```
   
   Redeploy:
   ```bash
   sam build && sam deploy --config-env dev
   ```

2. **Check Bedrock API Latency**:
   Monitor CloudWatch metrics for Bedrock API response times.

3. **Verify Network Connectivity**:
   Ensure Lambda has internet access (if in VPC, check NAT Gateway).

#### Problem: Rate limiting errors

**Symptoms**:
- "ThrottlingException" in CloudWatch logs
- Frequent retry attempts

**Solutions**:

1. **Exponential Backoff** (already implemented):
   The system automatically retries with exponential backoff and jitter.

2. **Request Quota Increase**:
   Contact AWS Support to increase Bedrock API quotas.

3. **Monitor Retry Metrics**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/ai-branding-chatbot-signboard-agent-dev \
     --filter-pattern "retry"
   ```

### AWS Deployment Issues

#### Problem: SAM deployment fails

**Solutions**:

1. **Check Stack Status**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name ai-branding-chatbot-dev \
     --query 'Stacks[0].StackStatus'
   ```

2. **View Failed Events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name ai-branding-chatbot-dev \
     --max-items 20 \
     --query 'StackEvents[?contains(ResourceStatus, `FAILED`)]'
   ```

3. **Delete and Redeploy**:
   ```bash
   aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev
   # Wait for deletion, then redeploy
   ./safe_deploy.sh
   ```

### Streamlit Connection Issues

#### Problem: Cannot connect to API

**Symptoms**:
- Connection timeout errors
- "Failed to fetch" messages

**Solutions**:

1. **Verify API URL**:
   Check `.env` file has correct `API_BASE_URL`.

2. **Test API Endpoint**:
   ```bash
   curl -X GET $API_BASE_URL/
   ```

3. **Check Lambda Cold Start**:
   First request may take longer. Wait 5-10 seconds and retry.

## 📖 Additional Documentation

- [Signboard Generation Fix](docs/SIGNBOARD_GENERATION_FIX.md) - Complete troubleshooting guide for image generation issues
- [Signboard Prompt Length Fix](SIGNBOARD_PROMPT_LENGTH_FIX.md) - **NEW**: Titan Image Generator v2 prompt validation fix
- [Test Guide](TEST_SIGNBOARD_FIX.md) - **NEW**: Testing guide for signboard generation
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Step-by-step deployment guide
- [Hackathon Rules](docs/AWS%20Hackathon%20rules.md) - AWS AI Agent Global Hackathon requirements
- [Architecture Overview](docs/AWS%20Hackathon%20overview.md) - System architecture and design

## 🆕 Recent Updates (2025-10-19)

### Signboard Generation Fix - Prompt Length Validation

**Issue**: Images not generating due to prompt length exceeding Titan Image Generator v2's 512 character limit.

**Fixed**:
- ✅ Added 512 character limit validation in `_create_image_prompt()`
- ✅ Implemented intelligent truncation preserving key information
- ✅ Updated `_optimize_prompt_for_titan()` with proper validation
- ✅ Added comprehensive logging for debugging
- ✅ Deployed to dev environment

**Status**: ✅ **DEPLOYED - READY FOR TESTING**

See [SIGNBOARD_PROMPT_LENGTH_FIX.md](SIGNBOARD_PROMPT_LENGTH_FIX.md) for complete details.

## 🤝 Contributing

This project is for the AWS AI Agent Global Hackathon. For issues or questions:

1. Check CloudWatch logs for error details
2. Review troubleshooting guide above
3. Consult [Signboard Generation Fix](docs/SIGNBOARD_GENERATION_FIX.md) for known issues

## 📄 License

MIT License - See LICENSE file for details
