"""
Iteration 4: Tool-Enhanced BS Detector with Web Search
Builds on m2_langgraph.py by adding web search capabilities
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from modules.m1_baseline import check_claim
from config.llm_factory import LLMFactory
from tools.search_tool import WebSearchTool, generate_search_queries


class BSDetectorState(BaseModel):
    """Enhanced state with search capabilities"""
    # Input
    claim: str
    
    # Initial assessment (from baseline)
    initial_verdict: Optional[str] = None
    initial_confidence: Optional[int] = None
    initial_reasoning: Optional[str] = None
    
    # Search decision
    needs_search: bool = False
    confidence_threshold: int = 70
    
    # Search process
    search_queries: List[str] = Field(default_factory=list)
    search_results: List[dict] = Field(default_factory=list)
    extracted_facts: List[str] = Field(default_factory=list)
    
    # Evidence analysis
    evidence_summary: Optional[str] = None
    evidence_supports_claim: Optional[bool] = None
    
    # Final assessment
    final_verdict: Optional[str] = None
    final_confidence: Optional[int] = None
    final_reasoning: Optional[str] = None
    
    # Metadata
    sources_used: List[str] = Field(default_factory=list)
    used_search: bool = False
    error: Optional[str] = None


# Node functions
def initial_check_node(state: BSDetectorState) -> dict:
    """Initial BS detection using baseline detector"""
    llm = LLMFactory.create_llm()
    
    try:
        # Use baseline detector
        result = check_claim(state.claim, llm)
        
        # Determine if search needed
        confidence = result.get("confidence", 0)
        needs_search = confidence < state.confidence_threshold
        
        return {
            "initial_verdict": result.get("verdict"),
            "initial_confidence": confidence,
            "initial_reasoning": result.get("reasoning"),
            "needs_search": needs_search
        }
    except Exception as e:
        return {
            "error": f"Initial check failed: {str(e)}",
            "needs_search": True  # Search on error
        }


def generate_queries_node(state: BSDetectorState) -> dict:
    """Generate search queries for the claim"""
    queries = generate_search_queries(state.claim, num_queries=3)
    return {"search_queries": queries}


def search_web_node(state: BSDetectorState) -> dict:
    """Perform web search for evidence"""
    tool = WebSearchTool(max_results=3)
    
    try:
        # Search all queries
        search_results = tool.search_multiple(state.search_queries)
        
        # Extract facts
        facts = tool.extract_facts(search_results)
        
        # Extract sources
        sources = []
        for result in search_results:
            if result.get("success") and result.get("results"):
                sources.append(result["query"])
        
        return {
            "search_results": search_results,
            "extracted_facts": facts,
            "sources_used": sources,
            "used_search": True
        }
    except Exception as e:
        return {
            "error": f"Search failed: {str(e)}",
            "used_search": True
        }


def analyze_evidence_node(state: BSDetectorState) -> dict:
    """Analyze search results and determine if they support/refute the claim"""
    if not state.extracted_facts:
        return {
            "evidence_summary": "No evidence found through search.",
            "evidence_supports_claim": None
        }
    
    llm = LLMFactory.create_llm()
    
    # Create evidence summary
    facts_text = "\n".join(f"- {fact}" for fact in state.extracted_facts[:5])
    
    prompt = f"""
    Analyze this evidence in relation to the claim.
    
    Claim: {state.claim}
    
    Evidence found:
    {facts_text}
    
    Provide:
    1. A brief summary of what the evidence shows
    2. Whether the evidence SUPPORTS, REFUTES, or is INCONCLUSIVE regarding the claim
    3. Key facts that influenced your assessment
    
    Format your response as:
    SUMMARY: [1-2 sentences]
    ASSESSMENT: [SUPPORTS/REFUTES/INCONCLUSIVE]
    KEY FACTS: [List 2-3 most relevant facts]
    """
    
    try:
        response = llm.invoke(prompt)
        analysis = response.content
        
        # Parse assessment
        supports = None
        if "REFUTES" in analysis.upper():
            supports = False
        elif "SUPPORTS" in analysis.upper():
            supports = True
        
        return {
            "evidence_summary": analysis,
            "evidence_supports_claim": supports
        }
    except Exception as e:
        return {
            "evidence_summary": f"Evidence analysis failed: {str(e)}",
            "evidence_supports_claim": None
        }


def revise_verdict_node(state: BSDetectorState) -> dict:
    """Revise verdict based on evidence"""
    # If no evidence or analysis failed, keep initial verdict
    if state.evidence_supports_claim is None:
        return {
            "final_verdict": state.initial_verdict,
            "final_confidence": max(state.initial_confidence - 10, 40),  # Lower confidence
            "final_reasoning": f"{state.initial_reasoning}\n\nNote: Web search was attempted but didn't provide clear evidence."
        }
    
    # Strong evidence against initial verdict
    if state.evidence_supports_claim == False and state.initial_verdict == "LEGITIMATE":
        return {
            "final_verdict": "BS",
            "final_confidence": 80,
            "final_reasoning": f"Initially seemed legitimate, but evidence indicates otherwise.\n\n{state.evidence_summary}"
        }
    elif state.evidence_supports_claim == True and state.initial_verdict == "BS":
        return {
            "final_verdict": "LEGITIMATE",
            "final_confidence": 80,
            "final_reasoning": f"Initially seemed like BS, but evidence supports the claim.\n\n{state.evidence_summary}"
        }
    
    # Evidence confirms initial verdict
    confidence_boost = 15 if state.evidence_supports_claim else 0
    return {
        "final_verdict": state.initial_verdict,
        "final_confidence": min(state.initial_confidence + confidence_boost, 95),
        "final_reasoning": f"{state.initial_reasoning}\n\nEvidence analysis:\n{state.evidence_summary}"
    }


def format_output_node(state: BSDetectorState) -> dict:
    """Format final output"""
    # Use final verdict if search was done, otherwise initial
    if state.used_search:
        verdict = state.final_verdict or state.initial_verdict
        confidence = state.final_confidence or state.initial_confidence
        reasoning = state.final_reasoning or state.initial_reasoning
    else:
        verdict = state.initial_verdict
        confidence = state.initial_confidence
        reasoning = state.initial_reasoning
    
    # Add source attribution
    if state.sources_used:
        reasoning += f"\n\nSources consulted: {len(state.sources_used)} web searches"
    
    return {
        "final_verdict": verdict,
        "final_confidence": confidence,
        "final_reasoning": reasoning
    }


# Routing functions
def route_after_initial_check(state: BSDetectorState) -> str:
    """Route based on confidence level"""
    if state.needs_search:
        return "generate_queries"
    return "format_output"


# Note: route_after_evidence was removed as it's not used in the current graph


# Build the graph
def create_bs_detector_with_tools():
    """Create the tool-enhanced BS detector graph"""
    workflow = StateGraph(BSDetectorState)
    
    # Add nodes
    workflow.add_node("initial_check", initial_check_node)
    workflow.add_node("generate_queries", generate_queries_node)
    workflow.add_node("search_web", search_web_node)
    workflow.add_node("analyze_evidence", analyze_evidence_node)
    workflow.add_node("revise_verdict", revise_verdict_node)
    workflow.add_node("format_output", format_output_node)
    
    # Add edges
    workflow.set_entry_point("initial_check")
    
    # Conditional routing after initial check
    workflow.add_conditional_edges(
        "initial_check",
        route_after_initial_check,
        {
            "generate_queries": "generate_queries",
            "format_output": "format_output"
        }
    )
    
    # Linear flow for search path
    workflow.add_edge("generate_queries", "search_web")
    workflow.add_edge("search_web", "analyze_evidence")
    workflow.add_edge("analyze_evidence", "revise_verdict")
    workflow.add_edge("revise_verdict", "format_output")
    
    # End
    workflow.add_edge("format_output", END)
    
    # Compile
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Convenience function
def check_claim_with_tools(claim: str) -> dict:
    """Check a claim using tool-enhanced detection"""
    app = create_bs_detector_with_tools()
    
    # Run the graph
    config = {"configurable": {"thread_id": "tools-1"}}
    state = BSDetectorState(claim=claim)
    result = app.invoke(state.model_dump(), config)
    
    return {
        "verdict": result.get("final_verdict"),
        "confidence": result.get("final_confidence"),
        "reasoning": result.get("final_reasoning"),
        "used_search": result.get("used_search", False),
        "sources": result.get("sources_used", [])
    }


# Demo
if __name__ == "__main__":
    print("Tool-Enhanced BS Detector Demo")
    print("=" * 50)
    
    # Test claims that benefit from search
    test_claims = [
        # Low confidence - should trigger search
        "The Boeing 797 will have quantum engines",
        
        # Factual claim - search should help
        "The Concorde could fly at Mach 2.04",
        
        # High confidence - might skip search
        "Airplanes can fly backwards like helicopters",
    ]
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        print("-" * 40)
        
        result = check_claim_with_tools(claim)
        
        print(f"Verdict: {result['verdict']}")
        print(f"Confidence: {result['confidence']}%")
        print(f"Used Search: {'Yes' if result['used_search'] else 'No'}")
        
        if result['sources']:
            print(f"Sources: {len(result['sources'])} searches performed")
        
        print(f"\nReasoning: {result['reasoning'][:200]}...")