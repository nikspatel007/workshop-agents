"""
Iteration 2: Convert baseline BS detector to LangGraph.
Builds on m1_baseline.py by adding graph-based processing with retry logic.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from Iteration 1
from modules.m1_baseline import BSDetectorOutput, check_claim
from config.llm_factory import LLMFactory


# Step 1: Define State using Pydantic BaseModel
class BSDetectorState(BaseModel):
    """State that flows through our graph - using Pydantic for validation"""
    # Input
    claim: str
    
    # Processing control
    retry_count: int = 0
    max_retries: int = 3
    
    # Output from detection
    verdict: Optional[str] = None
    confidence: Optional[int] = None
    reasoning: Optional[str] = None
    
    # Error tracking
    error: Optional[str] = None
    
    # Keep original result format
    result: Optional[dict] = None
    
    model_config = {
        "arbitrary_types_allowed": True
    }


# Step 2: Create Nodes
def detect_bs_node(state: BSDetectorState) -> dict:
    """
    Main detection node - uses our baseline detector from Iteration 1.
    This shows how to wrap existing functionality in a graph node.
    """
    try:
        # Get LLM (reuse from our config)
        llm = LLMFactory.create_llm()
        
        # Use the baseline detector from Iteration 1
        result = check_claim(state.claim, llm)
        
        # Return updates to state
        return {
            "verdict": result.get("verdict"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
            "error": result.get("error"),
            "result": result  # Keep full result for compatibility
        }
        
    except Exception as e:
        # On error, increment retry count
        return {
            "error": str(e),
            "retry_count": state.retry_count + 1
        }


def retry_node(state: BSDetectorState) -> dict:
    """
    Retry node with exponential backoff.
    Shows how to add retry logic as a separate concern.
    """
    retry_count = state.retry_count
    
    # Exponential backoff: 1s, 2s, 4s
    wait_time = 2 ** (retry_count - 1)
    print(f"⏳ Retry {retry_count}/{state.max_retries} - waiting {wait_time}s...")
    time.sleep(wait_time)
    
    # Return empty dict, detection will happen when we loop back
    return {}


def format_output_node(state: BSDetectorState) -> dict:
    """
    Format the final output to match baseline format.
    This ensures backward compatibility.
    """
    # If we have a stored result, use it
    if state.result:
        return {}
    
    # Otherwise, construct result from state
    result = {
        "verdict": state.verdict or "ERROR",
        "confidence": state.confidence or 0,
        "reasoning": state.reasoning or "No analysis available",
    }
    
    if state.error:
        result["error"] = state.error
    
    return {"result": result}


# Step 3: Create Routing Functions
def route_after_detection(state: BSDetectorState) -> str:
    """
    Decide what to do after detection attempt.
    This is our conditional edge logic.
    """
    # Success - we got a valid verdict
    if state.verdict and state.verdict not in ["ERROR", None]:
        return "success"
    
    # Error - check if we should retry
    if state.retry_count < state.max_retries:
        return "retry"
    
    # Max retries reached
    return "error"


# Step 4: Build the Graph
def create_bs_detector_graph():
    """
    Create the LangGraph version of our BS detector.
    This adds retry logic to our baseline detector.
    """
    # Initialize graph with our state schema
    graph = StateGraph(BSDetectorState)
    
    # Add nodes
    graph.add_node("detect", detect_bs_node)
    graph.add_node("retry", retry_node)
    graph.add_node("format_output", format_output_node)
    
    # Set entry point
    graph.set_entry_point("detect")
    
    # Add conditional routing after detection
    graph.add_conditional_edges(
        "detect",
        route_after_detection,
        {
            "success": "format_output",
            "retry": "retry",
            "error": "format_output"
        }
    )
    
    # After retry, go back to detection
    graph.add_edge("retry", "detect")
    
    # Format output leads to end
    graph.add_edge("format_output", END)
    
    # Compile the graph
    return graph.compile()


# Step 5: Create Easy-to-Use Functions
def check_claim_with_graph(claim: str, max_retries: int = 3) -> dict:
    """
    Check a claim using the LangGraph version.
    
    This maintains the same interface as the baseline version
    but adds retry capability.
    """
    # Create the graph
    app = create_bs_detector_graph()
    
    # Initialize state with Pydantic model
    initial_state = BSDetectorState(
        claim=claim,
        retry_count=0,
        max_retries=max_retries
    )
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    # Return the formatted result
    return final_state.get("result") or {
        "verdict": "ERROR",
        "confidence": 0,
        "reasoning": "Graph execution failed",
        "error": "Unknown error"
    }


def interactive_chat():
    """
    Interactive chat loop using the graph-based detector.
    Shows how to reuse the graph for multiple queries.
    """
    # Create the graph once
    app = create_bs_detector_graph()
    
    print("🤖 BS Detector with LangGraph (type 'quit' to exit)")
    print("=" * 50)
    print("Now with automatic retry on errors!")
    print()
    
    while True:
        # Get user input
        claim = input("Enter aviation claim: ").strip()
        
        # Check for exit
        if claim.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        # Skip empty input
        if not claim:
            continue
        
        # Process with graph
        print("\n🔍 Analyzing...")
        
        # Run the graph with Pydantic state
        state = app.invoke(BSDetectorState(
            claim=claim,
            retry_count=0,
            max_retries=3
        ))
        
        # Display results
        result = state.get("result") or {}
        
        if result.get("verdict") and result["verdict"] != "ERROR":
            print(f"\n📊 Verdict: {result['verdict']}")
            print(f"🎯 Confidence: {result['confidence']}%")
            print(f"💭 Reasoning: {result['reasoning']}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        print("-" * 50)


def visualize_graph():
    """Return visual representation of the graph structure."""
    app = create_bs_detector_graph()
    
    # Get the mermaid code
    mermaid_code = app.get_graph().draw_mermaid()
    
    # Check if we're in a Jupyter environment
    try:
        from IPython.display import Image
        import base64
        
        # Use mermaid.ink API to render
        graph_bytes = mermaid_code.encode("utf-8")
        base64_string = base64.b64encode(graph_bytes).decode("ascii")
        image_url = f"https://mermaid.ink/img/{base64_string}?type=png"
        
        # Return the image for display
        return Image(url=image_url)
        
    except ImportError:
        # Fallback to text output if not in Jupyter
        print("BS Detector Graph Structure:")
        print("=" * 50)
        print(mermaid_code)
        print("\nGraph Flow:")
        print("1. Start → Detect BS")
        print("2. If success → Format Output → End")
        print("3. If error & retries left → Retry → Detect BS")
        print("4. If max retries → Format Output → End")
        return None


# Demo functions showing both patterns
def demo_single_run():
    """Demo: Single claim check with graph"""
    print("=== Single Run Demo ===")
    
    claim = "The Concorde could fly at Mach 2.04"
    print(f"Checking: '{claim}'")
    
    result = check_claim_with_graph(claim)
    print(f"Result: {result}")


def demo_comparison():
    """Demo: Compare baseline vs graph versions"""
    print("=== Baseline vs Graph Comparison ===")
    
    claim = "Helicopters can fly upside down"
    llm = LLMFactory.create_llm()
    
    # Baseline version (no retry)
    print("\n1. Baseline version:")
    baseline_result = check_claim(claim, llm)
    print(f"   Result: {baseline_result}")
    
    # Graph version (with retry)
    print("\n2. Graph version (with retry):")
    graph_result = check_claim_with_graph(claim)
    print(f"   Result: {graph_result}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "chat":
            interactive_chat()
        elif sys.argv[1] == "visualize":
            visualize_graph()
        elif sys.argv[1] == "compare":
            demo_comparison()
        else:
            # Check a single claim
            result = check_claim_with_graph(" ".join(sys.argv[1:]))
            print(f"Result: {result}")
    else:
        # Default: show all demos
        demo_single_run()
        print("\n" + "="*50 + "\n")
        visualize_graph()
        print("\n" + "="*50)
        print("\nRun with 'chat' argument for interactive mode:")
        print("  python m2_langgraph.py chat")