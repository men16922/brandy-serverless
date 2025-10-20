#!/usr/bin/env python3
"""
Generate AWS Architecture Diagram for AI Branding Chatbot
Uses the diagrams library to create infrastructure visualization
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import Dynamodb
from diagrams.aws.storage import S3
from diagrams.aws.ml import Bedrock
from diagrams.aws.management import Cloudwatch
from diagrams.onprem.client import Client

# Diagram configuration
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.0"
}

node_attr = {
    "fontsize": "12",
    "height": "1.2",
    "width": "1.2"
}

edge_attr = {
    "fontsize": "10"
}

# Create main architecture diagram
with Diagram(
    "AI Branding Chatbot - AWS Architecture",
    filename="docs/aws_architecture_diagram",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr
):
    # Client Layer
    streamlit = Client("Streamlit UI\n(localhost:8501)")
    
    # API Gateway
    api_gateway = APIGateway("API Gateway\nHTTP API")
    
    # Supervisor Agent (highlighted)
    with Cluster("Supervisor Agent"):
        supervisor = Lambda("Supervisor\nSession Mgmt\nError Recovery\nOrchestration")
    
    # Specialized Agents
    with Cluster("Specialized Agents"):
        with Cluster("Analysis"):
            product_insight = Lambda("Product\nInsight")
            market_analyst = Lambda("Market\nAnalyst")
        
        with Cluster("Generation"):
            reporter = Lambda("Reporter\nName Gen")
            signboard = Lambda("Signboard\nImage Gen")
            interior = Lambda("Interior\nDesign")
        
        with Cluster("Output"):
            report_gen = Lambda("Report\nGenerator")
    
    # AWS Services
    with Cluster("AI/ML Services"):
        bedrock = Bedrock("Amazon Bedrock")
        with Cluster("Bedrock Models"):
            claude = Bedrock("Claude 4 Sonnet\nText & Reasoning")
            sdxl = Bedrock("Titan Image Gen v2\nImage Generation")
    
    with Cluster("Storage"):
        dynamodb = Dynamodb("DynamoDB\nSessions\nTTL: 24h")
        s3 = S3("S3 Bucket\nImages & Reports")
    
    with Cluster("Monitoring"):
        cloudwatch = Cloudwatch("CloudWatch\nLogs & Metrics")
    
    # Connections
    streamlit >> Edge(label="HTTPS") >> api_gateway
    api_gateway >> Edge(label="Route All") >> supervisor
    
    # Supervisor to Agents
    supervisor >> Edge(label="Invoke") >> product_insight
    supervisor >> Edge(label="Invoke") >> market_analyst
    supervisor >> Edge(label="Invoke") >> reporter
    supervisor >> Edge(label="Invoke") >> signboard
    supervisor >> Edge(label="Invoke") >> interior
    supervisor >> Edge(label="Invoke") >> report_gen
    
    # Agents to Bedrock
    product_insight >> Edge(label="Analysis") >> claude
    market_analyst >> Edge(label="Research") >> claude
    reporter >> Edge(label="Reasoning") >> claude
    signboard >> Edge(label="Generate") >> sdxl
    interior >> Edge(label="Recommend") >> claude
    report_gen >> Edge(label="Synthesize") >> claude
    
    # Storage Access
    supervisor >> Edge(label="CRUD") >> dynamodb
    product_insight >> Edge(label="R/W") >> dynamodb
    market_analyst >> Edge(label="R/W") >> dynamodb
    reporter >> Edge(label="R/W") >> dynamodb
    signboard >> Edge(label="R/W") >> dynamodb
    signboard >> Edge(label="Upload") >> s3
    interior >> Edge(label="R/W") >> dynamodb
    report_gen >> Edge(label="R/W") >> dynamodb
    report_gen >> Edge(label="Upload") >> s3
    
    # Monitoring
    supervisor >> cloudwatch
    product_insight >> cloudwatch
    market_analyst >> cloudwatch
    reporter >> cloudwatch
    signboard >> cloudwatch
    interior >> cloudwatch
    report_gen >> cloudwatch

print("✅ Architecture diagram generated: docs/aws_architecture_diagram.png")

# Create workflow sequence diagram
with Diagram(
    "AI Branding Chatbot - 5-Step Workflow",
    filename="docs/workflow_sequence_diagram",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr
):
    user = Client("User")
    api = APIGateway("API Gateway")
    sup = Lambda("Supervisor")
    
    # Step 1: Analysis
    with Cluster("Step 1: Business Analysis"):
        pi = Lambda("Product\nInsight")
        ma = Lambda("Market\nAnalyst")
        claude1 = Bedrock("Claude")
    
    # Step 2: Names
    with Cluster("Step 2: Name Generation"):
        rep = Lambda("Reporter")
        claude2 = Bedrock("Claude")
    
    # Step 3: Signboard
    with Cluster("Step 3: Signboard Design"):
        sb = Lambda("Signboard")
        sdxl_img = Bedrock("SDXL")
        s3_img = S3("S3")
    
    # Step 4: Interior
    with Cluster("Step 4: Interior Design"):
        int_agent = Lambda("Interior")
        claude3 = Bedrock("Claude")
    
    # Step 5: Report
    with Cluster("Step 5: Report Generation"):
        rg = Lambda("Report Gen")
        claude4 = Bedrock("Claude")
        s3_report = S3("S3")
    
    ddb = Dynamodb("DynamoDB")
    
    # Workflow flow
    user >> api >> sup
    
    # Step 1
    sup >> pi >> claude1
    sup >> ma >> claude1
    pi >> ddb
    ma >> ddb
    
    # Step 2
    sup >> rep >> claude2 >> ddb
    
    # Step 3
    sup >> sb >> sdxl_img >> s3_img
    sb >> ddb
    
    # Step 4
    sup >> int_agent >> claude3 >> ddb
    
    # Step 5
    sup >> rg >> claude4
    rg >> s3_report
    rg >> ddb

print("✅ Workflow diagram generated: docs/workflow_sequence_diagram.png")

# Create Bedrock integration diagram
with Diagram(
    "AI Branding Chatbot - Bedrock Integration",
    filename="docs/bedrock_integration_diagram",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr
):
    with Cluster("Lambda Agents"):
        agents = [
            Lambda("Product\nInsight"),
            Lambda("Market\nAnalyst"),
            Lambda("Reporter"),
            Lambda("Signboard"),
            Lambda("Interior"),
            Lambda("Report Gen")
        ]
    
    with Cluster("Amazon Bedrock"):
        with Cluster("Foundation Models"):
            claude_model = Bedrock("Claude 4 Sonnet\nus.anthropic.claude-sonnet-4")
            sdxl_model = Bedrock("Titan Image Gen v2\namazon.titan-image-generator-v2")
        
        with Cluster("Capabilities"):
            reasoning = Bedrock("Reasoning Engine\nChain-of-Thought")
            knowledge_base = Bedrock("Knowledge Base\nVector Search")
    
    with Cluster("Shared Resources"):
        bedrock_client = Lambda("BedrockClient\nShared Module")
        reasoning_engine = Lambda("ReasoningEngine\nShared Module")
    
    # Connections
    for agent in agents:
        agent >> bedrock_client
    
    bedrock_client >> claude_model
    bedrock_client >> sdxl_model
    bedrock_client >> knowledge_base
    
    reasoning_engine >> claude_model
    reasoning_engine >> reasoning
    
    agents[1] >> Edge(label="Vector Search") >> knowledge_base
    agents[2] >> Edge(label="Autonomous Decisions") >> reasoning_engine

print("✅ Bedrock integration diagram generated: docs/bedrock_integration_diagram.png")

print("\n📊 All diagrams generated successfully!")
print("   - docs/aws_architecture_diagram.png")
print("   - docs/workflow_sequence_diagram.png")
print("   - docs/bedrock_integration_diagram.png")
