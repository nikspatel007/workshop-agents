"""
LLM Factory for creating language model instances across different providers.
Supports OpenAI, Anthropic, AWS Bedrock, and Azure OpenAI.
"""

import os
from typing import Optional, Any


class LLMFactory:
    """Factory class for creating LLM instances"""
    
    @staticmethod
    def create_llm(
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create an LLM instance based on the provider.
        
        Args:
            provider: The LLM provider ('openai', 'anthropic', 'bedrock', 'azure')
            model: The specific model to use (optional)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            An instance of the appropriate LLM class
            
        Raises:
            ValueError: If the provider is not supported
            EnvironmentError: If required API keys are missing
        """
        providers = {
            "openai": LLMFactory._create_openai,
            "anthropic": LLMFactory._create_anthropic,
            "bedrock": LLMFactory._create_bedrock,
            "azure": LLMFactory._create_azure
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
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found in environment variables"
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", 0.7)
        
        return ChatOpenAI(
            model=model or "gpt-4",
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_anthropic(model: Optional[str], **kwargs):
        """Create Anthropic LLM instance"""
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found in environment variables"
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", 0.7)
        
        return ChatAnthropic(
            model=model or "claude-3-opus-20240229",
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _create_bedrock(model: Optional[str], **kwargs):
        """Create AWS Bedrock LLM instance"""
        from langchain_aws import ChatBedrock
        
        region = os.getenv("AWS_REGION", "us-east-1")
        
        # Extract temperature if provided in kwargs
        temperature = kwargs.pop("temperature", 0.7)
        model_kwargs = kwargs.pop("model_kwargs", {})
        model_kwargs["temperature"] = temperature
        
        return ChatBedrock(
            model_id=model or "anthropic.claude-v2",
            region_name=region,
            model_kwargs=model_kwargs,
            **kwargs
        )
    
    @staticmethod
    def _create_azure(model: Optional[str], **kwargs):
        """Create Azure OpenAI LLM instance"""
        from langchain_openai import AzureChatOpenAI
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            raise EnvironmentError(
                "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY "
                "must be set in environment variables"
            )
        
        # Extract temperature to avoid duplicate argument error
        temperature = kwargs.pop("temperature", 0.7)
        
        return AzureChatOpenAI(
            deployment_name=model or "gpt-4",
            openai_api_base=endpoint,
            openai_api_key=api_key,
            openai_api_version="2023-05-15",
            temperature=temperature,
            **kwargs
        )