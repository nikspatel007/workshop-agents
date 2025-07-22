#!/usr/bin/env python3
"""
Demo script for Iteration 1: Baseline BS Detector
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m1_baseline import check_claim, BSDetectorOutput
from config.llm_factory import LLMFactory


def main():
    """Run baseline BS detector demo"""
    print("=" * 60)
    print("BS Detector - Iteration 1: Baseline Demo (with Pydantic)")
    print("=" * 60)
    
    # Show Pydantic model
    print("\n1. Pydantic Model Structure")
    print("-" * 30)
    
    sample_output = BSDetectorOutput(
        verdict="BS",
        confidence=95,
        reasoning="Commercial aircraft cannot reach escape velocity"
    )
    print(f"Model fields: {BSDetectorOutput.model_fields.keys()}")
    print(f"Model data: {sample_output.model_dump()}")
    
    # Test model validation
    print("\n2. Testing Model Validation")
    print("-" * 30)
    
    # Test valid model
    try:
        valid_output = BSDetectorOutput(
            verdict="LEGITIMATE",
            confidence=85,
            reasoning="This is a valid aviation claim"
        )
        print("✓ Valid model created successfully")
    except Exception as e:
        print(f"✗ Valid model failed: {e}")
    
    # Test invalid confidence
    try:
        from pydantic import ValidationError
        invalid_output = BSDetectorOutput(
            verdict="BS",
            confidence=150,  # Invalid: > 100
            reasoning="Test"
        )
        print("✗ Invalid model should have failed")
    except ValidationError:
        print("✓ Model correctly rejected invalid confidence (>100)")
    
    # Test with LLM if available
    print("\n3. Testing with LLM")
    print("-" * 30)
    
    try:
        llm = LLMFactory.create_llm()
        print(f"✓ Using {llm.__class__.__name__}")
        
        # Test claims
        test_claims = [
            "The Boeing 747 has four engines",
            "Commercial planes can fly to the moon",
            "Pilots need licenses to fly"
        ]
        
        for claim in test_claims:
            print(f"\nChecking: '{claim}'")
            result = check_claim(claim, llm)
            
            print(f"  Verdict: {result['verdict']} ({result['confidence']}% confident)")
            print(f"  Reasoning: {result['reasoning']}")
            
            if result.get('error'):
                print(f"  ⚠️ Error: {result['error']}")
                
    except Exception as e:
        print(f"⚠️ Could not test with LLM: {e}")
        print("  Make sure you have API keys set up in .env")
    
    print("\n" + "=" * 60)
    print("Demo complete! Check notebooks/01_Baseline.ipynb for more.")


if __name__ == "__main__":
    main()