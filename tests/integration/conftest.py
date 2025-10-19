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

# Set default environment variables for tests (AWS dev environment)
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('SESSIONS_TABLE', 'ai-branding-chatbot-sessions')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('S3_BUCKET', 'ai-branding-chatbot-assets-908601828278')

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambda'))


class AWSEnvironmentChecker:
    """AWS environment availability checker"""
    
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    def is_aws_configured(self) -> bool:
        """Check if AWS credentials are configured"""
        try:
            sts = boto3.client('sts')
            sts.get_caller_identity()
            return True
        except Exception as e:
            print(f"❌ AWS credentials not configured: {e}")
            return False
    
    def check_services(self) -> bool:
        """Check if required AWS services are accessible"""
        try:
            # Check DynamoDB
            dynamodb = boto3.client('dynamodb', region_name=self.region)
            dynamodb.list_tables()
            
            # Check S3
            s3 = boto3.client('s3', region_name=self.region)
            s3.list_buckets()
            
            print("✅ AWS services are accessible")
            return True
            
        except Exception as e:
            print(f"❌ AWS services not accessible: {e}")
            return False


@pytest.fixture(scope="session")
def aws_environment():
    """
    Session-scoped fixture for AWS environment.
    Checks if AWS credentials are configured and services are accessible.
    """
    checker = AWSEnvironmentChecker()
    
    if not checker.is_aws_configured():
        pytest.skip("AWS credentials not configured. Run: aws configure")
    
    if not checker.check_services():
        pytest.skip("AWS services not accessible")
    
    yield checker
    
    print("🧹 AWS environment session completed")


@pytest.fixture
def dynamodb_client():
    """Create AWS DynamoDB client"""
    return boto3.client('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))


@pytest.fixture
def s3_client():
    """Create AWS S3 client"""
    return boto3.client('s3', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))


@pytest.fixture
def test_table_name():
    """AWS DynamoDB table name for tests"""
    return os.getenv('SESSIONS_TABLE', 'ai-branding-chatbot-sessions')


@pytest.fixture
def test_bucket_name():
    """AWS S3 bucket name for tests"""
    return os.getenv('S3_BUCKET', 'ai-branding-chatbot-assets-908601828278')


class TestEnvironment:
    """AWS test environment setup and management"""
    
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.dynamodb = boto3.client('dynamodb', region_name=self.region)
        self.table_name = os.getenv('SESSIONS_TABLE', 'ai-branding-chatbot-sessions')
        self.bucket_name = os.getenv('S3_BUCKET', 'ai-branding-chatbot-assets-908601828278')
    
    def verify_dynamodb_table(self):
        """Verify DynamoDB table exists"""
        try:
            self.dynamodb.describe_table(TableName=self.table_name)
            print(f"✅ DynamoDB table '{self.table_name}' exists")
            return True
        except Exception as e:
            print(f"❌ DynamoDB table not found: {e}")
            return False
    
    def verify_s3_bucket(self):
        """Verify S3 bucket exists"""
        try:
            s3 = boto3.client('s3', region_name=self.region)
            s3.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 bucket '{self.bucket_name}' exists")
            return True
        except Exception as e:
            print(f"❌ S3 bucket not found: {e}")
            return False
    
    def cleanup_test_data(self):
        """Cleanup test data (optional - AWS resources persist)"""
        print(f"ℹ️ Test data cleanup skipped (AWS resources persist)")


@pytest.fixture
def test_environment(aws_environment):
    """Test environment fixture with AWS resource verification"""
    env = TestEnvironment()
    
    if not env.verify_dynamodb_table():
        pytest.skip("DynamoDB table not found. Deploy to AWS first: ./safe_deploy.sh")
    
    if not env.verify_s3_bucket():
        pytest.skip("S3 bucket not found. Deploy to AWS first: ./safe_deploy.sh")
    
    yield env
    
    env.cleanup_test_data()
