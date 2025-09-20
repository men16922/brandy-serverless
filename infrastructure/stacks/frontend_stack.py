"""
Frontend Stack - App Runner for Streamlit application
"""

from aws_cdk import (
    Stack,
    aws_apprunner as apprunner,
    aws_iam as iam
)
from constructs import Construct

class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, api_stack, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.api_stack = api_stack
        self.environment = environment
        
        # IAM role for App Runner
        app_runner_role = iam.Role(
            self, "AppRunnerRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAppRunnerServicePolicyForECRAccess")
            ]
        )
        
        # App Runner service configuration will be added in later tasks
        # For now, just create the basic structure
        
        # Note: App Runner service creation requires container image or source code repository
        # This will be implemented when the Streamlit application is fully developed