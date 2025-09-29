"""
Data models for AI Branding Chatbot
Defines session data structures and validation logic
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum


class WorkflowStep(Enum):
    """Workflow step enumeration"""
    ANALYSIS = 1
    NAMING = 2
    SIGNBOARD = 3
    INTERIOR = 4
    REPORT = 5


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class AgentType(Enum):
    """Agent type enumeration"""
    SUPERVISOR = "supervisor"
    PRODUCT_INSIGHT = "product_insight"
    MARKET_ANALYST = "market_analyst"
    REPORTER = "reporter"
    SIGNBOARD = "signboard"
    INTERIOR = "interior"
    REPORT_GENERATOR = "report_generator"


@dataclass
class BusinessInfo:
    """Business information input data"""
    industry: str
    region: str
    size: str
    uploaded_image_url: Optional[str] = None
    description: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate business info fields"""
        if not all([self.industry, self.region, self.size]):
            return False
        
        # Basic validation for industry, region, size
        valid_industries = [
            "restaurant", "retail", "service", "healthcare", "education", 
            "technology", "manufacturing", "construction", "finance", "other"
        ]
        valid_regions = [
            "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", 
            "ulsan", "gyeonggi", "gangwon", "chungbuk", "chungnam", 
            "jeonbuk", "jeonnam", "gyeongbuk", "gyeongnam", "jeju"
        ]
        valid_sizes = ["small", "medium", "large"]
        
        return (
            self.industry.lower() in valid_industries and
            self.region.lower() in valid_regions and
            self.size.lower() in valid_sizes
        )


@dataclass
class AnalysisResult:
    """Business analysis result data"""
    summary: str
    score: float
    insights: List[str] = field(default_factory=list)
    market_trends: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def validate(self) -> bool:
        """Validate analysis result"""
        return (
            bool(self.summary) and
            0 <= self.score <= 100 and
            len(self.insights) > 0
        )


@dataclass
class NameSuggestion:
    """Business name suggestion data"""
    name: str
    description: str
    pronunciation_score: float
    search_score: float
    overall_score: float
    
    def validate(self) -> bool:
        """Validate name suggestion"""
        return (
            bool(self.name) and
            bool(self.description) and
            0 <= self.pronunciation_score <= 100 and
            0 <= self.search_score <= 100 and
            0 <= self.overall_score <= 100
        )


@dataclass
class BusinessNames:
    """Business names data with regeneration tracking"""
    suggestions: List[NameSuggestion] = field(default_factory=list)
    selected_name: Optional[str] = None
    regeneration_count: int = 0
    max_regenerations: int = 3
    
    def can_regenerate(self) -> bool:
        """Check if regeneration is allowed"""
        return self.regeneration_count < self.max_regenerations
    
    def add_regeneration(self) -> None:
        """Increment regeneration count"""
        if self.can_regenerate():
            self.regeneration_count += 1
    
    def validate(self) -> bool:
        """Validate business names data"""
        return (
            len(self.suggestions) <= 3 and
            all(suggestion.validate() for suggestion in self.suggestions) and
            0 <= self.regeneration_count <= self.max_regenerations
        )


@dataclass
class ImageResult:
    """Image generation result data"""
    url: str
    provider: str  # dalle, sdxl, gemini
    style: str
    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_fallback: bool = False
    
    def validate(self) -> bool:
        """Validate image result"""
        valid_providers = ["dalle", "sdxl", "gemini"]
        return (
            bool(self.url) and
            self.provider in valid_providers and
            bool(self.style) and
            bool(self.prompt)
        )


@dataclass
class SignboardImages:
    """Signboard images collection"""
    images: List[ImageResult] = field(default_factory=list)
    selected_image_url: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate signboard images"""
        return (
            len(self.images) <= 3 and
            all(image.validate() for image in self.images)
        )


@dataclass
class InteriorImages:
    """Interior images collection"""
    images: List[ImageResult] = field(default_factory=list)
    selected_image_url: Optional[str] = None
    budget_range: Optional[str] = None
    color_palette: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate interior images"""
        return (
            len(self.images) <= 3 and
            all(image.validate() for image in self.images)
        )


