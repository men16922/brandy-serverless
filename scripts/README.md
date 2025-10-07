# Scripts Directory

This directory contains utility scripts for development, deployment, and verification.

## Available Scripts

### 🔍 verify-bedrock-setup.sh

Verifies Amazon Bedrock configuration and permissions before deployment.

**Purpose:**
- Validates AWS credentials and Bedrock service access
- Checks Claude 3.5 Sonnet and SDXL model availability
- Verifies IAM permissions (bedrock:InvokeModel, bedrock:Retrieve)
- Confirms Knowledge Base and Agent configurations (if provided)
- Provides clear error messages for troubleshooting

**Usage:**
```bash
# Basic verification
./scripts/verify-bedrock-setup.sh

# With custom environment variables
BEDROCK_REGION=us-west-2 ./scripts/verify-bedrock-setup.sh

# With Knowledge Base
BEDROCK_KB_ID=your-kb-id ./scripts/verify-bedrock-setup.sh

# With Bedrock Agent
BEDROCK_AGENT_ID=your-agent-id \
BEDROCK_AGENT_ALIAS_ID=your-alias-id \
./scripts/verify-bedrock-setup.sh
```

**Environment Variables:**
- `BEDROCK_REGION` - AWS region (default: us-east-1)
- `CLAUDE_MODEL_ID` - Claude model ID (default: anthropic.claude-3-5-sonnet-20241022-v2:0)
- `SDXL_MODEL_ID` - SDXL model ID (default: stability.stable-diffusion-xl-v1)
- `BEDROCK_KB_ID` - Knowledge Base ID (optional)
- `BEDROCK_AGENT_ID` - Agent ID (optional)
- `BEDROCK_AGENT_ALIAS_ID` - Agent Alias ID (optional)
- `ENABLE_FALLBACK` - Enable fallback to OpenAI/Gemini (default: false)

**Exit Codes:**
- `0` - All verifications passed
- `1` - One or more critical errors found

**Requirements:**
- AWS CLI installed and configured
- Valid AWS credentials with Bedrock permissions
- jq installed (for JSON parsing)

**Example Output:**
```
🔍 Amazon Bedrock 설정 검증 중...

📦 AWS CLI 확인...
✅ AWS CLI 설치됨: aws-cli/2.30.1

🔑 AWS 자격증명 확인...
✅ AWS 자격증명 확인됨
   Account ID: 123456789012
   User/Role: arn:aws:iam::123456789012:user/developer

🌐 Bedrock 서비스 가용성 확인 (Region: us-east-1)...
✅ Bedrock 서비스 접근 가능

🤖 Claude 3.5 Sonnet 모델 확인...
✅ Claude 모델 사용 가능: anthropic.claude-3-5-sonnet-20241022-v2:0

🎨 Stable Diffusion XL 모델 확인...
✅ SDXL 모델 사용 가능: stability.stable-diffusion-xl-v1

✅ Bedrock 설정 검증 완료!
```

---

### 🚀 setup-local.sh

Sets up local development environment with Docker Compose services.

**Purpose:**
- Starts DynamoDB Local, MinIO, and Chroma services
- Validates Python virtual environment
- Performs health checks on all services
- Installs Python dependencies

**Usage:**
```bash
# Ensure virtual environment is activated first
source venv/bin/activate

# Run setup
./scripts/setup-local.sh
```

**Services Started:**
- DynamoDB Local (port 8000)
- DynamoDB Admin UI (port 8002)
- MinIO (ports 9000/9001)
- Chroma (port 8001)

**Requirements:**
- Docker and Docker Compose installed
- Python virtual environment activated
- Port 8000, 8001, 8002, 9000, 9001 available

---

### 🔧 validate-bedrock-config.py

Python script to validate Bedrock configuration from environment variables.

**Purpose:**
- Validates BedrockConfig dataclass
- Checks configuration consistency
- Provides detailed validation messages

**Usage:**
```bash
# Validate current configuration
python scripts/validate-bedrock-config.py

# Validate with custom environment
BEDROCK_REGION=us-west-2 python scripts/validate-bedrock-config.py
```

---

### 📦 sam-build.sh

Builds SAM application for deployment.

**Usage:**
```bash
./scripts/sam-build.sh
```

---

### 🚀 sam-deploy.sh

Deploys SAM application to AWS.

**Usage:**
```bash
# First deployment (interactive)
./scripts/sam-deploy.sh --guided

# Subsequent deployments
./scripts/sam-deploy.sh
```

---

### 🧪 sam-local.sh

Starts SAM local API Gateway for testing.

**Usage:**
```bash
./scripts/sam-local.sh
```

---

## Development Workflow

### Initial Setup
```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Setup local services
./scripts/setup-local.sh

# 3. Verify Bedrock configuration
./scripts/verify-bedrock-setup.sh
```

### Before Deployment
```bash
# 1. Verify Bedrock setup
./scripts/verify-bedrock-setup.sh

# 2. Build SAM application
./scripts/sam-build.sh

# 3. Deploy to AWS
./scripts/sam-deploy.sh --guided
```

### Local Testing
```bash
# 1. Start local services
./scripts/setup-local.sh

# 2. Start local API
./scripts/sam-local.sh

# 3. Run integration tests
python -m pytest tests/integration/ -v
```

## Troubleshooting

### verify-bedrock-setup.sh Issues

**AWS CLI not found:**
```bash
# macOS
brew install awscli

# Linux
pip install awscli

# Verify installation
aws --version
```

**AWS credentials not configured:**
```bash
# Configure credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

**Bedrock service not accessible:**
- Verify region supports Bedrock (us-east-1, us-west-2, etc.)
- Check AWS account has Bedrock enabled
- Verify IAM permissions include bedrock:ListFoundationModels

**Model not available:**
- Check model ID spelling
- Verify model is available in your region
- Use `aws bedrock list-foundation-models` to see available models

**IAM permission errors:**
Add required permissions to your IAM policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:Retrieve",
        "bedrock-agent-runtime:InvokeAgent"
      ],
      "Resource": "*"
    }
  ]
}
```

### setup-local.sh Issues

**Docker not running:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker daemon (Linux)
sudo systemctl start docker
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :8000,8001,8002,9000,9001

# Kill conflicting processes
sudo lsof -ti:8000 | xargs kill -9
```

**Virtual environment not activated:**
```bash
# Activate virtual environment
source venv/bin/activate

# Verify activation
echo $VIRTUAL_ENV
```

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Project README](../README.md)
