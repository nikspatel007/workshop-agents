# BS Detector - "Is This Going to Fly?"

An AI-powered BS detector with an aviation theme that uses multi-agent architecture to verify claims through evidence-based fact-checking.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Search Capabilities (No API Key Required!)
The BS Detector includes a simple search tool with aviation knowledge base:
- Works in ALL environments (local, Colab, SageMaker)
- No external dependencies or API keys
- Returns consistent aviation facts for workshop
- Can be extended with real search later (Playwright, MCP, etc.)

No additional setup required!

### 4. Run Tests
```bash
pytest tests/
```

## Project Structure
```
bs_detector/
├── config/          # LLM factory and settings
├── tools/           # MCP client and tool wrappers
├── modules/         # Agent implementations
├── notebooks/       # Interactive demos
├── tests/          # Test suite
└── utils/          # Helper functions
```

## Supported LLM Providers
- OpenAI (GPT-4)
- Anthropic (Claude)
- AWS Bedrock
- Azure OpenAI
- LM Studio (Local LLMs) - **NEW!**

### Using LM Studio (Run Offline!)
Want to run the workshop completely offline? Use LM Studio:

1. Download [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Mistral 7B)
3. Start the server in LM Studio
4. Set in `.env`: `DEFAULT_LLM_PROVIDER=lmstudio`

See [docs/using_lmstudio.md](docs/using_lmstudio.md) for detailed instructions.

## Environment Detection
Automatically detects and configures for:
- Local development
- Jupyter notebooks
- Google Colab
- AWS SageMaker

## Workshop Progress
- [x] Iteration 0: Environment & LLM Setup
- [ ] Iteration 1: Simple BS Detector
- [ ] Iteration 2: Structured Agent
- [ ] Iteration 3: Multi-Claim Extraction
- [ ] Iteration 4: Evidence-Based Checking
- [ ] Iteration 5: Human-in-the-Loop
- [ ] Iteration 6: Full Orchestration