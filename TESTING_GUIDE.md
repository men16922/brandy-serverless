# AgentCore 통합 테스트 가이드

## 빠른 시작

### 🏠 Local 환경 (추천 - 개발용)

```bash
# 1단계: Docker 서비스 시작 및 테스트 실행
./scripts/test-local.sh

# 상세 로그 보기
./scripts/test-local.sh verbose
```

### ☁️ Dev 환경 (AWS 배포 후)

```bash
# 1단계: AWS 자격 증명 확인
aws sts get-caller-identity

# 2단계: .env.dev 파일 설정
cp .env.dev.example .env.dev
# BEDROCK_AGENT_ID 등 설정

# 3단계: 테스트 실행
./scripts/test-dev.sh
```

---

## 환경별 상세 가이드

### 🏠 Local 환경

#### 특징
- ✅ 무료 (AWS 비용 없음)
- ✅ 빠른 실행 (~12초)
- ✅ Docker만 필요
- ⚠️ Bedrock API 호출 실패 (예상됨)
- ⚠️ Lambda 함수 없음

#### 사전 준비
```bash
# Docker 설치 확인
docker --version

# Python 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

#### 실행 방법

**방법 1: 스크립트 사용 (추천)**
```bash
./scripts/test-local.sh
```

**방법 2: 수동 실행**
```bash
# Docker 서비스 시작
docker-compose -f docker-compose.local.yml up -d

# 서비스 상태 확인
docker-compose -f docker-compose.local.yml ps

# 테스트 실행
pytest tests/integration/test_agentcore.py -v
```

**방법 3: 특정 테스트만 실행**
```bash
# Memory 테스트만
pytest tests/integration/test_agentcore.py::TestAgentCoreMemory -v

# Tool Use 테스트만
pytest tests/integration/test_agentcore.py::TestAgentCoreToolUse -v
```

#### 서비스 접근
- **DynamoDB Admin UI:** http://localhost:8002
  - 세션 데이터 시각화
  - 테이블 구조 확인
  
- **MinIO Console:** http://localhost:9001
  - 로그인: minioadmin / minioadmin
  - 파일 업로드/다운로드 확인
  
- **Chroma API:** http://localhost:8001
  - 벡터 데이터베이스 상태

#### 환경 설정
파일: `.env.test` (자동 로드됨)
```bash
ENVIRONMENT=local
SESSIONS_TABLE=branding-chatbot-sessions-test
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
```

---

### ☁️ Dev 환경

#### 특징
- ✅ 실제 AWS 서비스 사용
- ✅ End-to-end 테스트
- ✅ Bedrock API 호출 성공
- ✅ Lambda 함수 실행
- ⚠️ AWS 비용 발생
- ⚠️ 배포 필요

#### 사전 준비

**1. AWS 자격 증명 설정**
```bash
# AWS CLI 설정
aws configure

# 또는 프로파일 사용
export AWS_PROFILE=your-profile

# 확인
aws sts get-caller-identity
```

**2. SAM 스택 배포**
```bash
# 빌드
sam build

# 배포 (처음)
sam deploy --guided

# 배포 (이후)
sam deploy

# 배포 확인
aws cloudformation describe-stacks --stack-name branding-chatbot
```

**3. .env.dev 파일 설정**
```bash
# 파일 생성
cp .env.dev.example .env.dev

# 편집 (필수 항목)
ENVIRONMENT=dev
SESSIONS_TABLE=branding-chatbot-sessions-dev
BEDROCK_AGENT_ID=your-agent-id-here
```

#### 실행 방법

**방법 1: 스크립트 사용 (추천)**
```bash
./scripts/test-dev.sh
```

**방법 2: 수동 실행**
```bash
# 환경 변수 로드
source .env.dev

# 테스트 실행
pytest tests/integration/test_agentcore.py -v
```

#### AWS 리소스 확인

**DynamoDB 테이블**
```bash
# 테이블 목록
aws dynamodb list-tables

# 테이블 데이터 확인
aws dynamodb scan --table-name branding-chatbot-sessions-dev
```

**Lambda 함수**
```bash
# 함수 목록
aws lambda list-functions --query 'Functions[?contains(FunctionName, `branding-chatbot`)].FunctionName'

