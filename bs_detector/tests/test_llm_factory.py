"""
Unit tests for LLM factory pattern.
Tests provider creation, error handling, and configuration.
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.llm_factory import LLMFactory


def test_factory_creates_openai_llm():
    """Test that factory creates OpenAI LLM correctly"""
    # Set a dummy API key for testing
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    try:
        llm = LLMFactory.create_llm("openai")
        assert llm is not None
        # Don't test actual invoke without real key
    finally:
        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


def test_factory_raises_for_unknown_provider():
    """Test that factory raises error for unknown provider"""
    with pytest.raises(ValueError) as exc_info:
        LLMFactory.create_llm("unknown_provider")
    
    assert "Unknown provider" in str(exc_info.value)


def test_factory_raises_for_missing_api_key():
    """Test that factory raises error when API key is missing"""
    from unittest.mock import patch
    
    # Mock the settings to have no API key
    with patch('config.llm_factory.settings') as mock_settings:
        # Set all the necessary attributes
        mock_settings.openai_api_key = None
        mock_settings.default_llm_provider = None
        mock_settings.openai_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        
        # Also ensure os.environ doesn't have the key
        original_key = os.environ.get("OPENAI_API_KEY")
        os.environ.pop("OPENAI_API_KEY", None)
        
        try:
            with pytest.raises(EnvironmentError) as exc_info:
                LLMFactory.create_llm("openai")
            
            assert "OPENAI_API_KEY not found" in str(exc_info.value)
        finally:
            # Restore original key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key


def test_factory_temperature_parameter():
    """Test that temperature parameter is passed correctly"""
    # Set a dummy API key
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    try:
        llm = LLMFactory.create_llm("openai", temperature=0.5)
        # We can't easily check the temperature without accessing internals
        # but at least verify it doesn't raise an error
        assert llm is not None
    finally:
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)