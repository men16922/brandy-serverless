#!/usr/bin/env python3
"""
Fallback Configuration Validation Script

This script validates the fallback configuration and provides recommendations
for different deployment scenarios (local, dev, production, hackathon).

Usage:
    python scripts/validate-fallback-config.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.fallback_config import FallbackConfig, FallbackProvider


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_status(label: str, value: any, is_good: bool = None):
    """Print a status line with optional color coding."""
    status = ""
    if is_good is True:
        status = "✅"
    elif is_good is False:
        status = "⚠️ "
    
    print(f"  {status} {label}: {value}")


def validate_environment():
    """Validate current environment configuration."""
    print_section("Current Environment Variables")
    
    env_vars = [
        'ENVIRONMENT',
        'ENABLE_FALLBACK',
        'DEV_PROFILE',
        'FALLBACK_PROVIDER',
        'USE_AGENTCORE',
        'BEDROCK_REGION',
        'CLAUDE_MODEL_ID',
        'SDXL_MODEL_ID'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT SET')
        print_status(var, value)


def validate_fallback_config():
    """Validate fallback configuration."""
    print_section("Fallback Configuration Analysis")
    
    config = FallbackConfig.from_env()
    print(config)
    print()
    
    print_section("Feature Status")
    print_status("Fallback Enabled", config.is_fallback_enabled())
    print_status("Bedrock-Only Mode", config.should_use_bedrock_only())
    print_status("Production Mode", config.is_production_mode())
    print_status("Local Development", config.is_local_development())
    print_status("Fallback Provider", config.get_fallback_provider().value)
    print_status("AgentCore Enabled", config.use_agentcore)


def validate_hackathon_submission():
    """Validate configuration for hackathon submission."""
    print_section("Hackathon Submission Validation")
    
    config = FallbackConfig.from_env()
    issues = config.validate_hackathon_submission()
    
    if not issues:
        print_status("Configuration Status", "VALID FOR HACKATHON SUBMISSION", True)
        print("\n  Your configuration meets all hackathon requirements:")
        print("  - Bedrock-only mode (no fallback)")
        print("  - Production environment")
        print("  - AgentCore enabled")
        print("\n  You can proceed with deployment!")
    else:
        print_status("Configuration Status", "NEEDS ATTENTION FOR HACKATHON", False)
        print("\n  Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\n  Please fix these issues before hackathon submission.")


def show_recommendations():
    """Show configuration recommendations for different scenarios."""
    print_section("Configuration Recommendations")
    
    print("\n📋 Local Development:")
    print("  ENVIRONMENT=local")
    print("  ENABLE_FALLBACK=true")
    print("  DEV_PROFILE=true")
    print("  FALLBACK_PROVIDER=openai")
    print("  USE_AGENTCORE=true")
    
    print("\n📋 Development Server:")
    print("  ENVIRONMENT=dev")
    print("  ENABLE_FALLBACK=true")
    print("  DEV_PROFILE=true")
    print("  FALLBACK_PROVIDER=openai")
    print("  USE_AGENTCORE=true")
    
    print("\n📋 Production (General):")
    print("  ENVIRONMENT=prod")
    print("  ENABLE_FALLBACK=false")
    print("  DEV_PROFILE=false")
    print("  USE_AGENTCORE=true")
    
    print("\n🏆 Hackathon Submission:")
    print("  ENVIRONMENT=prod")
    print("  ENABLE_FALLBACK=false")
    print("  DEV_PROFILE=false")
    print("  USE_AGENTCORE=true")
    print("  BEDROCK_REGION=us-east-1")
    print("  (Bedrock-only mode, no fallback providers)")


def test_provider_selection():
    """Test fallback provider selection logic."""
    print_section("Provider Selection Test")
    
    config = FallbackConfig.from_env()
    provider = config.get_fallback_provider()
    
    if provider == FallbackProvider.NONE:
        print_status("Selected Provider", "NONE (Bedrock-only)", True)
        print("  All requests will use Amazon Bedrock exclusively.")
    elif provider == FallbackProvider.OPENAI:
        print_status("Selected Provider", "OpenAI", None)
        print("  Fallback to OpenAI (GPT-4, DALL-E) when Bedrock fails.")
    elif provider == FallbackProvider.GEMINI:
        print_status("Selected Provider", "Gemini", None)
        print("  Fallback to Google Gemini when Bedrock fails.")
    
    if config.is_fallback_enabled():
        print("\n  Provider Configuration:")
        if provider == FallbackProvider.OPENAI:
            openai_config = config.get_openai_config()
            print(f"    Model: {openai_config['model']}")
            print(f"    DALL-E Model: {openai_config['dalle_model']}")
            print(f"    API Key: {'SET' if openai_config['api_key'] else 'NOT SET'}")
        elif provider == FallbackProvider.GEMINI:
            gemini_config = config.get_gemini_config()
            print(f"    Model: {gemini_config['model']}")
            print(f"    Vision Model: {gemini_config['vision_model']}")
            print(f"    API Key: {'SET' if gemini_config['api_key'] else 'NOT SET'}")


def main():
    """Main validation function."""
    print("\n" + "=" * 70)
    print("  AWS AI Branding Chatbot - Fallback Configuration Validator")
    print("=" * 70)
    
    validate_environment()
    validate_fallback_config()
    test_provider_selection()
    validate_hackathon_submission()
    show_recommendations()
    
    print("\n" + "=" * 70)
    print("  Validation Complete")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
