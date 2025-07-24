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
         
All orchestrated via LangGraph State Machines with memory and tool management
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

### 2. LangGraph Agent Pattern

**IMPORTANT**: Always use Pydantic BaseModel for state management in LangGraph, never TypedDict.

```python
from langgraph.graph import StateGraph, State
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import BaseMessage

class AgentState(BaseModel):
    """Shared state for all agents - MUST use Pydantic BaseModel"""
    messages: List[BaseMessage] = Field(default_factory=list)
    current_claim: str = ""
    evidence: List[dict] = Field(default_factory=list)
    verdict: Optional[str] = None
    confidence: float = 0.0
    errors: List[str] = Field(default_factory=list)

def create_agent_graph():
    graph = StateGraph(AgentState)
    
    # Add nodes for each agent
    graph.add_node("claim_extractor", claim_extraction_node)
    graph.add_node("evidence_searcher", evidence_search_node)
    graph.add_node("bs_detector", bs_detection_node)
    
    # Define edges
    graph.add_edge("claim_extractor", "evidence_searcher")
    graph.add_edge("evidence_searcher", "bs_detector")
    
    # Compile and return
    return graph.compile()
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

## Notebook Documentation Standards

### Required for Each Notebook
1. **Title and Overview** - Clear description of what the iteration covers
2. **Mermaid Diagram** - Visual representation of the agent/system architecture
3. **Learning Objectives** - 3-5 bullet points of key takeaways
4. **Code Structure** - Clear sections with markdown headers
5. **Testing Examples** - Interactive cells demonstrating functionality

### Mermaid Diagram Template
```python
import base64
from IPython.display import Image, display

def render_mermaid_diagram(graph_definition):
    """Render mermaid diagram in Jupyter using mermaid.ink API"""
    graph_bytes = graph_definition.encode("utf-8")
    base64_string = base64.b64encode(graph_bytes).decode("ascii")
    image_url = f"https://mermaid.ink/img/{base64_string}?type=png"
    
    # Display the image
    return Image(url=image_url)

# Example usage
mermaid_graph = """
graph TD
    A[Input Text] --> B[Claim Extractor]
    B --> C{Multiple Claims?}
    C -->|Yes| D[Deduplicate]
    C -->|No| E[Single Claim]
    D --> F[BS Detector]
    E --> F
"""
display(render_mermaid_diagram(mermaid_graph))
```

## Implementation Checklist

### Module 0: Setup ✓
- [x] LLM factory for multiple providers
- [x] Environment detection (Jupyter/Colab/SageMaker)
- [x] MCP server configuration

### Module 1: Baseline ✓
- [x] Simple claim → verdict function
- [x] Basic prompt template
- [x] Response parsing

### Module 2: Prompt Engineering ✓
- [x] Structured prompts
- [x] Few-shot learning
- [x] Chain of thought
- [x] Pydantic structured output

### Module 3: LangGraph Integration ✓
- [x] LangGraph state definition
- [x] Input/output models (Pydantic)
- [x] Agent as graph node
- [x] State transitions and retry logic

### Module 4: Evaluation ✓
- [x] Test dataset creation
- [x] DeepEval integration
- [x] Baseline vs graph comparison
- [x] Metrics tracking

### Module 5: Tools & Routing ✓
- [x] Expert routing based on claim type
- [x] Tool integration (search)
- [x] Query generation strategy
- [x] Result aggregation in state

### Module 6: Human-in-the-Loop ✓
- [x] LangGraph interrupt() pattern
- [x] Conditional edges based on confidence
- [x] Human review with Command objects
- [x] State persistence for review

### Module 7: Memory Enhancement ✓
- [x] Entity extraction from claims
- [x] In-memory knowledge graph
- [x] Pattern detection for BS claims
- [x] Context retrieval for new claims
- [x] Simple implementation (no external deps)

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