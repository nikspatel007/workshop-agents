# Iteration 0: Setup Tasks

## Project Structure
- [ ] Create main project directory `is_this_going_to_fly/`
- [ ] Create subdirectories: `config/`, `tools/`, `modules/`, `notebooks/`, `utils/`, `tests/`
- [ ] Create `__init__.py` files in all Python packages
- [ ] Create `requirements.txt` with dependencies
- [ ] Create `.env.example` file

## LLM Factory Implementation
- [ ] Create `config/llm_factory.py`
- [ ] Implement `LLMFactory` class with `create_llm()` method
- [ ] Add provider methods: `_create_openai()`, `_create_anthropic()`, `_create_bedrock()`, `_create_azure()`
- [ ] Add error handling for missing API keys
- [ ] Create unit test for factory pattern

## Environment Configuration
- [ ] Create `config/settings.py`
- [ ] Implement environment detection function
- [ ] Load environment variables with python-dotenv
- [ ] Add platform-specific configurations
- [ ] Create validation for required settings

## MCP Server Setup
- [ ] Install DuckDuckGo MCP server: `npm install -g @duckduckgo/mcp-server`
- [ ] Create `mcp_config.json` configuration file
- [ ] Test MCP server connection
- [ ] Create `tools/mcp_client.py` wrapper
- [ ] Verify search functionality

## Testing Infrastructure
- [ ] Install DeepEval: `pip install deepeval`
- [ ] Create `tests/` directory structure
- [ ] Write first test case for LLM factory
- [ ] Set up pytest configuration
- [ ] Create test data directory

## Documentation
- [ ] Create main `README.md`
- [ ] Document environment setup steps
- [ ] Add troubleshooting section
- [ ] Create API key setup guide
- [ ] Add platform-specific instructions