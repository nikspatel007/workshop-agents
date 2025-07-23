"""
Clean SageMaker Setup Script - Creates a proper Jupyter kernel
"""

import subprocess
import sys
import os
import json


def install_packages():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    packages = [
        "ipykernel",  # Required for creating kernels
        "langchain>=0.1.0",
        "langgraph>=0.0.20",
        "langchain-aws",
        "langchain-community",
        "pydantic>=2.0",
        "python-dotenv",
        "duckduckgo-search",
        "boto3>=1.28.0",
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ All packages installed successfully!")


def create_workshop_kernel():
    """Create a dedicated kernel for the workshop"""
    print("\n🔧 Creating workshop kernel...")
    
    kernel_name = "workshop_kernel"
    display_name = "Workshop Kernel (BS Detector)"
    
    # Install the kernel
    subprocess.check_call([
        sys.executable, "-m", "ipykernel", "install",
        "--user",
        "--name", kernel_name,
        "--display-name", display_name
    ])
    
    print(f"✅ Created kernel: {display_name}")
    print(f"   Internal name: {kernel_name}")
    
    # Get kernel location and update with environment variables
    kernel_dir = os.path.expanduser(f"~/.local/share/jupyter/kernels/{kernel_name}")
    kernel_json_path = os.path.join(kernel_dir, "kernel.json")
    
    if os.path.exists(kernel_json_path):
        with open(kernel_json_path, 'r') as f:
            kernel_spec = json.load(f)
        
        # Add environment variables to the kernel
        kernel_spec["env"] = {
            "DEFAULT_LLM_PROVIDER": "bedrock",
            "BEDROCK_MODEL": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "AWS_DEFAULT_REGION": "us-west-2"
        }
        
        with open(kernel_json_path, 'w') as f:
            json.dump(kernel_spec, f, indent=2)
        
        print("✅ Added environment variables to kernel")
    
    return kernel_name


def create_verification_notebook():
    """Create a notebook to verify the setup"""
    print("\n📓 Creating verification notebook...")
    
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Workshop Setup Verification\n",
                    "\n",
                    "This notebook verifies that your workshop environment is set up correctly.\n",
                    "\n",
                    "**IMPORTANT**: Make sure you're using the **Workshop Kernel (BS Detector)** kernel.\n",
                    "- Check in the top right corner of the notebook\n",
                    "- If not, go to Kernel → Change kernel → Workshop Kernel (BS Detector)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Verify environment variables\n",
                    "import os\n",
                    "\n",
                    "print('🔍 Environment Check:')\n",
                    "print(f\"Provider: {os.environ.get('DEFAULT_LLM_PROVIDER', 'NOT SET')}\")\n",
                    "print(f\"Model: {os.environ.get('BEDROCK_MODEL', 'NOT SET')}\")\n",
                    "print(f\"Region: {os.environ.get('AWS_DEFAULT_REGION', 'NOT SET')}\")\n",
                    "\n",
                    "if os.environ.get('DEFAULT_LLM_PROVIDER') == 'bedrock':\n",
                    "    print('\\n✅ Environment variables are set correctly!')\n",
                    "else:\n",
                    "    print('\\n❌ Environment variables not set - make sure you\\'re using Workshop Kernel')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Verify packages\n",
                    "packages_ok = True\n",
                    "\n",
                    "print('📦 Package Check:')\n",
                    "for package in ['langchain', 'langgraph', 'langchain_aws', 'pydantic', 'boto3']:\n",
                    "    try:\n",
                    "        __import__(package.replace('-', '_'))\n",
                    "        print(f'✅ {package}')\n",
                    "    except ImportError:\n",
                    "        print(f'❌ {package} - NOT INSTALLED')\n",
                    "        packages_ok = False\n",
                    "\n",
                    "if packages_ok:\n",
                    "    print('\\n✅ All packages are installed!')\n",
                    "else:\n",
                    "    print('\\n❌ Some packages missing - the setup script may have failed')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test Bedrock connection\n",
                    "print('🤖 Bedrock Connection Test:')\n",
                    "\n",
                    "try:\n",
                    "    from langchain_aws import ChatBedrock\n",
                    "    \n",
                    "    llm = ChatBedrock(\n",
                    "        model_id=\"anthropic.claude-3-5-haiku-20241022-v1:0\",\n",
                    "        region_name=\"us-west-2\"\n",
                    "    )\n",
                    "    \n",
                    "    response = llm.invoke(\"Say 'Workshop ready!' and nothing else.\")\n",
                    "    print(f\"Response: {response.content}\")\n",
                    "    print('\\n✅ Bedrock connection successful!')\n",
                    "    \n",
                    "except Exception as e:\n",
                    "    print(f'❌ Bedrock connection failed: {e}')\n",
                    "    print('\\nTroubleshooting:')\n",
                    "    print('1. Check IAM role has bedrock:InvokeModel permission')\n",
                    "    print('2. Verify Claude 3.5 Haiku is available in us-west-2')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test workshop modules\n",
                    "print('🔧 Workshop Module Test:')\n",
                    "\n",
                    "try:\n",
                    "    from config.llm_factory import LLMFactory\n",
                    "    from modules.m1_baseline import check_claim\n",
                    "    \n",
                    "    llm = LLMFactory.create_llm()\n",
                    "    result = check_claim(\"The sky is green\", llm)\n",
                    "    \n",
                    "    print(f\"BS Detector result: {result}\")\n",
                    "    print('\\n✅ Workshop modules working!')\n",
                    "    \n",
                    "except Exception as e:\n",
                    "    print(f'❌ Module test failed: {e}')\n",
                    "    print('Make sure you\\'re in the bs_detector directory')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## Next Steps\n",
                    "\n",
                    "If all tests passed:\n",
                    "1. Open `notebooks/00_Setup.ipynb`\n",
                    "2. Make sure to select **Workshop Kernel (BS Detector)** as the kernel\n",
                    "3. Start the workshop!\n",
                    "\n",
                    "If any test failed, please review the error messages above."
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Workshop Kernel (BS Detector)",
                "language": "python",
                "name": "workshop_kernel"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open("Verify_Setup.ipynb", "w") as f:
        json.dump(notebook_content, f, indent=2)
    
    print("✅ Created Verify_Setup.ipynb")


def main():
    """Main setup function"""
    print("🚀 BS Detector Workshop Setup for SageMaker")
    print("=" * 50)
    
    # Change to the bs_detector directory if it exists
    if os.path.exists("bs_detector"):
        os.chdir("bs_detector")
        print("📁 Changed to bs_detector directory")
    
    # Install packages
    install_packages()
    
    # Create the workshop kernel
    kernel_name = create_workshop_kernel()
    
    # Create verification notebook
    create_verification_notebook()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Open Verify_Setup.ipynb")
    print("2. Select kernel: Kernel → Change kernel → Workshop Kernel (BS Detector)")
    print("3. Run all cells to verify setup")
    print("4. Then open notebooks/00_Setup.ipynb to start the workshop")
    print("\n💡 Important: Always use 'Workshop Kernel (BS Detector)' for all notebooks!")


if __name__ == "__main__":
    main()