# Using LM Studio with BS Detector

This guide explains how to use LM Studio as a local LLM provider for the BS Detector workshop, allowing you to run everything offline without needing API keys.

## What is LM Studio?

LM Studio is a desktop application that lets you run open-source LLMs locally on your machine. It provides an OpenAI-compatible API endpoint, making it easy to integrate with existing applications.

## Prerequisites

1. **Download LM Studio**: Get it from [https://lmstudio.ai/](https://lmstudio.ai/)
2. **System Requirements**: 
   - At least 8GB RAM (16GB+ recommended)
   - 10GB+ free disk space for models
   - macOS, Windows, or Linux

## Setup Instructions

### 1. Install and Configure LM Studio

1. Download and install LM Studio for your platform
2. Open LM Studio
3. Go to the "Models" tab and download a model (recommended models for BS Detector):
   - **Mistral 7B Instruct** - Good balance of performance and resource usage
   - **Llama 2 7B Chat** - Another solid option
   - **Phi-2** - Smaller model if you have limited resources

### 2. Start the Local Server

1. In LM Studio, go to the "Server" tab
2. Select your downloaded model
3. Click "Start Server" 
4. The server will run on `http://localhost:1234` by default

### 3. Configure BS Detector

#### Option A: Using Environment Variables

Add to your `.env` file:

```bash
# Use LM Studio as default provider
DEFAULT_LLM_PROVIDER=lmstudio

# Optional: Customize endpoint (default is http://localhost:1234/v1)
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Optional: Specify model name (uses loaded model by default)
LMSTUDIO_MODEL=mistral-7b-instruct
```

#### Option B: Programmatic Usage

```python
from config.llm_factory import LLMFactory

# Create LM Studio LLM instance
llm = LLMFactory.create_llm(provider="lmstudio")

# Or with custom settings
llm = LLMFactory.create_llm(
    provider="lmstudio",
    base_url="http://localhost:1234/v1",
    model="mistral-7b-instruct"
)
```

## Testing Your Setup

Run the test script to verify everything is working:

```bash
python test_lmstudio.py
```

You should see:
- ✅ Connection successful!
- Test results for various claims

## Using with Notebooks

In any notebook, you can use LM Studio by setting the provider:

```python
from config.llm_factory import LLMFactory

# Use LM Studio instead of OpenAI/Anthropic
llm = LLMFactory.create_llm(provider="lmstudio")

# Then use it normally
from modules.m1_baseline import check_claim
result = check_claim("The Boeing 747 has four engines", llm)
```

## Performance Tips

1. **Model Selection**:
   - Smaller models (3B-7B parameters) are faster but less accurate
   - Larger models (13B+) are more accurate but slower
   - For BS Detector, 7B models work well

2. **Quantization**:
   - Use quantized models (Q4, Q5) for better performance
   - They use less memory with minimal quality loss

3. **Context Length**:
   - BS Detector doesn't need long context
   - You can reduce context length in LM Studio settings for speed

## Troubleshooting

### "Connection refused" error
- Make sure LM Studio is running
- Check that the server is started
- Verify the endpoint URL matches your configuration

### Slow responses
- Try a smaller or more quantized model
- Close other applications to free up memory
- Consider using GPU acceleration if available

### Inconsistent results
- Local models may be less consistent than GPT-4/Claude
- Try different models to find one that works well
- Adjust temperature settings (lower = more consistent)

## Advantages of Using LM Studio

✅ **Privacy**: All data stays on your machine  
✅ **No API Costs**: Run unlimited queries for free  
✅ **Offline**: Works without internet connection  
✅ **Customizable**: Fine-tune models for your use case  

## Limitations

⚠️ **Quality**: May not match GPT-4/Claude performance  
⚠️ **Speed**: Depends on your hardware  
⚠️ **Features**: Some advanced features may not work as well  

## Example: Running the Full Workshop Offline

```python
# In any notebook or script
import os
os.environ["DEFAULT_LLM_PROVIDER"] = "lmstudio"

# Now all LLM calls will use LM Studio
from modules.m5_human_in_loop_v2 import check_claim_with_human_review_v2

result = check_claim_with_human_review_v2(
    "The International Space Station orbits Earth"
)
print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
```

That's it! You can now run the entire BS Detector workshop offline using LM Studio.