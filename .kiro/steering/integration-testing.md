# Integration Testing Strategy - AWS-Only Architecture

## Testing Philosophy

**AWS DEV ENVIRONMENT**: All integration tests use AWS dev environment directly. No mocks, no Docker Compose, no local services.

### Why AWS Dev Environment Testing?

1. **Real Environment**: Tests run against actual AWS services (DynamoDB, S3, Lambda)
2. **Consistency**: Dev environment matches production architecture
3. **Agent Collaboration**: Test real agent communication via AWS services
4. **Data Flow**: Verify actual data flow through AWS DynamoDB → S3 → Bedrock
5. **Error Recovery**: Test real error scenarios with AWS service failures
6. **Simplicity**: No Docker Compose complexity or local service management

### Prohibited Practices
- ❌ Mock objects (`unittest.mock`, `pytest-mock`)
- ❌ JSON file test data
- ❌ In-memory databases
- ❌ Docker Compose local services
- ❌ Unit tests (use integration tests instead)

## AWS Dev Environment Setup

### Prerequisites
```bash
# 1. Configure AWS credentials
aws configure

# 2. Deploy to AWS dev environment
./safe_deploy.sh

# 3. Verify deployment
aws cloudformation describe-stacks --stack-name ai-branding-chatbot-dev
```

### AWS Resources Used for Testing
- **DynamoDB**: ai-branding-chatbot-sessions
- **S3**: ai-branding-chatbot-assets-908601828278
- **Lambda**: 7 agent functions
- **API Gateway**: https://xxx.execute-api.us-east-1.amazonaws.com/dev

## Core Test Components

### 1. AWSEnvironmentChecker
```python
class AWSEnvironmentChecker:
    """AWS environment availability checker"""
    
    def is_aws_configured(self) -> bool:
        """Check if AWS credentials are configured"""
        
    def check_services(self) -> bool:
        """Check if required AWS services are accessible"""
```

### 2. TestEnvironment
```python
class TestEnvironment:
    """AWS test environment setup and management"""
    
    def verify_dynamodb_table(self) -> None:
        """Verify DynamoDB table exists in AWS"""
        
    def verify_s3_bucket(self) -> None:
        """Verify S3 bucket exists in AWS"""
        
    def cleanup_test_data(self) -> None:
        """Optional cleanup (AWS resources persist)"""
```

### 3. WorkflowIntegrationTester
```python
class WorkflowIntegrationTester:
    """Full workflow integration testing with AWS"""
    
    def test_full_5step_workflow(self) -> None:
        """분석→상호명→간판→인테리어→PDF 전체 프로세스"""
        
    def test_session_persistence(self) -> None:
        """Session data persistence in AWS DynamoDB"""
        
    def test_file_operations(self) -> None:
        """File upload/download with AWS S3"""
        
    def test_agent_coordination(self) -> None:
        """Agent communication and Supervisor monitoring"""
```

## Test Scenarios

### 1. Full Workflow Test
- Create session with real BusinessInfo
- Verify session state in AWS DynamoDB Console
- Execute each workflow step via Lambda
- Verify generated files in AWS S3 Console
- Validate PDF generation and download links

### 2. Agent Communication Test
- Supervisor Agent workflow monitoring
- Agent-to-agent message passing via AWS services
- Structured logging (agent, tool, latency_ms) verification
- Retry/fallback mechanism testing on failures

### 3. Data Persistence Test
- Session TTL behavior in DynamoDB
- File metadata consistency in S3
- Data recovery on mid-workflow failures
- Data isolation for concurrent sessions

### 4. Error Handling Test
- AI Provider failure with fallback images
- Network timeout scenarios
- Service interruption recovery
- Invalid input data handling

## pytest Implementation Strategy

### Fixture-Based Environment Management
```python
@pytest.fixture(scope="session")
def aws_environment():
    """Session-scoped AWS environment checker"""
    checker = AWSEnvironmentChecker()
    if not checker.is_aws_configured():
        pytest.skip("AWS credentials not configured")
    
    if not checker.check_services():
        pytest.skip("AWS services not accessible")
    
    yield checker

@pytest.fixture
def test_environment(aws_environment):
    """Per-test environment initialization"""
    env = TestEnvironment()
    if not env.verify_dynamodb_table():
        pytest.skip("DynamoDB table not found. Deploy first: ./safe_deploy.sh")
    if not env.verify_s3_bucket():
        pytest.skip("S3 bucket not found. Deploy first: ./safe_deploy.sh")
    yield env
    env.cleanup_test_data()
```

### Test Execution Flow
1. **Pre-Test**: Check AWS credentials and service availability
2. **Setup**: Verify AWS resources (DynamoDB table, S3 bucket)
3. **Test**: Execute workflow via AWS API Gateway
4. **Verify**: Check data in AWS Console (DynamoDB, S3, CloudWatch)
5. **Cleanup**: Optional cleanup (AWS resources persist)

