# Requirements Document

## Introduction

이 프로젝트는 AWS AI Agent Global Hackathon 제출을 위한 AI 브랜딩 챗봇입니다. 현재 로컬 개발 환경(Docker Compose, DynamoDB Local, MinIO 등)과 AWS 환경이 혼재되어 있어 복잡도가 높습니다. 이를 **AWS 전용 환경으로 단순화**하여 Streamlit만 로컬에서 실행하고 모든 백엔드 서비스는 AWS를 직접 사용하도록 리팩토링합니다.

## Requirements

### Requirement 1: 로컬 환경 코드 및 파일 제거

**User Story:** As a developer, I want to remove all local development infrastructure code, so that the project only uses AWS services and reduces complexity.

#### Acceptance Criteria

1. WHEN reviewing the codebase THEN all Docker Compose related files SHALL be removed
2. WHEN checking configuration files THEN local.json and local environment settings SHALL be removed
3. WHEN examining scripts THEN setup-local.sh and other local-only scripts SHALL be removed
4. WHEN inspecting source code THEN all local endpoint configurations (DynamoDB Local, MinIO, Chroma) SHALL be removed
5. WHEN checking base_agent.py THEN local environment detection and endpoint switching logic SHALL be removed

### Requirement 2: AWS 전용 환경 설정

**User Story:** As a developer, I want all backend services to use AWS directly, so that development and production environments are consistent.

#### Acceptance Criteria

1. WHEN Lambda functions execute THEN they SHALL always connect to AWS DynamoDB (no local endpoint)
2. WHEN agents store files THEN they SHALL always use AWS S3 (no MinIO)
3. WHEN API calls are made THEN they SHALL always use AWS API Gateway (no local API server)
4. WHEN environment variables are loaded THEN only 'dev' environment SHALL be supported
5. WHEN base_agent.py initializes THEN it SHALL remove local endpoint logic and use AWS SDK defaults

### Requirement 3: Streamlit 로컬 실행 유지

**User Story:** As a developer, I want to run Streamlit locally while connecting to AWS services, so that I can develop and test the UI easily.

#### Acceptance Criteria

1. WHEN Streamlit app starts THEN it SHALL run on localhost:8501
2. WHEN Streamlit makes API calls THEN it SHALL connect to AWS API Gateway endpoint
3. WHEN Streamlit displays data THEN it SHALL fetch from AWS DynamoDB via API
4. WHEN users upload files THEN they SHALL be stored in AWS S3
5. WHEN .env file is configured THEN it SHALL contain AWS API Gateway URL and credentials

### Requirement 4: 문서 업데이트

**User Story:** As a developer, I want updated documentation that reflects AWS-only architecture, so that setup and deployment are clear.

#### Acceptance Criteria

1. WHEN reading README.md THEN it SHALL describe AWS-only setup (no Docker Compose)
2. WHEN following deployment guide THEN it SHALL only mention SAM deploy to AWS
3. WHEN checking local-environment.md THEN it SHALL describe Streamlit local + AWS backend architecture
4. WHEN reviewing integration-testing.md THEN it SHALL remove Docker Compose testing references
5. WHEN reading DEPLOYMENT_FIX.md THEN it SHALL be updated to reflect current AWS-only approach

### Requirement 5: 테스트 환경 단순화

**User Story:** As a developer, I want integration tests to use AWS services directly, so that tests match production environment.

#### Acceptance Criteria

1. WHEN running integration tests THEN they SHALL connect to AWS dev environment
2. WHEN tests need data THEN they SHALL use AWS DynamoDB dev tables
3. WHEN tests store files THEN they SHALL use AWS S3 dev bucket
4. WHEN Docker Compose is removed THEN integration test fixtures SHALL be updated
5. WHEN pytest runs THEN it SHALL skip Docker-dependent tests or remove them

### Requirement 6: 스크립트 정리

**User Story:** As a developer, I want only necessary scripts for AWS deployment, so that the scripts directory is clean and maintainable.

#### Acceptance Criteria

1. WHEN reviewing scripts directory THEN local-only scripts SHALL be removed
2. WHEN deployment is needed THEN only safe_deploy.sh and SAM scripts SHALL remain
3. WHEN validation is needed THEN only AWS-compatible validation scripts SHALL remain
4. WHEN scripts are executed THEN they SHALL not reference Docker or local services
5. WHEN new developers onboard THEN script README SHALL clearly describe AWS-only workflow

### Requirement 7: 환경 변수 단순화

**User Story:** As a developer, I want simplified environment variables for AWS-only setup, so that configuration is straightforward.

#### Acceptance Criteria

1. WHEN .env file is created THEN it SHALL only contain AWS-related variables
2. WHEN ENVIRONMENT variable is set THEN it SHALL only accept 'dev' value
3. WHEN endpoint variables are checked THEN local endpoint variables SHALL be removed
4. WHEN .env.example is reviewed THEN it SHALL show only AWS configuration
5. WHEN environment is loaded THEN no local/dev switching logic SHALL exist

### Requirement 8: 코드 리팩토링

**User Story:** As a developer, I want clean code without local environment conditionals, so that the codebase is simpler and more maintainable.

#### Acceptance Criteria

1. WHEN base_agent.py is reviewed THEN local endpoint logic SHALL be removed
2. WHEN utils.py is checked THEN get_aws_clients SHALL not have local endpoint parameters
3. WHEN agent code is inspected THEN no environment-based endpoint switching SHALL exist
4. WHEN configuration is loaded THEN _load_environment_config SHALL only return AWS settings
5. WHEN imports are checked THEN no Docker or local service imports SHALL remain
