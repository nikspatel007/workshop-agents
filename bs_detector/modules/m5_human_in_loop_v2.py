"""
Iteration 5: Human-in-the-Loop Integration (Version 2)

This module adds a simple human review node that can be conditionally triggered.
Instead of using complex interrupts, we use a simple flag-based approach.
"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from modules.m4_tools import (
    ToolEnhancedState,
    current_events_expert_with_tools_node
)
from modules.m3_routing import (
    router_node,
    technical_expert_node,
    historical_expert_node,
    general_expert_node
)


class HumanInLoopState(ToolEnhancedState):
    """Extended state with human review fields"""
    needs_human_review: bool = False
    human_review_reason: Optional[str] = None
    skip_human_review: bool = False  # Flag to skip review in demo/test mode
    

def check_needs_review_node(state: HumanInLoopState) -> dict:
    """
    Check if human review is needed based on confidence and verdict
    """
    updates = {}
    
    # Skip if explicitly told to
    if state.skip_human_review:
        updates["needs_human_review"] = False
        return updates
    
    # Check conditions for human review
    if state.confidence and state.confidence < 50:
        updates["needs_human_review"] = True
        updates["human_review_reason"] = f"Low confidence: {state.confidence}%"
    elif state.verdict == "UNCERTAIN":
        updates["needs_human_review"] = True
        updates["human_review_reason"] = "AI returned uncertain verdict"
    elif state.claim_type == "current_event" and state.confidence and state.confidence < 70:
        updates["needs_human_review"] = True
        updates["human_review_reason"] = f"Current event with moderate confidence: {state.confidence}%"
    else:
        updates["needs_human_review"] = False
        
    return updates


def simulate_human_review_node(state: HumanInLoopState) -> dict:
    """
    Simulate human review for demo purposes
    In production, this would integrate with a real review system
    """
    print("\n" + "="*60)
    print("🤔 HUMAN REVIEW REQUESTED")
    print("="*60)
    print(f"\n**Claim**: {state.claim}")
    print(f"\n**AI Analysis**:")
    print(f"- Verdict: {state.verdict}")
    print(f"- Confidence: {state.confidence}%")
    print(f"- Reasoning: {state.reasoning}")
    print(f"\n**Review Reason**: {state.human_review_reason}")
    
    # Simulate human decision
    print("\n💭 Simulating human review...")
    
    # For demo: if confidence was very low, human increases it
    if state.confidence and state.confidence < 50:
        new_confidence = 85
        new_reasoning = f"Human review: Verified claim. {state.reasoning}"
    else:
        new_confidence = state.confidence
        new_reasoning = f"Human review: Confirmed AI assessment. {state.reasoning}"
    
    print(f"Human verdict: {state.verdict} (confidence: {new_confidence}%)")
    
    return {
        "confidence": new_confidence,
        "reasoning": new_reasoning
    }


def format_output_node(state: HumanInLoopState) -> dict:
    """Format the final output"""
    result = {
        "verdict": state.verdict or "ERROR",
        "confidence": state.confidence or 0,
        "reasoning": state.reasoning or "No reasoning provided",
        "claim_type": state.claim_type,
        "analyzing_agent": state.analyzing_agent,
        "used_search": state.search_performed,
        "tools_used": state.tools_used,
        "human_reviewed": state.needs_human_review,
        "human_review_reason": state.human_review_reason
    }
    
    if state.search_results:
        result["search_results"] = state.search_results
        
    return {"result": result}


def route_after_review_check(state: HumanInLoopState) -> str:
    """Route based on whether human review is needed"""
    if state.needs_human_review:
        return "human_review"
    else:
        return "format_output"


def create_human_in_loop_graph_v2():
    """
    Create the BS detector with human-in-the-loop (simplified version)
    """
    workflow = StateGraph(HumanInLoopState)
    
    # Add all nodes
    workflow.add_node("router", router_node)
    workflow.add_node("technical_expert", technical_expert_node)
    workflow.add_node("historical_expert", historical_expert_node)
    workflow.add_node("current_events_expert", current_events_expert_with_tools_node)
    workflow.add_node("general_expert", general_expert_node)
    workflow.add_node("check_needs_review", check_needs_review_node)
    workflow.add_node("human_review", simulate_human_review_node)
    workflow.add_node("format_output", format_output_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add edges from router to experts
    def route_to_expert(state: HumanInLoopState) -> str:
        if not state.claim_type:
            return "general_expert"
        return state.claim_type + "_expert"
    
    workflow.add_conditional_edges(
        "router",
        route_to_expert,
        {
            "technical_expert": "technical_expert",
            "historical_expert": "historical_expert", 
            "current_event_expert": "current_events_expert",
            "general_expert": "general_expert"
        }
    )
    
    # All experts go to review check
    for expert in ["technical_expert", "historical_expert", "current_events_expert", "general_expert"]:
        workflow.add_edge(expert, "check_needs_review")
    
    # Review check routes to human review or output
    workflow.add_conditional_edges(
        "check_needs_review",
        route_after_review_check,
        {
            "human_review": "human_review",
            "format_output": "format_output"
        }
    )
    
    # Human review goes to output
    workflow.add_edge("human_review", "format_output")
    
    # Output goes to END
    workflow.add_edge("format_output", END)
    
    return workflow.compile()


def check_claim_with_human_review_v2(claim: str, skip_human_review: bool = False) -> dict:
    """
    Check a claim with human-in-the-loop support
    
    Args:
        claim: The claim to check
        skip_human_review: If True, skip human review even if confidence is low
    
    Returns:
        Result dict with verdict, confidence, reasoning, etc.
    """
    app = create_human_in_loop_graph_v2()
    
    # Initial state
    initial_state = HumanInLoopState(
        claim=claim,
        skip_human_review=skip_human_review
    )
    
    # Run the graph
    result = app.invoke(initial_state.model_dump())
    
    # Return the result
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    
    # Fallback
    return {
        "verdict": result.get("verdict", "ERROR"),
        "confidence": result.get("confidence", 0),
        "reasoning": result.get("reasoning", "Processing failed"),
        "human_reviewed": result.get("needs_human_review", False)
    }


def demo():
    """Demo the human-in-the-loop system"""
    print("🤖 BS Detector with Human-in-the-Loop (v2)")
    print("=" * 50)
    
    test_claims = [
        ("The Boeing 747 has four engines", "High confidence claim"),
        ("A startup just invented teleportation", "Low confidence claim"),
        ("SpaceX launched yesterday", "Current event claim"),
    ]
    
    for claim, description in test_claims:
        print(f"\n\n{'='*70}")
        print(f"Testing: {description}")
        print(f"Claim: \"{claim}\"")
        print("="*70)
        
        result = check_claim_with_human_review_v2(claim)
        
        print(f"\n📊 Final Result:")
        print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
        print(f"Reasoning: {result['reasoning'][:100]}...")
        print(f"Human Reviewed: {result.get('human_reviewed', False)}")
        if result.get('human_review_reason'):
            print(f"Review Reason: {result['human_review_reason']}")


if __name__ == "__main__":
    demo()