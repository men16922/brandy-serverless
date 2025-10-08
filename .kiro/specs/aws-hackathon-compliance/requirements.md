# Requirements Document

## Introduction

This document defines the integrated requirements for adapting the AI Branding Chatbot project to meet AWS AI Agent Global Hackathon requirements.

### Project Overview

The AI Branding Chatbot is a fully automated branding system where business owners input only their industry, region, and size, and AI automatically generates business names, signboard designs, interior recommendations, and a comprehensive HTML branding report.

**Core Workflow**: 5-step automated generation (Analysis → Name → Signboard → Interior → Report)

**Architecture**:
- 6 specialized AI agents + 1 Supervisor Agent
- Automated workflow completing within 5 minutes
- Real-time monitoring with automatic fallback mechanisms
- Fully serverless architecture using AWS SAM
- NO MOCKS testing with Docker Compose-based integration tests

### Hackathon Core Requirements
1. **LLM Hosting**: Must use AWS Bedrock or Amazon SageMaker AI
2. **AWS Services**: Must use at least one of Amazon Bedrock AgentCore, Bedrock/Nova, or Amazon Q (AgentCore strongly recommended)
3. **AI Agent Qualification**:
   - Decision-making using Reasoning LLM
   - Autonomous task execution capability (with or without human intervention)
   - Integration with APIs, databases, external tools, or other agents

### Current Project Status (70% Complete)

**Completed Components**:
- Agent-Based Architecture (6 specialized agents + Supervisor)
- Step Functions workflow management
- DynamoDB and S3 integration
- Docker Compose local environment
- Integration tests (29 tests passing)
- Streamlit web interface
- HTML branding report generation with full Korean font support

**Hackathon Requirements Not Yet Met**:
- Currently using OpenAI DALL-E and Google Gemini (need to migrate to AWS Bedrock)
- Bedrock AgentCore not implemented (required)
- Reasoning LLM not explicitly used (required)
- Hackathon submission documents missing (architecture diagrams, demo video)

## Requirements

### Requirement 1: Amazon Bedrock 통합

**User Story:** As a hackathon participant, I want to use Amazon Bedrock as the primary LLM provider, so that my project meets the mandatory hackathon requirements.

#### Acceptance Criteria

1. WHEN the system initializes THEN it SHALL use Amazon Bedrock as the default LLM provider for all text generation tasks
2. WHEN generating business names THEN the Reporter Agent SHALL use Amazon Bedrock Claude 4 Sonnet for reasoning and name generation
3. WHEN analyzing market data THEN the Market Analyst Agent SHALL use Amazon Bedrock for trend analysis and insights
4. WHEN generating signboard designs THEN the Signboard Agent SHALL use Amazon Bedrock SDXL 1.0 for image generation
5. WHEN generating interior recommendations THEN the Interior Agent SHALL use Amazon Bedrock for design suggestions
6. IF Bedrock API fails THEN the system SHALL log the error and provide graceful degradation with fallback responses
7. WHEN using Bedrock THEN all API calls SHALL include proper error handling and retry logic with exponential backoff

### Requirement 2: Amazon Bedrock AgentCore 통합

**User Story:** As a hackathon participant, I want to implement Amazon Bedrock AgentCore with at least one primitive, so that my project qualifies for the "Best Amazon Bedrock AgentCore Implementation" prize category.

#### Acceptance Criteria

1. WHEN the Supervisor Agent coordinates workflow THEN it SHALL use Bedrock AgentCore for agent orchestration
2. WHEN agents need to communicate THEN they SHALL use AgentCore primitives for inter-agent messaging
3. WHEN the workflow requires decision-making THEN AgentCore SHALL provide reasoning capabilities for autonomous task execution
4. WHEN implementing AgentCore THEN the system SHALL use at least one AgentCore primitive (e.g., Tool Use, Memory, Planning)
5. WHEN AgentCore makes decisions THEN the system SHALL log the reasoning process for transparency
6. IF AgentCore is unavailable THEN the system SHALL fall back to direct Lambda invocation with Step Functions
7. WHEN using AgentCore THEN the implementation SHALL be well-documented in the architecture diagram

