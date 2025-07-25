# Iteration 0: Implementation Details

## 1. Project Structure

```
is_this_going_to_fly/
├── config/
│   ├── __init__.py
│   ├── llm_factory.py
│   └── settings.py
├── tools/
│   ├── __init__.py
│   └── mcp_client.py
├── modules/
│   └── __init__.py
├── notebooks/
│   └── 00_Setup.ipynb
├── utils/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_llm_factory.py
├── .env.example
├── mcp_config.json
├── requirements.txt
└── README.md
```

## 2. LLM Factory Implementation

```python
# config/llm_factory.py
import os
from typing import Optional, Any
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Abstract base class for LLM providers"""
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    async def ainvoke(self, prompt: str) -> str:
        pass

class LLMFactory:
    """Factory class for creating LLM instances"""
    
    @staticmethod
    def create_llm(
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
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
        
        return ChatOpenAI(
            model=model or "gpt-4",
            temperature=kwargs.get("temperature", 0.7),
            api_key=api_key
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
        
        return ChatAnthropic(
            model=model or "claude-3-opus-20240229",
            temperature=kwargs.get("temperature", 0.7),
            api_key=api_key
        )
    
    @staticmethod
    def _create_bedrock(model: Optional[str], **kwargs):
        """Create AWS Bedrock LLM instance"""
        from langchain_aws import ChatBedrock
        
        region = os.getenv("AWS_REGION", "us-east-1")
        
        return ChatBedrock(
            model_id=model or "anthropic.claude-v2",
            region_name=region,
            model_kwargs=kwargs
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
        
        return AzureChatOpenAI(
            deployment_name=model or "gpt-4",
            openai_api_base=endpoint,
            openai_api_key=api_key,
            openai_api_version="2023-05-15",
            temperature=kwargs.get("temperature", 0.7)
        )
```

## 3. Environment Configuration

```python
# config/settings.py
import os
import platform
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def detect_environment() -> str:
    """Detect the current runtime environment"""
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

def get_settings() -> Dict[str, Any]:
    """Get environment-specific settings"""
    env = detect_environment()
    
    settings = {
        "environment": env,
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "debug": os.getenv("BS_DETECTOR_DEBUG", "0") == "1",
        "platform": platform.system().lower()
    }
    
    # Environment-specific configurations
    if env == "colab":
        settings["notebook_type"] = "colab"
        settings["auth_method"] = "userdata"
    elif env == "sagemaker":
        settings["notebook_type"] = "sagemaker"
        settings["auth_method"] = "iam"
    else:
        settings["notebook_type"] = "jupyter"
        settings["auth_method"] = "env"
    
    return settings
```

## 4. Simple Tools Setup

```python
# tools/__init__.py
"""
Tools package for BS Detector.
Provides simple, extensible tool implementations.
"""

from typing import Dict, Any, Callable


class ToolRegistry:
    """Simple registry for managing tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
    
    def register(self, name: str, tool: Callable) -> None:
        """Register a tool function"""
        self.tools[name] = tool
    
    def get(self, name: str) -> Callable:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def list_tools(self) -> list[str]:
        """List all registered tools"""
        return list(self.tools.keys())


# Global registry instance
tool_registry = ToolRegistry()


# Example tool for testing
def echo_tool(message: str) -> str:
    """Simple echo tool for testing"""
    return f"Echo: {message}"


# Register the echo tool
tool_registry.register("echo", echo_tool)
```

## 5. Basic Mock Search Tool

```python
# tools/mock_search.py
"""
Mock search tool for workshop consistency.
Returns predictable aviation facts without external dependencies.
"""

from typing import List, Dict, Any


def search_aviation_facts(query: str) -> List[Dict[str, Any]]:
    """
    Mock search that returns aviation facts.
    Used for consistent workshop experience.
    """
    # Simple keyword-based responses
    mock_data = {
        "747": [
            {"fact": "The Boeing 747 has 4 engines", "confidence": 1.0},
            {"fact": "The 747 first flew in 1969", "confidence": 1.0}
        ],
        "concorde": [
            {"fact": "The Concorde could fly at Mach 2.04", "confidence": 1.0},
            {"fact": "The Concorde was retired in 2003", "confidence": 1.0}
        ],
        "default": [
            {"fact": "Commercial pilots need an ATP license", "confidence": 0.9},
            {"fact": "Modern aircraft have multiple redundant systems", "confidence": 0.9}
        ]
    }
    
    # Find matching facts
    query_lower = query.lower()
    for key, facts in mock_data.items():
        if key in query_lower:
            return facts
    
    return mock_data["default"]
```

## 6. Environment Variables Template

```bash
# .env.example
# LLM Provider Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, bedrock, azure

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...

# Debug Mode
BS_DETECTOR_DEBUG=0
```

## 7. First Test Case

```python
# tests/test_llm_factory.py
import pytest
import os
from config.llm_factory import LLMFactory

def test_factory_creates_openai_llm():
    """Test that factory creates OpenAI LLM correctly"""
    # Set a dummy API key for testing
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    llm = LLMFactory.create_llm("openai")
    assert llm is not None
    assert hasattr(llm, "invoke")
    assert hasattr(llm, "ainvoke")

def test_factory_raises_for_unknown_provider():
    """Test that factory raises error for unknown provider"""
    with pytest.raises(ValueError) as exc_info:
        LLMFactory.create_llm("unknown_provider")
    
    assert "Unknown provider" in str(exc_info.value)

def test_factory_raises_for_missing_api_key():
    """Test that factory raises error when API key is missing"""
    # Remove API key if it exists
    os.environ.pop("OPENAI_API_KEY", None)
    
    with pytest.raises(EnvironmentError) as exc_info:
        LLMFactory.create_llm("openai")
    
    assert "OPENAI_API_KEY not found" in str(exc_info.value)
```