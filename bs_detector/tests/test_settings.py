"""
Unit tests for settings and environment detection.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import detect_environment, get_settings


def test_detect_environment():
    """Test environment detection returns valid environment"""
    env = detect_environment()
    valid_envs = ["local", "jupyter", "colab", "sagemaker"]
    assert env in valid_envs


def test_get_settings():
    """Test that get_settings returns expected structure"""
    settings = get_settings()
    
    # Check required keys exist
    required_keys = ["environment", "llm_provider", "debug", "platform"]
    for key in required_keys:
        assert key in settings
    
    # Check types
    assert isinstance(settings["environment"], str)
    assert isinstance(settings["llm_provider"], str)
    assert isinstance(settings["debug"], bool)
    assert isinstance(settings["platform"], str)
    
    # Check environment-specific settings
    env = settings["environment"]
    assert "notebook_type" in settings
    assert "auth_method" in settings
    
    # Verify auth method is appropriate for environment
    if env == "colab":
        assert settings["auth_method"] == "userdata"
    elif env == "sagemaker":
        assert settings["auth_method"] == "iam"
    else:
        assert settings["auth_method"] == "env"


def test_platform_detection():
    """Test that platform is detected correctly"""
    settings = get_settings()
    platform = settings["platform"]
    
    # Should be one of the common platforms
    valid_platforms = ["darwin", "linux", "windows"]
    assert platform in valid_platforms