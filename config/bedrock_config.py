"""
Bedrock Configuration Module

This module provides configuration management for Amazon Bedrock services.
It reads environment variables and provides a structured configuration object
for all Bedrock-related settings.

Usage:
    from config.bedrock_config import BedrockConfig
    
    config = BedrockConfig.from_env()
    print(config.claude_model_id)
    print(config.is_fallback_enabled())
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BedrockConfig:
    """
    Configuration for Amazon Bedrock services.
    
    This dataclass encapsulates all Bedrock-related configuration including
    model IDs, region settings, and feature flags.
    
    Attributes:
        region: AWS region for Bedrock services (default: us-east-1)
        claude_model_id: Model ID for Claude 3.5 Sonnet
        sdxl_model_id: Model ID for Stable Diffusion XL
        knowledge_base_id: Optional Knowledge Base ID for vector search
        agent_id: Optional Agent ID for AgentCore orchestration
        agent_alias_id: Optional Agent Alias ID for AgentCore
        enable_fallback: Whether to enable fallback to OpenAI/Gemini
        max_retries: Maximum number of retry attempts for API calls
        timeout: Timeout in seconds for API calls
        max_tokens: Maximum tokens for text generation
        temperature: Temperature for text generation (0.0-1.0)
    """
    
    region: str = "us-east-1"
    # Using inference profile for Claude Sonnet 4
    claude_model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    sdxl_model_id: str = "stability.stable-diffusion-xl-v1"
    knowledge_base_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_alias_id: Optional[str] = None
    enable_fallback: bool = False
    max_retries: int = 3
    timeout: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7
    
    @classmethod
    def from_env(cls) -> 'BedrockConfig':
        """
        Create BedrockConfig from environment variables.
        
        Environment Variables:
            BEDROCK_REGION: AWS region (default: us-east-1)
            CLAUDE_MODEL_ID: Claude model ID
            SDXL_MODEL_ID: SDXL model ID
            BEDROCK_KB_ID: Knowledge Base ID (optional)
            BEDROCK_AGENT_ID: Agent ID (optional)
            BEDROCK_AGENT_ALIAS_ID: Agent Alias ID (optional)
            ENABLE_FALLBACK: Enable fallback (true/false)
            BEDROCK_MAX_RETRIES: Max retry attempts (default: 3)
            BEDROCK_TIMEOUT: Timeout in seconds (default: 30)
            BEDROCK_MAX_TOKENS: Max tokens (default: 2048)
            BEDROCK_TEMPERATURE: Temperature (default: 0.7)
        
        Returns:
            BedrockConfig instance with values from environment
        """
        return cls(
            region=os.getenv('BEDROCK_REGION', 'us-east-1'),
            # Using inference profile for Claude Sonnet 4
            claude_model_id=os.getenv(
                'CLAUDE_MODEL_ID',
                'us.anthropic.claude-sonnet-4-20250514-v1:0'
            ),
            sdxl_model_id=os.getenv(
                'SDXL_MODEL_ID',
                'stability.stable-diffusion-xl-v1'
            ),
            knowledge_base_id=os.getenv('BEDROCK_KB_ID') or None,
            agent_id=os.getenv('BEDROCK_AGENT_ID') or None,
            agent_alias_id=os.getenv('BEDROCK_AGENT_ALIAS_ID') or None,
            enable_fallback=os.getenv('ENABLE_FALLBACK', 'false').lower() == 'true',
            max_retries=int(os.getenv('BEDROCK_MAX_RETRIES', '3')),
            timeout=int(os.getenv('BEDROCK_TIMEOUT', '30')),
            max_tokens=int(os.getenv('BEDROCK_MAX_TOKENS', '2048')),
            temperature=float(os.getenv('BEDROCK_TEMPERATURE', '0.7'))
        )
    
    def is_fallback_enabled(self) -> bool:
        """
        Check if fallback to OpenAI/Gemini is enabled.
        
        Fallback is enabled when:
        - ENABLE_FALLBACK=true (explicit)
        - DEV_PROFILE=true (development mode)
        - ENVIRONMENT=local (local development)
        
        For hackathon submission, this should return False.
        
        Returns:
            True if fallback is enabled, False otherwise
        """
        if self.enable_fallback:
            return True
        
        dev_profile = os.getenv('DEV_PROFILE', 'false').lower() == 'true'
        environment = os.getenv('ENVIRONMENT', 'prod')
        
        return dev_profile or environment == 'local'
    
    def is_agentcore_enabled(self) -> bool:
        """
        Check if Bedrock AgentCore is configured and enabled.
        
        Returns:
            True if agent_id and agent_alias_id are set, False otherwise
        """
        return bool(self.agent_id and self.agent_alias_id)
    
    def is_knowledge_base_enabled(self) -> bool:
        """
        Check if Bedrock Knowledge Base is configured.
        
        Returns:
            True if knowledge_base_id is set, False otherwise
        """
        return bool(self.knowledge_base_id)
    
    def get_claude_params(self, **overrides) -> dict:
        """
        Get default parameters for Claude API calls.
        
        Args:
            **overrides: Override default parameters
        
        Returns:
            Dictionary of Claude API parameters
        """
        params = {
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
        }
        params.update(overrides)
        return params
    
    def get_sdxl_params(self, **overrides) -> dict:
        """
        Get default parameters for SDXL API calls.
        
        Args:
            **overrides: Override default parameters
        
        Returns:
            Dictionary of SDXL API parameters
        """
        params = {
            'width': 1024,
            'height': 1024,
            'cfg_scale': 7.0,
            'steps': 50,
        }
        params.update(overrides)
        return params
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        if not self.region:
            issues.append("BEDROCK_REGION is required")
        
        if not self.claude_model_id:
            issues.append("CLAUDE_MODEL_ID is required")
        
        if not self.sdxl_model_id:
            issues.append("SDXL_MODEL_ID is required")
        
        if self.max_retries < 0:
            issues.append("BEDROCK_MAX_RETRIES must be >= 0")
        
        if self.timeout <= 0:
            issues.append("BEDROCK_TIMEOUT must be > 0")
        
        if self.max_tokens <= 0:
            issues.append("BEDROCK_MAX_TOKENS must be > 0")
        
        if not (0.0 <= self.temperature <= 1.0):
            issues.append("BEDROCK_TEMPERATURE must be between 0.0 and 1.0")
        
        return issues
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"BedrockConfig(\n"
            f"  region={self.region},\n"
            f"  claude_model_id={self.claude_model_id},\n"
            f"  sdxl_model_id={self.sdxl_model_id},\n"
            f"  knowledge_base_id={self.knowledge_base_id or 'Not configured'},\n"
            f"  agent_id={self.agent_id or 'Not configured'},\n"
            f"  agent_alias_id={self.agent_alias_id or 'Not configured'},\n"
            f"  enable_fallback={self.enable_fallback},\n"
            f"  max_retries={self.max_retries},\n"
            f"  timeout={self.timeout}s,\n"
            f"  max_tokens={self.max_tokens},\n"
            f"  temperature={self.temperature}\n"
            f")"
        )


# Global configuration instance (lazy-loaded)
_config: Optional[BedrockConfig] = None


def get_bedrock_config() -> BedrockConfig:
    """
    Get the global BedrockConfig instance.
    
    This function provides a singleton pattern for configuration access.
    The configuration is loaded once from environment variables and cached.
    
    Returns:
        BedrockConfig instance
    """
    global _config
    if _config is None:
        _config = BedrockConfig.from_env()
    return _config


def reset_bedrock_config():
    """
    Reset the global configuration instance.
    
    This is useful for testing when you need to reload configuration
    from updated environment variables.
    """
    global _config
    _config = None


if __name__ == '__main__':
    # Example usage and validation
    config = BedrockConfig.from_env()
    print("Bedrock Configuration:")
    print(config)
    print("\nValidation:")
    issues = config.validate()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid!")
    
    print("\nFeature Flags:")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  AgentCore enabled: {config.is_agentcore_enabled()}")
    print(f"  Knowledge Base enabled: {config.is_knowledge_base_enabled()}")
