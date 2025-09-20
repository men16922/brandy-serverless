"""
API Stack - Lambda functions and API Gateway
"""

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, storage_stack, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.storage_stack = storage_stack
        self.environment = environment
        
        # Common environment variables for Lambda functions
        common_env = {
            "ENVIRONMENT": environment,
            "SESSIONS_TABLE": storage_stack.sessions_table.table_name,
            "STORAGE_BUCKET": storage_stack.storage_bucket.bucket_name,
            "REGION": self.region
        }
        
        # Lambda layer for shared utilities
        self.shared_layer = _lambda.LayerVersion(
            self, "SharedLayer",
            code=_lambda.Code.from_asset("src/lambda/shared"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Shared utilities for branding chatbot Lambda functions"
        )
        
        # Session Manager Lambda
        self.session_manager = self._create_lambda_function(
            "SessionManager",
            "src/lambda/session-manager",
            common_env
        )
        
        # Business Analyzer Lambda
        self.business_analyzer = self._create_lambda_function(
            "BusinessAnalyzer", 
            "src/lambda/business-analyzer",
            common_env
        )
        
        # Name Suggester Lambda
        self.name_suggester = self._create_lambda_function(
            "NameSuggester",
            "src/lambda/name-suggester", 
            common_env
        )
        
        # Image Generator Lambda
        self.image_generator = self._create_lambda_function(
            "ImageGenerator",
            "src/lambda/image-generator",
            common_env,
            timeout=Duration.seconds(30)
        )
        
        # Report Generator Lambda (Container)
        self.report_generator = self._create_lambda_function(
            "ReportGenerator",
            "src/lambda/report-generator",
            common_env,
            timeout=Duration.seconds(60)
        )
        
        # Grant permissions to Lambda functions
        self._grant_permissions()
        
        # HTTP API Gateway
        self.api = apigw.HttpApi(
            self, "BrandingChatbotApi",
            api_name=f"branding-chatbot-api-{environment}",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.GET, apigw.CorsHttpMethod.POST, apigw.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # API routes will be added in later tasks
        
    def _create_lambda_function(self, name: str, code_path: str, environment: dict, timeout: Duration = Duration.seconds(5)) -> _lambda.Function:
        """Create a Lambda function with common configuration"""
        return _lambda.Function(
            self, name,
            function_name=f"branding-chatbot-{name.lower()}-{self.environment}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(code_path),
            layers=[self.shared_layer],
            environment=environment,
            timeout=timeout,
            memory_size=512
        )
    
    def _grant_permissions(self):
        """Grant necessary permissions to Lambda functions"""
        functions = [
            self.session_manager,
            self.business_analyzer, 
            self.name_suggester,
            self.image_generator,
            self.report_generator
        ]
        
        for func in functions:
            # DynamoDB permissions
            self.storage_stack.sessions_table.grant_read_write_data(func)
            
            # S3 permissions
            self.storage_stack.storage_bucket.grant_read_write(func)
            
            # Bedrock permissions (for dev environment)
            if self.environment != "local":
                func.add_to_role_policy(
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        resources=["*"]
                    )
                )