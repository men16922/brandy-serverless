# Requirements Document

## Introduction

Report Generator Agent의 index.py 파일이 1282줄로 너무 커서 유지보수가 어렵습니다. 이미 일부 모듈(data_collector.py, data_sanitizer.py, alternative_report_generator.py 등)이 분리되어 있지만, index.py에는 여전히 많은 기능이 남아있습니다. 

목표는 index.py를 200줄 이하로 줄이고, 각 기능을 독립적인 모듈로 분리하여 코드의 가독성과 유지보수성을 향상시키는 것입니다.

## Requirements

### Requirement 1: 핵심 기능 분석 및 모듈 분리

**User Story:** As a developer, I want to understand what functions are in index.py, so that I can properly separate them into logical modules.

#### Acceptance Criteria

1. WHEN analyzing index.py THEN the system SHALL identify all major function groups
2. WHEN grouping functions THEN the system SHALL categorize them by responsibility (data collection, report generation, storage, etc.)
3. WHEN identifying dependencies THEN the system SHALL map which functions call which other functions

### Requirement 2: Report Generation 모듈 분리

**User Story:** As a developer, I want report generation logic separated from the main agent class, so that report generation can be tested and maintained independently.

#### Acceptance Criteria

1. WHEN creating report_generator.py THEN it SHALL contain all report generation methods (_generate_pdf_report, _generate_alternative_report, etc.)
2. WHEN the module is created THEN it SHALL have a clear interface for generating different report formats
3. WHEN generating reports THEN the module SHALL handle both Bedrock-enhanced and fallback scenarios
4. WHEN errors occur THEN the module SHALL provide appropriate fallback mechanisms

### Requirement 3: Storage 모듈 분리

**User Story:** As a developer, I want S3/storage operations separated into a dedicated module, so that storage logic is centralized and reusable.

#### Acceptance Criteria

1. WHEN creating storage_manager.py THEN it SHALL contain all S3 upload/download operations
2. WHEN storing files THEN it SHALL generate presigned URLs automatically
3. WHEN handling images THEN it SHALL add presigned URLs to image lists
4. WHEN errors occur THEN it SHALL provide clear error messages

### Requirement 4: Business Logic 유틸리티 분리

**User Story:** As a developer, I want business logic utilities (color palette, budget guide, recommendations) separated, so that they can be easily modified and tested.

#### Acceptance Criteria

1. WHEN creating business_utils.py THEN it SHALL contain _generate_color_palette, _generate_budget_guide, _generate_recommendations
2. WHEN generating color palettes THEN it SHALL support industry-specific colors
3. WHEN generating budget guides THEN it SHALL provide realistic cost estimates
4. WHEN generating recommendations THEN it SHALL be based on business info and analysis

### Requirement 5: Bedrock Integration 모듈 분리

**User Story:** As a developer, I want Bedrock integration logic separated, so that AI-enhanced features are clearly isolated and can be toggled.

#### Acceptance Criteria

1. WHEN creating bedrock_integration.py THEN it SHALL contain _synthesize_insights_with_bedrock and related Bedrock calls
2. WHEN Bedrock is disabled THEN the system SHALL gracefully fall back to non-AI methods
3. WHEN Bedrock calls fail THEN the system SHALL log warnings and continue with fallback
4. WHEN insights are synthesized THEN they SHALL be added to session data

### Requirement 6: 리팩토링된 index.py 구조

**User Story:** As a developer, I want index.py to be a thin orchestration layer, so that it's easy to understand the overall flow.

#### Acceptance Criteria

1. WHEN refactoring index.py THEN it SHALL be reduced to under 200 lines
2. WHEN the agent executes THEN index.py SHALL only orchestrate calls to other modules
3. WHEN initializing THEN index.py SHALL import and initialize all required modules
4. WHEN handling requests THEN index.py SHALL delegate to appropriate modules
5. WHEN errors occur THEN index.py SHALL use BaseAgent error handling

### Requirement 7: 기존 기능 유지

**User Story:** As a user, I want all existing functionality to work exactly as before, so that the refactoring doesn't break anything.

#### Acceptance Criteria

1. WHEN refactoring is complete THEN all existing API endpoints SHALL work identically
2. WHEN generating reports THEN the output format SHALL be unchanged
3. WHEN using Bedrock THEN the integration SHALL work as before
4. WHEN errors occur THEN error handling SHALL be consistent with previous behavior

### Requirement 8: Import 경로 및 의존성 관리

**User Story:** As a developer, I want clear import paths and minimal circular dependencies, so that modules can be tested independently.

#### Acceptance Criteria

1. WHEN creating new modules THEN they SHALL use relative imports for local modules
2. WHEN importing shared modules THEN they SHALL handle both Lambda Layer and local paths
3. WHEN modules depend on each other THEN circular dependencies SHALL be avoided
4. WHEN testing THEN each module SHALL be importable independently
