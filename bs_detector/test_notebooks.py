#!/usr/bin/env python3
"""
Test that notebook code snippets still work after cleanup
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Testing Notebook Code Snippets")
print("=" * 50)

# Test 00_Setup imports
print("\n📓 Testing 00_Setup imports...")
try:
    from config.llm_factory import LLMFactory
    llm = LLMFactory.create_llm()
    print("✅ Setup imports work")
except Exception as e:
    print(f"❌ Setup failed: {e}")

# Test 01_Baseline
print("\n📓 Testing 01_Baseline...")
try:
    from modules.m1_baseline import check_claim, BSDetectorOutput
    # Would need LLM to fully test
    print("✅ Baseline imports work")
except Exception as e:
    print(f"❌ Baseline failed: {e}")

# Test 02_PromptEngineering
print("\n📓 Testing 02_PromptEngineering...")
try:
    from modules.m2_prompt_engineering import (
        create_structured_prompt,
        create_few_shot_prompt,
        BSDetectionResult
    )
    prompt = create_structured_prompt("Test")
    print("✅ Prompt Engineering imports work")
except Exception as e:
    print(f"❌ Prompt Engineering failed: {e}")

# Test 03_LangGraph
print("\n📓 Testing 03_LangGraph...")
try:
    from modules.m3_langgraph import check_claim_with_graph, create_bs_detector_graph
    graph = create_bs_detector_graph()
    print("✅ LangGraph imports work")
except Exception as e:
    print(f"❌ LangGraph failed: {e}")

# Test 04_Evaluation
print("\n📓 Testing 04_Evaluation...")
try:
    from modules.m1_baseline import check_claim
    from modules.m3_langgraph import check_claim_with_graph
    from modules.m4_evaluation import create_test_dataset
    dataset = create_test_dataset()
    print("✅ Evaluation imports work")
except Exception as e:
    print(f"❌ Evaluation failed: {e}")

# Test 05_Tools
print("\n📓 Testing 05_Tools...")
try:
    from modules.m5_tools import check_claim_with_tools
    # Note: notebook doesn't actually import this, it defines inline
    print("✅ Tools module exists")
except Exception as e:
    print(f"❌ Tools failed: {e}")

# Test 06_HumanInLoop
print("\n📓 Testing 06_HumanInLoop...")
try:
    # Notebook 06 is self-contained, but let's test our module exists
    from modules.m6_human_in_loop_simple import create_human_in_loop_graph
    graph = create_human_in_loop_graph()
    print("✅ Human-in-loop module works")
except Exception as e:
    print(f"❌ Human-in-loop failed: {e}")

# Test utils
print("\n📓 Testing shared utilities...")
try:
    from modules.utils import render_mermaid_diagram, format_verdict
    diagram = render_mermaid_diagram("graph TD\n    A --> B")
    print("✅ Utilities work")
except Exception as e:
    print(f"❌ Utilities failed: {e}")

print("\n" + "=" * 50)
print("✅ Notebook compatibility test complete!")
print("\nNote: Full notebook execution would require an LLM.")
print("These tests verify imports and basic functionality.")