# 로그 확인
aws logs tail /aws/lambda/branding-chatbot-supervisor-dev --follow
```

**CloudWatch Logs**
```bash
# 로그 그룹 목록
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/branding-chatbot

# 최근 로그
aws logs tail /aws/lambda/branding-chatbot-supervisor-dev --since 10m
```

---

## 테스트 결과 해석

### ✅ 성공 케이스

**Local 환경:**
```
======================= 14 passed, 96 warnings in 11.92s =======================
✅ All tests passed!
```

**Dev 환경:**
```
======================= 14 passed in 45.23s =======================
✅ All tests passed in DEV environment!
```

### ⚠️ 예상되는 경고

**Local 환경:**
- `ResourceNotFoundException` - Lambda 함수 없음 (정상)
- `UnrecognizedClientException` - Bedrock API 인증 실패 (정상)
- `DeprecationWarning` - datetime.utcnow() 사용 (무시 가능)

**Dev 환경:**
- `DeprecationWarning` - datetime.utcnow() 사용 (무시 가능)

### ❌ 실패 케이스

**Docker 서비스 없음:**
```
SKIPPED [1] Docker Compose services not running
```
→ 해결: `docker-compose -f docker-compose.local.yml up -d`

**AWS 자격 증명 오류:**
```
ERROR: The security token included in the request is invalid
```
→ 해결: `aws configure` 또는 `export AWS_PROFILE=your-profile`

**DynamoDB 테이블 없음:**
```
ERROR: ResourceNotFoundException: Table not found
```
→ 해결: SAM 재배포 또는 수동 테이블 생성

---

## 트러블슈팅

### Local 환경

**문제: Docker 서비스가 시작되지 않음**
```bash
# Docker 상태 확인
docker info

# Docker Desktop 재시작
# macOS: Docker Desktop 앱 재시작
# Linux: sudo systemctl restart docker

# 서비스 재시작
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

**문제: 포트 충돌**
```bash
# 포트 사용 확인
lsof -i :8000,8001,8002,9000,9001

# 프로세스 종료
sudo lsof -ti:8000 | xargs kill -9

# 또는 docker-compose.local.yml에서 포트 변경
```

**문제: 테스트가 멈춤**
```bash
# Ctrl+C로 중단 후
docker-compose -f docker-compose.local.yml logs

# 특정 서비스 로그
docker-compose -f docker-compose.local.yml logs dynamodb-local
```

### Dev 환경

**문제: AWS 자격 증명 오류**
```bash
# 현재 자격 증명 확인
aws sts get-caller-identity

# 프로파일 설정
export AWS_PROFILE=your-profile

# 또는 직접 설정
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

**문제: Lambda 함수 없음**
```bash
# SAM 스택 상태 확인
aws cloudformation describe-stacks --stack-name branding-chatbot

# 재배포
sam build && sam deploy

# 함수 확인
aws lambda list-functions | grep branding-chatbot
```

**문제: Bedrock 권한 오류**
```bash
# IAM 역할 확인
aws iam get-role --role-name branding-chatbot-supervisor-role

# Bedrock 권한 추가 (template.yaml 수정 후 재배포)
```

---

## 성능 벤치마크

### Local 환경
- **전체 테스트:** ~12초
- **Memory 테스트:** ~2분 (Bedrock API 호출 포함)
- **Tool Use 테스트:** ~10초

### Dev 환경
- **전체 테스트:** ~45초
- **Memory 테스트:** ~15초
- **Tool Use 테스트:** ~20초 (Lambda cold start 포함)

---

## 다음 단계

### Local 개발
1. ✅ 테스트 작성 및 실행
2. ✅ Docker 환경에서 검증
3. → Dev 환경 배포 준비

### Dev 배포
1. → SAM 스택 배포
2. → .env.dev 설정
3. → Dev 환경 테스트 실행
4. → CloudWatch 로그 확인

### Production 준비
1. → .env.prod 설정
2. → Production 스택 배포
3. → 성능 테스트
4. → 모니터링 설정

---

## 참고 자료

- [테스트 상세 가이드](tests/integration/README.md)
- [테스트 결과](tests/integration/TEST_RESULTS.md)
- [Task 9 요구사항](.kiro/specs/aws-hackathon-compliance/tasks.md)
- [Docker Compose 설정](docker-compose.local.yml)
- [SAM 템플릿](template.yaml)
