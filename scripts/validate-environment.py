#!/usr/bin/env python3
"""
로컬 환경 검증 스크립트
실제 서비스 연동 테스트 - NO MOCKS
"""

import os
import sys
import time
import boto3
import requests
import socket
from datetime import datetime, timezone
from typing import Dict, Any, List

# 색상 출력
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message: str, status: str = "info"):
    """상태 메시지 출력"""
    color = Colors.NC
    if status == "success":
        color = Colors.GREEN
        prefix = "✅"
    elif status == "error":
        color = Colors.RED
        prefix = "❌"
    elif status == "warning":
        color = Colors.YELLOW
        prefix = "⚠️"
    else:
        color = Colors.BLUE
        prefix = "🔍"
    
    print(f"{color}{prefix} {message}{Colors.NC}")

def check_virtual_environment() -> bool:
    """Python 가상환경 확인"""
    print_status("Checking Python virtual environment...")
    
    if not os.environ.get('VIRTUAL_ENV'):
        print_status("Virtual environment not activated", "error")
        print("Please activate virtual environment:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        return False
    
    venv_path = os.environ['VIRTUAL_ENV']
    python_path = sys.executable
    
    if 'venv' not in python_path:
        print_status(f"Python not running from venv: {python_path}", "error")
        return False
    
    print_status(f"Virtual environment active: {venv_path}", "success")
    print_status(f"Python executable: {python_path}", "success")
    return True

def check_docker_services() -> bool:
    """Docker 서비스 상태 확인"""
    print_status("Checking Docker services...")
    
    services = {
        'DynamoDB Local': ('localhost', 8000),
        'DynamoDB Admin': ('localhost', 8002),
        'MinIO API': ('localhost', 9000),
        'MinIO Console': ('localhost', 9001),
        'Chroma': ('localhost', 8001)
    }
    
    all_running = True
    
    for service_name, (host, port) in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print_status(f"{service_name} running on {host}:{port}", "success")
            else:
                print_status(f"{service_name} not responding on {host}:{port}", "error")
                all_running = False
        except Exception as e:
            print_status(f"{service_name} check failed: {e}", "error")
            all_running = False
    
    return all_running

def test_dynamodb_operations() -> bool:
    """실제 DynamoDB Local 연동 테스트"""
    print_status("Testing DynamoDB Local operations...")
    
    try:
        # 실제 DynamoDB Local 클라이언트 생성
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        table_name = f'test-validation-{int(time.time())}'
        
        # 실제 테이블 생성
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # 테이블 생성 대기
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name, WaiterConfig={'Delay': 1, 'MaxAttempts': 10})
        
        # 실제 데이터 저장
        test_data = {
            'id': {'S': 'test-session-123'},
            'businessInfo': {'M': {
                'industry': {'S': 'restaurant'},
                'region': {'S': 'seoul'},
                'size': {'S': 'small'}
            }},
            'currentStep': {'N': '1'},
            'status': {'S': 'active'},
            'createdAt': {'S': datetime.now(timezone.utc).isoformat()},
            'agentLogs': {'L': [
                {'M': {
                    'agent': {'S': 'supervisor'},
                    'tool': {'S': 'workflow.monitor'},
                    'latency_ms': {'N': '250'},
                    'status': {'S': 'success'}
                }}
            ]}
        }
        
        dynamodb.put_item(TableName=table_name, Item=test_data)
        
        # 실제 데이터 조회
        response = dynamodb.get_item(
            TableName=table_name,
            Key={'id': {'S': 'test-session-123'}}
        )
        
        if 'Item' not in response:
            raise Exception("Data not found after insertion")
        
        retrieved_item = response['Item']
        if retrieved_item['status']['S'] != 'active':
            raise Exception("Data integrity check failed")
        
        # 정리
        dynamodb.delete_table(TableName=table_name)
        
        print_status("DynamoDB operations successful", "success")
        print_status("  - Table creation/deletion: OK", "success")
        print_status("  - Data insertion/retrieval: OK", "success")
        print_status("  - Complex nested data: OK", "success")
        print_status(f"  - Admin UI: http://localhost:8002", "success")
        
        return True
        
    except Exception as e:
        print_status(f"DynamoDB test failed: {e}", "error")
        return False

