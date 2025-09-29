"""
Unit tests for session data models
Tests session creation, validation, and state management
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambda'))

from shared.models import (
    WorkflowSession, BusinessInfo, AnalysisResult, NameSuggestion, 
    BusinessNames, ImageResult, SignboardImages, InteriorImages,
    AgentLog, WorkflowStep, SessionStatus, AgentType,
    create_session_id, calculate_ttl, is_session_expired,
    validate_workflow_step_transition
)


class TestBusinessInfo:
    """Test BusinessInfo model"""
    
    def test_valid_business_info(self):
        """Test valid business info creation and validation"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small",
            description="Korean BBQ restaurant"
        )
        
        assert business_info.validate() is True
        assert business_info.industry == "restaurant"
        assert business_info.region == "seoul"
        assert business_info.size == "small"
    
    def test_invalid_business_info(self):
        """Test invalid business info validation"""
        # Missing required fields
        business_info = BusinessInfo(
            industry="",
            region="seoul",
            size="small"
        )
        assert business_info.validate() is False
        
        # Invalid industry
        business_info = BusinessInfo(
            industry="invalid_industry",
            region="seoul", 
            size="small"
        )
        assert business_info.validate() is False
        
        # Invalid region
        business_info = BusinessInfo(
            industry="restaurant",
            region="invalid_region",
            size="small"
        )
        assert business_info.validate() is False
        
        # Invalid size
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="invalid_size"
        )
        assert business_info.validate() is False


class TestAnalysisResult:
    """Test AnalysisResult model"""
    
    def test_valid_analysis_result(self):
        """Test valid analysis result creation"""
        analysis = AnalysisResult(
            summary="Great business potential in Seoul restaurant market",
            score=85.5,
            insights=["High foot traffic area", "Growing food delivery market"],
            market_trends=["Korean BBQ popularity increasing"],
            recommendations=["Focus on authentic flavors", "Optimize for delivery"]
        )
        
        assert analysis.validate() is True
        assert analysis.score == 85.5
        assert len(analysis.insights) == 2
        assert analysis.generated_at is not None
    
    def test_invalid_analysis_result(self):
        """Test invalid analysis result validation"""
        # Empty summary
        analysis = AnalysisResult(
            summary="",
            score=85.5,
            insights=["Some insight"]
        )
        assert analysis.validate() is False
        
        # Invalid score range
        analysis = AnalysisResult(
            summary="Valid summary",
            score=150,  # > 100
            insights=["Some insight"]
        )
        assert analysis.validate() is False
        
        # No insights
        analysis = AnalysisResult(
            summary="Valid summary",
            score=85.5,
            insights=[]
        )
        assert analysis.validate() is False


class TestNameSuggestion:
    """Test NameSuggestion model"""
    
    def test_valid_name_suggestion(self):
        """Test valid name suggestion creation"""
        suggestion = NameSuggestion(
            name="맛있는집",
            description="Delicious Korean restaurant name",
            pronunciation_score=90.0,
            search_score=85.0,
            overall_score=87.5
        )
        
        assert suggestion.validate() is True
        assert suggestion.name == "맛있는집"
        assert suggestion.overall_score == 87.5
    
    def test_invalid_name_suggestion(self):
        """Test invalid name suggestion validation"""
        # Empty name
        suggestion = NameSuggestion(
            name="",
            description="Valid description",
            pronunciation_score=90.0,
            search_score=85.0,
            overall_score=87.5
        )
        assert suggestion.validate() is False
        
        # Invalid score range
        suggestion = NameSuggestion(
            name="Valid name",
            description="Valid description",
            pronunciation_score=150.0,  # > 100
            search_score=85.0,
            overall_score=87.5
        )
        assert suggestion.validate() is False


