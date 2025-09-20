"""
Storage Stack - DynamoDB and S3 resources
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.environment = environment
        
        # DynamoDB table for workflow sessions
        self.sessions_table = dynamodb.Table(
            self, "WorkflowSessions",
            table_name=f"branding-chatbot-sessions-{environment}",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN
        )
        
        # S3 bucket for images and reports
        self.storage_bucket = s3.Bucket(
            self, "StorageBucket",
            bucket_name=f"branding-chatbot-storage-{environment}",
            versioned=False,
            public_read_access=False,
            removal_policy=RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldSessions",
                    enabled=True,
                    expiration=Duration.days(30),
                    prefix="sessions/"
                )
            ]
        )