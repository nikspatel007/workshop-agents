# Iteration 0: Testing Guide

## Test Overview
This iteration focuses on testing the foundational components: LLM factory, environment detection, and MCP connectivity.

## Running Tests

### 1. Unit Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=config --cov=tools

# Run specific test file
pytest tests/test_llm_factory.py -v
```

### 2. Manual Testing

#### Test LLM Factory
```python
# In a Python shell or notebook
from config.llm_factory import LLMFactory

# Test each provider (ensure API keys are set)
providers = ["openai", "anthropic", "bedrock", "azure"]

for provider in providers:
    try:
        llm = LLMFactory.create_llm(provider)
        response = llm.invoke("Say 'Hello, workshop!'")
        print(f"{provider}: ✓ {response.content[:50]}...")
    except Exception as e:
        print(f"{provider}: ✗ {str(e)}")
```

#### Test Environment Detection
```python
from config.settings import detect_environment, get_settings

# Check environment
env = detect_environment()
print(f"Detected environment: {env}")

# Get all settings
settings = get_settings()
for key, value in settings.items():
    print(f"{key}: {value}")
```

#### Test MCP Connection
```python
import asyncio
from tools.mcp_client import MCPClient

async def test_mcp():
    client = MCPClient()
    connected = await client.test_connection()
    print(f"MCP connection: {'✓' if connected else '✗'}")

asyncio.run(test_mcp())
```

## Validation Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] All dependencies installed from requirements.txt
- [ ] At least one LLM API key configured
- [ ] Node.js installed (for MCP)
- [ ] DuckDuckGo MCP server installed

### LLM Factory
- [ ] Can create LLM instance with default provider
- [ ] Handles missing API keys gracefully
- [ ] Supports all four providers (if keys available)
- [ ] Temperature parameter works correctly
- [ ] Error messages are clear and helpful

### Environment Detection
- [ ] Correctly identifies Jupyter environment
- [ ] Correctly identifies Colab (if testing in Colab)
- [ ] Correctly identifies SageMaker (if testing in SageMaker)
- [ ] Falls back to "local" appropriately
- [ ] Settings are environment-appropriate

### MCP Setup
- [ ] mcp_config.json is valid JSON
- [ ] MCP server can be started
- [ ] Connection test passes
- [ ] Error handling works for missing config

## Performance Benchmarks

### LLM Factory Creation
- Target: < 100ms to create LLM instance
- Measure with:
```python
import time

start = time.time()
llm = LLMFactory.create_llm()
end = time.time()
print(f"Factory creation time: {(end - start)*1000:.2f}ms")
```

### Environment Detection
- Target: < 10ms
- Should be near-instantaneous

## Common Issues and Solutions

### Issue: ImportError for LLM providers
**Solution**: Install the specific provider package
```bash
pip install langchain-openai  # For OpenAI
pip install langchain-anthropic  # For Anthropic
pip install langchain-aws  # For Bedrock
```

### Issue: MCP server won't start
**Solution**: Check Node.js installation
```bash
node --version  # Should be 14.x or higher
npm --version   # Should be 6.x or higher
```

### Issue: API key not found
**Solution**: Check .env file location and format
```bash
# .env should be in project root
# Format: KEY=value (no quotes unless part of value)
```

## DeepEval Integration Test

```python
# tests/test_setup_deepeval.py
import deepeval
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

def test_llm_basic_response():
    """Test that LLM gives relevant responses"""
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm()
    
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output=llm.invoke("What is the capital of France?").content
    )
    
    metric = AnswerRelevancyMetric(threshold=0.8)
    assert metric.measure(test_case)
```

## Success Criteria
✅ All unit tests pass
✅ Manual tests work for at least one LLM provider
✅ Environment detection is accurate
✅ MCP connection test succeeds
✅ No import errors
✅ Performance targets met