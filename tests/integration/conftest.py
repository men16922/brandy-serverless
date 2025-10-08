#!/usr/bin/env python3
"""
pytest configuration for integration tests
Provides shared fixtures and test environment setup
"""

import pytest
import os
import sys
import subprocess
import time
import boto3
import requests
from typing import Dict, Any
from pathlib import Path

# Load .env.test file if it exists
def load_env_file():
    """Load environment variables from .env.test file"""
    env_file = Path(__file__).parent.parent.parent / '.env.test'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load environment variables from .env.test
load_env_file()

# Set default environment variables for tests (fallback)
os.environ.setdefault('ENVIRONMENT', 'local')
os.environ.setdefault('SESSIONS_TABLE', 'branding-chatbot-sessions-test')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambda'))


class DockerComposeManager:
    """Docker Compose service management"""
    
    def __init__(self):
        self.compose_file = "docker-compose.local.yml"
        self.services = ["dynamodb-local", "minio", "chroma"]
    
    def is_docker_available(self) -> bool:
        """Check if Docker is running"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def are_services_running(self) -> bool:
        """Check if Docker Compose services are running"""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file, "ps", "-q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            running_containers = result.stdout.strip().split('\n')
            return len([c for c in running_containers if c]) >= len(self.services)
        except Exception:
            return False
    
    def wait_for_health(self, timeout: int = 60) -> bool:
        """Wait for all services to be healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check DynamoDB Local
                dynamodb = boto3.client(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-east-1',
                    aws_access_key_id='dummy',
                    aws_secret_access_key='dummy'
                )
                dynamodb.list_tables()
                
                # Check MinIO
                response = requests.get('http://localhost:9000/minio/health/live', timeout=5)
                if response.status_code != 200:
                    raise Exception("MinIO not healthy")
                
                # Check Chroma (port check)
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', 8001))
                sock.close()
                if result != 0:
                    raise Exception("Chroma not healthy")
                
                print("✅ All Docker services are healthy")
                return True
                
            except Exception as e:
                print(f"⏳ Waiting for services... ({e})")
                time.sleep(2)
        
        return False


@pytest.fixture(scope="session")
def docker_services():
    """
    Session-scoped fixture for Docker Compose services.
    Checks if services are running and healthy.
    """
    manager = DockerComposeManager()
    
    if not manager.is_docker_available():
        pytest.skip("Docker not available")
    
    if not manager.are_services_running():
        pytest.skip(
            "Docker Compose services not running. "
            "Run: docker-compose -f docker-compose.local.yml up -d"
        )
    
    if not manager.wait_for_health():
        pytest.skip("Services failed health check")
    
    yield manager
    
    print("🧹 Docker services session completed")


@pytest.fixture
def dynamodb_client():
    """Create DynamoDB Local client"""
    return boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )


@pytest.fixture
def s3_client():
    """Create MinIO S3 client"""
    return boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        region_name='us-east-1'
    )


@pytest.fixture
def test_table_name():
    """Standard test table name"""
    return 'branding-chatbot-sessions-test'


@pytest.fixture
def cleanup_dynamodb_table(dynamodb_client, test_table_name):
    """Cleanup fixture that removes test table after test"""
    yield
    
    try:
        dynamodb_client.delete_table(TableName=test_table_name)
        print(f"✅ Cleaned up test table: {test_table_name}")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


class TestEnvironment:
    """Test environment setup and management"""
    
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
        """Create DynamoDB test table"""
        try:
            # Delete existing table
            try:
                self.dynamodb.delete_table(TableName=self.table_name)
                time.sleep(2)
            except:
                pass
            
            # Create new table
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
            
            # Wait for table creation
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name, WaiterConfig={'Delay': 1, 'MaxAttempts': 30})
            
            print(f"✅ DynamoDB table '{self.table_name}' created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create DynamoDB table: {e}")
            return False
    
    def cleanup_test_data(self):
        """Cleanup test data"""
        try:
            self.dynamodb.delete_table(TableName=self.table_name)
            print(f"✅ Test table '{self.table_name}' cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


@pytest.fixture
def test_environment(docker_services):
    """Test environment fixture with DynamoDB table setup"""
    env = TestEnvironment()
    
    if not env.setup_dynamodb_table():
        pytest.skip("Failed to setup test environment")
    
    yield env
    
    env.cleanup_test_data()
