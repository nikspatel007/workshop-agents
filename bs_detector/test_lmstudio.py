#!/usr/bin/env python3
"""
Test script for LM Studio integration with BS Detector

This script demonstrates how to use LM Studio as a local LLM provider.
Make sure LM Studio is running with a model loaded before running this script.

Prerequisites:
1. Install LM Studio from https://lmstudio.ai/
2. Download and load a model (e.g., Mistral, Llama, etc.)
3. Start the local server (usually runs on http://localhost:1234)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.llm_factory import LLMFactory
from modules.m1_baseline import check_claim


def test_lmstudio_connection():
    """Test basic connection to LM Studio"""
    print("🔌 Testing LM Studio Connection...")
    print("-" * 50)
    
    try:
        # Create LM Studio LLM instance
        llm = LLMFactory.create_llm(provider="lmstudio")
        
        # Test with a simple query
        response = llm.invoke("Say 'Hello from LM Studio!' if you can hear me.")
        print("✅ Connection successful!")
        print(f"Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nMake sure:")
        print("1. LM Studio is running")
        print("2. A model is loaded in LM Studio")
        print("3. The server is started (default: http://localhost:1234)")
        return False


def test_bs_detector_with_lmstudio():
    """Test BS detector using LM Studio"""
    print("\n\n🤖 Testing BS Detector with LM Studio")
    print("=" * 50)
    
    # Create LLM instance
    llm = LLMFactory.create_llm(provider="lmstudio")
    
    # Test claims
    test_claims = [
        "The Boeing 747 has four engines",
        "Airplanes can fly backwards at supersonic speeds",
        "The Wright brothers first flew in 1903"
    ]
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        print("-" * 40)
        
        try:
            result = check_claim(claim, llm)
            print(f"Verdict: {result['verdict']}")
            print(f"Confidence: {result['confidence']}%")
            print(f"Reasoning: {result['reasoning']}")
        except Exception as e:
            print(f"Error: {str(e)}")


def test_custom_endpoint():
    """Test with custom LM Studio endpoint"""
    print("\n\n🔧 Testing Custom Endpoint")
    print("=" * 50)
    
    # You can override the endpoint
    custom_endpoint = "http://localhost:8080/v1"  # Example custom endpoint
    
    try:
        _ = LLMFactory.create_llm(
            provider="lmstudio",
            base_url=custom_endpoint
        )
        print(f"✅ Created LLM with custom endpoint: {custom_endpoint}")
    except Exception as e:
        print(f"❌ Failed with custom endpoint: {str(e)}")


def main():
    """Main test function"""
    print("🚀 LM Studio Integration Test")
    print("=" * 70)
    print()
    
    # Test connection first
    if test_lmstudio_connection():
        # If connection successful, test BS detector
        test_bs_detector_with_lmstudio()
        
        # Optionally test custom endpoint
        # test_custom_endpoint()
    
    print("\n\n📝 Configuration Notes:")
    print("-" * 50)
    print("You can configure LM Studio in your .env file:")
    print("  LMSTUDIO_BASE_URL=http://localhost:1234/v1")
    print("  LMSTUDIO_MODEL=your-model-name")
    print("  DEFAULT_LLM_PROVIDER=lmstudio")
    print("\nOr use it programmatically:")
    print("  llm = LLMFactory.create_llm(provider='lmstudio')")


if __name__ == "__main__":
    main()