# Shared utilities for Lambda functions
# Common logging, error handling, and AWS client initialization

import json
import logging
import boto3
import os
from datetime import datetime

def setup_logging():
    """Setup structured logging for Lambda functions"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_aws_clients():
    """Initialize AWS service clients based on environment"""
    environment = os.getenv('ENVIRONMENT', 'local')
    
    if environment == 'local':
        # Local development configuration
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        s3 = boto3.client('s3', endpoint_url='http://localhost:9000')
    else:
        # AWS environment configuration
        dynamodb = boto3.resource('dynamodb')
        s3 = boto3.client('s3')
    
    return {
        'dynamodb': dynamodb,
        's3': s3
    }

def create_response(status_code, body, headers=None):
    """Create standardized API response"""
    if headers is None:
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body)
    }