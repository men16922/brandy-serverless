#!/usr/bin/env python3
"""
Bedrock Configuration Validation Script

This script validates the Bedrock configuration by:
1. Loading configuration from environment variables
2. Checking for required settings
3. Validating configuration values
4. Reporting any issues

Usage:
    python scripts/validate-bedrock-config.py
    
    # Or with custom environment
    BEDROCK_REGION=us-west-2 python scripts/validate-bedrock-config.py
"""

import sys
import os

# Add parent directory to path to import config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.bedrock_config import BedrockConfig, get_bedrock_config


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_check(label: str, value: any, status: str = "✓"):
    """Print a configuration check result."""
    print(f"{status} {label}: {value}")


def validate_configuration():
    """Validate Bedrock configuration and print results."""
    print_section("Bedrock Configuration Validation")
    
    # Load configuration
    try:
        config = BedrockConfig.from_env()
        print_check("Configuration loaded", "Success")
    except Exception as e:
        print_check("Configuration loaded", f"Failed: {e}", "✗")
        return False
    
    # Print configuration
    print_section("Current Configuration")
    print(config)
    
    # Validate configuration
    print_section("Configuration Validation")
    issues = config.validate()
    
    if not issues:
        print_check("Configuration validation", "All checks passed")
    else:
        print_check("Configuration validation", f"{len(issues)} issue(s) found", "✗")
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    
    # Check feature flags
    print_section("Feature Flags")
    print_check("Fallback enabled", config.is_fallback_enabled())
    print_check("AgentCore enabled", config.is_agentcore_enabled())
    print_check("Knowledge Base enabled", config.is_knowledge_base_enabled())
    
    # Check environment variables
    print_section("Environment Variables")
    env_vars = [
        'BEDROCK_REGION',
        'CLAUDE_MODEL_ID',
        'SDXL_MODEL_ID',
        'BEDROCK_KB_ID',
        'BEDROCK_AGENT_ID',
        'BEDROCK_AGENT_ALIAS_ID',
        'ENABLE_FALLBACK',
        'DEV_PROFILE',
        'ENVIRONMENT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Truncate long values
            display_value = value if len(value) < 50 else f"{value[:47]}..."
            print_check(var, display_value)
        else:
            print_check(var, "Not set", "○")
    
    # Check for hackathon submission readiness
    print_section("Hackathon Submission Readiness")
    
    checks = []
    
    # Check 1: Fallback should be disabled
    if not config.is_fallback_enabled():
        print_check("Fallback disabled", "Yes (Bedrock-only mode)")
        checks.append(True)
    else:
        print_check("Fallback disabled", "No (fallback enabled)", "⚠")
        print("  Note: Set ENABLE_FALLBACK=false for production")
        checks.append(False)
    
    # Check 2: Region should be us-east-1 (recommended)
    if config.region == 'us-east-1':
        print_check("Region is us-east-1", "Yes (recommended)")
        checks.append(True)
    else:
        print_check("Region is us-east-1", f"No (using {config.region})", "⚠")
        print("  Note: us-east-1 has best Bedrock model availability")
        checks.append(False)
    
    # Check 3: Model IDs are set
    if config.claude_model_id and config.sdxl_model_id:
        print_check("Model IDs configured", "Yes")
        checks.append(True)
    else:
        print_check("Model IDs configured", "No", "✗")
        checks.append(False)
    
    # Check 4: AgentCore configuration (optional but recommended)
    if config.is_agentcore_enabled():
        print_check("AgentCore configured", "Yes (recommended)")
        checks.append(True)
    else:
        print_check("AgentCore configured", "No (optional)", "○")
        print("  Note: Configure BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID for AgentCore")
        checks.append(True)  # Not required, so don't fail
    
    # Check 5: Knowledge Base configuration (optional)
    if config.is_knowledge_base_enabled():
        print_check("Knowledge Base configured", "Yes (optional)")
    else:
        print_check("Knowledge Base configured", "No (optional)", "○")
        print("  Note: Configure BEDROCK_KB_ID for vector search")
    
    # Summary
    print_section("Summary")
    
    if all(checks):
        print("✓ Configuration is valid and ready for deployment!")
        return True
    else:
        print("⚠ Configuration has warnings. Review the issues above.")
        print("  For hackathon submission, ensure ENABLE_FALLBACK=false")
        return True  # Warnings don't fail validation
    
    return True


def main():
    """Main entry point."""
    try:
        success = validate_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