## AWS Resource Verification

### WorkflowSessions 테이블 스키마
```python
# 테스트에서 생성할 실제 테이블 구조
table_schema = {
    'TableName': 'WorkflowSessions',
    'KeySchema': [
        {'AttributeName': 'sessionId', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'sessionId', 'AttributeType': 'S'},
        {'AttributeName': 'currentStep', 'AttributeType': 'N'},
        {'AttributeName': 'createdAt', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'StepIndex',
            'KeySchema': [
                {'AttributeName': 'currentStep', 'KeyType': 'HASH'},
                {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ],
    'TimeToLiveSpecification': {
        'AttributeName': 'ttl',
        'Enabled': True
    }
}
```

### 데이터 검증 패턴
```python
def test_session_data_integrity():
    """세션 데이터 무결성 테스트"""
    # 1. 세션 생성
    session_data = create_test_session()
    
    # 2. DynamoDB에 저장 확인
    stored_session = dynamodb_client.get_item(
        TableName='WorkflowSessions',
        Key={'sessionId': {'S': session_data['sessionId']}}
    )
    
    # 3. DynamoDB Admin UI에서도 확인 가능
    # http://localhost:8002에서 시각적으로 데이터 확인
    
    # 4. 데이터 구조 검증
    assert stored_session['Item']['currentStep']['N'] == '1'
    assert 'ttl' in stored_session['Item']
    assert 'businessInfo' in stored_session['Item']
```

## CI/CD 통합 고려사항

### GitHub Actions 설정
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:20.10.7
        options: --privileged
    
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-docker-compose
      
      - name: Run Integration Tests
        run: |
          pytest tests/integration/ -v --tb=short
        timeout-minutes: 10
      
      - name: Collect logs on failure
        if: failure()
        run: |
          docker-compose -f docker-compose.local.yml logs > docker-logs.txt
        
      - name: Upload artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-artifacts
          path: |
            docker-logs.txt
            tests/reports/
```

## 성능 및 안정성 검증

### 성능 테스트
- 각 워크플로 단계별 응답 시간 측정
- Docker 서비스 시작 시간 최적화 (30초 이내)
- 동시 세션 처리 능력 테스트

### 안정성 테스트
- 반복 실행 시 일관된 결과 보장
- 메모리 누수 및 리소스 정리 확인
- 네트워크 지연 시뮬레이션

## 디버깅 및 트러블슈팅

### 로컬 서비스 접근
- **DynamoDB Admin**: http://localhost:8002 - 테이블 구조 및 데이터 확인
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin) - 파일 업로드/다운로드 상태
- **Chroma**: http://localhost:8001/api/v1/collections - 벡터 컬렉션 상태

### 일반적인 문제 해결
1. **포트 충돌**: `lsof -i :8000,8001,8002,9000,9001`로 포트 사용 확인
2. **Docker 메모리 부족**: Docker Desktop 메모리 할당 증가 (최소 4GB)
3. **서비스 시작 실패**: `docker-compose -f docker-compose.local.yml logs [service-name]`로 로그 확인
4. **데이터 정리**: `docker-compose -f docker-compose.local.yml down -v`로 볼륨까지 완전 삭제

## 테스트 작성 가이드라인

### DO (필수 사항)
- ✅ 실제 Docker 서비스 연동으로 end-to-end 테스트 작성
- ✅ DynamoDB Local에 실제 데이터 저장/조회
- ✅ MinIO에 실제 파일 업로드/다운로드
- ✅ Chroma에 실제 벡터 데이터 저장
- ✅ DynamoDB Admin UI로 데이터 시각적 검증
- ✅ Agent 간 실제 통신 및 Supervisor 모니터링 테스트
- ✅ 실제 오류 시나리오 및 폴백 메커니즘 검증
- ✅ 테스트 후 실제 데이터 완전 정리

### DON'T (절대 금지)
- ❌ Mock 객체 사용 (`Mock()`, `patch()`, `MagicMock()` 등)
- ❌ JSON 파일로 테스트 데이터 관리
- ❌ 단위 테스트 작성 (복잡성만 증가, 실제 연동 검증 불가)
- ❌ 인메모리 데이터베이스 사용
- ❌ 가짜 HTTP 응답 생성
- ❌ 테스트 간 데이터 공유 (격리 원칙 위반)
- ❌ Docker 없이 테스트 실행 (환경 일관성 보장 불가)
- ❌ 하드코딩된 타임아웃 (환경별 차이 고려 안함)

이 통합 테스트 전략을 통해 AI 브랜딩 챗봇의 전체 워크플로가 실제 환경에서 안정적으로 동작함을 보장할 수 있습니다.