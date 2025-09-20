#!/usr/bin/env python3
"""
Docker Compose 기반 통합 테스트
실제 로컬 서비스들을 사용한 end-to-end 테스트
"""

import pytest
import os
import sys
import subprocess
import time
import boto3
import requests
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda'))

from shared.models import WorkflowSession, BusinessInfo, AgentLog, AgentType


class DockerComposeManager:
    """Docker Compose 서비스 관리"""
    
    def __init__(self):
        self.compose_file = "docker-compose.local.yml"
        self.services = ["dynamodb-local", "minio", "chroma"]
    
    def is_docker_available(self) -> bool:
        """Docker 실행 상태 확인"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def are_services_running(self) -> bool:
        """서비스 실행 상태 확인"""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file, "ps", "-q"],
                capture_output=True, text=True, timeout=10
            )
            running_containers = result.stdout.strip().split('\n')
            return len([c for c in running_containers if c]) >= len(self.services)
        except Exception:
            return False
    
    def wait_for_health(self, timeout: int = 60) -> bool:
        """서비스 헬스체크 대기"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # DynamoDB Local 체크
                dynamodb = boto3.client(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-east-1',
                    aws_access_key_id='dummy',
                    aws_secret_access_key='dummy'
                )
                dynamodb.list_tables()
                
                # MinIO 체크
                response = requests.get('http://localhost:9000/minio/health/live', timeout=5)
                if response.status_code != 200:
                    raise Exception("MinIO not healthy")
                
                # Chroma 체크 (단순 연결 확인)
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', 8001))
                sock.close()
                if result != 0:
                    raise Exception("Chroma not healthy")
                
                print("✅ All services are healthy")
                return True
                
            except Exception as e:
                print(f"⏳ Waiting for services... ({e})")
                time.sleep(2)
        
        return False