### Requirement 3: Reasoning LLM 의사결정 시스템

**User Story:** As a hackathon participant, I want to demonstrate autonomous AI agent capabilities with reasoning LLMs, so that my project meets the AWS-defined AI agent qualification.

#### Acceptance Criteria

1. WHEN the Supervisor Agent receives a new branding request THEN it SHALL use reasoning LLM to analyze requirements and plan the workflow
2. WHEN the Market Analyst evaluates business viability THEN it SHALL use reasoning LLM to assess market conditions and provide recommendations
3. WHEN the Reporter Agent generates business names THEN it SHALL use reasoning LLM to evaluate name quality, pronunciation, and brand fit
4. WHEN selecting the best signboard design THEN the system SHALL use reasoning LLM to compare designs based on brand identity and market trends
5. WHEN generating the final report THEN the system SHALL use reasoning LLM to synthesize insights from all agents
6. WHEN reasoning decisions are made THEN the system SHALL store the reasoning chain in DynamoDB for audit and explanation
7. IF reasoning LLM provides low-confidence results THEN the system SHALL request human review or provide alternative options

### Requirement 4: 자율적 작업 실행 능력

**User Story:** As a business owner, I want the AI agents to autonomously complete the entire branding workflow without constant human intervention, so that I can receive comprehensive branding materials efficiently.

#### Acceptance Criteria

1. WHEN a user submits business information THEN the system SHALL autonomously execute all 5 workflow steps without requiring intermediate approvals
2. WHEN an agent encounters an error THEN the Supervisor SHALL autonomously decide whether to retry, use fallback, or request human intervention
3. WHEN generating multiple design options THEN agents SHALL autonomously evaluate and rank options based on learned criteria
4. WHEN the workflow is paused THEN the system SHALL save state and allow resumption without data loss
5. IF human input is needed THEN the system SHALL clearly indicate what decision is required and why
6. WHEN the workflow completes THEN the system SHALL autonomously generate and deliver the final PDF report
7. WHEN monitoring workflow progress THEN users SHALL be able to view real-time status updates without manual polling

### Requirement 5: 외부 도구 및 API 통합

**User Story:** As a hackathon participant, I want to demonstrate integration with external tools, APIs, and databases, so that my project shows comprehensive AI agent capabilities.

#### Acceptance Criteria

1. WHEN agents need market data THEN they SHALL query DynamoDB for industry trends and regional multipliers
2. WHEN generating images THEN agents SHALL integrate with Amazon Bedrock SDXL API for signboard designs
3. WHEN storing generated assets THEN agents SHALL use S3 API for file uploads and presigned URL generation
4. WHEN analyzing business names THEN the Reporter Agent SHALL integrate with external pronunciation scoring APIs or libraries
5. WHEN generating reports THEN the Report Generator SHALL use PDF generation libraries and S3 for storage
6. WHEN agents need vector search THEN they SHALL integrate with Amazon Bedrock Knowledge Base (production) or Chroma (local)
7. WHEN API calls fail THEN the system SHALL implement circuit breaker patterns and graceful degradation

### Requirement 6: 아키텍처 다이어그램 및 문서화

**User Story:** As a hackathon judge, I want to see a clear architecture diagram and comprehensive documentation, so that I can evaluate the technical execution and reproducibility of the project.

#### Acceptance Criteria

1. WHEN submitting to the hackathon THEN the project SHALL include a detailed architecture diagram showing all AWS services
2. WHEN documenting the system THEN the diagram SHALL clearly show agent interactions, data flows, and AWS service integrations
3. WHEN explaining the architecture THEN the documentation SHALL highlight Bedrock AgentCore usage and reasoning LLM decision points
4. WHEN providing setup instructions THEN the README SHALL include step-by-step deployment guide with SAM CLI commands
5. WHEN documenting agents THEN each agent SHALL have clear descriptions of its responsibilities and Bedrock model usage
6. IF the project uses multiple AWS regions THEN the documentation SHALL specify which services are deployed in which regions
7. WHEN creating the demo video THEN it SHALL show the end-to-end agentic workflow with reasoning explanations

