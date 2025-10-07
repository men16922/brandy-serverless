# Product Overview

## AI 브랜딩 챗봇 - AWS Hackathon Edition

A serverless AI branding system that generates complete business branding through a 5-step workflow using **Amazon Bedrock-powered agent-based architecture**.

### Core Workflow
1. **Business Analysis** - Product Insight + Market Analyst Agents analyze industry/region/size using **Bedrock Claude**
2. **Name Suggestions** - Reporter Agent generates 3 business name candidates with **Reasoning LLM** scoring
3. **Signboard Design** - Signboard Agent creates designs using **Bedrock SDXL** (primary) + DALL-E, Gemini (fallback)
4. **Interior Recommendations** - Interior Agent generates 3 interior options with **Bedrock Claude** reasoning
5. **HTML Report** - Report Generator Agent creates comprehensive branding report with **Bedrock Claude** insights

### Key Features (Hackathon Compliant)
- **Amazon Bedrock Integration**: Primary LLM provider (Claude 3.5 Sonnet, SDXL)
- **Bedrock AgentCore**: Supervisor Agent uses AgentCore for orchestration
- **Reasoning LLM**: Autonomous decision-making with Chain-of-Thought reasoning
- **Agent-Based Architecture**: 6 specialized agents + 1 Supervisor Agent
- **Multi-AI Integration**: Bedrock (primary) + OpenAI/Gemini (fallback for dev)
- **Environment Flexibility**: Local development with Chroma, production with Bedrock KB
- **Session Management**: 24-hour TTL sessions with DynamoDB storage
- **Fallback System**: Graceful degradation with fallback results

### AWS Services Used
- **Amazon Bedrock**: Claude 3.5 Sonnet (text), SDXL (images), Knowledge Base
- **Bedrock AgentCore**: Tool Use, Memory primitives for agent orchestration
- **AWS Lambda**: 7 serverless functions (6 agents + 1 supervisor)
- **Step Functions**: Express (parallel processing) + Standard (user wait)
- **DynamoDB**: Session storage with TTL
- **S3**: Image and report storage
- **API Gateway**: HTTP API endpoints

### Target Users
- Small to medium businesses needing complete branding solutions
- Entrepreneurs looking for automated brand identity generation
- Marketing agencies seeking rapid prototyping tools
- **Hackathon judges** evaluating AI agent capabilities

### Success Metrics
- Text responses ≤ 5 seconds
- Image generation ≤ 30 seconds  
- Complete workflow ≤ 5 minutes
- High availability with automatic retries and fallbacks
- **Bedrock API success rate** ≥ 95%
- **Reasoning confidence score** ≥ 0.7

### Project Status
- ✅ **70% Complete**: Infrastructure, agents, UI, tests
- 🔄 **30% In Progress**: Bedrock integration, AgentCore, Reasoning Engine
- 🎯 **Target**: AWS AI Agent Global Hackathon submission