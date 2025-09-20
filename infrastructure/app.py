#!/usr/bin/env python3
"""
AWS CDK App for AI Branding Chatbot
Deploys serverless infrastructure for the branding workflow system
"""

import aws_cdk as cdk
from constructs import Construct
from stacks.api_stack import ApiStack
from stacks.storage_stack import StorageStack
from stacks.workflow_stack import WorkflowStack
from stacks.frontend_stack import FrontendStack

app = cdk.App()

# Environment configuration
environment = app.node.try_get_context("environment") or "dev"
account = app.node.try_get_context("account")
region = app.node.try_get_context("region") or "us-east-1"

env = cdk.Environment(account=account, region=region)

# Storage stack (DynamoDB, S3)
storage_stack = StorageStack(
    app, 
    f"BrandingChatbot-Storage-{environment}",
    environment=environment,
    env=env
)

# API stack (Lambda functions, API Gateway)
api_stack = ApiStack(
    app,
    f"BrandingChatbot-Api-{environment}",
    storage_stack=storage_stack,
    environment=environment,
    env=env
)

# Workflow stack (Step Functions)
workflow_stack = WorkflowStack(
    app,
    f"BrandingChatbot-Workflow-{environment}",
    api_stack=api_stack,
    environment=environment,
    env=env
)

# Frontend stack (App Runner)
frontend_stack = FrontendStack(
    app,
    f"BrandingChatbot-Frontend-{environment}",
    api_stack=api_stack,
    environment=environment,
    env=env
)

app.synth()