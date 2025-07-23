# Running BS Detector Workshop on Amazon SageMaker

This guide explains how to run the workshop notebooks on Amazon SageMaker.

## Prerequisites

1. AWS Account with SageMaker access
2. IAM role with SageMaker permissions
3. S3 bucket for storing notebooks (optional)

## Method 1: Upload Individual Notebooks

### Step 1: Create SageMaker Notebook Instance

1. Go to AWS SageMaker Console
2. Click "Notebook instances" → "Create notebook instance"
3. Configure:
   - **Name**: `bs-detector-workshop`
   - **Instance type**: `ml.t3.medium` (or larger for faster execution)
   - **Platform**: Choose latest Python 3
   - **IAM role**: Create new or use existing with S3 access

### Step 2: Upload Notebooks

1. Once instance is running, click "Open Jupyter" or "Open JupyterLab"
2. In Jupyter interface:
   - Click "Upload" button
   - Select all notebooks from `bs_detector/notebooks/`
   - Upload in order: 00 through 06

### Step 3: Upload Required Files

Create the following directory structure in SageMaker:
```
bs_detector/
├── notebooks/          (your uploaded notebooks)
├── modules/           (upload all .py files)
├── config/            (upload all .py files)
├── data/              (upload aviation_claims_dataset.json)
└── tools/             (upload search_tool.py)
```

## Method 2: Use Git Integration

### Step 1: Clone Repository in SageMaker

1. Open terminal in SageMaker notebook instance
2. Clone your repository:
```bash
cd SageMaker
git clone https://github.com/YOUR_USERNAME/workshop-agents.git
```

### Step 2: Install Dependencies

Create a setup notebook or run in terminal:
```python
!pip install langchain langgraph langchain-openai langchain-anthropic langchain-community pydantic
```

## Method 3: Create SageMaker-Ready Package

### Step 1: Create Setup Script

Create `sagemaker_setup.py`:
```python
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    packages = [
        "langchain>=0.1.0",
        "langgraph>=0.0.20", 
        "langchain-openai",
        "langchain-anthropic",
        "langchain-community",
        "pydantic>=2.0",
        "python-dotenv",
        "duckduckgo-search"
    ]
    
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def setup_environment():
    """Set up environment variables"""
    import os
    
    # Prompt for API keys if not in environment
    if not os.environ.get("OPENAI_API_KEY"):
        key = input("Enter OpenAI API key (or press Enter to skip): ")
        if key:
            os.environ["OPENAI_API_KEY"] = key
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        key = input("Enter Anthropic API key (or press Enter to skip): ")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key

if __name__ == "__main__":
    print("🚀 Setting up BS Detector Workshop for SageMaker...")
    install_requirements()
    setup_environment()
    print("✅ Setup complete!")
```

### Step 2: Create Archive for Upload

```bash
# Create a zip file with all necessary files
cd /Users/nikpatel/Documents/GitHub/workshop-agents
zip -r bs_detector_workshop.zip bs_detector/ -x "*.pyc" -x "*__pycache__*" -x "*.ipynb_checkpoints*"
```

### Step 3: Upload and Extract in SageMaker

1. Upload `bs_detector_workshop.zip` to SageMaker
2. In terminal:
```bash
unzip bs_detector_workshop.zip
cd bs_detector
python sagemaker_setup.py
```

## Environment Configuration

### Option 1: Use SageMaker Secrets Manager

1. Store API keys in AWS Secrets Manager
2. In notebooks, retrieve them:
```python
import boto3
import json

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Use in notebook
secrets = get_secret("bs-detector-api-keys")
os.environ["OPENAI_API_KEY"] = secrets.get("openai_key", "")
```

### Option 2: Notebook Cell Configuration

Add this to the first cell of each notebook:
```python
import os

# Configure API keys (replace with your keys or use Secrets Manager)
os.environ["OPENAI_API_KEY"] = "your-key-here"
os.environ["ANTHROPIC_API_KEY"] = "your-key-here"

# For LM Studio (if using local models)
os.environ["LMSTUDIO_BASE_URL"] = "http://localhost:1234/v1"
```

## SageMaker-Specific Considerations

### 1. Kernel Selection
- Use `conda_python3` kernel for best compatibility
- Or create custom kernel with all dependencies

### 2. Instance Type Recommendations
- **Development**: `ml.t3.medium` (2 vCPU, 4 GB RAM)
- **Workshop delivery**: `ml.t3.large` or `ml.t3.xlarge`
- **With local LLMs**: `ml.g4dn.xlarge` (GPU instance)

### 3. Lifecycle Configuration (Optional)

Create a lifecycle config to auto-install packages:
```bash
#!/bin/bash
set -e

# This script runs on notebook start
pip install langchain langgraph langchain-openai langchain-anthropic pydantic
```

### 4. Cost Optimization
- Stop instances when not in use
- Use Spot instances for development
- Consider SageMaker Studio for better cost management

## Testing Your Setup

Create a test notebook to verify everything works:
```python
# Cell 1: Test imports
try:
    from config.llm_factory import LLMFactory
    from modules.m1_baseline import check_claim
    print("✅ Imports successful!")
except Exception as e:
    print(f"❌ Import error: {e}")

# Cell 2: Test LLM
try:
    llm = LLMFactory.create_llm()
    response = llm.invoke("Say 'Hello SageMaker'")
    print(f"✅ LLM working: {response.content}")
except Exception as e:
    print(f"❌ LLM error: {e}")

# Cell 3: Test BS detector
try:
    from modules.m1_baseline import check_claim
    result = check_claim("The sky is green", llm)
    print(f"✅ BS Detector working: {result}")
except Exception as e:
    print(f"❌ BS Detector error: {e}")
```

## Troubleshooting

### Common Issues:

1. **Import errors**: Ensure all module files are uploaded and paths are correct
2. **API key errors**: Check environment variables are set
3. **Memory issues**: Upgrade to larger instance type
4. **Package conflicts**: Create fresh conda environment

### SageMaker Studio Alternative

Consider using SageMaker Studio for:
- Better environment management
- Persistent storage
- Easier collaboration
- Built-in Git integration

## Quick Start Script

Save this as `quick_setup.sh` and run in SageMaker terminal:
```bash
#!/bin/bash
# Quick setup script for SageMaker

# Install packages
pip install langchain langgraph langchain-openai langchain-anthropic pydantic python-dotenv

# Create directory structure
mkdir -p bs_detector/{config,modules,tools,data,notebooks}

# Set permissions
chmod -R 755 bs_detector/

echo "✅ Setup complete! Upload your files to the created directories."
```

## Next Steps

1. Upload notebooks in order (00-06)
2. Test each notebook individually
3. Consider creating a "Run All" notebook for the complete workshop
4. Add checkpoints to save progress between cells

Remember to stop your SageMaker instance when done to avoid charges!