class TestBusinessNames:
    """Test BusinessNames model"""
    
    def test_regeneration_logic(self):
        """Test regeneration count and limits"""
        names = BusinessNames(max_regenerations=3)
        
        # Initial state
        assert names.can_regenerate() is True
        assert names.regeneration_count == 0
        
        # Add regenerations
        names.add_regeneration()
        assert names.regeneration_count == 1
        assert names.can_regenerate() is True
        
        names.add_regeneration()
        names.add_regeneration()
        assert names.regeneration_count == 3
        assert names.can_regenerate() is False
        
        # Should not increment beyond max
        names.add_regeneration()
        assert names.regeneration_count == 3
    
    def test_validation_with_suggestions(self):
        """Test validation with name suggestions"""
        suggestion1 = NameSuggestion(
            name="맛있는집",
            description="Delicious restaurant",
            pronunciation_score=90.0,
            search_score=85.0,
            overall_score=87.5
        )
        
        suggestion2 = NameSuggestion(
            name="행복한식당",
            description="Happy restaurant",
            pronunciation_score=88.0,
            search_score=82.0,
            overall_score=85.0
        )
        
        names = BusinessNames(
            suggestions=[suggestion1, suggestion2],
            regeneration_count=1
        )
        
        assert names.validate() is True
        assert len(names.suggestions) == 2


class TestImageResult:
    """Test ImageResult model"""
    
    def test_valid_image_result(self):
        """Test valid image result creation"""
        image = ImageResult(
            url="https://example.com/image.jpg",
            provider="dalle",
            style="modern",
            prompt="Modern Korean restaurant signboard",
            metadata={"resolution": "1024x1024"}
        )
        
        assert image.validate() is True
        assert image.provider == "dalle"
        assert image.is_fallback is False
        assert image.generated_at is not None
    
    def test_invalid_image_result(self):
        """Test invalid image result validation"""
        # Invalid provider
        image = ImageResult(
            url="https://example.com/image.jpg",
            provider="invalid_provider",
            style="modern",
            prompt="Valid prompt"
        )
        assert image.validate() is False
        
        # Empty URL
        image = ImageResult(
            url="",
            provider="dalle",
            style="modern",
            prompt="Valid prompt"
        )
        assert image.validate() is False


class TestAgentLog:
    """Test AgentLog model"""
    
    def test_valid_agent_log(self):
        """Test valid agent log creation"""
        log = AgentLog(
            agent="product_insight",
            tool="kb.search",
            latency_ms=1500,
            status="success",
            metadata={"query": "restaurant analysis"}
        )
        
        assert log.validate() is True
        assert log.agent == "product_insight"
        assert log.latency_ms == 1500
        assert log.timestamp is not None
    
    def test_invalid_agent_log(self):
        """Test invalid agent log validation"""
        # Invalid agent
        log = AgentLog(
            agent="invalid_agent",
            tool="kb.search",
            latency_ms=1500,
            status="success"
        )
        assert log.validate() is False
        
        # Invalid status
        log = AgentLog(
            agent="product_insight",
            tool="kb.search",
            latency_ms=1500,
            status="invalid_status"
        )
        assert log.validate() is False
        
        # Negative latency
        log = AgentLog(
            agent="product_insight",
            tool="kb.search",
            latency_ms=-100,
            status="success"
        )
        assert log.validate() is False


