"""
LLM Factory for creating language model instances across different providers.
Supports OpenAI, Anthropic, AWS Bedrock, and Azure OpenAI.
"""

from typing import Optional, Any
from .settings import settings


class LLMFactory:
    """Factory class for creating LLM instances"""
    
    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create an LLM instance based on the provider.
        
        Args:
            provider: The LLM provider (defaults to configured provider)
            model: The specific model to use (optional)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            An instance of the appropriate LLM class
            
        Raises:
            ValueError: If the provider is not supported
            EnvironmentError: If required API keys are missing
        """
        # Use default provider if not specified
        if provider is None:
            provider = settings.default_llm_provider
            if not provider:
                raise EnvironmentError(
                    "No LLM provider configured. Please set API keys in .env file."
                )
        providers = {
            "openai": LLMFactory._create_openai,
            "anthropic": LLMFactory._create_anthropic,
            "bedrock": LLMFactory._create_bedrock,
            "azure": LLMFactory._create_azure,
            "lmstudio": LLMFactory._create_lmstudio
        }
        
        if provider not in providers:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: {list(providers.keys())}"
            )
            
        return providers[provider](model, **kwargs)
    
    @staticmethod
    def _create_openai(model: Optional[str], **kwargs):
        """Create OpenAI LLM instance"""
        from langchain_openai import ChatOpenAI
        import os
        
        # Check both settings and environment directly
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. Please set it in .env file."
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", settings.llm_temperature)
        
        return ChatOpenAI(
            model=model or settings.openai_model,
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_anthropic(model: Optional[str], **kwargs):
        """Create Anthropic LLM instance"""
        from langchain_anthropic import ChatAnthropic
        
        if not settings.anthropic_api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found. Please set it in .env file."
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", settings.llm_temperature)
        
        return ChatAnthropic(
            model=model or settings.anthropic_model,
            temperature=temperature,
            api_key=settings.anthropic_api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_bedrock(model: Optional[str], **kwargs):
        """Create AWS Bedrock LLM instance"""
        from langchain_aws import ChatBedrock
        
        if not (settings.aws_access_key_id and settings.aws_secret_access_key):
            raise EnvironmentError(
                "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY in .env file."
            )
        
        # Extract temperature if provided in kwargs
        temperature = kwargs.pop("temperature", settings.llm_temperature)
        model_kwargs = kwargs.pop("model_kwargs", {})
        model_kwargs["temperature"] = temperature
        
        return ChatBedrock(
            model_id=model or settings.bedrock_model,
            region_name=settings.aws_region,
            model_kwargs=model_kwargs,
            **kwargs
        )
    
    @staticmethod
    def _create_azure(model: Optional[str], **kwargs):
        """Create Azure OpenAI LLM instance"""
        from langchain_openai import AzureChatOpenAI
        
        if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
            raise EnvironmentError(
                "Azure OpenAI credentials not found. Please set AZURE_OPENAI_ENDPOINT "
                "and AZURE_OPENAI_API_KEY in .env file."
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", settings.llm_temperature)
        
        return AzureChatOpenAI(
            deployment_name=model or settings.azure_deployment,
            openai_api_base=settings.azure_openai_endpoint,
            openai_api_key=settings.azure_openai_api_key,
            openai_api_version="2023-05-15",
            temperature=temperature,
            **kwargs
        )
    
    @staticmethod
    def _create_lmstudio(model: Optional[str], **kwargs):
        """
        Create LM Studio LLM instance (OpenAI-compatible local endpoint)
        
        LM Studio provides an OpenAI-compatible API endpoint for local models.
        Default endpoint is http://localhost:1234/v1
        """
        from langchain_openai import ChatOpenAI
        import os
        
        # Get LM Studio endpoint from settings or use default
        base_url = getattr(settings, 'lmstudio_base_url', None) or os.environ.get(
            "LMSTUDIO_BASE_URL", 
            "http://localhost:1234/v1"
        )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", settings.llm_temperature)
        
        # LM Studio doesn't require an API key, but OpenAI client needs one
        # Use a dummy key if none provided
        api_key = kwargs.pop("api_key", "lm-studio")
        
        # Get model from settings or use the one currently loaded in LM Studio
        # LM Studio will use whatever model is currently loaded if not specified
        model_name = model or getattr(settings, 'lmstudio_model', None) or "phi-4"
        
        return ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            **kwargs
        )