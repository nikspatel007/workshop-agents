"""
Integration tests that verify packages are installed correctly.
"""

import pytest


def test_langchain_core_installed():
    """Test that langchain core is installed"""
    try:
        import langchain
        assert langchain.__version__
    except ImportError:
        pytest.fail("langchain not installed. Run: pip install -r bs_detector/requirements.txt")


def test_langchain_community_installed():
    """Test that langchain community is installed"""
    try:
        import langchain_community
        assert langchain_community.__version__
    except ImportError:
        pytest.fail("langchain-community not installed. Run: pip install -r bs_detector/requirements.txt")


def test_provider_packages():
    """Test which provider packages are available"""
    available = []
    missing = []
    
    try:
        import langchain_openai
        available.append("langchain-openai")
    except ImportError:
        missing.append("langchain-openai")
    
    try:
        import langchain_anthropic
        available.append("langchain-anthropic")
    except ImportError:
        missing.append("langchain-anthropic")
    
    try:
        import langchain_aws
        available.append("langchain-aws")
    except ImportError:
        missing.append("langchain-aws")
    
    if available:
        print(f"\n✓ Available provider packages: {', '.join(available)}")
    if missing:
        print(f"✗ Missing provider packages: {', '.join(missing)}")
    
    # At least one provider should be installed
    if len(available) == 0:
        pytest.fail(
            "No LLM provider packages installed. Run: pip install -r bs_detector/requirements.txt\n"
            "This will install: langchain-openai, langchain-anthropic, langchain-aws"
        )


def test_other_dependencies():
    """Test other required dependencies"""
    import dotenv
    import pytest
    
    # Optional but recommended
    try:
        import langgraph
        print("✓ langgraph installed")
    except ImportError:
        print("  langgraph not installed (optional)")
    
    try:
        import deepeval
        print("✓ deepeval installed")
    except ImportError:
        print("  deepeval not installed (optional)")