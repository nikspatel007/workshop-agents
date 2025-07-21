"""
Unit tests for tools package.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import tool_registry
from tools.mock_search import search_aviation_facts


def test_tool_registry():
    """Test tool registry functionality"""
    # Test listing tools
    tools = tool_registry.list_tools()
    assert "echo" in tools
    
    # Test getting a tool
    echo = tool_registry.get("echo")
    assert echo is not None
    assert echo("test") == "Echo: test"
    
    # Test registering a new tool
    def test_tool(x: int) -> int:
        return x * 2
    
    tool_registry.register("double", test_tool)
    assert "double" in tool_registry.list_tools()
    
    double = tool_registry.get("double")
    assert double(5) == 10


def test_tool_not_found():
    """Test that getting non-existent tool raises error"""
    with pytest.raises(ValueError) as exc_info:
        tool_registry.get("nonexistent")
    
    assert "Tool 'nonexistent' not found" in str(exc_info.value)


def test_mock_search():
    """Test mock search functionality"""
    # Test 747 search
    results = search_aviation_facts("Boeing 747")
    assert len(results) > 0
    assert any("747" in fact["fact"] for fact in results)
    
    # Test Concorde search
    results = search_aviation_facts("Concorde speed")
    assert len(results) > 0
    assert any("Concorde" in fact["fact"] for fact in results)
    
    # Test default search
    results = search_aviation_facts("random query")
    assert len(results) > 0
    assert results[0]["confidence"] > 0