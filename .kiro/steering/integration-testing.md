# Integration Testing Strategy

## 테스트 철학

**NO MOCKS 정책**: Mock 객체나 JSON 파일 사용 금지. 실제 Docker Compose 환경에서 실제 데이터베이스를 사용한 end-to-end 통합 테스트만 수행합니다.

### 절대 금지 사항
- ❌ Mock 객체 사용 (`unittest.mock`, `pytest-mock` 등)
- ❌ JSON 파일로 테스트 데이터 저장
- ❌ 가짜 데이터베이스나 인메모리 DB 사용
- ❌ 단위 테스트 작성 (복잡성만 증가)

### 왜 통합 테스트만 사용하는가?

1. **실제 환경 검증**: 단위 테스트로는 확인할 수 없는 서비스 간 실제 연동 검증
2. **Agent 협업 확인**: Supervisor Agent와 각 전문 Agent 간의 실제 통신 및 조정 검증  
3. **데이터 플로우 검증**: DynamoDB → S3 → Chroma 간 실제 데이터 흐름 확인
4. **오류 복구 검증**: 실제 서비스 장애 시나리오에서의 폴백 메커니즘 동작 확인
5. **복잡성 감소**: 단위 테스트 작성/유지보수 오버헤드 제거

## Docker Compose 기반 테스트 환경

### 서비스 구성
```yaml
# docker-compose.local.yml
services:
  dynamodb-local:      # 포트 8000 - 세션 데이터 저장
  dynamodb-admin:      # 포트 8002 - DynamoDB UI 관리
  minio:              # 포트 9000/9001 - S3 호환 파일 저장
  chroma:             # 포트 8001 - 벡터 데이터베이스
```

### 테스트 환경 접근 URL
- **DynamoDB Admin UI**: http://localhost:8002 (테이블 및 데이터 시각화)
- **MinIO Console**: http://localhost:9001 (파일 업로드/다운로드 관리)
- **Chroma API**: http://localhost:8001 (벡터 검색 테스트)

## 핵심 테스트 컴포넌트

### 1. DockerComposeManager
```python
class DockerComposeManager:
    """Docker Compose 서비스 라이프사이클 관리"""
    
    def start_services(self) -> bool:
        """docker-compose.local.yml 서비스 시작"""
        
    def wait_for_health(self, timeout: int = 60) -> bool:
        """모든 서비스 헬스체크 대기"""
        
    def stop_services(self) -> None:
        """서비스 정리 및 데이터 클린업"""
        
    def is_docker_available(self) -> bool:
        """Docker 실행 상태 확인"""
```

### 2. TestEnvironment
```python
class TestEnvironment:
    """실제 서비스를 사용한 테스트 환경 구성"""
    
    def setup_dynamodb_tables(self) -> None:
        """DynamoDB Local에 실제 WorkflowSessions 테이블 생성"""
        
    def setup_s3_buckets(self) -> None:
        """MinIO에 실제 버킷 및 폴더 구조 생성"""
        
    def setup_chroma_collections(self) -> None:
        """Chroma에 테스트용 벡터 컬렉션 생성"""
        
    def cleanup_test_data(self) -> None:
        """테스트 데이터 완전 정리"""
```

### 3. WorkflowIntegrationTester
```python
class WorkflowIntegrationTester:
    """전체 워크플로 통합 테스트"""
    
    def test_full_5step_workflow(self) -> None:
        """분석→상호명→간판→인테리어→PDF 전체 프로세스"""
        
    def test_session_persistence(self) -> None:
        """세션 데이터 DynamoDB 저장/복원"""
        
    def test_file_operations(self) -> None:
        """MinIO 파일 업로드/다운로드"""
        
    def test_agent_coordination(self) -> None:
        """Agent 간 통신 및 Supervisor 모니터링"""
```

## 테스트 시나리오

### 1. 전체 워크플로 테스트
- 실제 BusinessInfo로 세션 생성
- DynamoDB Admin UI에서 세션 상태 확인
- 각 단계별 Agent 실행 및 결과 검증
- MinIO Console에서 생성된 파일들 확인
- PDF 생성 및 다운로드 링크 검증

### 2. Agent 통신 테스트
- Supervisor Agent의 워크플로 모니터링
- Agent 간 메시지 전달 확인
- 구조화된 로그 (agent, tool, latency_ms) 검증
- 실패 시 재시도/폴백 메커니즘 테스트

### 3. 데이터 지속성 테스트
- 세션 TTL 동작 확인 (DynamoDB Admin UI에서 시각적 확인)
- 파일 메타데이터 일관성 검증
- 중간 단계 실패 시 데이터 복구
- 동시 세션 처리 시 데이터 격리

### 4. 오류 처리 테스트
- AI Provider 실패 시 폴백 이미지 사용
- 네트워크 타임아웃 시나리오
- 서비스 일시 중단 시 복구 메커니즘
- 잘못된 입력 데이터 처리

## pytest 구현 전략

### Fixture 기반 환경 관리
```python
@pytest.fixture(scope="session")
def docker_services():
    """세션 전체에서 Docker 서비스 관리"""
    manager = DockerComposeManager()
    if not manager.is_docker_available():
        pytest.skip("Docker not available - 통합 테스트 건너뜀")
    
    manager.start_services()
    manager.wait_for_health()
    yield manager
    manager.stop_services()

@pytest.fixture
def test_environment(docker_services):
    """각 테스트별 환경 초기화"""
    env = TestEnvironment()
    env.setup_all()
    yield env
    env.cleanup_test_data()
```

### 테스트 실행 플로우
1. **Pre-Test**: Docker 가용성 확인, 포트 충돌 체크
2. **Setup**: Docker Compose 시작, 서비스 헬스체크
3. **Test**: 실제 API 호출로 워크플로 실행
4. **Verify**: 데이터베이스/스토리지 상태 검증 (UI 도구 활용)
5. **Cleanup**: 테스트 데이터 정리, Docker 서비스 중지

## DynamoDB 스키마 및 데이터 검증

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