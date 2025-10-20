# Design Document

## Overview

This design refactors the Report Generator Agent's index.py (1282 lines) into a modular architecture with clear separation of concerns. The refactored system will maintain all existing functionality while improving maintainability, testability, and code clarity.

## Architecture

### Current State
```
index.py (1282 lines)
├── ReportGeneratorAgent class
├── Data collection methods
├── Report generation methods
├── Storage methods
├── Business logic utilities
├── Bedrock integration
└── Lambda handler
```

### Target State
```
index.py (< 200 lines)
├── ReportGeneratorAgent (orchestration only)
└── lambda_handler

report_generator.py
├── ReportGenerator class
├── generate_pdf_report()
├── generate_alternative_report()
└── format-specific generation

storage_manager.py
├── StorageManager class
├── store_report()
├── generate_presigned_urls()
└── add_presigned_urls_to_images()

business_utils.py
├── BusinessUtils class
├── generate_color_palette()
├── generate_budget_guide()
└── generate_recommendations()

bedrock_integration.py
├── BedrockIntegration class
├── synthesize_insights()
└── enhance_report_with_ai()

data_collector.py (existing)
data_sanitizer.py (existing)
alternative_report_generator.py (existing)
```

## Components and Interfaces

### 1. ReportGeneratorAgent (index.py)

**Purpose:** Thin orchestration layer that coordinates all modules

**Interface:**
```python
class ReportGeneratorAgent(BaseAgent):
    def __init__(self):
        # Initialize all module instances
        self.report_generator = ReportGenerator(...)
        self.storage_manager = StorageManager(...)
        self.business_utils = BusinessUtils(...)
        self.bedrock_integration = BedrockIntegration(...)
        self.data_collector = DataCollector(...)
        self.data_sanitizer = DataSanitizer(...)
    
    def execute(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Parse request
        # Delegate to appropriate module
        # Return response
```

**Responsibilities:**
- Parse Lambda event
- Initialize modules
- Orchestrate workflow
- Handle errors using BaseAgent
- Return Lambda response

**Size Target:** < 200 lines

### 2. ReportGenerator (report_generator.py)

**Purpose:** Handle all report generation logic

**Interface:**
```python
class ReportGenerator:
    def __init__(self, logger, bedrock_integration, business_utils):
        self.logger = logger
        self.bedrock = bedrock_integration
        self.business_utils = business_utils
    
    def generate_report(
        self, 
        session_data: Dict[str, Any], 
        format: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate report in specified format
        Returns: {
            "content": bytes or str,
            "format": str,
            "content_type": str,
            "file_extension": str,
            "bedrock_enhanced": bool
        }
        """
    
    def generate_pdf_report(self, session_data: Dict) -> Dict:
        # PDF generation logic
    
    def generate_html_report(self, session_data: Dict) -> Dict:
        # HTML generation logic
    
    def generate_json_report(self, session_data: Dict) -> Dict:
        # JSON generation logic
    
    def generate_text_report(self, session_data: Dict) -> Dict:
        # Text generation logic
```

**Responsibilities:**
- Generate reports in multiple formats (PDF, HTML, JSON, text)
- Coordinate with Bedrock for AI-enhanced content
- Use business_utils for color palettes, budgets, recommendations
- Handle format-specific errors with fallbacks
- Delegate to alternative_report_generator for complex formats

**Dependencies:**
- bedrock_integration (for AI enhancements)
- business_utils (for business logic)
- alternative_report_generator (for HTML/JSON)
- pdf_template (for PDF generation)

### 3. StorageManager (storage_manager.py)

**Purpose:** Handle all S3/storage operations

