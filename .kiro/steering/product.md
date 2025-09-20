# Product Overview

## AI 브랜딩 챗봇 (Agent-Based Architecture)

A serverless AI branding system that generates complete business branding through a 5-step workflow using agent-based architecture.

### Core Workflow
1. **Business Analysis** - Product Insight + Market Analyst Agents analyze industry/region/size
2. **Name Suggestions** - Reporter Agent generates 3 business name candidates with scoring
3. **Signboard Design** - Signboard Agent creates designs using DALL-E, SDXL, and Gemini in parallel
4. **Interior Recommendations** - Interior Agent generates 3 interior options based on signboard style
5. **PDF Report** - Report Generator Agent creates comprehensive branding report

### Key Features
- **Agent-Based Architecture**: Each workflow step handled by specialized agents
- **Supervisor Agent**: Monitors entire workflow, handles failures and retries
- **Multi-AI Integration**: Parallel processing with DALL-E, SDXL, and Gemini
- **Environment Flexibility**: Local development with Chroma, production with Bedrock KB
- **Session Management**: 24-hour TTL sessions with DynamoDB storage
- **Fallback System**: Graceful degradation with fallback results

### Target Users
- Small to medium businesses needing complete branding solutions
- Entrepreneurs looking for automated brand identity generation
- Marketing agencies seeking rapid prototyping tools

### Success Metrics
- Text responses ≤ 5 seconds
- Image generation ≤ 30 seconds  
- Complete workflow ≤ 5 minutes
- High availability with automatic retries and fallbacks