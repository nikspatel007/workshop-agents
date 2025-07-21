# Iteration 1 → Iteration 2 Handoff

## What's Ready for You

### Working BS Detection Function
```python
from modules.m1_baseline import check_claim
from config.llm_factory import LLMFactory

llm = LLMFactory.create_llm()
result = check_claim("The A380 has 6 engines", llm)

# Result structure:
{
    "verdict": "BS",
    "confidence": 92,
    "reasoning": "The A380 has 4 engines, not 6...",
    "error": None
}
```

### Established Patterns
- Structured output format (dict with 4 keys)
- Error handling that returns structured errors
- Performance baseline of < 2 seconds
- Test coverage showing 87% accuracy

### Known Limitations
1. Single LLM call can be inconsistent
2. No structured output guarantees
3. Limited context for complex claims
4. No retry mechanism for failures

## What You'll Build in Iteration 2

### BSAgent Class
Transform the simple function into a proper agent:
```python
class BSAgent:
    def __init__(self, llm, config=None):
        self.llm = llm
        self.config = config or {}
    
    def check(self, claim: str) -> BSCheckResult:
        # Your implementation here
        pass
```

### Pydantic Models
Create structured input/output models:
```python
class ClaimInput(BaseModel):
    claim: str
    context: Optional[str] = None
    
class BSCheckResult(BaseModel):
    verdict: Literal["BS", "LEGITIMATE"]
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    processing_time: float
    retry_count: int = 0
```

### Enhanced Features
1. **Retry Logic**: Handle transient failures
2. **Structured Output**: Use Pydantic for validation
3. **Logging**: Track agent operations
4. **Configuration**: Customizable behavior
5. **Async Support**: Prepare for future scaling

## Interface Contract

### Input Enhancement
```python
# From simple string
claim = "The 747 can fly backwards"

# To structured input
claim_input = ClaimInput(
    claim="The 747 can fly backwards",
    context="Discussing aircraft capabilities"
)
```

### Output Enhancement  
```python
# From dict
{"verdict": "BS", "confidence": 95, ...}

# To Pydantic model
BSCheckResult(
    verdict="BS",
    confidence=95,
    reasoning="Aircraft cannot fly backwards...",
    processing_time=1.23,
    retry_count=0
)
```

## Dependencies You'll Need

### New Imports
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json
```

### Base Agent Pattern
```python
# From CLAUDE.md
class BaseAgent:
    """All agents inherit from this"""
    def __init__(self, llm, tools=None):
        self.llm = llm
        self.tools = tools or []
    
    async def process(self, input_data):
        """Override in subclasses"""
        raise NotImplementedError
```

## Key Improvements to Make

### 1. Reliability
- Add retry logic for LLM failures
- Validate outputs with Pydantic
- Handle edge cases better
- Log all operations

### 2. Consistency  
- Use JSON mode if available
- Implement caching for development
- Standardize error messages
- Add operation tracking

### 3. Extensibility
- Configuration system
- Plugin points for future tools
- Async-ready architecture
- Clean class hierarchy

## Testing Requirements

### Unit Tests to Add
```python
def test_agent_retry_logic():
    """Test that agent retries on failure"""
    
def test_pydantic_validation():
    """Test input/output validation"""
    
def test_async_operation():
    """Test async check method"""
    
def test_configuration():
    """Test agent configuration options"""
```

### Performance Targets
- Maintain < 2 second response time
- Add < 100ms overhead vs baseline
- Support concurrent operations
- Memory efficient for batches

## Migration Guide

### Update Existing Code
```python
# Old way
from modules.m1_baseline import check_claim
result = check_claim(claim, llm)

# New way  
from modules.m2_agent import BSAgent
agent = BSAgent(llm)
result = agent.check(claim)
# or
result = await agent.acheck(claim)
```

### Backward Compatibility
Consider providing a compatibility function:
```python
def check_claim_compat(claim: str, llm) -> dict:
    """Backward compatible function"""
    agent = BSAgent(llm)
    result = agent.check(claim)
    return result.dict()
```

## Design Considerations

### Why Agent Pattern?
1. **Encapsulation**: State and behavior together
2. **Reusability**: Easy to instantiate multiple agents
3. **Extensibility**: Inherit and override
4. **Testability**: Mock and test in isolation

### Why Pydantic?
1. **Validation**: Automatic input/output validation
2. **Documentation**: Self-documenting models
3. **Serialization**: Easy JSON conversion
4. **Type Safety**: IDE support and type checking

### Why Retry Logic?
1. **Reliability**: Handle transient failures
2. **Cost**: Avoid wasting successful partial work
3. **User Experience**: Smoother operation
4. **Production Ready**: Essential for real use

## Your Deliverables
1. `modules/m2_agent.py` - BSAgent implementation
2. `modules/models.py` - Pydantic models
3. `tests/test_agent.py` - Comprehensive tests
4. `notebooks/02_Agent.ipynb` - Demo notebook
5. Updated performance metrics

## Success Criteria
- ✅ BSAgent class with proper inheritance
- ✅ Pydantic models for I/O
- ✅ Retry logic (max 3 attempts)
- ✅ Async support
- ✅ Maintains baseline performance
- ✅ Improved consistency
- ✅ Clean, documented code

Remember: This iteration is about structure and reliability, not new functionality!