class TestEnvironment:
    """테스트 환경 설정"""
    
    def __init__(self):
        self.dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        self.table_name = 'branding-chatbot-sessions-test'
    
    def setup_dynamodb_table(self):
        """DynamoDB 테스트 테이블 생성"""
        try:
            # 기존 테이블 삭제
            try:
                self.dynamodb.delete_table(TableName=self.table_name)
                time.sleep(2)
            except:
                pass
            
            # 새 테이블 생성
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'sessionId', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'sessionId', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # 테이블 생성 대기
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name, WaiterConfig={'Delay': 1, 'MaxAttempts': 30})
            
            print(f"✅ DynamoDB table '{self.table_name}' created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create DynamoDB table: {e}")
            return False
    
    def cleanup_test_data(self):
        """테스트 데이터 정리"""
        try:
            self.dynamodb.delete_table(TableName=self.table_name)
            print(f"✅ Test table '{self.table_name}' cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


@pytest.fixture(scope="session")
def docker_services():
    """Docker 서비스 관리 fixture"""
    manager = DockerComposeManager()
    
    if not manager.is_docker_available():
        pytest.skip("Docker not available")
    
    if not manager.are_services_running():
        pytest.skip("Docker Compose services not running. Run: docker-compose -f docker-compose.local.yml up -d")
    
    if not manager.wait_for_health():
        pytest.skip("Services failed health check")
    
    yield manager
    
    print("🧹 Docker services session completed")


@pytest.fixture
def test_environment(docker_services):
    """테스트 환경 fixture"""
    env = TestEnvironment()
    
    if not env.setup_dynamodb_table():
        pytest.skip("Failed to setup test environment")
    
    yield env
    
    env.cleanup_test_data()


class TestDockerIntegration:
    """Docker Compose 기반 통합 테스트"""
    
    def test_docker_services_health(self, docker_services):
        """Docker 서비스 헬스체크"""
        assert docker_services.is_docker_available()
        assert docker_services.are_services_running()
        assert docker_services.wait_for_health(timeout=30)
    
    def test_dynamodb_connection(self, test_environment):
        """DynamoDB Local 연결 테스트"""
        # 테이블 목록 조회
        response = test_environment.dynamodb.list_tables()
        assert test_environment.table_name in response['TableNames']
        
        # 테스트 아이템 생성
        test_item = {
            'sessionId': {'S': 'test-session-123'},
            'currentStep': {'N': '1'},
            'status': {'S': 'active'},
            'createdAt': {'S': datetime.utcnow().isoformat()}
        }
        
        test_environment.dynamodb.put_item(
            TableName=test_environment.table_name,
            Item=test_item
        )
        
        # 아이템 조회
        response = test_environment.dynamodb.get_item(
            TableName=test_environment.table_name,
            Key={'sessionId': {'S': 'test-session-123'}}
        )
        
        assert 'Item' in response
        assert response['Item']['sessionId']['S'] == 'test-session-123'
    
    def test_minio_connection(self, docker_services):
        """MinIO 연결 테스트"""
        # MinIO 헬스체크
        response = requests.get('http://localhost:9000/minio/health/live', timeout=10)
        assert response.status_code == 200
        
        # S3 클라이언트로 버킷 목록 조회 테스트
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url='http://localhost:9000',
                aws_access_key_id='minioadmin',
                aws_secret_access_key='minioadmin',
                region_name='us-east-1'
            )
            
            # 버킷 목록 조회 (빈 목록이어도 연결 성공)
            response = s3_client.list_buckets()
            assert 'Buckets' in response
            
        except Exception as e:
            pytest.fail(f"MinIO S3 connection failed: {e}")
    
    def test_chroma_connection(self, docker_services):
        """Chroma 연결 테스트"""
        # Chroma 기본 연결 테스트 (포트 8001이 응답하는지 확인)
        try:
            response = requests.get('http://localhost:8001/', timeout=10)
            # 어떤 응답이든 받으면 서비스가 실행 중
            assert response.status_code in [200, 404, 422]  # 다양한 응답 허용
        except requests.exceptions.ConnectionError:
            pytest.fail("Chroma service not responding on port 8001")
    
    def test_session_workflow_with_real_storage(self, test_environment):
        """실제 스토리지를 사용한 세션 워크플로 테스트"""
        # 1. 세션 생성
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small",
            description="Korean BBQ restaurant"
        )
        
        session = WorkflowSession.create_new(business_info)
        assert session.validate()
        
        # 2. DynamoDB에 세션 저장 (간단한 형태로)
        dynamodb_item = {
            'sessionId': {'S': session.session_id},
            'currentStep': {'N': str(session.current_step)},
            'status': {'S': session.status},
            'createdAt': {'S': session.created_at},
            'updatedAt': {'S': session.updated_at},
            'ttl': {'N': str(session.ttl)}
        }
        
        test_environment.dynamodb.put_item(
            TableName=test_environment.table_name,
            Item=dynamodb_item
        )
        
        # 3. 세션 조회 및 검증
        response = test_environment.dynamodb.get_item(
            TableName=test_environment.table_name,
            Key={'sessionId': {'S': session.session_id}}
        )
        
        assert 'Item' in response
        retrieved_item = response['Item']
        assert retrieved_item['sessionId']['S'] == session.session_id
        assert retrieved_item['status']['S'] == 'active'
        assert retrieved_item['currentStep']['N'] == '1'
        
        # 4. Agent 로그 추가 테스트
        agent_log = AgentLog(
            agent=AgentType.PRODUCT_INSIGHT.value,
            tool="kb.search",
            latency_ms=1500,
            status="success",
            metadata={"test": True}
        )
        
        session.add_agent_log(agent_log)
        assert len(session.agent_logs) == 1
        assert session.current_agent == AgentType.PRODUCT_INSIGHT.value
        
        print(f"✅ Session workflow test completed for session: {session.session_id}")
    
    def test_agent_execution_simulation(self, test_environment):
        """Agent 실행 시뮬레이션 테스트"""
        # 세션 생성
        business_info = BusinessInfo(
            industry="technology",
            region="gyeonggi",
            size="medium"
        )
        
        session = WorkflowSession.create_new(business_info)
        
        # Agent 실행 시뮬레이션
        agents_to_test = [
            (AgentType.SUPERVISOR, "workflow.monitor", 500),
            (AgentType.PRODUCT_INSIGHT, "kb.search", 2000),
            (AgentType.MARKET_ANALYST, "market.analyze", 1800),
            (AgentType.REPORTER, "name.generate", 3000)
        ]
        
        for agent_type, tool, latency in agents_to_test:
            agent_log = AgentLog(
                agent=agent_type.value,
                tool=tool,
                latency_ms=latency,
                status="success",
                metadata={
                    "session_id": session.session_id,
                    "test_mode": True
                }
            )
            
            session.add_agent_log(agent_log)
        
        # 로그 검증
        assert len(session.agent_logs) == len(agents_to_test)
        
        # 각 Agent별 로그 확인
        for i, (agent_type, tool, latency) in enumerate(agents_to_test):
            log = session.agent_logs[i]
            assert log.agent == agent_type.value
            assert log.tool == tool
            assert log.latency_ms == latency
            assert log.status == "success"
        
        print(f"✅ Agent execution simulation completed with {len(agents_to_test)} agents")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])