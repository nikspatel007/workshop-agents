# Iteration 0 → Iteration 1 Handoff

## What's Ready for You

### LLM Access
```python
from config.llm_factory import LLMFactory

# Create LLM instance (provider from environment)
llm = LLMFactory.create_llm()

# Use it for inference
response = llm.invoke("Your prompt here")
print(response.content)
```

### Project Structure
```
is_this_going_to_fly/
├── config/          # ✅ LLM factory and settings
├── tools/           # ✅ MCP client ready
├── modules/         # 📁 Ready for your baseline module
├── notebooks/       # 📁 Ready for your notebook
└── tests/          # ✅ Testing infrastructure
```

### Environment Variables
Ensure `.env` file has at least one provider configured:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

## What You'll Build in Iteration 1

### Simple BS Detector Function
Create `modules/m1_baseline.py` with:
- `check_claim(claim: str, llm) -> Dict[str, Any]` function
- Basic prompt template for aviation claims
- Response parsing logic

### Expected Interface
```python
# What iteration 2 will expect from you
from modules.m1_baseline import check_claim

result = check_claim(
    "The Boeing 747 can fly backwards",
    llm
)
# Returns: {
#     "verdict": "BS",
#     "confidence": 95,
#     "reasoning": "Aircraft cannot fly backwards..."
# }
```

## Dependencies You Can Use

### Available Imports
```python
# LLM
from config.llm_factory import LLMFactory

# Settings
from config.settings import get_settings, detect_environment

# Standard libraries
import re  # For response parsing
import json  # For structured data
from typing import Dict, Any  # For type hints
```

### Testing Tools
```python
# For your tests
import pytest
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric
```

## Key Design Constraints

### Keep It Simple
- Single LLM call only
- No agents or complex chains yet
- Basic string parsing is fine
- Focus on prompt engineering

### Performance Target
- < 2 seconds per claim
- Single claim at a time
- No batch processing yet

### Error Handling
- Handle LLM timeouts
- Parse unexpected responses gracefully
- Return structured errors

## Testing Your Implementation

### Unit Test Template
```python
# tests/test_baseline.py
def test_check_claim_bs():
    llm = LLMFactory.create_llm()
    result = check_claim(
        "Commercial planes can fly to the moon",
        llm
    )
    assert result["verdict"] == "BS"
    assert result["confidence"] > 80
```

### Manual Testing
```python
# In notebook or script
test_claims = [
    "The Boeing 747 has four engines",  # Legitimate
    "Pilots can open windows during flight"  # BS
]

for claim in test_claims:
    result = check_claim(claim, llm)
    print(f"{claim[:30]}... -> {result['verdict']}")
```

## Tips for Success

### Prompt Engineering
- Be specific about aviation context
- Ask for structured output
- Include confidence scoring
- Request brief reasoning

### Response Parsing
- Use regex for simple extraction
- Have fallback values
- Validate confidence is 0-100
- Ensure verdict is BS/LEGITIMATE

### Common Pitfalls to Avoid
- Don't over-engineer parsing
- Don't add multiple LLM calls
- Don't implement caching yet
- Don't worry about edge cases

## Questions This Iteration Answers
1. How well can a simple prompt detect BS claims?
2. What's the baseline performance?
3. What are the failure modes?
4. How consistent are the responses?

## Your Deliverables
1. `modules/m1_baseline.py` - Core implementation
2. `notebooks/01_Baseline.ipynb` - Interactive demo
3. `tests/test_baseline.py` - Unit tests
4. Performance metrics documented

Remember: This is just the baseline. Keep it simple and focused!