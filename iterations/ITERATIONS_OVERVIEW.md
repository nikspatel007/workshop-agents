# BS Detector Workshop: Iterations Overview

## Overview
This document outlines all iterations for building the BS detector system. Each iteration builds upon the previous one, gradually increasing complexity while maintaining clear learning objectives.

## Iteration Progression

### ✅ Iteration 0: Environment & LLM Setup (10 min)
**Status**: Documentation Complete

**What We Build**:
- LLM factory pattern for provider abstraction
- Environment detection (Jupyter/Colab/SageMaker)
- MCP server configuration
- Project structure and testing framework

**Key Learning**:
- Factory pattern implementation
- Cross-platform compatibility
- Configuration management
- Development environment setup

**Deliverables**:
- `config/llm_factory.py`
- `config/settings.py`
- `tools/mcp_client.py`
- Test infrastructure

---

### ✅ Iteration 1: Simple BS Detector (15 min)
**Status**: Documentation Complete

**What We Build**:
- Basic `check_claim()` function
- Aviation-focused prompt engineering
- Response parsing with regex
- Performance baseline establishment

**Key Learning**:
- Prompt engineering techniques
- LLM response parsing
- Error handling patterns
- Performance measurement

**Deliverables**:
- `modules/m1_baseline.py`
- Test suite with DeepEval
- Performance benchmarks
- Interactive notebook

---

### 📝 Iteration 2: Introduction to LangGraph (15 min)
**Status**: Documentation Complete

**What We Build**:
- First LangGraph-based BS detector
- Understanding of nodes, state, edges, routing
- Retry logic using graph cycles
- Simple chat interface for testing

**Key Learning**:
- **Node**: Function that processes state
- **State**: Shared data between nodes (TypedDict)
- **Edge**: Connection between nodes
- **Routing**: Conditional flow control
- **Graph**: Complete state machine

**Core Components**:
```python
# 1. State
class BSDetectorState(TypedDict):
    claim: str
    verdict: Optional[str]
    retry_count: int

# 2. Node
def detect_bs_node(state) -> dict:
    return {"verdict": "BS"}

# 3. Graph
graph = StateGraph(BSDetectorState)
graph.add_node("detect", detect_bs_node)
graph.compile()
```

**Execution Patterns**:
- Single run: `app.invoke(state)`
- Chat loop: Simple input/output loop

**Expected Understanding**:
- How to build a graph step by step
- State management basics
- Conditional routing for retries
- Two ways to execute graphs

---

### 📝 Iteration 3: Multi-Step Processing (15 min)
**Status**: Planned

**What We Build**:
- Multi-node graph for claim extraction
- Chain of processing steps
- More complex state management
- Advanced routing patterns

**Key Learning**:
- Building processing pipelines
- State with lists and complex data
- Multiple routing conditions
- Node composition patterns

**Graph Structure**:
```python
# Multi-step processing
Start → Split → Extract → Deduplicate → Filter → Output
         ↓
      No Data → END
```

**Core Components**:
```python
class ExtractorState(TypedDict):
    text: str
    sentences: List[str]
    claims: List[dict]
    filtered_claims: List[dict]
    
graph.add_node("split", split_text_node)
graph.add_node("extract", extract_claims_node)
graph.add_conditional_edges("extract", has_claims_router, {...})
```

**Expected Capabilities**:
- Process text through multiple stages
- Handle variable-length outputs
- Conditional processing based on results
- Clean error propagation

---

### 📝 Iteration 4: Evidence-Based Checking (20 min)
**Status**: Planned

**What We Build**:
- DuckDuckGo MCP integration
- `EvidenceRetriever` agent
- Search query generation
- Evidence scoring system

**Key Learning**:
- MCP tool integration
- Search query optimization
- Evidence ranking algorithms
- Tool calling patterns

**Planned Components**:
```python
class EvidenceRetriever(BaseAgent):
    def __init__(self, llm, search_tool: DuckDuckGoMCPTool)
    async def find_evidence(self, claim: Claim) -> Evidence
    def generate_queries(self, claim: Claim) -> List[str]
    def score_evidence(self, evidence: List[SearchResult]) -> float
```

**Expected Improvements**:
- 40% accuracy improvement
- Real-time fact checking
- Source attribution
- Confidence calibration

---

### 📝 Iteration 5: Human-in-the-Loop (15 min)
**Status**: Planned

**What We Build**:
- Confidence threshold system
- Jupyter widget UI for reviews
- Decision logging mechanism
- Feedback incorporation

**Key Learning**:
- Human-AI collaboration patterns
- UI/UX for ML systems
- Decision audit trails
- Active learning concepts

**Planned Components**:
```python
class HumanReviewUI:
    def __init__(self, confidence_threshold: float = 0.7)
    def needs_review(self, result: BSCheckResult) -> bool
    def show_review_widget(self, claim: Claim, result: BSCheckResult)
    def log_decision(self, decision: HumanDecision)
```

**Expected Features**:
- Interactive review interface
- Confidence-based routing
- Decision history tracking
- Feedback loop for improvement

---

### 📝 Iteration 6: Full Orchestration (20 min)
**Status**: Planned

**What We Build**:
- LangGraph state machine
- Complete pipeline integration
- Error recovery strategies
- Performance monitoring

**Key Learning**:
- Workflow orchestration
- State management patterns
- Pipeline optimization
- Production considerations

**Planned Components**:
```python
class BSDetectorPipeline:
    def __init__(self, agents: Dict[str, BaseAgent])
    def create_graph(self) -> Graph
    async def run(self, text: str) -> PipelineResult
    def visualize(self) -> None
```

**Expected Capabilities**:
- End-to-end processing
- Parallel agent execution
- State persistence
- Performance analytics

---

## Progressive Complexity

### Complexity Growth
- **Iteration 0-1**: Single function → Single LLM call
- **Iteration 2**: Function → LangGraph basics (node, state, edge, routing)
- **Iteration 3**: Single node → Multi-step pipeline
- **Iteration 4**: No tools → Web search integration
- **Iteration 5**: Automatic → Human oversight
- **Iteration 6**: Simple graphs → Full orchestration

### Skill Development
1. **Basic**: Prompt engineering, Pydantic models
2. **Intermediate**: LangGraph fundamentals, state management, routing
3. **Advanced**: Tool integration, complex graphs, orchestration

### Time Investment
- **Core iterations (0-3)**: 55 minutes
- **Advanced iterations (4-6)**: 55 minutes
- **Total workshop**: 110 minutes (leaving 10 min buffer)

## Implementation Strategy

### For Each Iteration
1. Review previous iteration's HANDOFF.md
2. Implement core functionality
3. Add tests with DeepEval
4. Create interactive notebook
5. Document lessons learned
6. Prepare handoff for next iteration

### Success Metrics
- Each iteration builds on previous
- Clear improvement in capabilities
- Maintainable, documented code
- Testable components
- Workshop-friendly timing

## Workshop Considerations

### Participant Experience
- **Beginners**: Focus on iterations 0-2
- **Intermediate**: Complete iterations 0-4
- **Advanced**: All iterations + extensions

### Fallback Options
- Pre-built solutions for each iteration
- Simplified versions for time constraints
- Optional extensions for fast learners

### Key Takeaways
1. Incremental development works
2. Structure improves reliability
3. Tools enhance capabilities
4. Human oversight matters
5. Orchestration enables scale