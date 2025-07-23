"""
SageMaker Setup Script for BS Detector Workshop
This script sets up the environment for running the workshop on SageMaker with AWS Bedrock
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def install_requirements():
    """Install required packages for SageMaker"""
    print("📦 Installing required packages...")
    
    packages = [
        "langchain>=0.1.0",
        "langgraph>=0.0.20",
        "langchain-aws",  # For Bedrock support
        "langchain-community",
        "pydantic>=2.0",
        "python-dotenv",
        "duckduckgo-search",
        "boto3>=1.28.0",  # For AWS services
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ All packages installed successfully!")


def setup_bedrock_config():
    """Configure AWS Bedrock for the workshop"""
    print("\n🔧 Setting up AWS Bedrock configuration...")
    
    # Check if running in SageMaker
    if os.path.exists("/opt/ml"):
        print("✅ Running in SageMaker environment")
        
        # SageMaker provides AWS credentials automatically via IAM role
        print("✅ Using SageMaker execution role for AWS credentials")
        
        # Set default Bedrock model - Claude 3 Haiku
        os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
        os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        
    else:
        print("⚠️  Not running in SageMaker - manual AWS configuration needed")
        
        # For local testing
        region = input("Enter AWS region (default: us-east-1): ").strip() or "us-east-1"
        os.environ["AWS_DEFAULT_REGION"] = region
        os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-sonnet-20240229-v1:0"
        os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
    
    # Create .env file for the workshop
    env_content = f"""# BS Detector Workshop Configuration
# Generated for SageMaker with AWS Bedrock

# Default LLM Provider
DEFAULT_LLM_PROVIDER=bedrock

# AWS Bedrock Configuration
BEDROCK_MODEL=anthropic.claude-3-5-haiku-20241022-v1:0
AWS_DEFAULT_REGION=us-west-2

# Model Parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Optional: Add other providers as fallback
# OPENAI_API_KEY=your-key-here
# ANTHROPIC_API_KEY=your-key-here
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with Bedrock configuration")


def test_bedrock_connection():
    """Test that Bedrock is accessible"""
    print("\n🧪 Testing AWS Bedrock connection...")
    
    try:
        import boto3
        
        # Create Bedrock client
        bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
        
        # Test with a simple prompt
        from config.llm_factory import LLMFactory
        
        llm = LLMFactory.create_llm(provider="bedrock")
        response = llm.invoke("Say 'Hello from AWS Bedrock!'")
        
        if hasattr(response, 'content'):
            print(f"✅ Bedrock test successful: {response.content}")
        else:
            print(f"✅ Bedrock test successful: {response}")
            
        return True
        
    except Exception as e:
        print(f"❌ Bedrock test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure your SageMaker execution role has Bedrock permissions")
        print("2. Check that Bedrock is available in your region")
        print("3. Verify the model ID is correct")
        return False


def create_test_notebook():
    """Create a test notebook to verify setup"""
    print("\n📓 Creating test notebook...")
    
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# BS Detector Workshop - Setup Test\n", "\n", "This notebook tests that everything is set up correctly."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test imports\n",
                    "try:\n",
                    "    from config.llm_factory import LLMFactory\n",
                    "    from modules.m1_baseline import check_claim\n",
                    "    print('✅ Imports successful!')\n",
                    "except Exception as e:\n",
                    "    print(f'❌ Import error: {e}')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test Bedrock LLM\n",
                    "try:\n",
                    "    llm = LLMFactory.create_llm()\n",
                    "    response = llm.invoke('What is 2+2?')\n",
                    "    print(f'✅ Bedrock LLM working!')\n",
                    "    print(f'Response: {response.content if hasattr(response, \"content\") else response}')\n",
                    "except Exception as e:\n",
                    "    print(f'❌ LLM error: {e}')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test BS Detector\n",
                    "try:\n",
                    "    llm = LLMFactory.create_llm()\n",
                    "    result = check_claim('The sky is green', llm)\n",
                    "    print(f'✅ BS Detector working!')\n",
                    "    print(f'Result: {result}')\n",
                    "except Exception as e:\n",
                    "    print(f'❌ BS Detector error: {e}')"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open("Test_Setup.ipynb", "w") as f:
        json.dump(notebook_content, f, indent=2)
    
    print("✅ Created Test_Setup.ipynb")


def main():
    """Main setup function"""
    print("🚀 BS Detector Workshop Setup for SageMaker")
    print("=" * 50)
    
    # Change to the right directory
    if os.path.exists("bs_detector"):
        os.chdir("bs_detector")
    
    # Install packages
    install_requirements()
    
    # Setup Bedrock
    setup_bedrock_config()
    
    # Test connection
    bedrock_ok = test_bedrock_connection()
    
    # Create test notebook
    create_test_notebook()
    
    print("\n" + "=" * 50)
    if bedrock_ok:
        print("✅ Setup complete! You can now run the workshop notebooks.")
        print("\nStart with:")
        print("1. Test_Setup.ipynb - Verify everything works")
        print("2. notebooks/00_Setup.ipynb - Begin the workshop")
    else:
        print("⚠️  Setup complete but Bedrock test failed.")
        print("Please check your AWS permissions and try Test_Setup.ipynb")
    
    print("\n💡 Tip: The workshop uses AWS Bedrock by default.")
    print("No API keys needed - it uses your SageMaker execution role!")


if __name__ == "__main__":
    main()