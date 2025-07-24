"""
Iteration 5: Multi-Agent Routing System
Builds on m3_langgraph.py by adding specialized agents for different claim types
"""

from typing import Optional, Literal
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime

from config.llm_factory import LLMFactory
from modules.node_updates import RouterUpdate, ExpertUpdate


class MultiAgentState(BaseModel):
    """State for multi-agent BS detector"""
    # Input
    claim: str
    
    # Routing decision
    claim_type: Optional[Literal["technical", "historical", "current_event", "general"]] = None
    confidence_level: Optional[Literal["high", "medium", "low"]] = None
    
    # Processing control
    retry_count: int = 0
    max_retries: int = 3
    
    # Output from detection
    verdict: Optional[str] = None
    confidence: Optional[int] = None
    reasoning: Optional[str] = None
    analyzing_agent: Optional[str] = None
    
    # Error tracking
    error: Optional[str] = None


def router_node(state: MultiAgentState) -> dict:
    """
    Router that analyzes the claim and decides which specialist to use
    Returns a dict that can be used to update the state
    """
    try:
        llm = LLMFactory.create_llm()
        
        # Create structured LLM for router
        structured_llm = llm.with_structured_output(RouterUpdate)
        
        router_prompt = """You are a routing expert that analyzes claims and determines which specialist should handle them.

Analyze the given claim and determine:
1. claim_type: One of [technical, historical, current_event, general]
2. confidence_level: One of [high, medium, low] based on how certain you are

Categories:
- technical: Claims about technology, specifications, capabilities
- historical: Claims about past events, dates, historical facts
- current_event: Claims about recent or ongoing events (use when temporal context suggests recency)
- general: Everything else"""
        
        messages = [
            SystemMessage(content=router_prompt),
            HumanMessage(content=f'Route this claim: "{state.claim}"')
        ]
        
        # Get structured response
        router_update = structured_llm.invoke(messages)
        
        # Convert Pydantic model to dict for state update
        return router_update.model_dump()
        
    except Exception as e:
        # Default to general expert on error - return dict
        default_update = RouterUpdate(
            claim_type="general",
            confidence_level="medium"
        )
        return default_update.model_dump()


def technical_expert_node(state: MultiAgentState) -> dict:
    """
    Technical expert for technology-related claims
    Returns a dict for state update
    """
    llm = LLMFactory.create_llm()
    
    # Create structured LLM for expert analysis
    structured_llm = llm.with_structured_output(ExpertUpdate)
    
    expert_prompt = """You are a technical expert specializing in technology, engineering, and scientific claims.
    
Analyze this claim for technical accuracy. You have deep knowledge of:
- Engineering specifications and capabilities
- Technology limitations and possibilities
- Scientific principles and facts

Determine if the claim is LEGITIMATE, BS, or UNCERTAIN.
Provide your confidence (0-100) and detailed reasoning."""
    
    messages = [
        SystemMessage(content=expert_prompt),
        HumanMessage(content=f'Analyze this technical claim: "{state.claim}"')
    ]
    
    try:
        # Get structured response
        expert_update = structured_llm.invoke(messages)
        # Add the expert name
        update_dict = expert_update.model_dump()
        update_dict["analyzing_agent"] = "Technical Expert"
        return update_dict
    except Exception as e:
        # Fallback to parsing if structured output fails
        response = llm.invoke(messages)
        return _parse_expert_response(response.content, "Technical Expert")


def historical_expert_node(state: MultiAgentState) -> dict:
    """
    Historical expert for claims about past events
    """
    llm = LLMFactory.create_llm()
    
    expert_prompt = """You are a historical expert specializing in historical facts and past events.
    
Analyze this claim for historical accuracy. You have deep knowledge of:
- Historical dates and events
- Past achievements and failures
- Historical context and significance

Determine if the claim is LEGITIMATE or BS.

Provide your analysis in this format:
VERDICT: [LEGITIMATE/BS]
CONFIDENCE: [0-100]
REASONING: [Your historical analysis]
"""
    
    messages = [
        SystemMessage(content=expert_prompt),
        HumanMessage(content=f'Analyze this historical claim: "{state.claim}"')
    ]
    
    response = llm.invoke(messages)
    return _parse_expert_response(response.content, "Historical Expert")


def current_events_expert_node(state: MultiAgentState) -> dict:
    """
    Expert for current events and recent developments
    Note: In the real implementation, this would have access to tools
    """
    llm = LLMFactory.create_llm()
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    expert_prompt = f"""You are a current events expert. Today's date is {current_date}.
    
Analyze this claim about recent or current events. Note that without access to real-time data,
you should be less confident about very recent claims.

Determine if the claim is LEGITIMATE or BS based on your knowledge.

Provide your analysis in this format:
VERDICT: [LEGITIMATE/BS]
CONFIDENCE: [0-100]
REASONING: [Your analysis, noting any limitations]
"""
    
    messages = [
        SystemMessage(content=expert_prompt),
        HumanMessage(content=f'Analyze this current event claim: "{state.claim}"')
    ]
    
    response = llm.invoke(messages)
    return _parse_expert_response(response.content, "Current Events Expert")