def test_minio_operations() -> bool:
    """실제 MinIO S3 호환성 테스트"""
    print_status("Testing MinIO S3 operations...")
    
    try:
        # 실제 MinIO S3 클라이언트 생성
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin',
            region_name='us-east-1'
        )
        
        bucket_name = f'test-validation-{int(time.time())}'
        
        # 실제 버킷 생성
        s3.create_bucket(Bucket=bucket_name)
        
        # 실제 파일 업로드 (다양한 타입)
        test_files = [
            ('session-data.json', '{"sessionId": "test-123", "status": "active"}', 'application/json'),
            ('report.txt', 'Test report content\nGenerated at: ' + datetime.now().isoformat(), 'text/plain'),
            ('image-metadata.json', '{"width": 1024, "height": 768, "format": "PNG"}', 'application/json')
        ]
        
        for filename, content, content_type in test_files:
            s3.put_object(
                Bucket=bucket_name,
                Key=f'test-data/{filename}',
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
        
        # 실제 파일 다운로드 및 검증
        for filename, expected_content, _ in test_files:
            response = s3.get_object(Bucket=bucket_name, Key=f'test-data/{filename}')
            downloaded_content = response['Body'].read().decode('utf-8')
            
            if downloaded_content != expected_content:
                raise Exception(f"Content mismatch for {filename}")
        
        # 버킷 목록 확인
        buckets = s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        
        if bucket_name not in bucket_names:
            raise Exception("Bucket not found in list")
        
        # 정리
        for filename, _, _ in test_files:
            s3.delete_object(Bucket=bucket_name, Key=f'test-data/{filename}')
        s3.delete_bucket(Bucket=bucket_name)
        
        print_status("MinIO S3 operations successful", "success")
        print_status("  - Bucket creation/deletion: OK", "success")
        print_status("  - File upload/download: OK", "success")
        print_status("  - Multiple file types: OK", "success")
        print_status(f"  - Console UI: http://localhost:9001", "success")
        
        return True
        
    except Exception as e:
        print_status(f"MinIO test failed: {e}", "error")
        return False

def test_chroma_connection() -> bool:
    """Chroma 벡터 데이터베이스 연결 테스트"""
    print_status("Testing Chroma connection...")
    
    try:
        # 기본 연결 테스트
        response = requests.get('http://localhost:8001/api/v1/heartbeat', timeout=10)
        
        if response.status_code == 200:
            print_status("Chroma service responding", "success")
            print_status(f"  - API endpoint: http://localhost:8001", "success")
            return True
        else:
            print_status(f"Chroma returned status {response.status_code}", "warning")
            return True  # 서비스가 응답하면 OK
            
    except requests.exceptions.ConnectionError:
        print_status("Chroma service not responding", "error")
        return False
    except Exception as e:
        print_status(f"Chroma test failed: {e}", "error")
        return False

def test_python_dependencies() -> bool:
    """Python 의존성 확인"""
    print_status("Checking Python dependencies...")
    
    required_packages = [
        'boto3',
        'requests', 
        'pytest',
        'pydantic',
        'streamlit'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"  - {package}: OK", "success")
        except ImportError:
            print_status(f"  - {package}: MISSING", "error")
            missing_packages.append(package)
    
    if missing_packages:
        print_status(f"Missing packages: {', '.join(missing_packages)}", "error")
        print("Run: pip install -r requirements.txt")
        return False
    
    print_status("All required dependencies available", "success")
    return True

def run_integration_test_sample() -> bool:
    """간단한 통합 테스트 실행"""
    print_status("Running integration test sample...")
    
    try:
        # 실제 서비스들을 사용한 간단한 워크플로 테스트
        session_id = f"integration-test-{int(time.time())}"
        
        # 1. DynamoDB에 세션 생성
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        table_name = 'integration-test-sessions'
        
        # 테이블 생성 (이미 있으면 무시)
        try:
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'sessionId', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'sessionId', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            time.sleep(2)  # 테이블 생성 대기
        except:
            pass  # 테이블이 이미 존재
        
        # 세션 데이터 저장
        session_data = {
            'sessionId': {'S': session_id},
            'businessInfo': {'M': {
                'industry': {'S': 'technology'},
                'region': {'S': 'seoul'},
                'size': {'S': 'startup'}
            }},
            'currentStep': {'N': '1'},
            'status': {'S': 'active'},
            'createdAt': {'S': datetime.now(timezone.utc).isoformat()}
        }
        
        dynamodb.put_item(TableName=table_name, Item=session_data)
        
        # 2. MinIO에 관련 파일 저장
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin',
            region_name='us-east-1'
        )
        
        bucket_name = 'integration-test-files'
        
        # 버킷 생성 (이미 있으면 무시)
        try:
            s3.create_bucket(Bucket=bucket_name)
        except:
            pass
        
        # 세션 관련 파일 저장
        session_file_content = f"""
Session Analysis Report
======================
Session ID: {session_id}
Business Type: Technology Startup
Region: Seoul
Created: {datetime.now().isoformat()}

This is a test file for integration testing.
No mocks were used in the creation of this data.
        """.strip()
        
        s3.put_object(
            Bucket=bucket_name,
            Key=f'sessions/{session_id}/analysis.txt',
            Body=session_file_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # 3. 데이터 검증
        # DynamoDB에서 세션 조회
        db_response = dynamodb.get_item(
            TableName=table_name,
            Key={'sessionId': {'S': session_id}}
        )
        
        if 'Item' not in db_response:
            raise Exception("Session not found in DynamoDB")
        
        # MinIO에서 파일 조회
        s3_response = s3.get_object(
            Bucket=bucket_name,
            Key=f'sessions/{session_id}/analysis.txt'
        )
        
        file_content = s3_response['Body'].read().decode('utf-8')
        if session_id not in file_content:
            raise Exception("File content validation failed")
        
        print_status("Integration test sample successful", "success")
        print_status(f"  - Session created: {session_id}", "success")
        print_status("  - DynamoDB storage: OK", "success")
        print_status("  - MinIO file storage: OK", "success")
        print_status("  - Cross-service data consistency: OK", "success")
        
        return True
        
    except Exception as e:
        print_status(f"Integration test failed: {e}", "error")
        return False

def main():
    """메인 검증 함수"""
    print("=" * 60)
    print("🧪 로컬 환경 전체 검증 시작")
    print("=" * 60)
    print()
    
    tests = [
        ("Python Virtual Environment", check_virtual_environment),
        ("Docker Services", check_docker_services),
        ("Python Dependencies", test_python_dependencies),
        ("DynamoDB Operations", test_dynamodb_operations),
        ("MinIO S3 Operations", test_minio_operations),
        ("Chroma Connection", test_chroma_connection),
        ("Integration Test Sample", run_integration_test_sample)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_status(f"Test {test_name} crashed: {e}", "error")
            failed += 1
        
        time.sleep(1)  # 테스트 간 간격
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("🏁 검증 결과 요약")
    print("=" * 60)
    print_status(f"통과: {passed}", "success")
    print_status(f"실패: {failed}", "error" if failed > 0 else "success")
    print(f"총 테스트: {passed + failed}")
    
    if failed == 0:
        print()
        print_status("🎉 모든 검증 통과! 로컬 환경이 완벽하게 설정되었습니다.", "success")
        print()
        print("다음 단계:")
        print("  1. 전체 통합 테스트: python -m pytest tests/integration/ -v")
        print("  2. Streamlit 앱: cd src/streamlit && streamlit run app.py")
        print("  3. SAM 로컬 API: sam build && sam local start-api --port 3000")
        print()
        print("관리 도구:")
        print("  - DynamoDB Admin: http://localhost:8002")
        print("  - MinIO Console: http://localhost:9001")
        return 0
    else:
        print()
        print_status("❌ 일부 검증이 실패했습니다.", "error")
        print()
        print("해결 방법:")
        print("  1. 가상환경 활성화: source venv/bin/activate")
        print("  2. Docker 서비스 재시작: ./scripts/setup-local.sh")
        print("  3. 의존성 설치: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())