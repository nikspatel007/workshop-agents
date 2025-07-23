"""
Iteration 6: Human-in-the-Loop Integration

This module adds human review capabilities to our BS detector for cases where:
1. Confidence is very low (<50%)
2. Multiple experts disagree
3. Claims involve recent events with conflicting search results
4. User explicitly requests human review

Key concepts:
- Uncertainty detection
- Human review requests
- Feedback incorporation
- Async human input handling
"""

from typing import Optional, Dict, List, Any, Literal, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import asyncio
import time

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


class HumanReviewRequest(BaseModel):
    """Request for human review"""
    claim: str
    ai_verdict: Optional[str] = None
    ai_confidence: Optional[int] = None
    ai_reasoning: Optional[str] = None
    uncertainty_reasons: List[str] = Field(default_factory=list)
    expert_opinions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    search_results: Optional[List[Dict[str, Any]]] = None
    request_time: datetime = Field(default_factory=datetime.now)
    
    def format_for_human(self) -> str:
        """Format the review request for human display"""
        output = f"\n{'='*60}\n"
        output += f"🤔 HUMAN REVIEW REQUESTED\n"
        output += f"{'='*60}\n\n"
        output += f"**Claim**: {self.claim}\n\n"
        
        if self.ai_verdict:
            output += f"**AI Assessment**:\n"
            output += f"- Verdict: {self.ai_verdict}\n"
            output += f"- Confidence: {self.ai_confidence}%\n"
            output += f"- Reasoning: {self.ai_reasoning}\n\n"
        
        if self.uncertainty_reasons:
            output += f"**Uncertainty Reasons**:\n"
            for reason in self.uncertainty_reasons:
                output += f"- {reason}\n"
            output += "\n"
        
        if self.expert_opinions:
            output += f"**Expert Opinions**:\n"
            for expert, opinion in self.expert_opinions.items():
                output += f"\n{expert}:\n"
                output += f"  - Verdict: {opinion.get('verdict', 'N/A')}\n"
                output += f"  - Confidence: {opinion.get('confidence', 'N/A')}%\n"
                output += f"  - Reasoning: {opinion.get('reasoning', 'N/A')}\n"
        
        if self.search_results:
            output += f"\n**Search Results**: {len(self.search_results)} results found\n"
            for i, result in enumerate(self.search_results[:3]):
                output += f"  {i+1}. {result.get('fact', result.get('summary', 'N/A'))[:100]}...\n"
        
        output += f"\n{'='*60}\n"
        return output


class HumanFeedback(BaseModel):
    """Human feedback on a claim"""
    verdict: Literal["BS", "LEGITIMATE", "UNCERTAIN"]
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    additional_context: Optional[str] = None
    sources: Optional[List[str]] = None


class HumanInLoopState(ToolEnhancedState):
    """Extended state with human-in-the-loop fields"""
    # Human interaction fields
    needs_human_review: bool = False
    human_review_request: Optional[HumanReviewRequest] = None
    human_feedback: Optional[HumanFeedback] = None
    review_reasons: List[str] = Field(default_factory=list)
    
    # Multi-expert tracking
    expert_opinions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    expert_disagreement: bool = False
    
    # Uncertainty metrics
    uncertainty_score: float = 0.0
    conflicting_evidence: bool = False


def calculate_uncertainty(state: HumanInLoopState) -> float:
    """Calculate uncertainty score based on various factors"""
    uncertainty = 0.0
    
    # Low confidence increases uncertainty
    if state.confidence:
        if state.confidence < 50:
            uncertainty += 0.4
        elif state.confidence < 70:
            uncertainty += 0.2
    
    # Expert disagreement
    if state.expert_opinions:
        verdicts = [op.get("verdict") for op in state.expert_opinions.values()]
        if len(set(verdicts)) > 1:  # Different verdicts
            uncertainty += 0.3
            
    # Conflicting search results
    if state.search_results and len(state.search_results) > 1:
        # Simple heuristic: if search results mention both confirming and denying
        results_text = " ".join([str(r) for r in state.search_results])
        if "confirm" in results_text.lower() and "deny" in results_text.lower():
            uncertainty += 0.2
    
    # Recent events with no clear evidence
    if state.claim_type == "current_event" and not state.search_performed:
        uncertainty += 0.1
    
    return min(uncertainty, 1.0)