def general_expert_node(state: MultiAgentState) -> dict:
    """
    General expert for claims that don't fit other categories
    """
    llm = LLMFactory.create_llm()
    
    expert_prompt = """You are a general knowledge expert analyzing claims for misinformation.
    
Analyze this claim and determine if it is LEGITIMATE or BS.
Use your broad knowledge and critical thinking skills.

Provide your analysis in this format:
VERDICT: [LEGITIMATE/BS]
CONFIDENCE: [0-100]
REASONING: [Your analysis]
"""
    
    messages = [
        SystemMessage(content=expert_prompt),
        HumanMessage(content=f'Analyze this claim: "{state.claim}"')
    ]
    
    response = llm.invoke(messages)
    return _parse_expert_response(response.content, "General Expert")


def _create_expert_node(expert_name: str, expert_prompt: str):
    """Factory function to create expert nodes with structured output"""
    def expert_node(state: MultiAgentState) -> dict:
        llm = LLMFactory.create_llm()
        
        # Create structured LLM for expert analysis
        structured_llm = llm.with_structured_output(ExpertUpdate)
        
        messages = [
            SystemMessage(content=expert_prompt),
            HumanMessage(content=f'Analyze this claim: "{state.claim}"')
        ]
        
        try:
            # Get structured response
            expert_update = structured_llm.invoke(messages)
            # Add the expert name
            update_dict = expert_update.model_dump()
            update_dict["analyzing_agent"] = expert_name
            return update_dict
        except Exception as e:
            # Fallback to parsing if structured output fails
            response = llm.invoke(messages)
            return _parse_expert_response(response.content, expert_name)
    
    return expert_node


def _parse_expert_response(content: str, expert_name: str) -> dict:
    """Helper to parse expert responses"""
    verdict = "UNCERTAIN"
    confidence = 50
    reasoning = content
    
    if "VERDICT:" in content:
        verdict_line = content.split("VERDICT:")[1].split("\n")[0].strip()
        if "LEGITIMATE" in verdict_line:
            verdict = "LEGITIMATE"
        elif "BS" in verdict_line:
            verdict = "BS"
    
    if "CONFIDENCE:" in content:
        try:
            confidence = int(content.split("CONFIDENCE:")[1].split("\n")[0].strip())
        except:
            confidence = 50
    
    if "REASONING:" in content:
        reasoning = content.split("REASONING:")[1].strip()
    
    return {
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "analyzing_agent": expert_name
    }


def create_multi_agent_bs_detector():
    """Create the multi-agent BS detector graph"""
    workflow = StateGraph(MultiAgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("technical_expert", technical_expert_node)
    workflow.add_node("historical_expert", historical_expert_node)
    workflow.add_node("current_events_expert", current_events_expert_node)
    workflow.add_node("general_expert", general_expert_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional routing based on claim type
    def route_to_expert(state: MultiAgentState) -> str:
        """Route to appropriate expert based on claim type"""
        claim_type = state.claim_type or "general"
        return f"{claim_type.replace('_', '_')}_expert"
    
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
    
    # All experts go to END
    workflow.add_edge("technical_expert", END)
    workflow.add_edge("historical_expert", END)
    workflow.add_edge("current_events_expert", END)
    workflow.add_edge("general_expert", END)
    
    return workflow.compile()


def check_claim_with_routing(claim: str) -> dict:
    """Check a claim using multi-agent routing"""
    app = create_multi_agent_bs_detector()
    
    state = MultiAgentState(claim=claim)
    result = app.invoke(state.model_dump())
    
    return {
        "verdict": result.get("verdict"),
        "confidence": result.get("confidence"),
        "reasoning": result.get("reasoning"),
        "claim_type": result.get("claim_type"),
        "analyzing_agent": result.get("analyzing_agent")
    }


# Demo
if __name__ == "__main__":
    print("Multi-Agent BS Detector Demo")
    print("=" * 50)
    
    test_claims = [
        "The Boeing 787 uses composite materials",
        "The Wright brothers first flew in 1903",
        "Tesla announced a new car model yesterday",
        "Eating chocolate cures all diseases"
    ]
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        print("-" * 40)
        
        result = check_claim_with_routing(claim)
        
        print(f"Routed to: {result['claim_type']} -> {result['analyzing_agent']}")
        print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
        print(f"Reasoning: {result['reasoning'][:100]}...")