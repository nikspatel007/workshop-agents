"""
Quick test script to verify Bedrock connection in SageMaker
"""

import os
import sys

# Set environment variables
os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"

print("🔧 Testing Bedrock Configuration")
print(f"Region: {os.environ.get('AWS_DEFAULT_REGION')}")
print(f"Model: {os.environ.get('BEDROCK_MODEL')}")
print(f"Provider: {os.environ.get('DEFAULT_LLM_PROVIDER')}")

# Test 1: Basic boto3 connection
print("\n📋 Test 1: Boto3 Connection")
try:
    import boto3
    bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
    print("✅ Boto3 bedrock-runtime client created successfully")
except Exception as e:
    print(f"❌ Boto3 error: {e}")
    sys.exit(1)

# Test 2: Direct Bedrock call with Messages API
print("\n📋 Test 2: Direct Bedrock API Call (Messages API)")
try:
    import json
    
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
    
    response = bedrock.invoke_model(
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

# Test 3: LangChain Bedrock
print("\n📋 Test 3: LangChain Bedrock")
try:
    from langchain_aws import ChatBedrock
    
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-west-2",
        model_kwargs={"temperature": 0.7}
    )
    
    response = llm.invoke("Say 'Hello from Bedrock'")
    print("✅ LangChain Bedrock successful")
    print(f"Response: {response.content if hasattr(response, 'content') else response}")
    
except Exception as e:
    print(f"❌ LangChain Bedrock error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: LLM Factory
print("\n📋 Test 4: LLM Factory")
try:
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm(provider="bedrock")
    response = llm.invoke("What is 2+2?")
    
    print("✅ LLM Factory successful")
    print(f"Response: {response.content if hasattr(response, 'content') else response}")
    
except Exception as e:
    print(f"❌ LLM Factory error: {e}")
    import traceback
    traceback.print_exc()

print("\n✨ Testing complete!")