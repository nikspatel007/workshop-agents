# BS Detector Workshop: Iterations Overview

## Overview
This document outlines all iterations for building the BS detector system. Each iteration builds upon the previous one, gradually increasing complexity while maintaining clear learning objectives.

## Iteration Progression

### ✅ Iteration 0: Environment & LLM Setup (10 min)
**Status**: Complete

**What We Build**:
- LLM factory pattern for provider abstraction
- Environment detection (Jupyter/Colab/SageMaker)
- Project structure and testing framework
- Basic MCP setup for later use

**Key Learning**:
- Factory pattern implementation
- Cross-platform compatibility
- Configuration management
- Development environment setup

**Deliverables**:
- `config/llm_factory.py`
- `config/settings.py`
- `tools/` directory structure
- Test infrastructure

---

### ✅ Iteration 1: Baseline BS Detector (15 min)
**Status**: Complete

**What We Build**:
- Basic `check_claim()` function with Pydantic
- Aviation-focused prompt engineering
- Structured output parsing
- Error handling and confidence scoring

**Key Learning**:
- Prompt engineering techniques
- Pydantic for structured outputs
- Error handling patterns
- Building a solid foundation

**Deliverables**:
- `modules/m1_baseline.py`
- Basic test suite
- Performance baseline
- Interactive notebook

---

### ✅ Iteration 2: Introduction to LangGraph (15 min)
**Status**: Complete

**What We Build**:
- Convert baseline to LangGraph architecture
- Add retry logic with exponential backoff
- Interactive chat interface
- Graph visualization

**Key Learning**:
- **Core LangGraph concepts**: State, Node, Edge, Routing, Graph
- State management with Pydantic BaseModel
- Conditional routing for control flow
- Building on previous work (wrapping baseline)

**Deliverables**:
- `modules/m2_langgraph.py`
- Graph-based BS detector with retry
- Chat interface pattern
- Visual graph representation

---

### 📝 Iteration 3: Adding Evaluation with DeepEval (15 min)
**Status**: Planned

**What We Build**:
- Systematic evaluation framework using DeepEval
- Custom metrics for BS detection accuracy
- Test dataset of aviation claims
- Performance tracking over iterations

**Key Learning**:
- LLM evaluation best practices
- DeepEval metrics (relevancy, hallucination, custom)
- Creating evaluation datasets
- Tracking improvements quantitatively

**Core Components**:
```python
# Custom metric for BS detection
class BSDetectionAccuracy(BaseMetric):
    def measure(self, test_case: LLMTestCase) -> float
    
# Evaluation suite
def evaluate_bs_detector(detector_func):
    test_cases = load_aviation_test_set()
    metrics = [BSDetectionAccuracy(), HallucinationMetric()]
    return deepeval.evaluate(test_cases, metrics)
```

**Why This Next**: Before adding complexity (tools, multi-agent), we need to measure if we're actually improving. This teaches students to think empirically about agent development.

---

### 📝 Iteration 4: Tool Integration - Web Search (20 min)
**Status**: Planned

**What We Build**:
- Add DuckDuckGo search tool to LangGraph
- New node for evidence gathering
- Tool-calling patterns in graphs
- Evidence-based verdict revision

**Key Learning**:
- Tool integration in LangGraph
- Tool binding to nodes
- State updates from tool results
- Conditional tool usage based on confidence

**Graph Evolution**:
```
Detect BS → Low Confidence? → Search Evidence → Revise Verdict
    ↓                                              ↓
High Confidence → Format Output ←─────────────────┘
```

**Core Components**:
```python
class BSDetectorState(BaseModel):
    claim: str
    initial_verdict: Optional[str]
    evidence: List[dict] = Field(default_factory=list)
    final_verdict: Optional[str]
    search_queries: List[str] = Field(default_factory=list)

def search_evidence_node(state: BSDetectorState) -> dict:
    if state.confidence < 70:  # Only search if uncertain
        queries = generate_search_queries(state.claim)
        evidence = search_tool.invoke(queries)
        return {"evidence": evidence, "search_queries": queries}
```

**Expected Improvements**:
- Higher accuracy on fact-checkable claims
- Source attribution for verdicts
- Measured improvement via DeepEval

---

### 📝 Iteration 5: Human-in-the-Loop (15 min)
**Status**: Planned

**What We Build**:
- Human review node in LangGraph
- Confidence-based routing to human
- Simple review interface (terminal/notebook)
- Feedback incorporation into verdict