### Requirement 7: 배포 가능한 프로젝트

**User Story:** As a hackathon judge, I want to deploy and test the project in my own AWS account, so that I can verify its functionality and reproducibility.

#### Acceptance Criteria

1. WHEN deploying the project THEN it SHALL use AWS SAM for infrastructure as code deployment
2. WHEN running `sam build && sam deploy --guided` THEN all resources SHALL be created successfully in the target AWS account
3. WHEN the deployment completes THEN the system SHALL output the API Gateway endpoint URL for testing
4. WHEN testing locally THEN developers SHALL be able to use `sam local start-api` with Docker Compose services
5. WHEN providing deployment instructions THEN the README SHALL include AWS credentials setup and region selection guidance
6. IF deployment fails THEN error messages SHALL clearly indicate missing permissions or configuration issues
7. WHEN the project is deployed THEN it SHALL include CloudWatch dashboards for monitoring agent performance

### Requirement 8: 데모 비디오 및 프레젠테이션

**User Story:** As a hackathon participant, I want to create a compelling 3-minute demo video, so that judges can understand the project's value and technical execution.

#### Acceptance Criteria

1. WHEN creating the demo video THEN it SHALL be approximately 3 minutes in length
2. WHEN presenting the problem THEN the video SHALL clearly explain what real-world branding challenge the system solves
3. WHEN demonstrating functionality THEN the video SHALL show the complete workflow from input to PDF report generation
4. WHEN explaining technical execution THEN the video SHALL highlight Bedrock AgentCore usage and reasoning LLM decisions
5. WHEN showing the UI THEN the video SHALL include footage of the Streamlit interface and agent status updates
6. WHEN discussing impact THEN the video SHALL provide measurable benefits (time saved, cost reduction, quality improvement)
7. WHEN uploading the video THEN it SHALL be publicly accessible on YouTube, Vimeo, or Facebook Video

### Requirement 9: 성능 및 확장성

**User Story:** As a hackathon judge, I want to see that the AI agent system is scalable and performs well, so that I can evaluate its production readiness.

#### Acceptance Criteria

1. WHEN processing a branding request THEN text responses SHALL complete within 5 seconds
2. WHEN generating images THEN the Signboard Agent SHALL complete within 30 seconds per image
3. WHEN executing the full workflow THEN the system SHALL complete within 5 minutes
4. WHEN handling concurrent requests THEN the system SHALL support at least 10 simultaneous sessions without degradation
5. WHEN scaling agents THEN Lambda functions SHALL automatically scale based on demand
6. IF system load is high THEN CloudWatch metrics SHALL trigger alarms for monitoring
7. WHEN optimizing costs THEN the system SHALL use HTTP API Gateway instead of REST API for cost efficiency

### Requirement 10: 테스트 및 품질 보증

**User Story:** As a developer, I want comprehensive integration tests, so that I can ensure the system works correctly with all AWS services.

#### Acceptance Criteria

1. WHEN running integration tests THEN they SHALL use Docker Compose with real DynamoDB Local, MinIO, and Chroma
2. WHEN testing Bedrock integration THEN tests SHALL verify API calls, error handling, and response parsing
3. WHEN testing agent coordination THEN tests SHALL verify Supervisor Agent orchestration and inter-agent communication
4. WHEN testing the full workflow THEN tests SHALL execute all 5 steps and verify final PDF generation
5. WHEN tests complete THEN they SHALL provide detailed logs and coverage reports
6. IF any test fails THEN the CI/CD pipeline SHALL prevent deployment
7. WHEN running `./scripts/dev.sh test` THEN all integration tests SHALL pass successfully

