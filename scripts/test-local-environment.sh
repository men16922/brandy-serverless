#!/bin/bash
# 로컬 환경 전체 테스트 스크립트

set -e

echo "🧪 로컬 환경 전체 테스트 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 추적
TESTS_PASSED=0
TESTS_FAILED=0

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}🔍 Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 1. Python 가상환경 확인
run_test "Python Virtual Environment" '
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "Virtual environment not activated"
        exit 1
    fi
    echo "Virtual environment: $VIRTUAL_ENV"
    python --version
    which python | grep -q venv
'

# 2. Docker 서비스 확인
run_test "Docker Services Status" '
    docker-compose -f docker-compose.local.yml ps | grep -q "Up"
'

# 3. DynamoDB Local 연결 테스트
run_test "DynamoDB Local Connection" '
    curl -s http://localhost:8000 > /dev/null
    echo "DynamoDB Local responding on port 8000"
'

# 4. DynamoDB Admin UI 접근 테스트
run_test "DynamoDB Admin UI" '
    curl -s http://localhost:8002 > /dev/null
    echo "DynamoDB Admin UI accessible at http://localhost:8002"
'

# 5. MinIO 서비스 테스트
run_test "MinIO Service" '
    curl -s http://localhost:9000/minio/health/live | grep -q "200 OK" || 
    curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live | grep -q "200"
    echo "MinIO service healthy"
'

# 6. MinIO Console 접근 테스트
run_test "MinIO Console" '
    curl -s -o /dev/null -w "%{http_code}" http://localhost:9001 | grep -q "200"
    echo "MinIO Console accessible at http://localhost:9001"
'

# 7. Chroma 서비스 테스트
run_test "Chroma Service" '
    nc -z localhost 8001
    echo "Chroma service responding on port 8001"
'

# 8. Python 의존성 확인
run_test "Python Dependencies" '
    python -c "import boto3, requests, pytest; print(\"Core dependencies available\")"
    pip list | grep -q boto3
    pip list | grep -q pytest
'

# 9. 실제 DynamoDB 테이블 생성/삭제 테스트
run_test "DynamoDB Table Operations" '
    python3 << EOF
import boto3
import time

# DynamoDB 클라이언트 생성
dynamodb = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)

# 테스트 테이블 생성
table_name = "test-environment-validation"
try:
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    
    # 테이블 생성 대기
    waiter = dynamodb.get_waiter("table_exists")
    waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10})
    
    # 테스트 아이템 추가
    dynamodb.put_item(
        TableName=table_name,
        Item={
            "id": {"S": "test-item-1"},
            "data": {"S": "test data"},
            "timestamp": {"S": "2024-01-01T00:00:00Z"}
        }
    )
    
    # 아이템 조회
    response = dynamodb.get_item(
        TableName=table_name,
        Key={"id": {"S": "test-item-1"}}
    )
    
    assert "Item" in response
    assert response["Item"]["data"]["S"] == "test data"
    
    # 테이블 삭제
    dynamodb.delete_table(TableName=table_name)
    
    print("DynamoDB operations successful")
    
except Exception as e:
    print(f"DynamoDB test failed: {e}")
    exit(1)
EOF
'

# 10. MinIO S3 호환성 테스트
run_test "MinIO S3 Compatibility" '
    python3 << EOF
import boto3
from datetime import datetime

# S3 클라이언트 생성
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    region_name="us-east-1"
)

# 테스트 버킷 생성
bucket_name = "test-environment-validation"
try:
    s3.create_bucket(Bucket=bucket_name)
    
    # 테스트 파일 업로드
    test_content = f"Test file created at {datetime.now()}"
    s3.put_object(
        Bucket=bucket_name,
        Key="test-file.txt",
        Body=test_content.encode("utf-8")
    )
    
    # 파일 다운로드 및 검증
    response = s3.get_object(Bucket=bucket_name, Key="test-file.txt")
    downloaded_content = response["Body"].read().decode("utf-8")
    
    assert downloaded_content == test_content
    
    # 정리
    s3.delete_object(Bucket=bucket_name, Key="test-file.txt")
    s3.delete_bucket(Bucket=bucket_name)
    
    print("MinIO S3 operations successful")
    
except Exception as e:
    print(f"MinIO S3 test failed: {e}")
    exit(1)
EOF
'

# 11. 통합 테스트 실행
run_test "Integration Tests Execution" '
    python -m pytest tests/integration/test_workflow.py::TestDockerIntegration::test_docker_services_health -v --tb=short
'

# 12. 전체 통합 테스트 (간단한 버전)
run_test "Full Integration Test Sample" '
    python -m pytest tests/integration/test_workflow.py::TestDockerIntegration::test_dynamodb_connection -v --tb=short
'

# 결과 요약
echo -e "\n" 
echo "=================================================="
echo "🧪 로컬 환경 테스트 결과 요약"
echo "=================================================="
echo -e "${GREEN}✅ 통과: $TESTS_PASSED${NC}"
echo -e "${RED}❌ 실패: $TESTS_FAILED${NC}"
echo "총 테스트: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 모든 테스트 통과! 로컬 환경이 정상적으로 설정되었습니다.${NC}"
    echo ""
    echo "다음 단계:"
    echo "  1. 통합 테스트 실행: python -m pytest tests/integration/ -v"
    echo "  2. Streamlit 앱 실행: cd src/streamlit && streamlit run app.py"
    echo "  3. SAM 로컬 API: sam build && sam local start-api --port 3000"
    echo ""
    echo "관리 UI 접근:"
    echo "  - DynamoDB Admin: http://localhost:8002"
    echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
    exit 0
else
    echo -e "\n${RED}❌ 일부 테스트가 실패했습니다. 위의 오류를 확인하고 수정하세요.${NC}"
    echo ""
    echo "문제 해결 가이드:"
    echo "  1. 가상환경 활성화: source venv/bin/activate"
    echo "  2. Docker 서비스 재시작: docker-compose -f docker-compose.local.yml down -v && docker-compose -f docker-compose.local.yml up -d"
    echo "  3. 의존성 재설치: pip install -r requirements.txt"
    echo "  4. 포트 충돌 확인: lsof -i :8000,8001,8002,9000,9001"
    exit 1
fi