"""
Iteration 5: Tool-Enhanced Multi-Agent BS Detector
Builds on m5_routing.py by adding web search tools to the current events expert

Key features:
- Extends the multi-agent system from m5
- Adds tools specifically to the current_events_expert
- Other experts remain unchanged
- LLM decides when to use tools based on information sufficiency
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
import json
from datetime import datetime

from config.llm_factory import LLMFactory
from tools.search_tool import WebSearchTool
from modules.m5_routing import (
    MultiAgentState,
    router_node,
    technical_expert_node,
    historical_expert_node,
    general_expert_node,
    _parse_expert_response
)


# Structured output for web search
class WebSearchResult(BaseModel):
    """Structured output from web search"""
    query: str
    facts: List[str] = Field(description="Key facts found")
    sources: List[str] = Field(description="Source URLs or descriptions")
    search_successful: bool = True
    error: Optional[str] = None


# Define the tool with proper documentation
@tool
def search_for_information(query: str) -> str:
    """
    Search the web for current information about a topic.
    
    Use this tool when you need to verify claims but lack sufficient 
    information to make a confident assessment. This is particularly 
    useful for:
    - Claims about current events or recent developments
    - Specific facts or figures you're uncertain about
    - Information that may have changed since your training
    - Data you need to verify but don't have access to
    - Time-sensitive claims (include specific dates in your query)
    
    When searching for events mentioned as "yesterday", "today", etc.,
    use specific dates based on the current date provided in the system prompt.
    
    Args:
        query: A specific search query to find relevant information.
               Include dates when searching for time-sensitive events.
        
    Returns:
        JSON string with facts found and sources
    """
    try:
        search_tool = WebSearchTool(max_results=3)
        
        # Perform search
        result = search_tool.search_web(query)
        
        if result["success"]:
            # Extract facts
            facts = search_tool.extract_facts([result])[:5]  # Limit to 5 facts
            
            # Create structured result
            search_result = WebSearchResult(
                query=query,
                facts=facts,
                sources=[result.get("query", "Web search")],
                search_successful=True
            )
        else:
            search_result = WebSearchResult(
                query=query,
                facts=[],
                sources=[],
                search_successful=False,
                error=result.get("error", "Search failed")
            )
            
        return search_result.model_dump_json()
        
    except Exception as e:
        error_result = WebSearchResult(
            query=query,
            facts=[],
            sources=[],
            search_successful=False,
            error=str(e)
        )
        return error_result.model_dump_json()


# Enhanced state to track tool usage
class ToolEnhancedState(MultiAgentState):
    """Extended state that includes tool usage tracking"""
    search_performed: bool = False
    search_results: Optional[List[WebSearchResult]] = None
    tools_used: List[str] = Field(default_factory=list)
    messages: List[dict] = Field(default_factory=list)


def current_events_expert_with_tools_node(state: ToolEnhancedState) -> dict:
    """
    Enhanced current events expert with web search capability
    """
    llm = LLMFactory.create_llm()
    
    # Bind the search tool to the LLM
    llm_with_tools = llm.bind_tools([search_for_information])
    
    # Get current date for context
    current_date = datetime.now()
    date_str = current_date.strftime("%B %d, %Y")
    
    expert_prompt = f"""You are a current events expert analyzing claims for misinformation.

IMPORTANT: Today's date is {date_str}. When claims mention "yesterday", "today", "this week", etc., interpret them relative to this current date.

Your goal is to determine if a claim is LEGITIMATE or BS based on available information.

If you lack sufficient information to make a confident assessment, use the search_for_information tool to gather current information. Don't guess or make assumptions when you're uncertain about recent events.

Base your decision to search on:
- Your confidence in the information you have
- Whether the claim involves recent or current events
- Whether you need specific data to verify the claim
- Your knowledge cutoff limitations

When searching for time-sensitive information, include specific dates in your search queries.

