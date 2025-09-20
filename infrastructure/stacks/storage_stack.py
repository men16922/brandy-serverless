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
        
        # DynamoDB table for workflow sessions with agent support
        self.sessions_table = dynamodb.Table(
            self, "WorkflowSessions",
            table_name=f"branding-chatbot-sessions-{environment}",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN,
            point_in_time_recovery=True if environment == "prod" else False
        )
        
        # GSI for querying sessions by status (for Supervisor Agent monitoring)
        self.sessions_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updatedAt",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # GSI for querying sessions by current step (for workflow monitoring)
        self.sessions_table.add_global_secondary_index(
            index_name="StepIndex", 
            partition_key=dynamodb.Attribute(
                name="currentStep",
                type=dynamodb.AttributeType.NUMBER
            ),
            sort_key=dynamodb.Attribute(
                name="updatedAt", 
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # S3 bucket for images and reports with proper structure
        self.storage_bucket = s3.Bucket(
            self, "StorageBucket",
            bucket_name=f"branding-chatbot-storage-{environment}",
            versioned=False,
            public_read_access=False,
            removal_policy=RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                    allowed_origins=["*"],  # Configure based on your domain
                    allowed_headers=["*"],
                    max_age=3000
                )
            ],
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldSessions",
                    enabled=True,
                    expiration=Duration.days(30),
                    prefix="sessions/"
                ),
                s3.LifecycleRule(
                    id="TransitionToIA",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(7)
                        )
                    ],
                    prefix="sessions/"
                )
            ],
            notification_configuration=s3.NotificationConfiguration()
        )
        
        # Create folder structure using custom resource (for initial setup)
        from aws_cdk import custom_resources as cr
        
        # Custom resource to create initial folder structure
        folder_structure = cr.AwsCustomResource(
            self, "CreateFolderStructure",
            on_create=cr.AwsSdkCall(
                service="S3",
                action="putObject",
                parameters={
                    "Bucket": self.storage_bucket.bucket_name,
                    "Key": "fallbacks/signs/.placeholder",
                    "Body": ""
                },
                physical_resource_id=cr.PhysicalResourceId.of("folder-structure")
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=[self.storage_bucket.arn_for_objects("*")]
            )
        )
        
        # Additional folder creation
        for folder in ["fallbacks/interiors", "templates/pdf-templates"]:
            cr.AwsCustomResource(
                self, f"CreateFolder{folder.replace('/', '').replace('-', '')}",
                on_create=cr.AwsSdkCall(
                    service="S3",
                    action="putObject", 
                    parameters={
                        "Bucket": self.storage_bucket.bucket_name,
                        "Key": f"{folder}/.placeholder",
                        "Body": ""
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"folder-{folder}")
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                    resources=[self.storage_bucket.arn_for_objects("*")]
                )
            )