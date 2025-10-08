# AgentCore Integration Tests

## 개요

AgentCore 통합 테스트는 Bedrock AgentCore 오케스트레이션, Tool Use primitive, Memory primitive를 검증합니다.

## 환경별 실행 방법

### 🏠 Local 환경 (Docker Compose)

**특징:**
- Docker Compose로 로컬 서비스 실행
- DynamoDB Local, MinIO, Chroma 사용
- Bedrock API/Lambda 호출 실패 (예상됨)
- 에러 처리 및 fallback 메커니즘 검증

**실행 방법:**

```bash
# 1. 간단한 방법 (스크립트 사용)
./scripts/test-local.sh

# 2. Verbose 모드
./scripts/test-local.sh verbose

# 3. 수동 실행
docker-compose -f docker-compose.local.yml up -d
pytest tests/integration/test_agentcore.py -v
```

**환경 설정:**
- 파일: `.env.test`
- 자동 로드: `conftest.py`에서 자동으로 로드됨

**서비스 접근:**
- DynamoDB Admin UI: http://localhost:8002
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Chroma API: http://localhost:8001

---

### ☁️ Dev 환경 (AWS)

**특징:**
- 실제 AWS 서비스 사용
- Lambda 함수 배포 필요
- Bedrock API 호출 성공
- End-to-end 워크플로 테스트

**사전 준비:**

1. **AWS 자격 증명 설정**
   ```bash
   aws configure
   # 또는
   export AWS_PROFILE=your-profile
   ```

2. **SAM 스택 배포**
   ```bash
   sam build
   sam deploy --guided
   ```

3. **`.env.dev` 파일 설정**
   ```bash
   # .env.dev 파일 편집
   BEDROCK_AGENT_ID=your-agent-id-here
   SESSIONS_TABLE=branding-chatbot-sessions-dev
   ```

**실행 방법:**

```bash
# 1. 간단한 방법 (스크립트 사용)
./scripts/test-dev.sh

# 2. Verbose 모드
./scripts/test-dev.sh verbose

# 3. 수동 실행
source .env.dev
pytest tests/integration/test_agentcore.py -v
```

**환경 설정:**
- 파일: `.env.dev`
- 수동 로드: `source .env.dev` 또는 스크립트 사용

**AWS 리소스 확인:**
- DynamoDB: https://console.aws.amazon.com/dynamodb
- Lambda: https://console.aws.amazon.com/lambda
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch

---

## 테스트 구조

### 테스트 클래스

1. **TestAgentCoreOrchestration** - 전체 오케스트레이션
   - `test_agentcore_orchestrator_initialization`
   - `test_agentcore_orchestration_step1`
   - `test_agentcore_full_workflow`

2. **TestAgentCoreToolUse** - Tool Use primitive
   - `test_tool_use_agent_invocation`
   - `test_tool_use_multiple_agents`
   - `test_tool_use_error_handling`

3. **TestAgentCoreMemory** - Memory primitive
   - `test_memory_store_and_retrieve`
   - `test_memory_persistence_across_steps`
   - `test_memory_empty_session`

4. **TestAgentCoreInterAgentCommunication** - Agent 간 통신
   - `test_sequential_agent_communication`
   - `test_parallel_agent_execution`

5. **TestAgentCoreFallback** - Step Functions fallback
   - `test_fallback_detection`
   - `test_orchestration_without_agentcore`

6. **TestAgentCoreReasoningDecisions** - Reasoning LLM
   - `test_reasoning_next_step_decision`

### 특정 테스트 실행

```bash
# 특정 클래스
pytest tests/integration/test_agentcore.py::TestAgentCoreMemory -v

# 특정 테스트
pytest tests/integration/test_agentcore.py::TestAgentCoreMemory::test_memory_store_and_retrieve -v

# 키워드로 필터링
pytest tests/integration/test_agentcore.py -k "memory" -v
```

---

## 환경 비교

| 항목 | Local | Dev |
|------|-------|-----|
| **서비스** | Docker Compose | AWS |
| **DynamoDB** | DynamoDB Local | Real DynamoDB |
| **S3** | MinIO | Real S3 |
| **Vector DB** | Chroma | Bedrock KB |
| **Lambda** | ❌ 없음 | ✅ 배포됨 |
| **Bedrock API** | ⚠️ 실패 (예상) | ✅ 성공 |
| **테스트 범위** | 메커니즘 검증 | End-to-end |
| **실행 시간** | ~12초 | ~30-60초 |
| **비용** | 무료 | AWS 요금 발생 |

---

## 트러블슈팅

### Local 환경

**Docker 서비스가 시작되지 않음:**
```bash
# Docker 상태 확인
docker info

# 서비스 재시작
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d

# 로그 확인
docker-compose -f docker-compose.local.yml logs
```

**포트 충돌:**
```bash
# 포트 사용 확인
lsof -i :8000,8001,8002,9000,9001

# 프로세스 종료
sudo lsof -ti:8000 | xargs kill -9
```

### Dev 환경

**AWS 자격 증명 오류:**
```bash
# 자격 증명 확인
aws sts get-caller-identity

# 프로파일 설정
export AWS_PROFILE=your-profile
```

**Lambda 함수 없음:**
```bash
# SAM 배포
sam build
sam deploy

# Lambda 함수 확인
aws lambda list-functions --query 'Functions[?contains(FunctionName, `branding-chatbot`)].FunctionName'
```

**DynamoDB 테이블 없음:**
```bash
# 테이블 생성 (SAM이 자동 생성하지만 수동으로도 가능)
aws dynamodb create-table \
    --table-name branding-chatbot-sessions-dev \
    --attribute-definitions AttributeName=sessionId,AttributeType=S \
    --key-schema AttributeName=sessionId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

---

## CI/CD 통합

### GitHub Actions 예시

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
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run local tests
        run: ./scripts/test-local.sh

  test-dev:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run dev tests
        run: ./scripts/test-dev.sh
```

---

## 참고 자료

- [Task 9 Requirements](.kiro/specs/aws-hackathon-compliance/tasks.md)
- [Test Results](TEST_RESULTS.md)
- [Docker Compose Configuration](../../docker-compose.local.yml)
- [SAM Template](../../template.yaml)