def uncertainty_detector_node(state: HumanInLoopState) -> dict:
    """Detect if human review is needed based on uncertainty"""
    uncertainty = calculate_uncertainty(state)
    state.uncertainty_score = uncertainty
    
    updates = {"uncertainty_score": uncertainty}
    review_reasons = []
    
    # Check if forced review
    if hasattr(state, '_force_human_review') and state._force_human_review:
        review_reasons.append("Human review explicitly requested")
        needs_review = True
    else:
        # Check various conditions for human review
        if state.confidence and state.confidence < 50:
            review_reasons.append(f"Very low confidence: {state.confidence}%")
        
        if state.expert_disagreement:
            review_reasons.append("Experts disagree on verdict")
        
        if uncertainty > 0.6:
            review_reasons.append(f"High uncertainty score: {uncertainty:.2f}")
        
        if state.claim_type == "current_event" and state.search_performed:
            if not state.search_results or all(not r for r in state.search_results):
                review_reasons.append("No evidence found for recent event")
        
        # Determine if human review is needed
        needs_review = len(review_reasons) > 0 or uncertainty > 0.6
    
    if needs_review:
        # Create human review request
        review_request = HumanReviewRequest(
            claim=state.claim,
            ai_verdict=state.verdict,
            ai_confidence=state.confidence,
            ai_reasoning=state.reasoning,
            uncertainty_reasons=review_reasons,
            expert_opinions=state.expert_opinions,
            search_results=state.search_results
        )
        
        updates.update({
            "needs_human_review": True,
            "human_review_request": review_request,
            "review_reasons": review_reasons
        })
    else:
        updates["needs_human_review"] = False
    
    return updates


def human_review_node(state: HumanInLoopState) -> dict:
    """Handle human review process"""
    if not state.human_review_request:
        return {}
    
    print(state.human_review_request.format_for_human())
    
    # In a real system, this would be async with a queue
    # For demo, we'll simulate or use a callback
    updates = {}
    
    # Check if we have a human input handler registered
    if hasattr(state, "_human_input_handler") and state._human_input_handler:
        feedback = state._human_input_handler(state.human_review_request)
        if feedback:
            updates["human_feedback"] = feedback
            updates["verdict"] = feedback.verdict
            updates["confidence"] = feedback.confidence
            updates["reasoning"] = f"Human review: {feedback.reasoning}"
            if feedback.additional_context:
                updates["reasoning"] += f" Context: {feedback.additional_context}"
    else:
        # No handler provided - use interactive input
        print("\n🧑 HUMAN REVIEW REQUIRED")
        print("The AI needs your help to verify this claim.")
        
        # Try to use interactive input
        try:
            feedback = interactive_human_input(state.human_review_request)
            updates["human_feedback"] = feedback
            updates["verdict"] = feedback.verdict
            updates["confidence"] = feedback.confidence
            updates["reasoning"] = f"Human review: {feedback.reasoning}"
            if feedback.additional_context:
                updates["reasoning"] += f" Context: {feedback.additional_context}"
        except (EOFError, KeyboardInterrupt):
            # Fallback to simulated if interactive not available
            print("\n⏳ Interactive input not available, using simulated feedback...")
            time.sleep(1)
            
            simulated_feedback = HumanFeedback(
                verdict="UNCERTAIN",
                confidence=60,
                reasoning="This claim requires expert verification beyond my knowledge"
            )
            
            updates["human_feedback"] = simulated_feedback
            updates["verdict"] = simulated_feedback.verdict
            updates["confidence"] = simulated_feedback.confidence
            updates["reasoning"] = f"Human review: {simulated_feedback.reasoning}"
    
    return updates


def multi_expert_aggregator_node(state: HumanInLoopState) -> dict:
    """Aggregate opinions from multiple experts"""
    # Collect all expert opinions
    opinions = {}
    
    # Store the current expert's opinion
    if state.verdict and state.analyzing_agent:
        opinions[state.analyzing_agent] = {
            "verdict": state.verdict,
            "confidence": state.confidence,
            "reasoning": state.reasoning
        }
    
    # Check for disagreement
    if len(opinions) > 1:
        verdicts = [op["verdict"] for op in opinions.values()]
        if len(set(verdicts)) > 1:
            state.expert_disagreement = True
    
    return {
        "expert_opinions": opinions,
        "expert_disagreement": state.expert_disagreement
    }


def route_after_uncertainty_check(state: HumanInLoopState) -> str:
    """Route based on uncertainty check"""
    if state.needs_human_review:
        return "human_review"
    else:
        return "format_output"