**Interface:**
```python
class StorageManager:
    def __init__(self, logger, s3_client=None):
        self.logger = logger
        self.s3_client = s3_client or get_s3_client()
    
    def store_report(
        self, 
        content: bytes or str,
        session_id: str,
        format: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Store report and return storage info
        Returns: {
            "presigned_url": str,
            "direct_url": str,
            "file_name": str,
            "file_size": int,
            "s3_key": str
        }
        """
    
    def add_presigned_urls_to_images(
        self, 
        images: List[Dict]
    ) -> List[Dict]:
        """Add presigned URLs to image list"""
    
    def get_download_url(self, session_id: str) -> str:
        """Get presigned URL for existing report"""
```

**Responsibilities:**
- Upload reports to S3/MinIO
- Generate presigned URLs (10 min expiry)
- Add presigned URLs to image lists
- Handle storage errors gracefully
- Manage file metadata

**Dependencies:**
- shared.s3_client (or local s3_client)

### 4. BusinessUtils (business_utils.py)

**Purpose:** Business logic utilities for branding

**Interface:**
```python
class BusinessUtils:
    def __init__(self, logger):
        self.logger = logger
    
    def generate_color_palette(
        self, 
        business_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate industry-specific color palette
        Returns: {
            "primary": str,
            "secondary": str,
            "accent": str,
            "background": str,
            "text": str
        }
        """
    
    def generate_budget_guide(
        self, 
        business_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate budget estimates
        Returns: {
            "signboard": {"min": int, "max": int},
            "interior": {"min": int, "max": int},
            "total": {"min": int, "max": int}
        }
        """
    
    def generate_recommendations(
        self,
        business_info: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Generate business recommendations"""
```

**Responsibilities:**
- Generate industry-specific color palettes
- Calculate budget estimates based on business size/region
- Provide business recommendations
- Support multiple industries (cafe, restaurant, retail, etc.)

**Dependencies:**
- None (pure business logic)

### 5. BedrockIntegration (bedrock_integration.py)

**Purpose:** Handle all Bedrock AI integration

**Interface:**
```python
class BedrockIntegration:
    def __init__(self, logger, enable_bedrock=True):
        self.logger = logger
        self.enable_bedrock = enable_bedrock
        self.bedrock_client = None
        self.reasoning_engine = None
        
        if enable_bedrock:
            self._initialize_bedrock()
    
    def synthesize_insights(
        self, 
        session_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Use Bedrock Claude to synthesize insights
        Returns: Synthesized insights text or None if disabled/failed
        """
    
    def enhance_report_content(
        self,
        base_content: str,
        session_data: Dict[str, Any]
    ) -> str:
        """Enhance report content with AI insights"""
    
    def is_enabled(self) -> bool:
        """Check if Bedrock is enabled and available"""
```

**Responsibilities:**
- Initialize Bedrock client and reasoning engine
- Synthesize insights from agent outputs
- Enhance report content with AI
- Handle Bedrock failures gracefully (fallback to non-AI)
- Respect ENABLE_FALLBACK environment variable

**Dependencies:**
- shared.bedrock_client (or local bedrock_client)
- shared.reasoning_engine (or local reasoning_engine)

## Data Models

### ReportGenerationRequest
```python
{
    "session_id": str,
    "format": str,  # "pdf", "html", "json", "text"
    "action": str   # "generate", "download"
}
```

### ReportGenerationResult
```python
{
    "success": bool,
    "sessionId": str,
    "reportUrl": str,
    "directUrl": str,
    "reportType": str,
    "reportContent": Optional[str],  # For JSON format
    "generatedAt": str,
    "fileSize": int,
    "fileName": str,
    "downloadExpiry": str,
    "processingTime": str,
    "bedrockEnhanced": bool,
    "components": {
        "businessAnalysis": bool,
        "businessNames": int,
        "signboardImages": int,
        "interiorImages": int,
        "colorPalette": bool,
        "budgetGuide": bool,
        "bedrockInsights": bool
    }
}
```

### StorageInfo
```python
{
    "presigned_url": str,
    "direct_url": str,
    "file_name": str,
    "file_size": int,
    "s3_key": str,
    "report_type": str
}
```

## Error Handling

### Module-Level Error Handling

Each module handles its own errors and provides fallbacks:

