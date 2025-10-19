# AI 브랜딩 챗봇 🤖

업종, 지역, 규모만 입력하면 AI가 **상호명, 간판 디자인, 인테리어, PDF 보고서**를 자동으로 만들어주는 서버리스 시스템입니다.

## 🎯 무엇을 하는 프로젝트인가요?

```
입력: "서울 강남에서 소규모 카페 운영 예정"
↓
AI가 자동 생성:
✅ 상호명 3개 후보 (발음/검색 점수 포함)
✅ 간판 디자인 3개 (DALL-E, SDXL, Gemini)
✅ 인테리어 추천 3개 (간판 스타일 맞춤)
✅ 종합 브랜딩 PDF 보고서
```

## 🏗️ 시스템 구조

### 6개 AI 에이전트가 순서대로 작업
1. **Supervisor** - 전체 작업 관리
2. **Product Insight** - 비즈니스 분석  
3. **Market Analyst** - 시장 동향 분석
4. **Reporter** - 상호명 생성
5. **Signboard** - 간판 디자인 (3개 AI 동시 사용)
6. **Interior** - 인테리어 추천

### 기술 스택
- **AWS SAM** - 서버리스 배포
- **Lambda + API Gateway** - 백엔드
- **DynamoDB + S3** - 데이터 저장
- **Step Functions** - 워크플로 관리

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
    --region us-east-1
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
aws sts get-caller-identity

# 4. Restart Streamlit with correct environment
source venv/bin/activate

```

#### 세션 생성 오류 (`Session ID is required`)
```bash
# SAM Local 재시작 (코드 변경사항 반영)
# 터미널에서 Ctrl+C로 중지 후 다시 시작
./scripts/dev.sh api
```

#### 의존성 오류
```bash
# 개발환경 재설정
./scripts/activate-dev.sh

# 수동 설치
source venv/bin/activate
pip install -r src/streamlit/requirements.txt
```

#### 포트 충돌
```bash
# 포트 사용 확인
lsof -i :3000,8501,8000,9000

# 프로세스 종료 후 재시작
./scripts/dev.sh cleanup
./scripts/dev.sh setup
```

## 🧪 테스트 (실제 DB 사용)

```bash
./scripts/dev.sh test      # 통합 테스트 실행 (Bedrock 검증 포함)
./scripts/dev.sh validate  # 환경 및 Bedrock 검증
```

**특징**: Mock 사용 안함. 실제 DynamoDB, MinIO, Chroma 사용하여 신뢰할 수 있는 테스트

### Bedrock 로컬 테스트

AWS Bedrock을 로컬에서 테스트하려면:

```bash
# 1. AWS 자격증명 설정
aws configure
# 또는 환경 변수 설정
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# 2. Bedrock 설정 검증
./scripts/verify-bedrock-setup.sh

# 3. 환경 변수 설정 (.env 파일)
BEDROCK_REGION=us-east-1
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
SDXL_MODEL_ID=stability.stable-diffusion-xl-v1
ENABLE_FALLBACK=true  # 로컬 개발 시 true, 제출 시 false

# 4. Bedrock 통합 테스트 실행
python -m pytest tests/integration/test_bedrock_integration.py -v
```

**참고**: AWS 자격증명 없이도 로컬 개발 가능 (Fallback 모드)

## 🛠️ 개발 명령어

### 통합 개발 스크립트 (권장)
```bash
./scripts/dev.sh setup     # 로컬 환경 설정
./scripts/dev.sh validate  # 환경 검증
./scripts/dev.sh test      # 통합 테스트 실행
./scripts/dev.sh build     # SAM 애플리케이션 빌드
./scripts/dev.sh api       # 로컬 API 서버 시작
./scripts/dev.sh app       # Streamlit 앱 시작
./scripts/dev.sh cleanup   # 환경 정리
./scripts/dev.sh help      # 도움말
```

### 개별 스크립트
```bash
# 환경 관리
./scripts/activate-dev.sh               # 개발환경 활성화
./scripts/setup-local.sh                # Docker 서비스 시작
python scripts/validate-environment.py  # 환경 전체 검증

# SAM 개발 워크플로
./scripts/sam-build.sh                  # SAM application build
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
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# API Gateway (from deployment)
API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/dev

# DynamoDB
SESSIONS_TABLE=ai-branding-chatbot-sessions

# S3
S3_BUCKET=ai-branding-chatbot-assets-908601828278

# OpenAI API (for fallback)
OPENAI_API_KEY=sk-...

# Bedrock Configuration
BEDROCK_REGION=us-east-1
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
BEDROCK_REGION=us-east-1
# AWS 자격증명 필수
```

### 환경 변수 검증

```bash
# 전체 환경 검증
./scripts/dev.sh validate

# Bedrock 설정만 검증
./scripts/verify-bedrock-setup.sh
```

## 📁 프로젝트 구조

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
- "⚠️ 폴백 이미지 (AI 생성 실패 시 대체)" message
- Placeholder images instead of actual designs

**Solutions**:

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/ai-branding-chatbot-signboard-agent-dev --follow
   ```
   
   Look for error messages about Bedrock initialization or API calls.

2. **Verify Bedrock Access**:
   ```bash
   aws bedrock list-foundation-models --region us-east-1 \
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
   - `BEDROCK_REGION`: `us-east-1`
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
