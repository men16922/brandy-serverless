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
    PAUSED = "paused"  # NEW: Session paused for review or intervention
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
class ReasoningStep:
    """Reasoning step for Chain-of-Thought tracking"""
    step_number: int
    agent_name: str
    timestamp: str
    operation: str  # 'decision', 'evaluation', 'ranking', 'synthesis'
    input_data: Dict[str, Any]
    reasoning: str
    decision: Any
    confidence: float
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    latency_ms: int = 0
    
    def validate(self) -> bool:
        """Validate reasoning step"""
        return (
            self.step_number > 0 and
            bool(self.agent_name) and
            bool(self.timestamp) and
            bool(self.operation) and
            0.0 <= self.confidence <= 1.0 and
            self.latency_ms >= 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DynamoDB storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningStep':
        """Create from dictionary (DynamoDB item)"""
        return cls(**data)


@dataclass
class BusinessInfo:
    """Business information input data"""
    industry: str
    region: str
    size: str
    description: Optional[str] = None
    country: Optional[str] = None  # New field for country
    city: Optional[str] = None     # New field for city
    
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
        
        # Region validation is now flexible - can be city, region, or "city, country" format
        # This allows backward compatibility with old format and new country/city fields
        return (
            self.industry.lower() in valid_industries and
            self.size.lower() in valid_sizes and
            bool(self.region)  # Just check region is not empty
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class NameSuggestion:
    """Business name suggestion data"""
    name: str
    description: str
    pronunciation_score: float
    memorability_score: float = 0.0
    relevance_score: float = 0.0
    search_score: float = 0.0
    overall_score: float = 0.0
    
    def validate(self) -> bool:
        """Validate name suggestion"""
        return (
            bool(self.name) and
            bool(self.description) and
            0 <= self.pronunciation_score <= 100 and
            0 <= self.memorability_score <= 100 and
            0 <= self.relevance_score <= 100 and
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
    error_message: Optional[str] = None  # Error message if generation failed
    generation_time_ms: Optional[int] = None  # Time taken to generate image
    retry_count: Optional[int] = None  # Number of retry attempts
    
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
    
    # Reasoning chain tracking (NEW for Hackathon)
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)
    
    # Step Functions tracking
    express_execution_arn: Optional[str] = None
    standard_execution_arn: Optional[str] = None
    
    # Pause/Resume tracking (NEW for Task 23 - Requirement 4.4, 4.6)
    pause_reason: Optional[str] = None
    paused_at: Optional[str] = None
    resume_count: int = 0
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    
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
    
    def add_reasoning_step(self, reasoning_step: ReasoningStep) -> None:
        """Add reasoning step to chain"""
        if reasoning_step.validate():
            self.reasoning_chain.append(reasoning_step)
            self.updated_at = datetime.utcnow().isoformat()
    
    def get_reasoning_chain(self) -> List[ReasoningStep]:
        """Get all reasoning steps"""
        return self.reasoning_chain
    
    def get_latest_reasoning(self) -> Optional[ReasoningStep]:
        """Get most recent reasoning step"""
        return self.reasoning_chain[-1] if self.reasoning_chain else None
    
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
    
    def pause(self, reason: str) -> None:
        """
        Pause workflow execution.
        
        This method implements Requirement 4.4:
        - Saves current state for later resumption
        - Records pause reason for transparency
        - Preserves all intermediate results
        
        Args:
            reason: Reason for pausing (e.g., 'low_confidence', 'human_review_required')
        """
        self.status = SessionStatus.PAUSED.value
        self.pause_reason = reason
        self.paused_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        
        # Log pause event
        pause_log = AgentLog(
            agent=self.current_agent or AgentType.SUPERVISOR.value,
            tool="workflow_pause",
            latency_ms=0,
            status="success",
            metadata={
                'pause_reason': reason,
                'current_step': self.current_step,
                'paused_at': self.paused_at
            }
        )
        self.add_agent_log(pause_log)
    
    def resume(self) -> None:
        """
        Resume paused workflow execution.
        
        This method implements Requirement 4.4:
        - Restores workflow from saved state
        - Increments resume counter for tracking
        - Clears pause metadata
        
        Returns:
            None
        
        Raises:
            ValueError: If session is not in PAUSED status
        """
        if self.status != SessionStatus.PAUSED.value:
            raise ValueError(f"Cannot resume session with status: {self.status}")
        
        self.status = SessionStatus.ACTIVE.value
        self.resume_count += 1
        self.updated_at = datetime.utcnow().isoformat()
        
        # Log resume event
        resume_log = AgentLog(
            agent=self.current_agent or AgentType.SUPERVISOR.value,
            tool="workflow_resume",
            latency_ms=0,
            status="success",
            metadata={
                'resume_count': self.resume_count,
                'previous_pause_reason': self.pause_reason,
                'paused_duration_seconds': self._calculate_pause_duration(),
                'current_step': self.current_step
            }
        )
        self.add_agent_log(resume_log)
        
        # Clear pause metadata (but keep for history in logs)
        # Note: We don't clear pause_reason to maintain audit trail
    
    def _calculate_pause_duration(self) -> Optional[int]:
        """Calculate duration of pause in seconds"""
        if not self.paused_at:
            return None
        
        try:
            paused_time = datetime.fromisoformat(self.paused_at.replace('Z', '+00:00'))
            now = datetime.utcnow()
            duration = (now - paused_time).total_seconds()
            return int(duration)
        except Exception:
            return None
    
    def save_intermediate_result(self, step_name: str, result: Any) -> None:
        """
        Save intermediate result for a workflow step.
        
        This method implements Requirement 4.4:
        - Stores intermediate results for recovery
        - Prevents data loss on failure
        - Enables step-by-step debugging
        
        Args:
            step_name: Name of the step (e.g., 'analysis', 'naming', 'signboard')
            result: Result data to save
        """
        self.intermediate_results[step_name] = {
            'data': result,
            'saved_at': datetime.utcnow().isoformat(),
            'step_number': self.current_step
        }
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_intermediate_result(self, step_name: str) -> Optional[Any]:
        """
        Retrieve intermediate result for a workflow step.
        
        Args:
            step_name: Name of the step
        
        Returns:
            Saved result data or None if not found
        """
        if step_name in self.intermediate_results:
            return self.intermediate_results[step_name].get('data')
        return None
    
    def is_paused(self) -> bool:
        """Check if session is paused"""
        return self.status == SessionStatus.PAUSED.value
    
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
        
        # Reasoning chain validation
        if not all(step.validate() for step in self.reasoning_chain):
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
        
        # Convert reasoning chain to JSON string for DynamoDB
        if self.reasoning_chain:
            data['reasoning_chain'] = json.dumps([asdict(step) for step in self.reasoning_chain])
        
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
        
        # Parse reasoning chain from JSON string
        if 'reasoning_chain' in data and isinstance(data['reasoning_chain'], str):
            reasoning_data = json.loads(data['reasoning_chain'])
            data['reasoning_chain'] = [ReasoningStep(**step) for step in reasoning_data]
        
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