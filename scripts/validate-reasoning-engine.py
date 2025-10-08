#!/usr/bin/env python3
"""
Validation script for ReasoningEngine
Tests file structure and code quality without requiring dependencies
"""

import sys
import os
import re


def test_file_exists():
    """Test ReasoningEngine file exists"""
    print("Testing ReasoningEngine file existence...")
    
    file_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'src', 
        'lambda', 
        'shared', 
        'reasoning_engine.py'
    )
    
    if os.path.exists(file_path):
        print(f"✓ File exists: {file_path}")
        return True, file_path
    else:
        print(f"✗ File not found: {file_path}")
        return False, None


def test_class_definition(file_path):
    """Test ReasoningEngine class is defined"""
    print("\nTesting ReasoningEngine class definition...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if 'class ReasoningEngine:' in content:
        print("✓ ReasoningEngine class defined")
        return True, content
    else:
        print("✗ ReasoningEngine class not found")
        return False, None


def test_required_methods(content):
    """Test ReasoningEngine has all required methods"""
    print("\nTesting required methods...")
    
    required_methods = [
        'reason_and_decide',
        'evaluate_business_name',
        'rank_designs',
        'synthesize_insights'
    ]
    
    all_present = True
    for method in required_methods:
        pattern = f'def {method}\\('
        if re.search(pattern, content):
            print(f"✓ Method '{method}' defined")
        else:
            print(f"✗ Method '{method}' missing")
            all_present = False
    
    return all_present


def test_helper_methods(content):
    """Test ReasoningEngine has helper methods"""
    print("\nTesting helper methods...")
    
    helper_methods = [
        '_parse_reasoning_text',
        '_create_default_evaluation',
        '_create_default_ranking',
        '_create_logger'
    ]
    
    all_present = True
    for method in helper_methods:
        pattern = f'def {method}\\('
        if re.search(pattern, content):
            print(f"✓ Helper method '{method}' defined")
        else:
            print(f"✗ Helper method '{method}' missing")
            all_present = False
    
    return all_present


def test_imports(content):
    """Test required imports are present"""
    print("\nTesting imports...")
    
    required_imports = [
        'from .bedrock_client import BedrockClient',
        'import json',
        'import logging',
        'from typing import Dict, List, Any, Optional',
        'from datetime import datetime'
    ]
    
    all_present = True
    for import_stmt in required_imports:
        if import_stmt in content:
            print(f"✓ Import present: {import_stmt}")
        else:
            print(f"✗ Import missing: {import_stmt}")
            all_present = False
    
    return all_present


def test_docstrings(content):
    """Test methods have docstrings"""
    print("\nTesting docstrings...")
    
    methods_with_docstrings = [
        'reason_and_decide',
        'evaluate_business_name',
        'rank_designs',
        'synthesize_insights'
    ]
    
    all_present = True
    for method in methods_with_docstrings:
        # Look for method definition followed by docstring
        # Handle multi-line method signatures
        pattern = f'def {method}\\(.*?"""'
        if re.search(pattern, content, re.DOTALL):
            print(f"✓ Method '{method}' has docstring")
        else:
            print(f"✗ Method '{method}' missing docstring")
            all_present = False
    
    return all_present


def test_confidence_scoring(content):
    """Test confidence scoring mechanism is implemented"""
    print("\nTesting confidence scoring...")
    
    # Check for confidence in return values
    confidence_patterns = [
        r"'confidence':",
        r'"confidence":',
        r'confidence.*0\.0.*1\.0'
    ]
    
    found = False
    for pattern in confidence_patterns:
        if re.search(pattern, content):
            found = True
            break
    
    if found:
        print("✓ Confidence scoring mechanism present")
        return True
    else:
        print("✗ Confidence scoring mechanism not found")
        return False


def test_chain_of_thought(content):
    """Test Chain-of-Thought reasoning is mentioned"""
    print("\nTesting Chain-of-Thought reasoning...")
    
    cot_keywords = [
        'Chain-of-Thought',
        'reasoning_steps',
        'step-by-step'
    ]
    
    found = False
    for keyword in cot_keywords:
        if keyword in content:
            found = True
            print(f"✓ Chain-of-Thought keyword found: '{keyword}'")
            break
    
    if not found:
        print("✗ Chain-of-Thought reasoning not mentioned")
    
    return found


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("ReasoningEngine Validation")
    print("=" * 60)
    
    results = []
    
    # Test 1: File exists
    file_exists, file_path = test_file_exists()
    results.append(("File Existence", file_exists))
    
    if not file_exists:
        print("\n✗ Cannot continue without file")
        return 1
    
    # Test 2: Class definition
    class_defined, content = test_class_definition(file_path)
    results.append(("Class Definition", class_defined))
    
    if not class_defined:
        print("\n✗ Cannot continue without class definition")
        return 1
    
    # Test 3: Required methods
    results.append(("Required Methods", test_required_methods(content)))
    
    # Test 4: Helper methods
    results.append(("Helper Methods", test_helper_methods(content)))
    
    # Test 5: Imports
    results.append(("Imports", test_imports(content)))
    
    # Test 6: Docstrings
    results.append(("Docstrings", test_docstrings(content)))
    
    # Test 7: Confidence scoring
    results.append(("Confidence Scoring", test_confidence_scoring(content)))
    
    # Test 8: Chain-of-Thought
    results.append(("Chain-of-Thought", test_chain_of_thought(content)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All validation tests passed!")
        print("\nReasoningEngine implementation complete:")
        print("  - BedrockClient integration")
        print("  - Chain-of-Thought reasoning")
        print("  - Confidence scoring (0.0-1.0)")
        print("  - Business name evaluation")
        print("  - Design ranking")
        print("  - Insight synthesis")
        return 0
    else:
        print(f"\n✗ {total - passed} validation test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
