# Iteration 4: Tool Integration - Web Search

## Overview
In this iteration, we add web search capabilities to our BS detector. This addresses a key limitation discovered in Iteration 3: the detector struggles with claims that need external verification.

## What We Build
- Integration of DuckDuckGo web search tool
- Smart search query generation
- Evidence-based verdict revision
- Conditional tool usage based on confidence

## Key Learning Objectives
1. **Tool Integration in LangGraph**
   - How to add tools to graph nodes
   - Tool invocation patterns
   - Handling tool responses

2. **Conditional Tool Usage**
   - Only search when needed (low confidence)
   - Cost-effective tool usage
   - Graceful fallbacks

3. **Evidence-Based Reasoning**
   - Incorporating external information
   - Revising decisions based on evidence
   - Source attribution

## Project Structure
```
bs_detector/
├── modules/
│   ├── m1_baseline.py         # From Iteration 1
│   ├── m2_langgraph.py        # From Iteration 2
│   ├── m3_evaluation.py       # From Iteration 3
│   └── m4_tools.py            # NEW: Tool-enhanced detector
├── tools/
│   └── search_tool.py         # NEW: Web search wrapper
├── tests/
│   └── test_tools.py          # NEW: Tool integration tests
└── notebooks/
    └── 04_Tools.ipynb         # NEW: Interactive tutorial
```

## Core Components

### 1. Enhanced State Model
```python
class BSDetectorState(BaseModel):
    # Input
    claim: str
    
    # Initial assessment
    initial_verdict: Optional[str] = None
    initial_confidence: Optional[int] = None
    initial_reasoning: Optional[str] = None
    
    # Search process
    needs_search: bool = False
    search_queries: List[str] = Field(default_factory=list)
    search_results: List[dict] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    
    # Final assessment
    final_verdict: Optional[str] = None
    final_confidence: Optional[int] = None
    final_reasoning: Optional[str] = None
    
    # Metadata
    sources_used: List[str] = Field(default_factory=list)
```

### 2. Graph Structure
```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Initial Check│ (Reuses m1_baseline)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Confidence │
│   Router    │──High──→ Format Output
└──────┬──────┘
       │Low
       ▼
┌─────────────┐
│Generate     │
│Search Query │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Web Search   │ (DuckDuckGo)
│    Tool     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Analyze    │
│  Evidence   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Revise    │
│   Verdict   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Format Output│
└──────┬──────┘
       │
       ▼
      END
```

### 3. Tool Integration Pattern
```python
from langchain_community.tools import DuckDuckGoSearchRun

# Tool setup
search_tool = DuckDuckGoSearchRun()

# Tool node
def search_evidence_node(state: BSDetectorState) -> dict:
    """Search for evidence using web search"""
    results = []
    for query in state.search_queries:
        try:
            search_results = search_tool.invoke(query)
            results.append({
                "query": query,
                "results": search_results
            })
        except Exception as e:
            print(f"Search error: {e}")
    
    return {"search_results": results}
```

## How It Works

1. **Initial Assessment**: Run claim through baseline detector
2. **Confidence Check**: If confidence < 70%, trigger search
3. **Query Generation**: Create relevant search queries
4. **Web Search**: Use DuckDuckGo to find evidence
5. **Evidence Analysis**: Extract relevant facts from results
6. **Verdict Revision**: Update verdict based on evidence
7. **Output**: Return final verdict with sources

## Success Criteria
1. ✅ Web search tool successfully integrated
2. ✅ Conditional routing based on confidence
3. ✅ Evidence improves accuracy on fact-checkable claims
4. ✅ Sources are properly attributed
5. ✅ Graceful handling of search failures

## Time Estimate
- **Setup and tool integration**: 5 minutes
- **Graph implementation**: 5 minutes
- **Testing and notebook**: 5 minutes
- **Documentation**: 5 minutes
- **Total**: 20 minutes

## Next Steps
After completing this iteration, we'll have:
- A BS detector that can fact-check using the internet
- Understanding of tool integration patterns
- Foundation for adding more tools
- Ready for Iteration 5: Human-in-the-Loop

## Key Takeaway
Tools transform agents from closed-system reasoners to open-world problem solvers!