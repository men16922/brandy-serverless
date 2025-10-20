# Product Overview

## AI 브랜딩 챗봇 - AWS Bedrock Implementation

An intelligent AI-powered branding system that generates comprehensive business branding materials through a 5-step automated workflow using Amazon Bedrock and serverless architecture.

### Core Workflow
1. **Business Analysis** - Product Insight + Market Analyst Agents analyze industry/region/size using **Bedrock Claude 4 Sonnet**
2. **Name Suggestions** - Reporter Agent generates 3 business name candidates with **Reasoning LLM** scoring
3. **Signboard Design** - Signboard Agent creates designs using **Bedrock Titan Image Generator v2**
4. **Interior Recommendations** - Interior Agent generates 3 interior options with **Bedrock Claude** reasoning
5. **HTML Report** - Report Generator Agent creates comprehensive branding report with **Bedrock Claude** insights

### Key Features (Hackathon Compliant)
- **Amazon Bedrock Integration**: Primary LLM provider (Claude 4 Sonnet, Titan Image Generator v2)
- **Reasoning Engine**: Chain-of-Thought reasoning for autonomous decision-making
- **Agent-Based Architecture**: 6 specialized agents + 1 Supervisor Agent
- **Supervisor Agent**: 
  - Session management (create, read, update sessions in DynamoDB)
  - API Gateway request routing and response handling
  - Autonomous error recovery with Reasoning LLM
  - Workflow orchestration via AgentCore (when enabled)
  - Structured logging and monitoring
- **Serverless Infrastructure**: AWS SAM, Lambda, DynamoDB, S3, API Gateway
- **Session Management**: 24-hour TTL sessions with DynamoDB storage
- **Visual Diagrams**: Auto-generated architecture diagrams using Python diagrams library

### AWS Services Used
- **Amazon Bedrock**: Claude 4 Sonnet (text/reasoning), Titan Image Generator v2 (images)
- **AWS Lambda**: 7 serverless functions (6 agents + 1 supervisor)
- **API Gateway**: HTTP API endpoints (cost-optimized)
- **DynamoDB**: Session storage with TTL
- **S3**: Image and report storage
- **CloudWatch**: Centralized logging and monitoring
- **AWS SAM**: Infrastructure as Code for deployment

### Architecture Diagrams
- **AWS Infrastructure Diagram**: Complete system architecture
- **5-Step Workflow Diagram**: Workflow sequence visualization
- **Bedrock Integration Diagram**: AI/ML integration details
- **Mermaid Diagrams**: Interactive diagrams for documentation

### Target Users
- Small to medium businesses needing complete branding solutions
- Entrepreneurs looking for automated brand identity generation
- Marketing agencies seeking rapid prototyping tools
- **Hackathon judges** evaluating AI agent capabilities

### Success Metrics
- Text responses ≤ 5 seconds
- Image generation ≤ 30 seconds  
- Complete workflow ≤ 5 minutes
- High availability with automatic retries and error recovery
- **Bedrock API success rate** ≥ 95%
- **Reasoning confidence score** ≥ 0.7
- Cost per workflow: ~$0.20

### Project Status
- ✅ **Infrastructure**: AWS SAM deployment, Lambda functions, DynamoDB, S3
- ✅ **Agents**: 6 specialized agents + Supervisor Agent
- ✅ **UI**: Streamlit web interface
- ✅ **Bedrock Integration**: Claude 4 Sonnet, Titan Image Generator v2
- ✅ **Documentation**: README, architecture diagrams, steering files
- 🎯 **Target**: AWS AI Agent Global Hackathon submission