**Key Learning**:
- Human-in-the-loop patterns with LangGraph
- Conditional routing based on confidence
- State persistence for human review
- Async human interaction handling

**Graph Evolution**:
```
Evidence Analysis → Confidence Check → Human Review → Final Verdict
                          ↓                              ↑
                   High Confidence → Auto Verdict ───────┘
```

**Core Components**:
```python
def route_to_human(state: BSDetectorState) -> str:
    if state.confidence < 60 or state.conflicting_evidence:
        return "human_review"
    return "auto_verdict"

def human_review_node(state: BSDetectorState) -> dict:
    # Show evidence and initial verdict
    print(f"Claim: {state.claim}")
    print(f"AI Verdict: {state.initial_verdict} ({state.confidence}%)")
    print(f"Evidence: {state.evidence}")
    
    human_verdict = input("Override verdict? (BS/LEGITIMATE/AGREE): ")
    return {"final_verdict": human_verdict, "human_reviewed": True}
```

---

### 📝 Iteration 6: Multi-Agent Orchestration (20 min)
**Status**: Planned

**What We Build**:
- Multiple specialized agents working together
- Orchestrator pattern with LangGraph
- Parallel processing capabilities
- Complete BS detection system

**Key Learning**:
- Multi-agent design patterns
- Agent specialization and communication
- Parallel node execution in LangGraph
- System-level thinking

**Agent Architecture**:
```
                    ┌─→ Claim Analyzer Agent
Input → Orchestrator ├─→ Evidence Searcher Agent  → Aggregator → Output
                    └─→ Fact Checker Agent
```

**Core Components**:
```python
class OrchestratorState(BaseModel):
    claim: str
    analysis_result: Optional[dict]
    search_result: Optional[dict]
    fact_check_result: Optional[dict]
    final_verdict: Optional[str]

# Parallel execution
graph.add_node("analyze", claim_analyzer_agent)
graph.add_node("search", evidence_searcher_agent)
graph.add_node("fact_check", fact_checker_agent)

# Fork from orchestrator
graph.add_edge("orchestrator", "analyze")
graph.add_edge("orchestrator", "search")
graph.add_edge("orchestrator", "fact_check")

# All merge at aggregator
graph.add_edge("analyze", "aggregator")
graph.add_edge("search", "aggregator")
graph.add_edge("fact_check", "aggregator")
```

---

## Progressive Complexity

### Building Blocks
1. **Iteration 0-1**: Foundation - LLM calls and structured outputs
2. **Iteration 2**: LangGraph basics - graphs, nodes, routing
3. **Iteration 3**: Evaluation - measuring what we build
4. **Iteration 4**: Tools - extending capabilities with search
5. **Iteration 5**: Human oversight - confidence-based escalation
6. **Iteration 6**: Multi-agent - specialized agents working together

### Key Principles
- Each iteration adds ONE major concept
- Always build on previous work (never throw away code)
- Measure improvements with DeepEval
- Keep the aviation domain throughout
- Maintain backward compatibility

### Time Investment
- **Foundation (0-2)**: 40 minutes
- **Enhancement (3-5)**: 50 minutes 
- **Advanced (6)**: 20 minutes
- **Buffer**: 10 minutes
- **Total**: 120 minutes

## Implementation Strategy

### For Each Iteration
1. Review previous HANDOFF.md
2. Add new capability to existing code
3. Measure improvement with DeepEval
4. Update notebook with new concepts
5. Document what changed and why

### Success Metrics
- Each iteration improves accuracy (measured)
- Code remains clean and modular
- Students understand WHY each addition matters
- Clear progression from simple to complex

## Workshop Flow

### Act 1: Foundation (40 min)
- Setup → Baseline → LangGraph basics
- Students can build basic agents

### Act 2: Enhancement (50 min)
- Evaluation → Tools → Human-in-loop
- Students learn to improve agents systematically

### Act 3: Advanced (20 min)
- Multi-agent orchestration
- Students see the full potential

### Flexibility
- Can stop after any iteration
- Each iteration is self-contained
- Fast learners can explore extensions

## Key Takeaways by Iteration
1. **Setup**: Good tooling matters
2. **Baseline**: Start simple, use structured outputs
3. **LangGraph**: Graphs enable complex flows
4. **Evaluation**: Measure everything
5. **Tools**: External data improves accuracy
6. **Human-in-loop**: Confidence-based escalation
7. **Multi-agent**: Specialization and orchestration