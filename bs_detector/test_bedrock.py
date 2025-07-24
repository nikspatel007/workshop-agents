"""
Comprehensive AWS Bedrock integration tests

This script tests:
1. Direct boto3 Bedrock API calls
2. LangChain integration with Bedrock  
3. LLMFactory with Bedrock provider
4. Workshop modules with Bedrock

Usage:
    python test_bedrock.py [--simple]
    
    --simple: Run only the essential tests (LangChain and modules)
"""

import os
import sys
import argparse
import json
import traceback


def setup_env():
    """Set up environment variables for Bedrock"""
    os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
    os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


def test_boto3_connection():
    """Test basic boto3 connection"""
    print("\n📋 Test 1: Boto3 Connection")
    try:
        import boto3
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        print("✅ Boto3 bedrock-runtime client created successfully")
        return bedrock
    except Exception as e:
        print(f"❌ Boto3 error: {e}")
        return None


def test_direct_bedrock_api(bedrock_client):
    """Test direct Bedrock API call with Messages API"""
    print("\n📋 Test 2: Direct Bedrock API Call (Messages API)")
    try:
        # Use the Messages API format for Claude 3
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        print("✅ Direct Bedrock API call successful")
        print(f"Response: {response_body.get('content', [{}])[0].get('text', 'No text in response')[:50]}...")
        
    except Exception as e:
        print(f"❌ Bedrock API error: {e}")
        print("Make sure your IAM role has bedrock:InvokeModel permission")


def test_langchain_bedrock():
    """Test LangChain Bedrock integration"""
    print("\n📋 Test: LangChain Bedrock")
    try:
        from langchain_aws import ChatBedrock
        
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            region_name="us-west-2",
            model_kwargs={"temperature": 0.7}
        )
        
        response = llm.invoke("Say 'Hello from Bedrock' and nothing else")
        print("✅ LangChain Bedrock successful")
        print(f"Response: {response.content if hasattr(response, 'content') else response}")
        return True
        
    except Exception as e:
        print(f"❌ LangChain Bedrock error: {e}")
        traceback.print_exc()
        return False


def test_llm_factory():
    """Test LLM Factory with Bedrock"""
    print("\n📋 Test: LLM Factory")
    try:
        from config.llm_factory import LLMFactory
        
        llm = LLMFactory.create_llm(provider="bedrock")
        response = llm.invoke("What is 2+2? Just give the number.")
        
        print("✅ LLM Factory successful")
        print(f"Response: {response.content if hasattr(response, 'content') else response}")
        return True
        
    except Exception as e:
        print(f"❌ LLM Factory error: {e}")
        traceback.print_exc()
        return False


def test_workshop_module():
    """Test workshop BS detector module"""
    print("\n📋 Test: BS Detector Module")
    try:
        from modules.m1_baseline import check_claim
        from config.llm_factory import LLMFactory
        
        llm = LLMFactory.create_llm()
        result = check_claim("The sky is purple", llm)
        
        print("✅ BS Detector module successful")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ BS Detector error: {e}")
        traceback.print_exc()
        return False


def run_full_tests():
    """Run comprehensive test suite"""
    setup_env()
    
    print("🔧 Testing Bedrock Configuration")
    print(f"Region: {os.environ.get('AWS_DEFAULT_REGION')}")
    print(f"Model: {os.environ.get('BEDROCK_MODEL')}")
    print(f"Provider: {os.environ.get('DEFAULT_LLM_PROVIDER')}")
    
    # Test 1: Boto3
    bedrock_client = test_boto3_connection()
    if not bedrock_client:
        print("\n❌ Cannot proceed without boto3 connection")
        sys.exit(1)
    
    # Test 2: Direct API
    test_direct_bedrock_api(bedrock_client)
    
    # Test 3: LangChain
    test_langchain_bedrock()
    
    # Test 4: LLM Factory
    test_llm_factory()
    
    # Test 5: Workshop Module
    test_workshop_module()
    
    print("\n✨ Testing complete!")


def run_simple_tests():
    """Run simple/essential tests only"""
    setup_env()
    
    print("🔧 Simple Bedrock Test")
    print("=" * 50)
    
    # Test LangChain
    langchain_ok = test_langchain_bedrock()
    
    # Test LLM Factory
    factory_ok = test_llm_factory()
    
    # Test BS Detector
    module_ok = test_workshop_module()
    
    print("\n✅ Testing complete!")
    
    if all([langchain_ok, factory_ok, module_ok]):
        print("\n🎉 All tests passed! You're ready to run the notebooks!")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("1. IAM role has bedrock:InvokeModel permission")
        print("2. Bedrock is available in us-west-2")
        print("3. langchain-aws is installed: pip install langchain-aws")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test AWS Bedrock integration")
    parser.add_argument('--simple', action='store_true', help='Run only essential tests')
    args = parser.parse_args()
    
    if args.simple:
        run_simple_tests()
    else:
        run_full_tests()