**ReportGenerator:**
- PDF generation fails → Try HTML
- HTML generation fails → Try JSON
- JSON generation fails → Try simple text
- All fail → Return error with partial data

**StorageManager:**
- S3 upload fails → Retry once
- Presigned URL generation fails → Log warning, continue
- All storage fails → Return error

**BusinessUtils:**
- Invalid industry → Use default color palette
- Missing data → Use reasonable defaults
- Never fails, always returns valid data

**BedrockIntegration:**
- Bedrock disabled → Return None (graceful degradation)
- Bedrock call fails → Log warning, return None
- Never blocks report generation

### Agent-Level Error Handling

ReportGeneratorAgent uses BaseAgent error handling:
```python
try:
    result = self.report_generator.generate_report(...)
    storage_info = self.storage_manager.store_report(...)
    return self.create_lambda_response(200, result)
except Exception as e:
    error_response = self.handle_error(e, "execute")
    return self.create_lambda_response(500, error_response)
```

## Testing Strategy

### Unit Tests (per module)

**test_report_generator.py:**
- Test each format generation independently
- Test Bedrock enhancement toggle
- Test fallback mechanisms
- Mock dependencies (bedrock, business_utils)

**test_storage_manager.py:**
- Test S3 upload with mocked s3_client
- Test presigned URL generation
- Test error handling

**test_business_utils.py:**
- Test color palette generation for each industry
- Test budget calculations
- Test recommendations
- No mocks needed (pure logic)

**test_bedrock_integration.py:**
- Test with Bedrock enabled/disabled
- Test insight synthesis
- Test fallback behavior
- Mock bedrock_client

### Integration Tests

**test_report_generator_agent.py:**
- Test full workflow with real AWS services
- Test different report formats
- Test with/without Bedrock
- Verify storage and URLs

## Migration Strategy

### Phase 1: Create New Modules (No Breaking Changes)
1. Create report_generator.py with ReportGenerator class
2. Create storage_manager.py with StorageManager class
3. Create business_utils.py with BusinessUtils class
4. Create bedrock_integration.py with BedrockIntegration class
5. Keep index.py unchanged

### Phase 2: Refactor index.py
1. Import new modules
2. Initialize module instances in __init__
3. Replace method calls with module calls
4. Remove old methods from index.py
5. Keep lambda_handler unchanged

### Phase 3: Testing
1. Run integration tests against AWS dev environment
2. Verify all report formats work
3. Verify Bedrock integration works
4. Verify storage and URLs work

### Phase 4: Cleanup
1. Remove commented-out code
2. Update requirements.txt if needed
3. Update documentation

## Performance Considerations

### Module Initialization
- Modules initialized once in __init__ (Lambda warm start optimization)
- Lazy loading for heavy dependencies (Bedrock, PDF libraries)

### Memory Usage
- Modules share logger instance (no duplication)
- S3 client reused across calls
- Bedrock client reused across calls

### Execution Time
- No performance degradation expected
- Cleaner code may improve maintainability-related performance

## Backward Compatibility

### API Compatibility
- Lambda event/response format unchanged
- All existing endpoints work identically
- Error responses maintain same structure

### Functionality Compatibility
- All report formats supported
- Bedrock integration works as before
- Storage behavior unchanged
- Fallback mechanisms preserved

## Dependencies

### New Module Dependencies

**report_generator.py:**
- bedrock_integration
- business_utils
- alternative_report_generator
- pdf_template

**storage_manager.py:**
- shared.s3_client or s3_client

**business_utils.py:**
- None (standalone)

**bedrock_integration.py:**
- shared.bedrock_client or bedrock_client
- shared.reasoning_engine or reasoning_engine

### Import Strategy

All modules use this pattern:
```python
# Try Lambda Layer import first
try:
    from shared.module import Class
except ImportError:
    # Fallback to local import
    from module import Class
```

This ensures compatibility with:
- Lambda Layer deployment
- Local development
- Testing environments
