# AI Agents Workshop Development Guide

## Project Goal
Build a BS detector using multi-agent architecture with LangChain/LangGraph, demonstrating real-world patterns for evidence-based fact-checking.

## Core Principles
- **DRY**: Create reusable components (agents, tools, prompts)
- **KISS**: Start simple, add complexity incrementally
- **SOLID**: Each module has single responsibility
- **YAGNI**: Only implement what's needed for workshop

## Naming Conventions
- **Files**: `snake_case.py` (e.g., `claim_extractor.py`)
- **Classes**: `PascalCase` (e.g., `ClaimExtractor`)
- **Functions**: `snake_case` (e.g., `extract_claims()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Modules**: Prefix with `m{number}_` for workshop order

## Architecture Overview
```
Input → Claim Extraction → Evidence Search → Credibility Scoring → Report Generation
         ↓                  ↓                 ↓                    ↓
         LLM               MCP/DuckDuckGo    LLM + Rules         LLM + Template
```

## Available MCP Tools
- **Playwright**: Browser automation for web scraping
- **Sequential Thinking**: Complex reasoning chains
- **Memory**: Persistent context across sessions
- **Context7**: Library documentation lookup
- **DuckDuckGo**: Web search (primary evidence source)

## Development Workflow

### 1. Module Structure
Each module should:
- Have clear input/output contracts
- Include type hints
- Handle errors gracefully
- Be testable in isolation

### 2. Agent Pattern
```python
class BaseAgent:
    """All agents inherit from this"""
    def __init__(self, llm, tools=None):
        self.llm = llm
        self.tools = tools or []
    
    async def process(self, input_data):
        """Override in subclasses"""
        raise NotImplementedError
```

### 3. Tool Integration
```python
# Use MCP tools via LangChain wrappers
from langchain.tools import Tool

def create_search_tool():
    return Tool(
        name="web_search",
        func=duckduckgo_search,
        description="Search web for evidence"
    )
```

### 4. Error Handling
```python
# Always provide fallbacks
try:
    evidence = await search_tool.run(query)
except Exception as e:
    logger.warning(f"Search failed: {e}")
    evidence = {"error": "Search unavailable", "fallback": True}
```

## Implementation Checklist

### Module 0: Setup ✓
- [ ] LLM factory for multiple providers
- [ ] Environment detection (Jupyter/Colab/SageMaker)
- [ ] MCP server configuration

### Module 1: Baseline
- [ ] Simple claim → verdict function
- [ ] Basic prompt template
- [ ] Response parsing

### Module 2: Structured Agent
- [ ] Agent base class
- [ ] Input/output models (Pydantic)
- [ ] Retry logic

### Module 3: Claim Extraction
- [ ] Split text into atomic claims
- [ ] Claim deduplication
- [ ] Relevance filtering

### Module 4: Evidence Search
- [ ] DuckDuckGo MCP integration
- [ ] Query generation strategy
- [ ] Result ranking/filtering

### Module 5: Human-in-the-Loop
- [ ] Confidence thresholds
- [ ] Review UI (Jupyter widgets)
- [ ] Decision logging

### Module 6: Orchestration
- [ ] LangGraph state machine
- [ ] Error recovery
- [ ] Performance monitoring

## Testing Strategy
```python
# Each module has accompanying tests
def test_claim_extraction():
    extractor = ClaimExtractor()
    claims = extractor.extract("The 747 has 4 engines. It flies at 500mph.")
    assert len(claims) == 2
    assert "747" in claims[0]
```

## Agent Evaluation Framework

### Recommended: DeepEval
DeepEval is the top choice for LLM agent evaluation in 2024 because:
- Treats evaluations as unit tests (Pytest integration)
- Comprehensive metrics for RAG and agent applications
- Self-explaining metrics for debugging
- Deterministic tool correctness evaluation

### Key Metrics for BS Detector

#### 1. Tool Correctness (Primary)
```python
from deepeval.metrics import ToolCorrectnessMetric

metric = ToolCorrectnessMetric()
# Evaluate if agent calls DuckDuckGo search correctly
test_case = LLMTestCase(
    input="The A380 has 6 engines",
    expected_tools=["web_search"],
    actual_tools=agent.get_tools_called()
)
```

#### 2. Answer Relevancy
```python
from deepeval.metrics import AnswerRelevancyMetric

# Ensure BS verdict matches evidence
metric = AnswerRelevancyMetric(threshold=0.8)
```

#### 3. Hallucination Detection
```python
from deepeval.metrics import HallucinationMetric

# Critical for fact-checking system
metric = HallucinationMetric(threshold=0.1)
```

#### 4. Custom G-Eval Metrics
```python
from deepeval.metrics import GEval

# Domain-specific aviation accuracy
aviation_accuracy = GEval(
    name="Aviation Fact Accuracy",
    criteria="The verdict must correctly identify false aviation claims",
    evaluation_params=["input", "output", "evidence"]
)
```

### Evaluation Pipeline
```python
# tests/evaluate_pipeline.py
import deepeval
from deepeval.test_case import LLMTestCase

def evaluate_bs_detector():
    test_cases = [
        LLMTestCase(
            input="The 747 can fly backwards",
            expected_output="BS",
            expected_tools=["web_search"],
            context=["Boeing 747 specifications"]
        )
    ]
    
    metrics = [
        ToolCorrectnessMetric(),
        AnswerRelevancyMetric(threshold=0.8),
        HallucinationMetric(threshold=0.1)
    ]
    
    deepeval.evaluate(test_cases, metrics)
```

### Alternative Frameworks
- **RAGAs**: Good for RAG-specific metrics but less flexible
- **UpTrain**: User-friendly dashboards, API-based
- **Berkeley Function Calling Leaderboard**: Industry standard for tool calling

## Performance Targets
- Claim extraction: < 2s per paragraph
- Evidence search: < 5s per claim
- Full pipeline: < 30s for typical input

## Common Pitfalls to Avoid
1. **Over-engineering**: Workshop is 1.5 hours, not production
2. **API limits**: Cache results, batch requests
3. **Blocking I/O**: Use async where possible
4. **Large contexts**: Summarize evidence before scoring

## Quick Commands
```bash
# Install dependencies
pip install -r bs_detector/requirements.txt

# Run tests
pytest bs_detector/tests/ -v

# Test individual modules
python -m modules.m1_baseline

# Run full pipeline
python orchestrate.py "The A380 can fly backwards"

# Start notebook server
jupyter lab --NotebookApp.token=''
```

## Debug Mode
Set environment variable for verbose logging:
```bash
export BS_DETECTOR_DEBUG=1
```

## Next Session TODOs
When continuing development, check:
1. Last completed module
2. Any failing tests
3. Performance bottlenecks
4. User feedback from workshop trials