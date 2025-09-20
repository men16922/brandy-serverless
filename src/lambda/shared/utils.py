# Shared utilities for Agent Lambda functions
# Agent-aware logging, error handling, and AWS client initialization

import json
import logging
import boto3
import os
from datetime import datetime
from typing import Dict, Any, Optional

class AgentLogger:
    """Agent-aware structured logger"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning with agent context"""
        extra = extra or {}
        extra.update({
            'agent': self.agent_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.logger.warning(message, extra=extra)

def setup_logging(agent_name: str = "unknown") -> AgentLogger:
    """Setup agent-aware structured logging"""
    return AgentLogger(agent_name)

def get_aws_clients():
    """Initialize AWS service clients based on environment"""
    environment = os.getenv('ENVIRONMENT', 'local')
    
    if environment == 'local':
        # Local development configuration
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        s3 = boto3.client('s3', endpoint_url='http://localhost:9000')
        stepfunctions = boto3.client('stepfunctions', endpoint_url='http://localhost:8083')
    else:
        # AWS environment configuration
        dynamodb = boto3.resource('dynamodb')
        s3 = boto3.client('s3')
        stepfunctions = boto3.client('stepfunctions')
    
    return {
        'dynamodb': dynamodb,
        's3': s3,
        'stepfunctions': stepfunctions
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
        'body': json.dumps(body, ensure_ascii=False)
    }

def measure_latency(func):
    """Decorator to measure function execution latency"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return result, latency_ms
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raise e
    return wrapper