def create_human_in_loop_bs_detector():
    """Create the enhanced BS detector with human-in-the-loop"""
    from langgraph.graph import StateGraph, END
    
    # Create graph with our enhanced state
    workflow = StateGraph(HumanInLoopState)
    
    # Add all nodes from previous iteration
    workflow.add_node("router", router_node)
    workflow.add_node("technical_expert", technical_expert_node)
    workflow.add_node("historical_expert", historical_expert_node)
    workflow.add_node("current_events_expert", current_events_expert_with_tools_node)
    workflow.add_node("general_expert", general_expert_node)
    
    # Add new human-in-the-loop nodes
    workflow.add_node("uncertainty_detector", uncertainty_detector_node)
    workflow.add_node("human_review", human_review_node)
    
    # Format output node
    def format_output_node(state: HumanInLoopState) -> dict:
        """Format the final output"""
        # Handle error cases
        if not state.verdict:
            return {"result": {
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": "Processing failed - no verdict generated",
                "human_reviewed": False
            }}
        
        result = {
            "verdict": state.verdict,
            "confidence": state.confidence or 0,
            "reasoning": state.reasoning or "No reasoning provided",
            "claim_type": state.claim_type,
            "analyzing_agent": state.analyzing_agent,
            "used_search": state.search_performed,
            "tools_used": state.tools_used,
            "human_reviewed": state.needs_human_review,
            "uncertainty_score": state.uncertainty_score
        }
        
        if state.search_results:
            result["search_results"] = state.search_results
            
        if state.human_feedback:
            result["human_feedback"] = {
                "verdict": state.human_feedback.verdict,
                "confidence": state.human_feedback.confidence,
                "reasoning": state.human_feedback.reasoning
            }
            
        return {"result": result}
    
    workflow.add_node("format_output", format_output_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add edges from router to experts
    def route_to_expert(state: HumanInLoopState) -> str:
        # Default to general if claim_type not set
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
    
    # All experts go to uncertainty detector
    for expert in ["technical_expert", "historical_expert", "current_events_expert", "general_expert"]:
        workflow.add_edge(expert, "uncertainty_detector")
    
    # Uncertainty detector routes to human review or output
    workflow.add_conditional_edges(
        "uncertainty_detector",
        route_after_uncertainty_check,
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


def check_claim_with_human_in_loop(
    claim: str, 
    human_input_handler: Optional[Callable] = None,
    force_human_review: bool = False
) -> dict:
    """Check a claim with human-in-the-loop support
    
    Args:
        claim: The claim to check
        human_input_handler: Optional handler for human input
        force_human_review: Force human review regardless of confidence
    """
    try:
        app = create_human_in_loop_bs_detector()
        
        initial_state = HumanInLoopState(claim=claim)
        
        # Attach human input handler if provided
        if human_input_handler:
            initial_state._human_input_handler = human_input_handler
            
        # Force human review if requested
        if force_human_review:
            initial_state._force_human_review = True
        
        final_state = app.invoke(initial_state)
        
        # The state is returned as a dict, check for result key
        if isinstance(final_state, dict) and "result" in final_state:
            return final_state["result"]
        
        # Otherwise construct result from state
        return {
            "verdict": final_state.get("verdict", "ERROR"),
            "confidence": final_state.get("confidence", 0),
            "reasoning": final_state.get("reasoning", "Processing failed"),
            "claim_type": final_state.get("claim_type"),
            "analyzing_agent": final_state.get("analyzing_agent"),
            "used_search": final_state.get("search_performed", False),
            "tools_used": final_state.get("tools_used", []),
            "human_reviewed": final_state.get("needs_human_review", False),
            "uncertainty_score": final_state.get("uncertainty_score", 0.0),
            "human_feedback": final_state.get("human_feedback")
        }
    except Exception as e:
        import traceback
        print(f"Error in check_claim_with_human_in_loop: {str(e)}")
        print(traceback.format_exc())
        return {
            "verdict": "ERROR",
            "confidence": 0,
            "reasoning": f"Processing failed: {str(e)}"
        }


# Demo human input handler
def interactive_human_input(request: HumanReviewRequest) -> HumanFeedback:
    """Interactive human input for demos"""
    print("\n🧑 Please provide your assessment:")
    
    while True:
        verdict = input("Verdict (BS/LEGITIMATE/UNCERTAIN): ").upper()
        if verdict in ["BS", "LEGITIMATE", "UNCERTAIN"]:
            break
        print("Invalid verdict. Please enter BS, LEGITIMATE, or UNCERTAIN")
    
    while True:
        try:
            confidence = int(input("Confidence (0-100): "))
            if 0 <= confidence <= 100:
                break
            print("Confidence must be between 0 and 100")
        except ValueError:
            print("Please enter a number")
    
    reasoning = input("Reasoning: ")
    
    additional = input("Additional context (optional, press Enter to skip): ")
    
    return HumanFeedback(
        verdict=verdict,
        confidence=confidence,
        reasoning=reasoning,
        additional_context=additional if additional else None
    )