#!/usr/bin/env python3
"""
Test runner for session models
Runs basic validation tests for data models
"""

import sys
import os
sys.path.append('src/lambda')

from shared.models import (
    WorkflowSession, BusinessInfo, AnalysisResult, NameSuggestion, 
    BusinessNames, ImageResult, SignboardImages, InteriorImages,
    AgentLog, WorkflowStep, SessionStatus, AgentType,
    create_session_id, calculate_ttl, is_session_expired,
    validate_workflow_step_transition
)


def test_business_info():
    """Test BusinessInfo model"""
    print("Testing BusinessInfo...")
    
    # Valid business info
    business_info = BusinessInfo(
        industry="restaurant",
        region="seoul",
        size="small",
        description="Korean BBQ restaurant"
    )
    
    assert business_info.validate() is True
    print("✓ Valid business info validation passed")
    
    # Invalid business info
    invalid_business_info = BusinessInfo(
        industry="invalid_industry",
        region="seoul",
        size="small"
    )
    assert invalid_business_info.validate() is False
    print("✓ Invalid business info validation passed")


def test_workflow_session():
    """Test WorkflowSession model"""
    print("Testing WorkflowSession...")
    
    business_info = BusinessInfo(
        industry="restaurant",
        region="seoul",
        size="small"
    )
    
    # Create new session
    session = WorkflowSession.create_new(business_info)
    
    assert session.session_id is not None
    assert session.current_step == WorkflowStep.ANALYSIS.value
    assert session.status == SessionStatus.ACTIVE.value
    assert session.business_info == business_info
    assert session.validate() is True
    print("✓ WorkflowSession creation passed")
    
    # Test step updates
    original_updated_at = session.updated_at
    session.update_step(WorkflowStep.NAMING)
    assert session.current_step == WorkflowStep.NAMING.value
    assert session.updated_at != original_updated_at
    print("✓ WorkflowSession step update passed")
    
    # Test agent log addition
    log = AgentLog(
        agent="product_insight",
        tool="kb.search",
        latency_ms=1500,
        status="success"
    )
    
    session.add_agent_log(log)
    assert len(session.agent_logs) == 1
    assert session.current_agent == "product_insight"
    print("✓ WorkflowSession agent log addition passed")
    
    # Test completion
    session.mark_completed()
    assert session.status == SessionStatus.COMPLETED.value
    assert session.current_step == WorkflowStep.REPORT.value
    print("✓ WorkflowSession completion passed")


def test_session_serialization():
    """Test session serialization"""
    print("Testing session serialization...")
    
    business_info = BusinessInfo(
        industry="restaurant",
        region="seoul",
        size="small"
    )
    
    # Create session with data
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
    print("✓ Session to_dict conversion passed")
    
    # Convert back from dict
    restored_session = WorkflowSession.from_dict(session_dict)
    
    assert restored_session.session_id == session.session_id
    assert restored_session.business_info.industry == business_info.industry
    assert restored_session.analysis_result.summary == analysis.summary
    assert len(restored_session.agent_logs) == 1
    assert restored_session.validate() is True
    print("✓ Session from_dict conversion passed")


def main():
    """Run all tests"""
    print("Running session model tests...\n")
    
    try:
        test_business_info()
        test_workflow_session()
        test_session_serialization()
        
        print("\n✅ All session model tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())