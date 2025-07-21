# Iteration 1: Simple BS Detector

## Overview
This iteration implements a basic BS detector using a single LLM call. We'll establish a baseline for claim verification with simple prompt engineering and response parsing.

## Learning Objectives
- Master prompt engineering for claim verification
- Implement response parsing techniques
- Establish performance baselines
- Understand LLM limitations for fact-checking

## Key Components
1. **check_claim()**: Core function for BS detection
2. **Prompt Template**: Aviation-focused claim analysis
3. **Response Parser**: Extract verdict, confidence, and reasoning
4. **Error Handling**: Graceful degradation

## Time Estimate
15 minutes

## Prerequisites
- Completed Iteration 0
- LLM factory working
- Basic Python regex knowledge

## Success Criteria
- Function correctly identifies obvious BS claims
- Confidence scores are reasonable (0-100)
- Response time < 2 seconds per claim
- Structured output format maintained