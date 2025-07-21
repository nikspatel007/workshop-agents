# Iteration 0: Environment & LLM Setup

## Overview
This iteration establishes the foundation for our BS detector system by setting up the development environment, creating the LLM factory pattern, and configuring MCP servers.

## Learning Objectives
- Understand the LLM factory pattern for provider abstraction
- Set up MCP (Model Context Protocol) for tool integration
- Configure environment detection for different platforms
- Establish project structure following best practices

## Key Components
1. **LLM Factory**: Abstraction layer for multiple LLM providers
2. **Environment Detection**: Support for Jupyter, Colab, and SageMaker
3. **MCP Configuration**: DuckDuckGo search server setup
4. **Project Structure**: Organized folder hierarchy

## Time Estimate
10 minutes

## Prerequisites
- Python 3.8+
- Node.js (for MCP server)
- API keys for at least one LLM provider

## Success Criteria
- LLM factory can create instances for different providers
- MCP server connects successfully
- Environment detection works correctly
- Basic project structure is in place