"""
Environment detection and configuration management.
Supports local development, Jupyter, Google Colab, and AWS SageMaker.
"""

import os
import platform
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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


def get_settings() -> Dict[str, Any]:
    """
    Get environment-specific settings.
    
    Returns:
        Dict containing configuration settings
    """
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