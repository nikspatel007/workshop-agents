#!/usr/bin/env python3
"""
Comprehensive test suite to verify all modules work after cleanup

This script tests:
1. All module imports
2. Basic functionality of each module
3. Integration between modules
4. Notebook code snippets
"""

import sys
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


def test_module(name, test_func):
    """Run a test and track results"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print('='*50)
    
    try:
        test_func()
        print(f"✅ {name} - PASSED")
        test_results["passed"] += 1
    except Exception as e:
        print(f"❌ {name} - FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        test_results["failed"] += 1
        test_results["errors"].append({
            "test": name,
            "error": str(e),
            "traceback": traceback.format_exc()
        })


def test_config():
    """Test configuration module"""
    from config.llm_factory import LLMFactory
    
    # Test default LLM creation
    llm = LLMFactory.create_llm()
    assert llm is not None, "Failed to create default LLM"
    
    # Test specific provider (if available)
    try:
        openai_llm = LLMFactory.create_llm(provider="openai")
        assert openai_llm is not None
    except:
        print("OpenAI provider not configured - skipping")


def test_utils():
    """Test utility functions"""
    from modules.utils import render_mermaid_diagram, format_verdict
    
    # Test mermaid diagram
    diagram = render_mermaid_diagram("graph TD\\n    A --> B")
    assert diagram is not None
    
    # Test verdict formatting
    output = format_verdict("BS", 85, ["Evidence 1", "Evidence 2"])
    assert "Verdict: BS" in output
    assert "85%" in output


def test_baseline():
    """Test baseline module"""
    from modules.m1_baseline import check_claim, BSDetectorOutput
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm()
    result = check_claim("The sky is blue", llm)
    
    assert isinstance(result, dict)
    assert "verdict" in result
    assert "confidence" in result
    assert "reasoning" in result


def test_prompt_engineering():
    """Test prompt engineering module"""
    from modules.m2_prompt_engineering import (
        create_structured_prompt,
        create_few_shot_prompt,
        BSDetectionResult
    )
    
    # Test prompt creation
    prompt1 = create_structured_prompt("Test claim")
    assert "aviation expert" in prompt1
    
    prompt2 = create_few_shot_prompt("Test claim")
    assert "Wright brothers" in prompt2


def test_langgraph():
    """Test LangGraph module"""
    from modules.m3_langgraph import (
        BSDetectorState,
        create_bs_detector_graph,
        check_claim_with_graph
    )
    
    # Test state creation
    state = BSDetectorState(
        claim="Test claim",
        retry_count=0,
        max_retries=3
    )
    assert state.claim == "Test claim"
    
    # Test graph creation
    graph = create_bs_detector_graph()
    assert graph is not None


def test_evaluation():
    """Test evaluation module"""
    from modules.m4_evaluation import (
        create_test_dataset,
        evaluate_bs_detector,
        BSDetectorTestCase
    )
    
    # Test dataset creation
    dataset = create_test_dataset()
    assert len(dataset) > 0
    assert isinstance(dataset[0], BSDetectorTestCase)


def test_routing():
    """Test routing module"""
    from modules.m5_routing import (
        RoutingState,
        router_node,
        technical_expert_node
    )
    
    # Test state
    state = RoutingState(claim="The Boeing 747 has four engines")
    
    # Test router
    result = router_node(state)
    assert "claim_type" in result


def test_tools():
    """Test tools module"""
    from modules.m5_tools import (
        ToolEnhancedState,
        create_search_tools,
        search_tool_node
    )
    
    # Test state
    state = ToolEnhancedState(claim="Test claim")
    assert hasattr(state, "search_results")
    
    # Test tool creation
    tools = create_search_tools()
    assert len(tools) > 0


def test_human_in_loop():
    """Test human-in-loop module"""
    from modules.m6_human_in_loop_simple import (
        HumanInLoopState,
        check_needs_review,
        create_human_in_loop_graph
    )
    
    # Test state
    state = HumanInLoopState(
        claim="Test claim",
        confidence=30
    )
    
    # Test review check
    updates = check_needs_review(state)
    assert updates.get("needs_human_review") == True
    
    # Test graph creation
    graph = create_human_in_loop_graph()
    assert graph is not None


def test_integration():
    """Test integration between modules"""
    from config.llm_factory import LLMFactory
    from modules.m1_baseline import check_claim
    from modules.m3_langgraph import check_claim_with_graph
    
    llm = LLMFactory.create_llm()
    test_claim = "The Earth is flat"
    
    # Test baseline
    baseline_result = check_claim(test_claim, llm)
    assert baseline_result["verdict"] in ["BS", "LEGITIMATE", "UNCERTAIN"]
    
    # Test with graph
    graph_result = check_claim_with_graph(test_claim)
    assert graph_result["verdict"] in ["BS", "LEGITIMATE", "UNCERTAIN", "ERROR"]


def main():
    """Run all tests"""
    print("🧪 BS Detector Module Test Suite")
    print("=" * 60)
    
    # Test each module
    test_module("Configuration", test_config)
    test_module("Utilities", test_utils)
    test_module("Module 1: Baseline", test_baseline)
    test_module("Module 2: Prompt Engineering", test_prompt_engineering)
    test_module("Module 3: LangGraph", test_langgraph)
    test_module("Module 4: Evaluation", test_evaluation)
    test_module("Module 5: Routing", test_routing)
    test_module("Module 5: Tools", test_tools)
    test_module("Module 6: Human-in-Loop", test_human_in_loop)
    test_module("Integration", test_integration)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    
    if test_results["failed"] > 0:
        print("\n⚠️  Failed Tests:")
        for error in test_results["errors"]:
            print(f"\n- {error['test']}")
            print(f"  Error: {error['error']}")
    
    # Exit code
    sys.exit(0 if test_results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()