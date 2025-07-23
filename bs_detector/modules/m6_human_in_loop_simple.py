"""
Iteration 6: Human-in-the-Loop Integration (Simplified)

This module uses LangGraph's built-in interrupt capability for human review.
Much simpler than the previous approach - uses graph interrupts when human input is needed.
"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from modules.m5_tools import (
    ToolEnhancedState,
    create_tool_enhanced_bs_detector,
    current_events_expert_with_tools_node
)
from modules.m5_routing import (
    router_node,
    technical_expert_node,
    historical_expert_node,
    general_expert_node
)
from config.llm_factory import LLMFactory


class HumanInLoopState(ToolEnhancedState):
    """Extended state with human review flag"""
    needs_human_review: bool = False
    human_review_reason: Optional[str] = None
    human_feedback_received: bool = False
    

def check_needs_review(state: HumanInLoopState) -> dict:
    """
    Check if human review is needed based on confidence and verdict
    This is a simple node that sets a flag for human review
    """
    updates = {}
    
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


def human_review_node(state: HumanInLoopState) -> dict:
    """
    Node that interrupts the graph for human input
    This node will cause the graph to pause and wait for human input
    """
    # This node simply returns the current state
    # The interrupt happens at the graph level
    print("\n" + "="*60)
    print("🤔 HUMAN REVIEW REQUESTED")
    print("="*60)
    print(f"\n**Claim**: {state.claim}")
    print(f"\n**AI Analysis**:")
    print(f"- Verdict: {state.verdict}")
    print(f"- Confidence: {state.confidence}%")
    print(f"- Reasoning: {state.reasoning}")
    print(f"\n**Review Reason**: {state.human_review_reason}")
    
    if state.search_results:
        print(f"\n**Search Results**: {len(state.search_results)} results found")
    
    print("\n" + "="*60)
    print("The graph is now interrupted. Human input required.")
    print("Please provide your verdict, confidence, and reasoning.")
    print("="*60 + "\n")
    
    # Return empty dict - the actual update will come from human input
    return {}


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
    if state.needs_human_review and not state.human_feedback_received:
        return "human_review"
    else:
        return "format_output"


def create_human_in_loop_graph():
    """
    Create the BS detector with human-in-the-loop using graph interrupts
    """
    # Create graph with checkpointing for interrupts
    workflow = StateGraph(HumanInLoopState)
    
    # Add all nodes from previous iterations
    workflow.add_node("router", router_node)
    workflow.add_node("technical_expert", technical_expert_node)
    workflow.add_node("historical_expert", historical_expert_node)
    workflow.add_node("current_events_expert", current_events_expert_with_tools_node)
    workflow.add_node("general_expert", general_expert_node)
    
    # Add human review nodes
    workflow.add_node("check_needs_review", check_needs_review)
    workflow.add_node("human_review", human_review_node)
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
    
    # IMPORTANT: Set interrupt_before for human review node
    # This will pause the graph before executing human_review
    workflow.add_edge("human_review", "format_output")
    
    # Output goes to END
    workflow.add_edge("format_output", END)
    
    # Compile with memory for interrupts
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["human_review"])


def check_claim_with_human_review(claim: str, thread_id: str = "default") -> dict:
    """
    Check a claim with human-in-the-loop support using graph interrupts
    
    Args:
        claim: The claim to check
        thread_id: Thread ID for conversation memory
    
    Returns:
        Result dict or None if interrupted for human review
    """
    app = create_human_in_loop_graph()
    
    # Configuration with thread ID for checkpointing
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initial state - convert to dict for invoke
    initial_state = HumanInLoopState(claim=claim)
    
    # Run the graph - it may interrupt for human review
    result = app.invoke(initial_state.model_dump(), config)
    
    # Check if we got a final result or if we're interrupted
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    
    # If no result, we're likely interrupted
    return None


def resume_after_human_input(
    thread_id: str,
    verdict: str,
    confidence: int,
    reasoning: str
) -> dict:
    """
    Resume graph execution after human provides input
    
    Args:
        thread_id: Thread ID to resume
        verdict: Human's verdict (BS/LEGITIMATE/UNCERTAIN)
        confidence: Human's confidence (0-100)
        reasoning: Human's reasoning
    
    Returns:
        Final result after incorporating human feedback
    """
    app = create_human_in_loop_graph()
    
    # Configuration with thread ID
    config = {"configurable": {"thread_id": thread_id}}
    
    # When resuming, we need to provide None as input (graph will use checkpoint)
    # and pass updates as a separate parameter
    result = app.invoke(None, config, interrupt_before=[])
    
    # If we're still interrupted, update with human feedback
    if result is None or "result" not in result:
        # Update state with human feedback
        human_updates = {
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": f"Human review: {reasoning}",
            "human_feedback_received": True
        }
        
        # Resume from interrupt with human feedback by updating the state
        result = app.invoke(human_updates, config)
    
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    
    return result


def interactive_demo():
    """Interactive demo showing human-in-the-loop"""
    print("🤖 BS Detector with Human-in-the-Loop")
    print("=" * 50)
    print("Using LangGraph's interrupt capability")
    print()
    
    test_claims = [
        "The Boeing 747 has four engines",  # High confidence, no review needed
        "A major airline filed for bankruptcy yesterday",  # Current event, may need review
        "Scientists discovered anti-gravity technology last week",  # Low confidence claim
    ]
    
    for i, claim in enumerate(test_claims):
        thread_id = f"demo_{i}"
        print(f"\nClaim {i+1}: {claim}")
        print("-" * 40)
        
        # First run - may interrupt
        result = check_claim_with_human_review(claim, thread_id)
        
        if result:
            # No human review needed
            print(f"✅ Verdict: {result['verdict']} ({result['confidence']}%)")
            print(f"📝 Reasoning: {result['reasoning']}")
        else:
            # Human review needed - simulate human input
            print("\n🧑 Simulating human input...")
            
            # In real usage, this would come from actual human input
            human_verdict = "BS" if "anti-gravity" in claim else "LEGITIMATE"
            human_confidence = 95
            human_reasoning = "Based on expert knowledge and verification"
            
            # Resume with human input
            final_result = resume_after_human_input(
                thread_id,
                human_verdict,
                human_confidence,
                human_reasoning
            )
            
            print(f"\n✅ Final Verdict: {final_result['verdict']} ({final_result['confidence']}%)")
            print(f"📝 Final Reasoning: {final_result['reasoning']}")
            print(f"👤 Human Reviewed: Yes")


# Example usage
if __name__ == "__main__":
    interactive_demo()