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
