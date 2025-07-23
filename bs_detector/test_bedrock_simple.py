"""
Simple Bedrock test focusing on LangChain integration
"""

import os

# Set environment variables
os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"

print("🔧 Simple Bedrock Test")
print("=" * 50)

# Test 1: Direct LangChain
print("\n📋 Test 1: Direct LangChain Bedrock")
try:
    from langchain_aws import ChatBedrock
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-west-2"
    )
    
    # Simple test
    response = llm.invoke("Say 'Hello from Bedrock' and nothing else")
    print("✅ Success!")
    print(f"Response: {response.content if hasattr(response, 'content') else response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: LLM Factory
print("\n📋 Test 2: LLM Factory")
try:
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm()
    response = llm.invoke("What is 2+2? Just give the number.")
    
    print("✅ Success!")
    print(f"Response: {response.content if hasattr(response, 'content') else response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: BS Detector
print("\n📋 Test 3: BS Detector Module")
try:
    from modules.m1_baseline import check_claim
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm()
    result = check_claim("The sky is purple", llm)
    
    print("✅ Success!")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Testing complete!")
print("\nIf all tests passed, you're ready to run the notebooks!")
print("If any failed, check:")
print("1. IAM role has bedrock:InvokeModel permission")
print("2. Bedrock is available in us-west-2")
print("3. langchain-aws is installed: pip install langchain-aws")