## Non-Functional Requirements

### Performance Requirements
- Text generation responses SHALL complete within 5 seconds
- Image generation SHALL complete within 30 seconds per image
- Full workflow execution SHALL complete within 5 minutes
- System SHALL support at least 10 concurrent sessions without degradation

### Scalability Requirements
- Lambda functions SHALL automatically scale based on demand
- DynamoDB SHALL use on-demand capacity mode for automatic scaling
- S3 SHALL handle unlimited file storage with lifecycle policies

### Security Requirements
- All Bedrock API calls SHALL use IAM role-based authentication
- API Gateway SHALL implement throttling and rate limiting
- Sensitive data SHALL be encrypted at rest in DynamoDB and S3
- CloudWatch logs SHALL not contain PII or API keys

### Reliability Requirements
- System SHALL implement automatic retry with exponential backoff for Bedrock API failures
- System SHALL provide graceful degradation with fallback responses when services are unavailable
- Session data SHALL persist for 24 hours with automatic TTL cleanup
- CloudWatch alarms SHALL trigger for critical failures

## Out of Scope

The following items are explicitly excluded from this hackathon submission:

- Production-level security hardening (fine-grained IAM policies, VPC isolation)
- Multi-language support beyond English and Korean
- Mobile application development
- Real-time collaboration features
- User authentication and authorization system
- Payment system integration
- A/B testing framework
- Advanced analytics dashboard
- Custom domain and SSL certificate setup
- Multi-region deployment
- Disaster recovery and backup strategies

## Success Criteria

The project successfully meets hackathon requirements when:

1. Amazon Bedrock is used as the primary LLM provider for all text and image generation
2. Amazon Bedrock AgentCore is implemented with at least one primitive (Tool Use or Memory)
3. Reasoning LLM system demonstrates autonomous decision-making with stored reasoning chains
4. Integration with external APIs, databases, and tools is demonstrated
5. Clear architecture diagram showing Bedrock integration is provided
6. Reproducible deployment via AWS SAM is documented and tested
7. 3-minute demo video is created and uploaded to public platform
8. Complete source code is published to public GitHub repository
9. Deployed project URL is accessible and functional
10. All integration tests pass successfully

## Assumptions and Constraints

### Assumptions
- AWS account has access to Bedrock services in us-east-1 region
- Bedrock models (Claude 4 Sonnet, SDXL) are available in the deployment region
- Users have basic understanding of AWS services and SAM deployment
- Docker and Docker Compose are available for local development
- Internet connectivity is available for API calls to Bedrock

### Constraints
- Budget limited to $100 AWS credits provided by hackathon
- Submission deadline: October 21, 2025 @ 9:00am GMT+9
- Demo video must be exactly 3 minutes or less
- Must use AWS Bedrock as primary LLM (no other cloud providers)
- Project must be deployable by judges in their own AWS accounts

## Dependencies

### Technical Dependencies
- AWS account with Bedrock service access enabled
- AWS SAM CLI (version 1.100.0 or higher)
- Docker (version 20.10 or higher) and Docker Compose (version 2.0 or higher)
- Python 3.11 or higher
- Git for version control

### AWS Service Dependencies
- Amazon Bedrock (Claude 4 Sonnet, SDXL, Knowledge Base)
- Bedrock AgentCore (Agent Runtime API)
- AWS Lambda (Python 3.11 runtime)
- Amazon DynamoDB (on-demand capacity)
- Amazon S3 (standard storage class)
- AWS Step Functions (Express and Standard workflows)
- Amazon API Gateway (HTTP API)
- Amazon CloudWatch (logs and metrics)

### External Dependencies
- GitHub account for public repository hosting
- YouTube or Vimeo account for demo video hosting
- $100 AWS credits (provided by hackathon organizers)

### Development Dependencies
- pytest for integration testing
- boto3 for AWS SDK
- streamlit for web interface
- structlog for structured logging
- pydantic for data validation
