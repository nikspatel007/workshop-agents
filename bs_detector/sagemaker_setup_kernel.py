"""
Enhanced SageMaker Setup Script that ensures packages are in the correct kernel
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def get_conda_env():
    """Get the current conda environment name"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'python3')
    print(f"📦 Current conda environment: {conda_env}")
    return conda_env


def install_requirements_in_kernel():
    """Install packages in the specific kernel that notebooks will use"""
    print("📦 Installing packages in notebook kernel environment...")
    
    # Get the Python executable that the notebook will use
    conda_env = get_conda_env()
    
    # Common SageMaker kernel paths
    kernel_paths = [
        f"/home/ec2-user/anaconda3/envs/{conda_env}/bin/python",  # SageMaker notebook instance
        f"/opt/conda/envs/{conda_env}/bin/python",  # Alternative path
        sys.executable  # Current Python
    ]
    
    # Find the correct Python executable
    python_exec = None
    for path in kernel_paths:
        if os.path.exists(path):
            python_exec = path
            print(f"✅ Found kernel Python at: {python_exec}")
            break
    
    if not python_exec:
        python_exec = sys.executable
        print(f"⚠️  Using current Python: {python_exec}")
    
    packages = [
        "langchain>=0.1.0",
        "langgraph>=0.0.20",
        "langchain-aws",
        "langchain-community",
        "pydantic>=2.0",
        "python-dotenv",
        "duckduckgo-search",
        "boto3>=1.28.0",
    ]
    
    # Install using the specific Python executable
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([python_exec, "-m", "pip", "install", package])
    
    print("✅ All packages installed in kernel environment!")
    return python_exec


def create_kernel_spec():
    """Create a custom kernel spec to ensure correct environment"""
    print("\n🔧 Creating custom kernel specification...")
    
    kernel_name = "bs_detector"
    display_name = "BS Detector Workshop"
    
    # Get the Python executable we're using
    python_exec = sys.executable
    
    kernel_spec = {
        "argv": [
            python_exec,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}"
        ],
        "display_name": display_name,
        "language": "python",
        "env": {
            "DEFAULT_LLM_PROVIDER": "bedrock",
            "BEDROCK_MODEL": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "AWS_DEFAULT_REGION": "us-west-2"
        }
    }
    
    # Create kernel directory
    import jupyter_core
    kernel_dir = Path(jupyter_core.paths.jupyter_data_dir()) / "kernels" / kernel_name
    kernel_dir.mkdir(parents=True, exist_ok=True)
    
    # Write kernel.json
    with open(kernel_dir / "kernel.json", "w") as f:
        json.dump(kernel_spec, f, indent=2)
    
    print(f"✅ Created kernel '{display_name}'")
    print(f"📍 Location: {kernel_dir}")
    
    # Install ipykernel in the environment
    subprocess.check_call([python_exec, "-m", "pip", "install", "ipykernel"])
    
    return kernel_name


def setup_notebook_metadata():
    """Update notebook metadata to use the correct kernel"""
    print("\n📓 Updating notebook kernel metadata...")
    
    notebooks_dir = Path("notebooks")
    if not notebooks_dir.exists():
        print("⚠️  Notebooks directory not found")
        return
    
    for notebook_path in notebooks_dir.glob("*.ipynb"):
        try:
            with open(notebook_path, 'r') as f:
                notebook = json.load(f)
            
            # Update kernel spec
            if 'metadata' not in notebook:
                notebook['metadata'] = {}
            
            notebook['metadata']['kernelspec'] = {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            }
            
            with open(notebook_path, 'w') as f:
                json.dump(notebook, f, indent=1)
            
            print(f"✅ Updated {notebook_path.name}")
            
        except Exception as e:
            print(f"⚠️  Could not update {notebook_path.name}: {e}")


