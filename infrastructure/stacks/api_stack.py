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
        
        # Lambda layer for shared Agent utilities
        self.shared_layer = _lambda.LayerVersion(
            self, "SharedAgentLayer",
            code=_lambda.Code.from_asset("src/lambda/shared"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Shared utilities for Agent Lambda functions"
        )
        
        # Supervisor Agent Lambda (최우선)
        self.supervisor_agent = self._create_lambda_function(
            "SupervisorAgent",
            "src/lambda/agents/supervisor",
            common_env,
            timeout=Duration.seconds(30),
            memory_size=1024
        )
        
        # Product Insight Agent Lambda
        self.product_insight_agent = self._create_lambda_function(
            "ProductInsightAgent",
            "src/lambda/agents/product-insight",
            {**common_env, "BEDROCK_KNOWLEDGE_BASE_ID": os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")},
            timeout=Duration.seconds(10)
        )
        
        # Market Analyst Agent Lambda
        self.market_analyst_agent = self._create_lambda_function(
            "MarketAnalystAgent",
            "src/lambda/agents/market-analyst",
            {**common_env, "BEDROCK_KNOWLEDGE_BASE_ID": os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")},
            timeout=Duration.seconds(10)
        )
        
        # Reporter Agent Lambda
        self.reporter_agent = self._create_lambda_function(
            "ReporterAgent",
            "src/lambda/agents/reporter",
            common_env,
            timeout=Duration.seconds(10)
        )
        
        # Signboard Agent Lambda
        self.signboard_agent = self._create_lambda_function(
            "SignboardAgent",
            "src/lambda/signboard-agent",  # 구현 예정
            common_env,
            timeout=Duration.seconds(35)
        )
        
        # Interior Agent Lambda
        self.interior_agent = self._create_lambda_function(
            "InteriorAgent",
            "src/lambda/interior-agent",  # 구현 예정
            common_env,
            timeout=Duration.seconds(35)
        )
        
        # Report Generator Agent Lambda (Container)
        self.report_generator_agent = self._create_lambda_function(
            "ReportGeneratorAgent",
            "src/lambda/report-generator-agent",  # 구현 예정
            common_env,
            timeout=Duration.seconds(60)
        )
        
        # Grant permissions to Agent Lambda functions
        self._grant_agent_permissions()
        
        # HTTP API Gateway with Agent endpoints
        self.api = apigw.HttpApi(
            self, "BrandingChatbotApi",
            api_name=f"branding-chatbot-api-{environment}",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.GET, apigw.CorsHttpMethod.POST, apigw.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # Agent API routes
        self._setup_agent_routes()
        
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
    
    def _grant_agent_permissions(self):
        """Grant necessary permissions to Agent Lambda functions"""
        agent_functions = [
            self.supervisor_agent,
            self.product_insight_agent,
            self.market_analyst_agent,
            self.reporter_agent,
            self.signboard_agent,
            self.interior_agent,
            self.report_generator_agent
        ]
        
        for func in agent_functions:
            # DynamoDB permissions
            self.storage_stack.sessions_table.grant_read_write_data(func)
            
            # S3 permissions
            self.storage_stack.storage_bucket.grant_read_write(func)
            
            # Bedrock permissions (for dev environment)
            if self.environment != "local":
                # Bedrock model invocation
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
                
                # Bedrock Knowledge Base permissions
                func.add_to_role_policy(
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "bedrock:Retrieve",
                            "bedrock:RetrieveAndGenerate"
                        ],
                        resources=["*"]
                    )
                )
            
            # Step Functions permissions (for Supervisor Agent)
            if func == self.supervisor_agent:
                func.add_to_role_policy(
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "states:DescribeExecution",
                            "states:DescribeStateMachine",
                            "states:ListExecutions",
                            "states:StartExecution",
                            "states:StopExecution"
                        ],
                        resources=["*"]
                    )
                )
    
    def _setup_agent_routes(self):
        """Setup API routes for Agent endpoints"""
        # Supervisor Agent routes
        self.api.add_routes(
            path="/status/{id}",
            methods=[apigw.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration(
                "SupervisorStatusIntegration",
                self.supervisor_agent
            )
        )
        
        self.api.add_routes(
            path="/workflow/monitor",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "SupervisorMonitorIntegration", 
                self.supervisor_agent
            )
        )
        
        # Product Insight Agent routes
        self.api.add_routes(
            path="/analysis/product",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "ProductInsightIntegration",
                self.product_insight_agent
            )
        )
        
        # Market Analyst Agent routes
        self.api.add_routes(
            path="/analysis/market",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "MarketAnalystIntegration",
                self.market_analyst_agent
            )
        )
        
        # Reporter Agent routes
        self.api.add_routes(
            path="/names/suggest",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "ReporterIntegration",
                self.reporter_agent
            )
        )
        
        # 기본 세션 관리 routes (Supervisor를 통해 처리)
        self.api.add_routes(
            path="/sessions",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "SessionCreateIntegration",
                self.supervisor_agent
            )
        )
        
        self.api.add_routes(
            path="/sessions/{id}",
            methods=[apigw.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration(
                "SessionGetIntegration",
                self.supervisor_agent
            )
        )