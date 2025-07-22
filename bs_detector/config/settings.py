"""
Configuration settings for the BS Detector workshop.
Uses Pydantic for validation and automatic .env loading.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, Literal, List
from pathlib import Path
import os
import platform


class Settings(BaseSettings):
    """Application settings with automatic .env loading"""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    azure_openai_api_key: Optional[str] = Field(default=None)
    azure_openai_endpoint: Optional[str] = Field(default=None)
    
    # AWS Settings
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: str = Field(default="us-east-1")
    
    # Default LLM Provider
    default_llm_provider: Optional[str] = Field(default=None)
    
    # Model Settings
    openai_model: str = Field(default="gpt-4.1-mini")
    anthropic_model: str = Field(default="claude-3.7-haiku")
    bedrock_model: str = Field(default="anthropic.claude-v2")
    azure_deployment: str = Field(default="gpt-4.1-mini")
    
    # General Settings
    llm_temperature: float = Field(default=0.7)
    llm_timeout: int = Field(default=30)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        # Try multiple locations for .env file
        possible_paths = [
            Path(".env"),  # Current directory
            Path("../.env"),  # Parent directory (for notebooks)
            Path(__file__).parent.parent / ".env"  # Relative to this file
        ]
        
        for path in possible_paths:
            if path.exists():
                kwargs['_env_file'] = str(path.absolute())
                break
                
        super().__init__(**kwargs)
        
        # Auto-detect default provider if not set
        if not self.default_llm_provider:
            self.default_llm_provider = self.get_first_configured_provider()
    
    @field_validator("default_llm_provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        """Validate the provider is supported"""
        if v and v not in ["openai", "anthropic", "bedrock", "azure"]:
            return None
        return v
    
    def get_configured_providers(self) -> List[str]:
        """Return list of providers that have API keys configured"""
        providers = []
        
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.aws_access_key_id and self.aws_secret_access_key:
            providers.append("bedrock")
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            providers.append("azure")
            
        return providers
    
    def get_first_configured_provider(self) -> Optional[str]:
        """Get the first configured provider or None"""
        providers = self.get_configured_providers()
        return providers[0] if providers else None


# Global settings instance
settings = Settings()


# Legacy functions for compatibility
def detect_environment() -> str:
    """
    Detect the current runtime environment.
    
    Returns:
        str: One of 'colab', 'sagemaker', 'jupyter', or 'local'
    """
    # Check for Google Colab
    try:
        import google.colab
        return "colab"
    except ImportError:
        pass
    
    # Check for AWS SageMaker
    if os.path.exists("/opt/ml/metadata/resource-metadata.json"):
        return "sagemaker"
    
    # Check for Jupyter
    try:
        get_ipython()
        return "jupyter"
    except NameError:
        pass
    
    # Default to local
    return "local"


def get_settings() -> dict:
    """
    Get environment-specific settings (legacy function).
    
    Returns:
        Dict containing configuration settings
    """
    env = detect_environment()
    
    return {
        "environment": env,
        "llm_provider": settings.default_llm_provider or "openai",
        "debug": os.getenv("BS_DETECTOR_DEBUG", "0") == "1",
        "platform": platform.system().lower(),
        "configured_providers": settings.get_configured_providers()
    }