#!/usr/bin/env python3
"""
Simple validation script for Task 23: Workflow State Management Enhancement

This script validates the WorkflowSession model enhancements without requiring
full BaseAgent initialization.

Requirements: 4.4, 4.6
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
shared_path = os.path.join(project_root, 'src', 'lambda', 'shared')

sys.path.insert(0, shared_path)

try:
    from models import WorkflowSession, BusinessInfo, SessionStatus, AgentType
    print("✓ Successfully imported models")
except ImportError as e:
    print(f"✗ Failed to import models: {e}")
    sys.exit(1)


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_session_status_enum():
    """Test SessionStatus enum has PAUSED status"""
    print_section("Test 1: SessionStatus Enum")
    
    try:
        # Verify PAUSED status exists
        assert hasattr(SessionStatus, 'PAUSED'), "SessionStatus should have PAUSED"
        assert SessionStatus.PAUSED.value == 'paused', "PAUSED value should be 'paused'"
        
        print(f"✓ SessionStatus.PAUSED exists")
        print(f"  Value: {SessionStatus.PAUSED.value}")
        
        # Verify all expected statuses
        expected_statuses = ['ACTIVE', 'PAUSED', 'COMPLETED', 'FAILED', 'EXPIRED']
        for status in expected_statuses:
            assert hasattr(SessionStatus, status), f"SessionStatus should have {status}"
            print(f"✓ SessionStatus.{status} exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_session_fields():
    """Test WorkflowSession has new pause/resume fields"""
    print_section("Test 2: WorkflowSession New Fields")
    
    try:
        # Create test session
        business_info = BusinessInfo(
            industry="restaurant",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        
        # Verify new fields exist
        assert hasattr(session, 'pause_reason'), "Session should have pause_reason field"
        assert hasattr(session, 'paused_at'), "Session should have paused_at field"
        assert hasattr(session, 'resume_count'), "Session should have resume_count field"
        assert hasattr(session, 'intermediate_results'), "Session should have intermediate_results field"
        
        print(f"✓ All new fields exist")
        print(f"  pause_reason: {session.pause_reason}")
        print(f"  paused_at: {session.paused_at}")
        print(f"  resume_count: {session.resume_count}")
        print(f"  intermediate_results: {session.intermediate_results}")
        
        # Verify initial values
        assert session.pause_reason is None, "pause_reason should be None initially"
        assert session.paused_at is None, "paused_at should be None initially"
        assert session.resume_count == 0, "resume_count should be 0 initially"
        assert isinstance(session.intermediate_results, dict), "intermediate_results should be dict"
        assert len(session.intermediate_results) == 0, "intermediate_results should be empty initially"
        
        print(f"✓ Initial values are correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pause_method():
    """Test WorkflowSession.pause() method"""
    print_section("Test 3: WorkflowSession.pause() Method")
    
    try:
        # Create test session
        business_info = BusinessInfo(
            industry="retail",
            region="busan",
            size="medium"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        print(f"  Initial status: {session.status}")
        
        # Test pause
        pause_reason = "low_confidence_score"
        session.pause(pause_reason)
        
        assert session.status == SessionStatus.PAUSED.value, "Session should be paused"
        assert session.pause_reason == pause_reason, "Pause reason should be set"
        assert session.paused_at is not None, "Paused timestamp should be set"
        assert session.is_paused(), "is_paused() should return True"
        
        print(f"✓ Session paused successfully")
        print(f"  Status: {session.status}")
        print(f"  Pause reason: {session.pause_reason}")
        print(f"  Paused at: {session.paused_at}")
        print(f"  is_paused(): {session.is_paused()}")
        
        # Verify agent log was added
        assert len(session.agent_logs) > 0, "Agent log should be added"
        last_log = session.agent_logs[-1]
        assert last_log.tool == 'workflow_pause', "Last log should be workflow_pause"
        assert last_log.status == 'success', "Pause log should be success"
        
        print(f"✓ Pause event logged correctly")
        print(f"  Log tool: {last_log.tool}")
        print(f"  Log status: {last_log.status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_method():
    """Test WorkflowSession.resume() method"""
    print_section("Test 4: WorkflowSession.resume() Method")
    
    try:
        # Create and pause session
        business_info = BusinessInfo(
            industry="service",
            region="daegu",
            size="large"
        )
        
        session = WorkflowSession.create_new(business_info)
        session.pause("human_review_required")
        
        print(f"✓ Created and paused session: {session.session_id}")
        print(f"  Status before resume: {session.status}")
        print(f"  Resume count before: {session.resume_count}")
        
        # Wait a moment to test pause duration
        time.sleep(1)
        
        # Test resume
        initial_resume_count = session.resume_count
        session.resume()
        
        assert session.status == SessionStatus.ACTIVE.value, "Session should be active"
        assert session.resume_count == initial_resume_count + 1, "Resume count should increment"
        assert not session.is_paused(), "is_paused() should return False"
        
        print(f"✓ Session resumed successfully")
        print(f"  Status after resume: {session.status}")
        print(f"  Resume count after: {session.resume_count}")
        print(f"  is_paused(): {session.is_paused()}")
        
        # Verify agent log was added
        last_log = session.agent_logs[-1]
        assert last_log.tool == 'workflow_resume', "Last log should be workflow_resume"
        assert last_log.status == 'success', "Resume log should be success"
        assert 'resume_count' in last_log.metadata, "Resume log should have resume_count"
        assert 'paused_duration_seconds' in last_log.metadata, "Resume log should have duration"
        
        print(f"✓ Resume event logged correctly")
        print(f"  Log tool: {last_log.tool}")
        print(f"  Resume count in log: {last_log.metadata['resume_count']}")
        print(f"  Pause duration: {last_log.metadata['paused_duration_seconds']}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_pause_resume_cycles():
    """Test multiple pause/resume cycles"""
    print_section("Test 5: Multiple Pause/Resume Cycles")
    
    try:
        # Create session
        business_info = BusinessInfo(
            industry="technology",
            region="seoul",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        
        # Test multiple cycles
        num_cycles = 3
        for i in range(1, num_cycles + 1):
            session.pause(f"test_pause_{i}")
            assert session.is_paused(), f"Should be paused in cycle {i}"
            
            session.resume()
            assert not session.is_paused(), f"Should be active in cycle {i}"
            assert session.resume_count == i, f"Resume count should be {i}"
            
            print(f"✓ Cycle {i} completed (resume_count={session.resume_count})")
        
        assert session.resume_count == num_cycles, f"Final resume count should be {num_cycles}"
        print(f"✓ All {num_cycles} cycles completed successfully")
        print(f"  Final resume count: {session.resume_count}")
        print(f"  Final status: {session.status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_intermediate_results():
    """Test intermediate result storage"""
    print_section("Test 6: Intermediate Result Storage")
    
    try:
        # Create session
        business_info = BusinessInfo(
            industry="healthcare",
            region="incheon",
            size="medium"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        
        # Save intermediate results
        test_results = {
            'analysis': {
                'score': 85,
                'insights': ['Good location', 'High competition']
            },
            'naming': {
                'suggestions': ['HealthHub', 'CareCenter', 'MediPro'],
                'selected': 'HealthHub'
            },
            'signboard': {
                'images': ['url1', 'url2', 'url3'],
                'selected': 'url1'
            }
        }
        
        for step_name, result in test_results.items():
            session.save_intermediate_result(step_name, result)
            print(f"✓ Saved intermediate result for: {step_name}")
        
        # Verify storage
        assert len(session.intermediate_results) == 3, "Should have 3 intermediate results"
        print(f"✓ All intermediate results stored: {len(session.intermediate_results)} steps")
        
        # Retrieve and verify
        for step_name, expected_result in test_results.items():
            retrieved = session.get_intermediate_result(step_name)
            assert retrieved == expected_result, f"Retrieved result should match for {step_name}"
            print(f"✓ Retrieved and verified: {step_name}")
        
        # Test retrieval of non-existent step
        non_existent = session.get_intermediate_result('non_existent_step')
        assert non_existent is None, "Non-existent step should return None"
        print(f"✓ Non-existent step returns None correctly")
        
        # Verify metadata
        for step_name in test_results.keys():
            result_data = session.intermediate_results[step_name]
            assert 'data' in result_data, f"{step_name} should have 'data' field"
            assert 'saved_at' in result_data, f"{step_name} should have 'saved_at' field"
            assert 'step_number' in result_data, f"{step_name} should have 'step_number' field"
            print(f"✓ Metadata verified for: {step_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pause_with_intermediate_results():
    """Test pause preserves intermediate results"""
    print_section("Test 7: Pause Preserves Intermediate Results")
    
    try:
        # Create session
        business_info = BusinessInfo(
            industry="education",
            region="gwangju",
            size="large"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        
        # Add intermediate results
        session.save_intermediate_result('analysis', {'score': 90})
        session.save_intermediate_result('naming', {'selected': 'EduPro'})
        print(f"✓ Added 2 intermediate results")
        
        # Pause workflow
        session.pause("human_review_required")
        print(f"✓ Workflow paused")
        
        # Verify intermediate results are preserved
        assert len(session.intermediate_results) == 2, "Intermediate results should be preserved"
        assert session.get_intermediate_result('analysis') is not None
        assert session.get_intermediate_result('naming') is not None
        print(f"✓ Intermediate results preserved during pause")
        
        # Resume workflow
        session.resume()
        print(f"✓ Workflow resumed")
        
        # Verify intermediate results still available
        analysis_result = session.get_intermediate_result('analysis')
        naming_result = session.get_intermediate_result('naming')
        
        assert analysis_result == {'score': 90}, "Analysis result should be intact"
        assert naming_result == {'selected': 'EduPro'}, "Naming result should be intact"
        print(f"✓ Intermediate results intact after resume")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_error_handling():
    """Test resume error handling for non-paused sessions"""
    print_section("Test 8: Resume Error Handling")
    
    try:
        # Create active session
        business_info = BusinessInfo(
            industry="finance",
            region="daejeon",
            size="small"
        )
        
        session = WorkflowSession.create_new(business_info)
        print(f"✓ Created test session: {session.session_id}")
        print(f"  Status: {session.status} (should be active)")
        
        # Try to resume non-paused session
        try:
            session.resume()
            print(f"✗ Should have raised ValueError")
            return False
        except ValueError as e:
            expected_msg = "Cannot resume session with status:"
            assert expected_msg in str(e), f"Error message should contain '{expected_msg}'"
            print(f"✓ Correctly raised ValueError for non-paused session")
            print(f"  Error message: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("  Task 23: Workflow State Management Validation")
    print("  Requirements: 4.4, 4.6")
    print("="*60)
    
    tests = [
        ("SessionStatus Enum", test_session_status_enum),
        ("WorkflowSession New Fields", test_workflow_session_fields),
        ("Pause Method", test_pause_method),
        ("Resume Method", test_resume_method),
        ("Multiple Pause/Resume Cycles", test_multiple_pause_resume_cycles),
        ("Intermediate Result Storage", test_intermediate_results),
        ("Pause Preserves Intermediate Results", test_pause_with_intermediate_results),
        ("Resume Error Handling", test_resume_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("✓ All validation tests passed!")
        print("\nTask 23 Implementation Complete:")
        print("  ✓ SessionStatus.PAUSED enum added")
        print("  ✓ WorkflowSession pause/resume methods")
        print("  ✓ Intermediate result storage and retrieval")
        print("  ✓ Resume counter tracking")
        print("  ✓ Pause duration calculation")
        print("  ✓ Agent log integration")
        print("  ✓ Error handling for invalid states")
        print("  ✓ Requirements 4.4 and 4.6 satisfied")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