def create_setup_notebook():
    """Create a setup notebook that configures the environment"""
    print("\n📓 Creating Setup_Environment.ipynb...")
    
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Environment Setup for BS Detector Workshop\n", "\n", "Run this notebook first to ensure your environment is configured correctly."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Set up environment variables\n",
                    "import os\n",
                    "import sys\n",
                    "\n",
                    "# Configure Bedrock\n",
                    "os.environ['DEFAULT_LLM_PROVIDER'] = 'bedrock'\n",
                    "os.environ['BEDROCK_MODEL'] = 'anthropic.claude-3-5-haiku-20241022-v1:0'\n",
                    "os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'\n",
                    "\n",
                    "print('✅ Environment variables set')\n",
                    "print(f'Provider: {os.environ[\"DEFAULT_LLM_PROVIDER\"]}')\n",
                    "print(f'Model: {os.environ[\"BEDROCK_MODEL\"]}')\n",
                    "print(f'Region: {os.environ[\"AWS_DEFAULT_REGION\"]}')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Verify packages are installed\n",
                    "import importlib\n",
                    "\n",
                    "packages = [\n",
                    "    'langchain',\n",
                    "    'langgraph',\n",
                    "    'langchain_aws',\n",
                    "    'langchain_community',\n",
                    "    'pydantic',\n",
                    "    'boto3'\n",
                    "]\n",
                    "\n",
                    "for package in packages:\n",
                    "    try:\n",
                    "        importlib.import_module(package.replace('-', '_'))\n",
                    "        print(f'✅ {package} is installed')\n",
                    "    except ImportError:\n",
                    "        print(f'❌ {package} is NOT installed')\n",
                    "        print(f'   Run: !pip install {package}')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test Bedrock connection\n",
                    "try:\n",
                    "    from config.llm_factory import LLMFactory\n",
                    "    \n",
                    "    llm = LLMFactory.create_llm()\n",
                    "    response = llm.invoke('Say hello!')\n",
                    "    print('✅ Bedrock connection successful!')\n",
                    "    print(f'Response: {response.content if hasattr(response, \"content\") else response}')\n",
                    "except Exception as e:\n",
                    "    print(f'❌ Bedrock connection failed: {e}')\n",
                    "    print('\\nTroubleshooting:')\n",
                    "    print('1. Check IAM role has bedrock:InvokeModel permission')\n",
                    "    print('2. Verify us-west-2 has Bedrock access')\n",
                    "    print('3. Run test_bedrock.py for detailed diagnostics')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## If packages are missing, run this cell:"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Install missing packages\n",
                    "!pip install langchain langgraph langchain-aws langchain-community pydantic boto3 python-dotenv duckduckgo-search\n",
                    "\n",
                    "print('\\n✅ Packages installed!')\n",
                    "print('⚠️  You may need to restart the kernel for changes to take effect')\n",
                    "print('   Kernel → Restart Kernel')"
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
    
    with open("Setup_Environment.ipynb", "w") as f:
        json.dump(notebook_content, f, indent=2)
    
    print("✅ Created Setup_Environment.ipynb")


def main():
    """Main setup function with kernel awareness"""
    print("🚀 BS Detector Workshop Setup for SageMaker (Kernel-Aware)")
    print("=" * 50)
    
    # Change to the right directory
    if os.path.exists("bs_detector"):
        os.chdir("bs_detector")
    
    # Install packages in the correct kernel environment
    python_exec = install_requirements_in_kernel()
    
    # Create environment setup
    from sagemaker_setup import setup_bedrock_config, test_bedrock_connection
    setup_bedrock_config()
    
    # Create setup notebook
    create_setup_notebook()
    
    # Update notebook metadata
    setup_notebook_metadata()
    
    # Test connection
    bedrock_ok = test_bedrock_connection()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Open Setup_Environment.ipynb and run all cells")
    print("2. If packages are missing, use the install cell in that notebook")
    print("3. You may need to restart kernel after installing packages")
    print("4. Then proceed with notebooks/00_Setup.ipynb")
    
    print("\n💡 Tips:")
    print("- Always run Setup_Environment.ipynb first in each session")
    print("- If imports fail, check kernel: Kernel → Change kernel → Python 3")
    print(f"- Packages installed in: {python_exec}")


if __name__ == "__main__":
    main()