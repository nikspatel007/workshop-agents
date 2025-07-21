# Iteration 0: Environment & LLM Setup

## Overview
This iteration establishes the foundation for our BS detector system by setting up the development environment and creating the LLM factory pattern.

## Learning Objectives
- Understand the LLM factory pattern for provider abstraction
- Configure environment detection for different platforms
- Establish project structure following best practices
- Set up testing infrastructure with DeepEval

## Key Components
1. **LLM Factory**: Abstraction layer for multiple LLM providers
2. **Environment Detection**: Support for Jupyter, Colab, and SageMaker
3. **Project Structure**: Organized folder hierarchy
4. **Testing Framework**: Unit tests and verification

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