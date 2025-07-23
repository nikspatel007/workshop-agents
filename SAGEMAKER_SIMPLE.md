# BS Detector Workshop - SageMaker Setup

## Quick Start (5 minutes)

### 1. Upload Workshop
Upload the `bs_detector` folder to your SageMaker notebook instance

### 2. Run Setup
Open terminal in SageMaker:
```bash
cd bs_detector
python sagemaker_setup.py
```

### 3. Verify Setup
- Open `Verify_Setup.ipynb`
- Change kernel to **Workshop Kernel (BS Detector)**
- Run all cells

### 4. Start Workshop
- Open `notebooks/00_Setup.ipynb`
- Make sure kernel is **Workshop Kernel (BS Detector)**
- Begin!

## What the Setup Does

- Installs all required packages in a dedicated kernel
- Configures AWS Bedrock (Claude 3.5 Haiku)
- Sets up environment variables
- No API keys needed - uses SageMaker IAM role

## Troubleshooting

**"No module named langchain"**
- Make sure you're using **Workshop Kernel (BS Detector)**, not Python 3

**"Bedrock connection failed"**
- Check IAM role has `bedrock:InvokeModel` permission
- Verify Bedrock is available in your region

**"Kernel not found"**
- Re-run `python sagemaker_setup.py`
- Refresh browser and check Kernel menu

## For Instructors

The clean setup script creates a dedicated Jupyter kernel with:
- All packages pre-installed
- Environment variables configured
- No hacks or workarounds needed

Participants just need to:
1. Run setup script once
2. Select the workshop kernel
3. Start learning!