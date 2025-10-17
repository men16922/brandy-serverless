# AI 브랜딩 챗봇 - 빠른 시작 가이드

## 🎯 개요

업종, 지역, 규모만 입력하면 AI가 **상호명, 간판 디자인, 인테리어, PDF 보고서**를 자동으로 생성하는 서버리스 시스템입니다.

## 🚀 5분 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository>
cd brandy-serverless

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. AWS 배포

```bash
# AWS 자격증명 설정
aws configure

# OpenAI API 키를 Secrets Manager에 저장
aws secretsmanager create-secret \
    --name openai-api-key \
    --secret-string '{"api_key":"sk-your-key-here"}' \
    --region us-east-1

# AWS dev 환경 배포 (5-10분 소요)
./deploy_to_dev.sh
```

### 3. Streamlit 앱 실행

```bash
# Streamlit 시작
streamlit run src/streamlit/app.py

# 브라우저 자동 오픈: http://localhost:8501
```

## 📱 사용 방법

1. **비즈니스 정보 입력**
   - 업종: 음식점/카페
   - 지역: 서울
   - 규모: 소규모

2. **분석 시작** 버튼 클릭

3. **5단계 자동 진행**
   - 비즈니스 분석
   - 상호명 3개 생성
   - 간판 디자인 3개 생성
   - 인테리어 추천 3개 생성
   - PDF 보고서 생성

## 🛠️ 개발 명령어

```bash
# 환경 검증
./scripts/dev.sh validate

# 통합 테스트
./scripts/dev.sh test

# SAM 빌드
sam build --config-env dev

# SAM 배포
sam deploy --config-env dev

# 로그 확인
sam logs --stack-name ai-branding-chatbot-dev --tail
```

## 📚 상세 문서

- **배포 가이드**: `DEPLOY_TO_AWS_DEV.md`
- **프로젝트 구조**: `README.md`
- **Task 완료 요약**: `TASK_26_COMPLETION_SUMMARY.md`

## 🐛 문제 해결

### API 연결 실패

```bash
# API URL 확인
aws cloudformation describe-stacks \
    --stack-name ai-branding-chatbot-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text

# .env 파일에 추가
echo "API_BASE_URL=<복사한 URL>" >> .env
```

### Streamlit 포트 충돌

```bash
# 다른 포트 사용
streamlit run src/streamlit/app.py --server.port 8502
```

### Lambda 타임아웃

```bash
# 로그 확인
sam logs --stack-name ai-branding-chatbot-dev --tail

# 재배포
sam build --config-env dev && sam deploy --config-env dev
```

## 🗑️ 환경 정리

```bash
# CloudFormation 스택 삭제
aws cloudformation delete-stack --stack-name ai-branding-chatbot-dev

# S3 버킷 비우기
aws s3 rm s3://ai-branding-chatbot-assets-dev/ --recursive
```

## 💡 유용한 팁

1. **빠른 재배포**: `sam build && sam deploy --config-env dev`
2. **실시간 로그**: `sam logs --stack-name ai-branding-chatbot-dev --tail`
3. **DynamoDB 확인**: AWS Console > DynamoDB > Tables
4. **S3 파일 확인**: AWS Console > S3 > Buckets

## 🎉 완료!

이제 http://localhost:8501 에서 AI 브랜딩 챗봇을 사용할 수 있습니다!