After searching (if needed), provide your analysis in this format:
VERDICT: [LEGITIMATE/BS]
CONFIDENCE: [0-100]
REASONING: [Your detailed explanation]

Be thorough but concise in your analysis."""
    
    # Create messages
    messages = [
        SystemMessage(content=expert_prompt),
        HumanMessage(content=f'Analyze this current event claim: "{state.claim}"')
    ]
    
    # Get LLM response with potential tool calls
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    # Check if the LLM wants to use tools
    tool_calls = getattr(response, 'tool_calls', [])
    search_results = []
    tools_used = []
    
    if tool_calls:
        # Execute tool calls
        for tool_call in tool_calls:
            if tool_call["name"] == "search_for_information":
                tools_used.append("search_for_information")
                
                # Execute the search
                result = search_for_information.invoke(tool_call["args"])
                
                # Add tool result to messages
                tool_message = ToolMessage(
                    content=result,
                    tool_call_id=tool_call["id"]
                )
                messages.append(tool_message)
                
                # Parse and store result
                try:
                    search_data = json.loads(result)
                    search_results.append(WebSearchResult(**search_data))
                except:
                    pass
        
        # Get final response after tool use
        final_response = llm_with_tools.invoke(messages)
        messages.append(final_response)
        analysis_content = final_response.content
    else:
        # No tool use, use initial response
        analysis_content = response.content
    
    # Parse the response
    parsed = _parse_expert_response(analysis_content, "Current Events Expert (with tools)")
    
    # Add tool usage info
    parsed.update({
        "search_performed": len(tool_calls) > 0,
        "search_results": search_results,
        "tools_used": tools_used,
    })
    
    return parsed


def create_tool_enhanced_bs_detector():
    """Create the tool-enhanced multi-agent BS detector graph"""
    workflow = StateGraph(ToolEnhancedState)
    
    # Add nodes - reuse most from m3_routing
    workflow.add_node("router", router_node)
    workflow.add_node("technical_expert", technical_expert_node)
    workflow.add_node("historical_expert", historical_expert_node)
    workflow.add_node("current_events_expert", current_events_expert_with_tools_node)  # Enhanced version
    workflow.add_node("general_expert", general_expert_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional routing based on claim type
    def route_to_expert(state: ToolEnhancedState) -> str:
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
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def check_claim_with_tools(claim: str) -> dict:
    """Check a claim using tool-enhanced multi-agent detection"""
    app = create_tool_enhanced_bs_detector()
    
    # Run the graph
    config = {"configurable": {"thread_id": "tools-1"}}
    state = ToolEnhancedState(claim=claim)
    result = app.invoke(state.model_dump(), config)
    
    return {
        "verdict": result.get("verdict"),
        "confidence": result.get("confidence"),
        "reasoning": result.get("reasoning"),
        "claim_type": result.get("claim_type"),
        "analyzing_agent": result.get("analyzing_agent"),
        "used_search": result.get("search_performed", False),
        "search_results": result.get("search_results", []),
        "tools_used": result.get("tools_used", [])
    }


# Demo
if __name__ == "__main__":
    print("Tool-Enhanced Multi-Agent BS Detector Demo")
    print("=" * 50)
    
    # Test claims that show different routing and tool usage
    test_claims = [
        "Water boils at 100 degrees Celsius",  # Technical - no tools needed
        "The Wright brothers first flew in 1903",  # Historical - no tools needed
        "SpaceX launched 5 rockets yesterday",  # Current events - should use tools
        "Tesla's stock price closed above $400 today",  # Current events - should use tools
    ]
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        print("-" * 40)
        
        result = check_claim_with_tools(claim)
        
        print(f"Routed to: {result['claim_type']} -> {result['analyzing_agent']}")
        print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
        print(f"Used Search: {'Yes' if result['used_search'] else 'No'}")
        
        if result['used_search']:
            print(f"Tools used: {', '.join(result['tools_used'])}")
        
        print(f"\nReasoning: {result['reasoning'][:200]}...")