#!/usr/bin/env python3
"""
Demo script for Iteration 2: LangGraph BS Detector
Shows the progression from baseline to graph-based architecture.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m1_baseline import check_claim
from modules.m2_langgraph import (
    check_claim_with_graph,
    interactive_chat,
    visualize_graph
)
from config.llm_factory import LLMFactory


def show_progression():
    """Demonstrate the progression from Iteration 1 to 2"""
    print("=" * 60)
    print("BS Detector: From Baseline to LangGraph")
    print("=" * 60)
    
    # Test claim
    claim = "The SR-71 Blackbird could fly at Mach 3.3"
    
    print(f"\nTest Claim: '{claim}'")
    print("-" * 60)
    
    # Iteration 1: Baseline
    print("\n📌 ITERATION 1: Baseline (single function)")
    print("-" * 40)
    
    llm = LLMFactory.create_llm()
    result1 = check_claim(claim, llm)
    
    print(f"Result: {result1['verdict']}")
    print(f"Confidence: {result1['confidence']}%")
    print(f"Method: Direct LLM call with Pydantic")
    
    # Iteration 2: LangGraph
    print("\n📌 ITERATION 2: LangGraph (graph-based)")
    print("-" * 40)
    
    result2 = check_claim_with_graph(claim, max_retries=3)
    
    print(f"Result: {result2['verdict']}")
    print(f"Confidence: {result2['confidence']}%")
    print(f"Method: Graph with nodes, state, and retry logic")
    
    # Show the difference
    print("\n🔄 WHAT'S NEW IN ITERATION 2:")
    print("-" * 40)
    print("✅ Graph-based architecture")
    print("✅ Automatic retry on errors")
    print("✅ Separation of concerns (nodes)")
    print("✅ Visual flow representation")
    print("✅ Reusable for chat interface")


def demo_error_handling():
    """Show how LangGraph handles errors with retry"""
    print("\n" + "=" * 60)
    print("Error Handling Demo")
    print("=" * 60)
    
    # Simulate a problematic claim
    claim = "🚁 " * 100  # Very long, might cause issues
    
    print(f"\nProblematic claim: {claim[:50]}...")
    print("\nWith LangGraph retry logic:")
    
    result = check_claim_with_graph(claim, max_retries=2)
    print(f"Final result: {result}")


def main():
    """Main demo flow"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "chat":
            print("\n🤖 Starting Interactive Chat Mode...")
            print("=" * 60)
            interactive_chat()
            
        elif command == "visualize":
            print("\n📊 Graph Structure:")
            print("=" * 60)
            visualize_graph()
            
        elif command == "compare":
            show_progression()
            
        elif command == "errors":
            demo_error_handling()
            
        else:
            # Process a single claim
            claim = " ".join(sys.argv[1:])
            print(f"\nChecking: '{claim}'")
            result = check_claim_with_graph(claim)
            print(f"\nResult: {result['verdict']}")
            print(f"Confidence: {result['confidence']}%")
            print(f"Reasoning: {result['reasoning']}")
    
    else:
        # Default: show all demos
        print("🚀 BS DETECTOR - LANGGRAPH DEMO")
        print("=" * 60)
        
        # Show progression
        show_progression()
        
        # Show graph
        print("\n" + "=" * 60)
        visualize_graph()
        
        print("\n" + "=" * 60)
        print("📌 AVAILABLE COMMANDS:")
        print("-" * 40)
        print("python demo_langgraph.py chat          # Interactive chat")
        print("python demo_langgraph.py visualize     # Show graph structure")
        print("python demo_langgraph.py compare       # Compare iterations")
        print("python demo_langgraph.py <claim>       # Check single claim")
        print("=" * 60)


if __name__ == "__main__":
    main()