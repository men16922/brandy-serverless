# AWS Dev 환경 배포 가이드

## 🎯 목표

로컬 Mock API 대신 실제 AWS dev 환경의 API Gateway를 사용하여 Streamlit 앱을 테스트합니다.

## 📋 사전 준비

### 1. AWS 자격증명 설정

```bash
# AWS CLI 설치 확인
aws --version

# AWS 자격증명 설정
aws configure
```

**입력 정보:**
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1`
- Default output format: `json`

**확인:**
```bash
aws sts get-caller-identity
```

### 2. 환경 변수 설정

`.env` 파일 생성 또는 수정:

```bash
# OpenAI API (필수)
OPENAI_API_KEY=sk-your-actual-key-here

# AWS Bedrock (선택사항)
BEDROCK_REGION=us-east-1
ENABLE_FALLBACK=true
DEV_PROFILE=true

# 배포 후 자동 설정됨
# API_BASE_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/Prod
```

### 3. OpenAI API 키 AWS Secrets Manager에 저장

```bash
# OpenAI API 키를 Secrets Manager에 저장
aws secretsmanager create-secret \
    --name openai-api-key \
    --description "OpenAI API Key for AI Branding Chatbot" \
    --secret-string '{"api_key":"sk-your-actual-key-here"}' \
    --region us-east-1

# 또는 기존 시크릿 업데이트
aws secretsmanager update-secret \
    --secret-id openai-api-key \
    --secret-string '{"api_key":"sk-your-actual-key-here"}' \
    --region us-east-1
```

## 🚀 배포 방법

### 방법 1: 자동 배포 스크립트 (권장)

```bash
./deploy_to_dev.sh
```

**실행 내용:**
1. AWS 자격증명 확인
2. SAM 빌드 (`sam build --config-env dev`)
3. SAM 배포 (`sam deploy --config-env dev`)
4. API Gateway URL 자동 추출
5. `.env` 파일에 API_BASE_URL 자동 추가
6. API 헬스체크

**예상 시간:** 5-10분 (첫 배포)

### 방법 2: 수동 배포

```bash
# 1. SAM 빌드
sam build --config-env dev

# 2. SAM 배포
sam deploy --config-env dev

# 3. API Gateway URL 확인
aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text

# 4. .env 파일에 API_BASE_URL 추가
echo "API_BASE_URL=<복사한 URL>" >> .env
```

## 📊 배포 확인

### 1. CloudFormation 스택 확인

```bash
aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].StackStatus' \
    --output text
```

**예상 출력:** `CREATE_COMPLETE` 또는 `UPDATE_COMPLETE`

### 2. API Gateway URL 확인

```bash
aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs' \
    --output table
```

### 3. API 테스트

```bash
# API Gateway URL을 변수에 저장
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

# 헬스체크
curl $API_URL/

# 세션 생성 테스트
curl -X POST $API_URL/sessions \
    -H "Content-Type: application/json" \
    -d '{
        "businessInfo": {
            "industry": "restaurant",
            "region": "seoul",
            "size": "small"
        }
    }'
```

### 4. Lambda 함수 확인

```bash
# Lambda 함수 목록
aws lambda list-functions \
    --query 'Functions[?contains(FunctionName, `branding-chatbot-dev`)].FunctionName' \
    --output table

# 특정 함수 로그 확인
sam logs --stack-name ai-branding-chatbot-dev --tail
```

## 🎨 Streamlit 앱 연결

### 1. .env 파일 확인

```bash
cat .env | grep API_BASE_URL
```

**예상 출력:**
```
API_BASE_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/Prod
```

### 2. Streamlit 앱 시작

```bash
# 가상환경 활성화
source venv/bin/activate

# Streamlit 실행
streamlit run src/streamlit/app.py
```

### 3. 브라우저 접속

```
http://localhost:8501
```

### 4. 워크플로 테스트

1. **비즈니스 정보 입력**
   - 업종: 음식점/카페
   - 지역: 서울
   - 규모: 소규모
   - 설명: "강남역 근처 모던한 카페"

2. **분석 시작** 버튼 클릭

3. **진행 상황 확인**
   - 5단계 진행 바
   - Agent 실행 상태
   - 실제 AI 생성 결과

4. **결과 확인**
   - 상호명 3개 (실제 AI 생성)
   - 간판 디자인 3개 (DALL-E, SDXL, Gemini)
   - 인테리어 추천 3개
   - PDF 보고서

## 🔍 모니터링

### CloudWatch 로그

```bash
# 실시간 로그 확인
sam logs --stack-name ai-branding-chatbot-dev --tail

# 특정 함수 로그
aws logs tail /aws/lambda/ai-branding-chatbot-dev-SupervisorAgent --follow

# 최근 10분 로그
sam logs --stack-name ai-branding-chatbot-dev --start-time '10min ago'
```

### DynamoDB 테이블 확인

```bash
# 테이블 목록
aws dynamodb list-tables \
    --query 'TableNames[?contains(@, `branding-chatbot-dev`)]' \
    --output table