class TestWorkflowSession:
    """Test WorkflowSession model"""
    
    def test_create_new_session(self):
        """Test creating a new workflow session"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        
        assert session.session_id is not None
        assert session.current_step == WorkflowStep.ANALYSIS.value
        assert session.status == SessionStatus.ACTIVE.value
        assert session.business_info == business_info
        assert session.created_at is not None
        assert session.updated_at is not None
        assert session.ttl > 0
        assert session.validate() is True
    
    def test_session_step_updates(self):
        """Test session step updates"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul", 
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        original_updated_at = session.updated_at
        
        # Update to naming step
        session.update_step(WorkflowStep.NAMING)
        assert session.current_step == WorkflowStep.NAMING.value
        assert session.updated_at != original_updated_at
    
    def test_agent_log_tracking(self):
        """Test agent log addition and tracking"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        
        # Add agent log
        log = AgentLog(
            agent="product_insight",
            tool="kb.search",
            latency_ms=1500,
            status="success"
        )
        
        session.add_agent_log(log)
        
        assert len(session.agent_logs) == 1
        assert session.current_agent == "product_insight"
        assert session.agent_logs[0].agent == "product_insight"
    
    def test_session_completion(self):
        """Test session completion"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        session.mark_completed()
        
        assert session.status == SessionStatus.COMPLETED.value
        assert session.current_step == WorkflowStep.REPORT.value
    
    def test_session_failure(self):
        """Test session failure handling"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        error_message = "Analysis failed due to timeout"
        
        session.mark_failed(error_message)
        
        assert session.status == SessionStatus.FAILED.value
        # The mark_failed method should add an agent log when error_message is provided
        assert len(session.agent_logs) == 1
        assert session.agent_logs[0].status == "error"
        assert session.agent_logs[0].error_message == error_message
        assert session.agent_logs[0].agent == AgentType.SUPERVISOR.value  # Since current_agent is None initially
    
    def test_session_expiration(self):
        """Test session expiration logic"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        
        # Should not be expired initially
        assert session.is_expired() is False
        
        # Set TTL to past time
        session.ttl = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        assert session.is_expired() is True
    
    def test_session_serialization(self):
        """Test session to_dict and from_dict conversion"""
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        # Create session with some data
        session = WorkflowSession.create_new(business_info)
        
        analysis = AnalysisResult(
            summary="Good potential",
            score=85.0,
            insights=["High traffic area"]
        )
        session.analysis_result = analysis
        
        log = AgentLog(
            agent="product_insight",
            tool="kb.search",
            latency_ms=1500,
            status="success"
        )
        session.add_agent_log(log)
        
        # Convert to dict
        session_dict = session.to_dict()
        
        assert isinstance(session_dict, dict)
        assert session_dict['session_id'] == session.session_id
        assert isinstance(session_dict['business_info'], str)  # Should be JSON string
        assert isinstance(session_dict['analysis_result'], str)  # Should be JSON string
        assert isinstance(session_dict['agent_logs'], str)  # Should be JSON string
        
        # Convert back from dict
        restored_session = WorkflowSession.from_dict(session_dict)
        
        assert restored_session.session_id == session.session_id
        assert restored_session.business_info.industry == business_info.industry
        assert restored_session.analysis_result.summary == analysis.summary
        assert len(restored_session.agent_logs) == 1
        assert restored_session.agent_logs[0].agent == "product_insight"
        assert restored_session.validate() is True


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_session_id(self):
        """Test session ID generation"""
        session_id1 = create_session_id()
        session_id2 = create_session_id()
        
        assert session_id1 != session_id2
        assert len(session_id1) == 36  # UUID4 format
        assert '-' in session_id1
    
    def test_calculate_ttl(self):
        """Test TTL calculation"""
        ttl_24h = calculate_ttl(24)
        ttl_1h = calculate_ttl(1)
        
        assert ttl_24h > ttl_1h
        assert ttl_24h > datetime.utcnow().timestamp()
    
    def test_is_session_expired(self):
        """Test session expiration check"""
        # Future TTL
        future_ttl = calculate_ttl(1)
        assert is_session_expired(future_ttl) is False
        
        # Past TTL
        past_ttl = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        assert is_session_expired(past_ttl) is True
    
    def test_validate_workflow_step_transition(self):
        """Test workflow step transition validation"""
        # Valid transitions
        assert validate_workflow_step_transition(1, 1) is True  # Stay on same step
        assert validate_workflow_step_transition(1, 2) is True  # Move forward one step
        assert validate_workflow_step_transition(3, 4) is True  # Move forward one step
        assert validate_workflow_step_transition(5, 6) is True  # The function allows any forward step
        
        # Invalid transitions
        assert validate_workflow_step_transition(1, 3) is False  # Skip steps
        assert validate_workflow_step_transition(3, 1) is False  # Move backward


if __name__ == "__main__":
    pytest.main([__file__, "-v"])