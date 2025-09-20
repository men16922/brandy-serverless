"""
Test project structure and basic configuration
"""

import os
import json
import pytest

def test_project_directories_exist():
    """Test that all required project directories exist"""
    required_dirs = [
        "src/lambda/session-manager",
        "src/lambda/business-analyzer", 
        "src/lambda/name-suggester",
        "src/lambda/image-generator",
        "src/lambda/report-generator",
        "src/lambda/shared",
        "src/streamlit",
        "infrastructure/stacks",
        "config",
        "scripts",
        "data/fallbacks/signs",
        "data/fallbacks/interiors",
        "tests"
    ]
    
    for directory in required_dirs:
        assert os.path.exists(directory), f"Directory {directory} should exist"

def test_lambda_functions_have_handler():
    """Test that all Lambda functions have index.py with lambda_handler"""
    lambda_dirs = [
        "src/lambda/session-manager",
        "src/lambda/business-analyzer",
        "src/lambda/name-suggester", 
        "src/lambda/image-generator",
        "src/lambda/report-generator"
    ]
    
    for lambda_dir in lambda_dirs:
        index_file = os.path.join(lambda_dir, "index.py")
        assert os.path.exists(index_file), f"Lambda function {lambda_dir} should have index.py"
        
        with open(index_file, 'r') as f:
            content = f.read()
            assert "lambda_handler" in content, f"Lambda function {lambda_dir} should have lambda_handler function"

def test_config_files_valid_json():
    """Test that configuration files are valid JSON"""
    config_files = [
        "config/local.json",
        "config/dev.json"
    ]
    
    for config_file in config_files:
        assert os.path.exists(config_file), f"Config file {config_file} should exist"
        
        with open(config_file, 'r') as f:
            try:
                config = json.load(f)
                assert "environment" in config, f"Config {config_file} should have environment field"
                assert "aws" in config, f"Config {config_file} should have aws field"
            except json.JSONDecodeError:
                pytest.fail(f"Config file {config_file} is not valid JSON")

def test_cdk_structure():
    """Test CDK infrastructure structure"""
    cdk_files = [
        "infrastructure/app.py",
        "infrastructure/cdk.json",
        "infrastructure/requirements.txt",
        "infrastructure/stacks/storage_stack.py",
        "infrastructure/stacks/api_stack.py",
        "infrastructure/stacks/workflow_stack.py",
        "infrastructure/stacks/frontend_stack.py"
    ]
    
    for cdk_file in cdk_files:
        assert os.path.exists(cdk_file), f"CDK file {cdk_file} should exist"

def test_scripts_executable():
    """Test that setup scripts are executable"""
    scripts = [
        "scripts/setup-local.sh",
        "scripts/deploy-dev.sh"
    ]
    
    for script in scripts:
        assert os.path.exists(script), f"Script {script} should exist"
        # Check if file is executable
        assert os.access(script, os.X_OK), f"Script {script} should be executable"

def test_fallback_data_exists():
    """Test that fallback data files exist"""
    fallback_files = [
        "data/fallbacks/signs/default-sign.json",
        "data/fallbacks/interiors/default-interior.json"
    ]
    
    for fallback_file in fallback_files:
        assert os.path.exists(fallback_file), f"Fallback file {fallback_file} should exist"
        
        with open(fallback_file, 'r') as f:
            try:
                data = json.load(f)
                assert "name" in data, f"Fallback file {fallback_file} should have name field"
                assert "image_url" in data, f"Fallback file {fallback_file} should have image_url field"
            except json.JSONDecodeError:
                pytest.fail(f"Fallback file {fallback_file} is not valid JSON")