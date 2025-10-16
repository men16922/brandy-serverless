"""
Fallback Configuration Module

This module provides fallback governance for AI providers when Amazon Bedrock
is unavailable or when running in development mode. It manages the selection
and configuration of fallback providers (OpenAI, Gemini).

Usage:
    from config.fallback_config import FallbackConfig
    
    config = FallbackConfig.from_env()
    if config.is_fallback_enabled():
        provider = config.get_fallback_provider()
        print(f"Using fallback provider: {provider}")
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FallbackProvider(Enum):
    """Enumeration of available fallback AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    NONE = "none"


@dataclass
class FallbackConfig:
    """
    Configuration for fallback AI provider governance.
    
    This class manages the fallback strategy when Amazon Bedrock is unavailable
    or when running in development mode. It determines whether fallback is enabled
    and which provider to use.
    
    Attributes:
        enable_fallback: Explicit fallback enable flag
        dev_profile: Development profile flag
        environment: Current environment (local/dev/prod)
        fallback_provider: Preferred fallback provider (openai/gemini)
        use_agentcore: Whether to use Bedrock AgentCore
    """
    
    enable_fallback: bool = False
    dev_profile: bool = False
    environment: str = "prod"
    fallback_provider: str = "openai"
    use_agentcore: bool = True
    
    @classmethod
    def from_env(cls) -> 'FallbackConfig':
        """
        Create FallbackConfig from environment variables.
        
        Environment Variables:
            ENABLE_FALLBACK: Explicit fallback enable (true/false)
            DEV_PROFILE: Development profile flag (true/false)
            ENVIRONMENT: Current environment (local/dev/prod)
            FALLBACK_PROVIDER: Preferred provider (openai/gemini)
            USE_AGENTCORE: Use Bedrock AgentCore (true/false)
        
        Returns:
            FallbackConfig instance with values from environment
        """
        return cls(
            enable_fallback=os.getenv('ENABLE_FALLBACK', 'false').lower() == 'true',
            dev_profile=os.getenv('DEV_PROFILE', 'false').lower() == 'true',
            environment=os.getenv('ENVIRONMENT', 'prod').lower(),
            fallback_provider=os.getenv('FALLBACK_PROVIDER', 'openai').lower(),
            use_agentcore=os.getenv('USE_AGENTCORE', 'true').lower() == 'true'
        )
    
    def is_fallback_enabled(self) -> bool:
        """
        Check if fallback to OpenAI/Gemini is enabled.
        
        Fallback is enabled when ANY of the following conditions are met:
        1. ENABLE_FALLBACK=true (explicit activation)
        2. DEV_PROFILE=true (development mode)
        3. ENVIRONMENT=local (local development)
        
        For hackathon submission, ensure:
        - ENABLE_FALLBACK=false
        - DEV_PROFILE=false
        - ENVIRONMENT=prod
        
        Returns:
            True if fallback is enabled, False otherwise (Bedrock-only mode)
        """
        # Explicit fallback flag takes precedence
        if self.enable_fallback:
            return True
        
        # Development profile enables fallback
        if self.dev_profile:
            return True
        
        # Local environment enables fallback
        if self.environment == 'local':
            return True
        
        # Production mode: Bedrock-only
        return False
    
    def get_fallback_provider(self) -> FallbackProvider:
        """
        Get the fallback AI provider to use.
        
        Selection logic:
        1. If fallback is disabled, return NONE
        2. Use FALLBACK_PROVIDER environment variable (openai/gemini)
        3. Default to OpenAI if not specified
        
        Returns:
            FallbackProvider enum value (OPENAI, GEMINI, or NONE)
        """
        if not self.is_fallback_enabled():
            return FallbackProvider.NONE
        
        provider_str = self.fallback_provider.lower()
        
        if provider_str == 'gemini':
            return FallbackProvider.GEMINI
        elif provider_str == 'openai':
            return FallbackProvider.OPENAI
        else:
            # Default to OpenAI for unknown providers
            return FallbackProvider.OPENAI
    
    def should_use_bedrock_only(self) -> bool:
        """
        Check if the system should use Bedrock exclusively.
        
        This is the inverse of is_fallback_enabled() and is useful
        for hackathon submission validation.
        
        Returns:
            True if Bedrock-only mode, False if fallback is allowed
        """
        return not self.is_fallback_enabled()
    
    def is_production_mode(self) -> bool:
        """
        Check if running in production mode.
        
        Production mode means:
        - ENVIRONMENT=prod
        - ENABLE_FALLBACK=false
        - DEV_PROFILE=false
        
        Returns:
            True if in production mode, False otherwise
        """
        return (
            self.environment == 'prod' and
            not self.enable_fallback and
            not self.dev_profile
        )
    
    def is_local_development(self) -> bool:
        """
        Check if running in local development mode.
        
        Returns:
            True if ENVIRONMENT=local, False otherwise
        """
        return self.environment == 'local'
    
    def get_openai_config(self) -> dict:
        """
        Get OpenAI configuration from environment.
        
        Returns:
            Dictionary with OpenAI configuration
        """
        return {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'secret_name': os.getenv('OPENAI_SECRET_NAME', 'openai-api-key'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'dalle_model': os.getenv('OPENAI_DALLE_MODEL', 'dall-e-3')
        }
    
    def get_gemini_config(self) -> dict:
        """
        Get Gemini configuration from environment.
        
        Returns:
            Dictionary with Gemini configuration
        """
        return {
            'api_key': os.getenv('GEMINI_API_KEY', ''),
            'model': os.getenv('GEMINI_MODEL', 'gemini-pro'),
            'vision_model': os.getenv('GEMINI_VISION_MODEL', 'gemini-pro-vision')
        }
    
    def validate_hackathon_submission(self) -> list[str]:
        """
        Validate configuration for hackathon submission.
        
        Hackathon requirements:
        - ENABLE_FALLBACK must be false
        - DEV_PROFILE must be false
        - ENVIRONMENT should be prod
        - USE_AGENTCORE should be true
        
        Returns:
            List of validation warnings/errors (empty if valid)
        """
        issues = []
        
        if self.enable_fallback:
            issues.append(
                "ENABLE_FALLBACK=true: Hackathon submission requires Bedrock-only mode. "
                "Set ENABLE_FALLBACK=false"
            )
        
        if self.dev_profile:
            issues.append(
                "DEV_PROFILE=true: Hackathon submission should use production profile. "
                "Set DEV_PROFILE=false"
            )
        
        if self.environment != 'prod':
            issues.append(
                f"ENVIRONMENT={self.environment}: Hackathon submission should use 'prod'. "
                f"Set ENVIRONMENT=prod"
            )
        
        if not self.use_agentcore:
            issues.append(
                "USE_AGENTCORE=false: Hackathon requires AgentCore implementation. "
                "Set USE_AGENTCORE=true"
            )
        
        return issues
    
    def get_mode_description(self) -> str:
        """
        Get a human-readable description of the current mode.
        
        Returns:
            String describing the current configuration mode
        """
        if self.is_production_mode():
            return "Production Mode (Bedrock-only, AgentCore enabled)"
        elif self.is_local_development():
            return "Local Development Mode (Fallback enabled)"
        elif self.dev_profile:
            return "Development Profile (Fallback enabled)"
        elif self.is_fallback_enabled():
            return f"Fallback Mode (Using {self.get_fallback_provider().value})"
        else:
            return "Bedrock-only Mode"
    
    def __str__(self) -> str:
        """String representation of configuration."""
        provider = self.get_fallback_provider()
        return (
            f"FallbackConfig(\n"
            f"  mode={self.get_mode_description()},\n"
            f"  enable_fallback={self.enable_fallback},\n"
            f"  dev_profile={self.dev_profile},\n"
            f"  environment={self.environment},\n"
            f"  fallback_provider={provider.value},\n"
            f"  use_agentcore={self.use_agentcore},\n"
            f"  bedrock_only={self.should_use_bedrock_only()}\n"
            f")"
        )


# Global configuration instance (lazy-loaded)
_fallback_config: Optional[FallbackConfig] = None


def get_fallback_config() -> FallbackConfig:
    """
    Get the global FallbackConfig instance.
    
    This function provides a singleton pattern for configuration access.
    The configuration is loaded once from environment variables and cached.
    
    Returns:
        FallbackConfig instance
    """
    global _fallback_config
    if _fallback_config is None:
        _fallback_config = FallbackConfig.from_env()
    return _fallback_config


def reset_fallback_config():
    """
    Reset the global configuration instance.
    
    This is useful for testing when you need to reload configuration
    from updated environment variables.
    """
    global _fallback_config
    _fallback_config = None


if __name__ == '__main__':
    # Example usage and validation
    config = FallbackConfig.from_env()
    print("Fallback Configuration:")
    print(config)
    print()
    
    print("Feature Checks:")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  Bedrock-only mode: {config.should_use_bedrock_only()}")
    print(f"  Production mode: {config.is_production_mode()}")
    print(f"  Local development: {config.is_local_development()}")
    print(f"  Fallback provider: {config.get_fallback_provider().value}")
    print()
    
    print("Hackathon Submission Validation:")
    issues = config.validate_hackathon_submission()
    if issues:
        print("⚠️  Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration is valid for hackathon submission!")
