# Setup Cell for SageMaker Notebooks

Add this cell at the top of each notebook if you're having package issues:

```python
# Setup cell - run this first!
import os
import sys

# Set environment variables
os.environ['DEFAULT_LLM_PROVIDER'] = 'bedrock'
os.environ['BEDROCK_MODEL'] = 'anthropic.claude-3-haiku-20240307-v1:0'
os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

# Check if packages are installed, if not, install them
try:
    import langchain
    import langgraph
    print("✅ Packages already installed")
except ImportError:
    print("📦 Installing packages...")
    !pip install langchain langgraph langchain-aws langchain-community pydantic boto3 python-dotenv duckduckgo-search
    print("✅ Packages installed! Please restart kernel: Kernel → Restart")
    print("   Then run this cell again")
```

## Common Issues and Solutions:

### Issue 1: "No module named 'langchain'"
**Solution**: Run the setup cell above and restart kernel

### Issue 2: "No kernel"
**Solution**: 
1. Select Kernel → Change kernel → Python 3
2. Or conda_python3 if available

### Issue 3: Packages installed but still not found
**Solution**:
1. Check which Python the notebook is using:
   ```python
   import sys
   print(sys.executable)
   ```
2. Install packages with that specific Python:
   ```python
   !{sys.executable} -m pip install langchain langgraph langchain-aws
   ```

### Issue 4: Every notebook requires reinstalling
**Solution**: 
1. Use the same kernel for all notebooks (Python 3)
2. Install packages once in the terminal:
   ```bash
   pip install -r requirements.txt
   ```

## For Workshop Instructors:

Consider creating a custom SageMaker Lifecycle Configuration that pre-installs packages:

```bash
#!/bin/bash
set -e

# Lifecycle config script
sudo -u ec2-user -i <<'EOF'
source activate python3
pip install langchain langgraph langchain-aws langchain-community pydantic boto3 python-dotenv duckduckgo-search
EOF
```

This ensures packages are available in all notebooks from the start.