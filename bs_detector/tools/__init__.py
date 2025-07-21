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