# 세션 데이터 스캔
aws dynamodb scan \
    --table-name ai-branding-chatbot-sessions-dev \
    --max-items 5
```

### S3 버킷 확인

```bash
# 버킷 목록
aws s3 ls | grep branding-chatbot-dev

# 버킷 내용 확인
aws s3 ls s3://ai-branding-chatbot-assets-dev/ --recursive
```

## 🐛 문제 해결

### 1. 배포 실패

```bash
# 스택 이벤트 확인
aws cloudformation describe-stack-events \
    --stack-name ai-branding-chatbot-dev \
    --max-items 20

# 스택 삭제 후 재배포
aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev
# 삭제 완료 대기 (5-10분)
./deploy_to_dev.sh
```

### 2. API Gateway 타임아웃

Lambda 함수가 30초 이상 걸리는 경우:

```bash
# template.yaml에서 Timeout 증가
# Globals:
#   Function:
#     Timeout: 300  # 5분

# 재배포
sam build --config-env dev
sam deploy --config-env dev
```

### 3. OpenAI API 키 오류

```bash
# Secrets Manager 확인
aws secretsmanager get-secret-value \
    --secret-id openai-api-key \
    --query SecretString \
    --output text

# 시크릿 업데이트
aws secretsmanager update-secret \
    --secret-id openai-api-key \
    --secret-string '{"api_key":"sk-new-key-here"}'
```

### 4. Lambda 권한 오류

```bash
# Lambda 실행 역할 확인
aws lambda get-function \
    --function-name ai-branding-chatbot-dev-SupervisorAgent \
    --query 'Configuration.Role'

# IAM 정책 확인
# AWS Console > IAM > Roles > <role-name>
```

### 5. Cold Start 느림

첫 요청이 느린 경우:

```bash
# Provisioned Concurrency 설정 (비용 발생)
aws lambda put-provisioned-concurrency-config \
    --function-name ai-branding-chatbot-dev-SupervisorAgent \
    --provisioned-concurrent-executions 1

# 또는 Warm-up 요청 보내기
curl $API_URL/
```

## 💰 비용 관리

### 예상 비용 (월간)

- **Lambda**: ~$5-10 (100만 요청 기준)
- **API Gateway**: ~$3-5 (100만 요청 기준)
- **DynamoDB**: ~$1-2 (On-Demand)
- **S3**: ~$1-2 (10GB 저장)
- **CloudWatch Logs**: ~$1-2
- **OpenAI API**: 사용량에 따라 다름

**총 예상 비용**: ~$15-25/월 (OpenAI 제외)

### 비용 절감 팁

1. **사용하지 않을 때 스택 삭제**
   ```bash
   aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev
   ```

2. **DynamoDB TTL 설정** (이미 설정됨)
   - 24시간 후 자동 삭제

3. **S3 Lifecycle 정책**
   - 30일 후 자동 삭제

4. **CloudWatch Logs 보존 기간**
   - 7일로 설정

## 🔄 업데이트 배포

코드 변경 후 재배포:

```bash
# 빠른 재배포
sam build --config-env dev && sam deploy --config-env dev

# 또는 스크립트 사용
./deploy_to_dev.sh
```

## 🗑️ 환경 정리

테스트 완료 후 리소스 삭제:

```bash
# CloudFormation 스택 삭제
aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev

# S3 버킷 비우기 (스택 삭제 전 필요할 수 있음)
aws s3 rm s3://ai-branding-chatbot-assets-dev/ --recursive

# Secrets Manager 시크릿 삭제 (선택사항)
aws secretsmanager delete-secret \
    --secret-id openai-api-key \
    --force-delete-without-recovery
```

## 📝 체크리스트

### 배포 전
- [ ] AWS 자격증명 설정
- [ ] OpenAI API 키 준비
- [ ] Secrets Manager에 API 키 저장
- [ ] .env 파일 설정
- [ ] SAM CLI 설치 확인

### 배포 중
- [ ] `./deploy_to_dev.sh` 실행
- [ ] CloudFormation 스택 생성 확인
- [ ] API Gateway URL 확인
- [ ] .env 파일 업데이트 확인

### 배포 후
- [ ] API 헬스체크 성공
- [ ] Lambda 함수 목록 확인
- [ ] DynamoDB 테이블 생성 확인
- [ ] S3 버킷 생성 확인
- [ ] Streamlit 앱 연결 테스트
- [ ] 전체 워크플로 테스트

## 🎉 완료!

이제 Streamlit 앱이 실제 AWS dev 환경의 API Gateway를 호출합니다!

```bash
# Streamlit 시작
streamlit run src/streamlit/app.py

# 브라우저 접속
# http://localhost:8501
```

실제 AI가 생성한 결과를 확인할 수 있습니다! 🚀