@dataclass
class AgentLog:
    """Agent execution log entry"""
    agent: str
    tool: str
    latency_ms: int
    status: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate agent log entry"""
        valid_agents = [agent.value for agent in AgentType]
        valid_statuses = ["success", "error", "timeout", "retry"]
        return (
            self.agent in valid_agents and
            bool(self.tool) and
            self.latency_ms >= 0 and
            self.status in valid_statuses
        )


@dataclass
class WorkflowSession:
    """Main workflow session data model"""
    session_id: str
    current_step: int
    status: str
    created_at: str
    updated_at: str
    ttl: int
    
    # Workflow data
    business_info: Optional[BusinessInfo] = None
    analysis_result: Optional[AnalysisResult] = None
    business_names: Optional[BusinessNames] = None
    signboard_images: Optional[SignboardImages] = None
    interior_images: Optional[InteriorImages] = None
    pdf_report_path: Optional[str] = None
    
    # Agent tracking
    agent_logs: List[AgentLog] = field(default_factory=list)
    current_agent: Optional[str] = None
    
    # Step Functions tracking
    express_execution_arn: Optional[str] = None
    standard_execution_arn: Optional[str] = None
    
    @classmethod
    def create_new(cls, business_info: BusinessInfo) -> 'WorkflowSession':
        """Create a new workflow session"""
        now = datetime.utcnow()
        session_id = str(uuid.uuid4())
        
        return cls(
            session_id=session_id,
            current_step=WorkflowStep.ANALYSIS.value,
            status=SessionStatus.ACTIVE.value,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            ttl=int((now + timedelta(hours=24)).timestamp()),
            business_info=business_info,
            business_names=BusinessNames(),
            signboard_images=SignboardImages(),
            interior_images=InteriorImages()
        )
    
    def update_step(self, step: WorkflowStep) -> None:
        """Update current workflow step"""
        self.current_step = step.value
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_agent_log(self, agent_log: AgentLog) -> None:
        """Add agent execution log"""
        if agent_log.validate():
            self.agent_logs.append(agent_log)
            self.current_agent = agent_log.agent
            self.updated_at = datetime.utcnow().isoformat()
    
    def mark_completed(self) -> None:
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED.value
        self.current_step = WorkflowStep.REPORT.value
        self.updated_at = datetime.utcnow().isoformat()
    
    def mark_failed(self, error_message: str = None) -> None:
        """Mark session as failed"""
        self.status = SessionStatus.FAILED.value
        self.updated_at = datetime.utcnow().isoformat()
        
        if error_message:
            error_log = AgentLog(
                agent=self.current_agent or AgentType.SUPERVISOR.value,
                tool="session_management",
                latency_ms=0,
                status="error",
                error_message=error_message
            )
            self.add_agent_log(error_log)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow().timestamp() > self.ttl
    
    def validate(self) -> bool:
        """Validate session data"""
        # Basic field validation
        if not all([self.session_id, self.current_step, self.status]):
            return False
        
        # Step validation
        if not (1 <= self.current_step <= 5):
            return False
        
        # Status validation
        valid_statuses = [status.value for status in SessionStatus]
        if self.status not in valid_statuses:
            return False
        
        # Business info validation (required for step 1+)
        if self.current_step >= 1 and self.business_info:
            if not self.business_info.validate():
                return False
        
        # Analysis result validation (required for step 2+)
        if self.current_step >= 2 and self.analysis_result:
            if not self.analysis_result.validate():
                return False
        
        # Business names validation (required for step 3+)
        if self.current_step >= 3 and self.business_names:
            if not self.business_names.validate():
                return False
        
        # Signboard images validation (required for step 4+)
        if self.current_step >= 4 and self.signboard_images:
            if not self.signboard_images.validate():
                return False
        
        # Interior images validation (required for step 5)
        if self.current_step >= 5 and self.interior_images:
            if not self.interior_images.validate():
                return False
        
        # Agent logs validation
        if not all(log.validate() for log in self.agent_logs):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage"""
        data = asdict(self)
        
        # Convert nested objects to JSON strings for DynamoDB
        if self.business_info:
            data['business_info'] = json.dumps(asdict(self.business_info))
        
        if self.analysis_result:
            data['analysis_result'] = json.dumps(asdict(self.analysis_result))
        
        if self.business_names:
            data['business_names'] = json.dumps(asdict(self.business_names))
        
        if self.signboard_images:
            data['signboard_images'] = json.dumps(asdict(self.signboard_images))
        
        if self.interior_images:
            data['interior_images'] = json.dumps(asdict(self.interior_images))
        
        if self.agent_logs:
            data['agent_logs'] = json.dumps([asdict(log) for log in self.agent_logs])
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowSession':
        """Create from dictionary (DynamoDB item)"""
        # Parse nested JSON fields
        if 'business_info' in data and isinstance(data['business_info'], str):
            business_info_data = json.loads(data['business_info'])
            data['business_info'] = BusinessInfo(**business_info_data)
        
        if 'analysis_result' in data and isinstance(data['analysis_result'], str):
            analysis_data = json.loads(data['analysis_result'])
            data['analysis_result'] = AnalysisResult(**analysis_data)
        
        if 'business_names' in data and isinstance(data['business_names'], str):
            names_data = json.loads(data['business_names'])
            suggestions = [NameSuggestion(**s) for s in names_data.get('suggestions', [])]
            names_data['suggestions'] = suggestions
            data['business_names'] = BusinessNames(**names_data)
        
        if 'signboard_images' in data and isinstance(data['signboard_images'], str):
            signboard_data = json.loads(data['signboard_images'])
            images = [ImageResult(**img) for img in signboard_data.get('images', [])]
            signboard_data['images'] = images
            data['signboard_images'] = SignboardImages(**signboard_data)
        
        if 'interior_images' in data and isinstance(data['interior_images'], str):
            interior_data = json.loads(data['interior_images'])
            images = [ImageResult(**img) for img in interior_data.get('images', [])]
            interior_data['images'] = images
            data['interior_images'] = InteriorImages(**interior_data)
        
        if 'agent_logs' in data and isinstance(data['agent_logs'], str):
            logs_data = json.loads(data['agent_logs'])
            data['agent_logs'] = [AgentLog(**log) for log in logs_data]
        
        return cls(**data)


# Utility functions for session management
def create_session_id() -> str:
    """Generate a new session ID"""
    return str(uuid.uuid4())


def calculate_ttl(hours: int = 24) -> int:
    """Calculate TTL timestamp for session expiration"""
    return int((datetime.utcnow() + timedelta(hours=hours)).timestamp())


def is_session_expired(ttl: int) -> bool:
    """Check if session TTL has expired"""
    return datetime.utcnow().timestamp() > ttl


def validate_workflow_step_transition(current_step: int, target_step: int) -> bool:
    """Validate if step transition is allowed"""
    # Can only move forward one step at a time, or stay on same step
    return target_step == current_step or target_step == current_step + 1