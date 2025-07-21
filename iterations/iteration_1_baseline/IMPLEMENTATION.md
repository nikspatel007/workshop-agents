# Iteration 1: Implementation Details

## 1. Core Implementation

```python
# modules/m1_baseline.py
"""
Simple BS detector using single LLM call.
This module provides baseline claim verification functionality.
"""

import re
import logging
from typing import Dict, Any, Optional
from config.llm_factory import LLMFactory

# Set up logging
logger = logging.getLogger(__name__)

# Prompt template for BS detection
BS_DETECTION_PROMPT = """You are an aviation expert and fact-checker. Your job is to determine if claims about aviation are BS (false/ridiculous) or LEGITIMATE (true/reasonable).

Analyze the following claim about aviation:
"{claim}"

Provide your analysis in this exact format:
VERDICT: [BS or LEGITIMATE]
CONFIDENCE: [0-100]%
REASONING: [Brief explanation in 1-2 sentences]

Remember:
- BS means the claim is false, impossible, or ridiculous
- LEGITIMATE means the claim is true, possible, or reasonable
- Be specific about aviation facts in your reasoning
"""

def check_claim(claim: str, llm: Any) -> Dict[str, Any]:
    """
    Check if an aviation claim is BS or legitimate.
    
    Args:
        claim: The aviation claim to verify
        llm: Language model instance from LLMFactory
        
    Returns:
        Dictionary with keys:
        - verdict: "BS" or "LEGITIMATE"
        - confidence: int between 0-100
        - reasoning: str explanation
        - error: Optional error message
    """
    try:
        # Validate input
        if not claim or not claim.strip():
            return {
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": "Empty claim provided",
                "error": "Invalid input"
            }
        
        # Truncate very long claims
        if len(claim) > 500:
            claim = claim[:500] + "..."
        
        # Format prompt
        prompt = BS_DETECTION_PROMPT.format(claim=claim)
        
        # Get LLM response
        logger.debug(f"Checking claim: {claim[:50]}...")
        response = llm.invoke(prompt)
        
        # Parse response
        parsed = parse_response(response.content)
        
        # Validate parsed response
        if parsed["verdict"] not in ["BS", "LEGITIMATE"]:
            logger.warning(f"Invalid verdict: {parsed['verdict']}")
            parsed["verdict"] = "ERROR"
            parsed["error"] = "Failed to determine verdict"
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error checking claim: {str(e)}")
        return {
            "verdict": "ERROR",
            "confidence": 0,
            "reasoning": "Failed to analyze claim",
            "error": str(e)
        }

def parse_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract verdict, confidence, and reasoning.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Parsed dictionary with verdict, confidence, and reasoning
    """
    result = {
        "verdict": "ERROR",
        "confidence": 0,
        "reasoning": "Failed to parse response",
        "error": None
    }
    
    try:
        # Extract verdict
        verdict_match = re.search(
            r'VERDICT:\s*\[?\s*(BS|LEGITIMATE)\s*\]?',
            response_text,
            re.IGNORECASE
        )
        if verdict_match:
            result["verdict"] = verdict_match.group(1).upper()
        
        # Extract confidence
        confidence_match = re.search(
            r'CONFIDENCE:\s*\[?\s*(\d+)\s*\]?%?',
            response_text,
            re.IGNORECASE
        )
        if confidence_match:
            confidence = int(confidence_match.group(1))
            # Ensure confidence is in valid range
            result["confidence"] = max(0, min(100, confidence))
        
        # Extract reasoning
        reasoning_match = re.search(
            r'REASONING:\s*\[?\s*(.+?)(?:\]|$)',
            response_text,
            re.IGNORECASE | re.DOTALL
        )
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
            # Clean up reasoning
            reasoning = re.sub(r'\s+', ' ', reasoning)
            result["reasoning"] = reasoning[:200]  # Limit length
        
        # Clear error if parsing succeeded
        if result["verdict"] in ["BS", "LEGITIMATE"]:
            result["error"] = None
            
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        result["error"] = f"Parse error: {str(e)}"
    
    return result

def check_claim_batch(claims: list[str], llm: Any) -> list[Dict[str, Any]]:
    """
    Check multiple claims (for testing purposes).
    
    Args:
        claims: List of claims to check
        llm: Language model instance
        
    Returns:
        List of results for each claim
    """
    results = []
    for claim in claims:
        result = check_claim(claim, llm)
        result["claim"] = claim  # Include original claim
        results.append(result)
    return results
```

## 2. Test Implementation

```python
# tests/test_baseline.py
import pytest
from modules.m1_baseline import check_claim, parse_response
from config.llm_factory import LLMFactory

class TestBaseline:
    """Test cases for baseline BS detector"""
    
    @pytest.fixture
    def llm(self):
        """Create LLM instance for testing"""
        return LLMFactory.create_llm()
    
    def test_obvious_bs_claim(self, llm):
        """Test detection of obvious BS claim"""
        result = check_claim(
            "Commercial airplanes can fly to the moon",
            llm
        )
        assert result["verdict"] == "BS"
        assert result["confidence"] > 80
        assert "moon" in result["reasoning"].lower()
    
    def test_legitimate_claim(self, llm):
        """Test detection of legitimate claim"""
        result = check_claim(
            "The Boeing 747 has four jet engines",
            llm
        )
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] > 70
        assert len(result["reasoning"]) > 10
    
    def test_empty_claim(self, llm):
        """Test handling of empty claim"""
        result = check_claim("", llm)
        assert result["verdict"] == "ERROR"
        assert result["error"] == "Invalid input"
    
    def test_parse_response_valid(self):
        """Test parsing of well-formatted response"""
        response = """
        VERDICT: [BS]
        CONFIDENCE: [95]%
        REASONING: [Planes cannot reach escape velocity needed for moon travel]
        """
        parsed = parse_response(response)
        assert parsed["verdict"] == "BS"
        assert parsed["confidence"] == 95
        assert "escape velocity" in parsed["reasoning"]
    
    def test_parse_response_malformed(self):
        """Test parsing of malformed response"""
        response = "This claim seems wrong to me."
        parsed = parse_response(response)
        assert parsed["verdict"] == "ERROR"
        assert parsed["confidence"] == 0
```

## 3. Notebook Implementation

```python
# notebooks/01_Baseline.ipynb

# Cell 1: Setup
import sys
sys.path.append('..')

from modules.m1_baseline import check_claim, check_claim_batch
from config.llm_factory import LLMFactory
import pandas as pd
import matplotlib.pyplot as plt

# Create LLM instance
llm = LLMFactory.create_llm()
print(f"Using LLM provider: {llm.__class__.__name__}")

# Cell 2: Test Individual Claims
test_claims = {
    "legitimate": [
        "The Boeing 747 has four engines",
        "Pilots must have a commercial license to fly passengers",
        "Aircraft use altimeters to measure altitude"
    ],
    "bs": [
        "Commercial planes can fly to the moon",
        "Airlines spray chemtrails for weather control",
        "Pilots can open windows during flight"
    ]
}

# Check each claim
for category, claims in test_claims.items():
    print(f"\n{category.upper()} CLAIMS:")
    for claim in claims:
        result = check_claim(claim, llm)
        print(f"\nClaim: {claim}")
        print(f"Verdict: {result['verdict']} ({result['confidence']}% confident)")
        print(f"Reasoning: {result['reasoning']}")

# Cell 3: Performance Analysis
import time

# Measure response times
times = []
results = []

for category, claims in test_claims.items():
    for claim in claims:
        start = time.time()
        result = check_claim(claim, llm)
        elapsed = time.time() - start
        
        times.append(elapsed)
        results.append({
            'claim': claim[:50] + '...' if len(claim) > 50 else claim,
            'category': category,
            'verdict': result['verdict'],
            'confidence': result['confidence'],
            'time': elapsed
        })

# Create DataFrame
df = pd.DataFrame(results)

# Cell 4: Visualizations
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Response time distribution
ax1.hist(times, bins=10, edgecolor='black')
ax1.set_xlabel('Response Time (seconds)')
ax1.set_ylabel('Count')
ax1.set_title('Response Time Distribution')
ax1.axvline(x=2.0, color='r', linestyle='--', label='Target: 2s')
ax1.legend()

# Confidence by verdict
df_valid = df[df['verdict'].isin(['BS', 'LEGITIMATE'])]
df_valid.boxplot(column='confidence', by='verdict', ax=ax2)
ax2.set_xlabel('Verdict')
ax2.set_ylabel('Confidence %')
ax2.set_title('Confidence Distribution by Verdict')

plt.tight_layout()
plt.show()

# Print summary statistics
print(f"\nAverage response time: {np.mean(times):.2f}s")
print(f"Max response time: {max(times):.2f}s")
print(f"Success rate: {(df['verdict'] != 'ERROR').mean():.1%}")
```

## 4. Advanced Testing with DeepEval

```python
# tests/test_baseline_deepeval.py
import deepeval
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, GEval

def test_bs_detection_relevancy():
    """Test that BS detection provides relevant analysis"""
    from modules.m1_baseline import check_claim
    from config.llm_factory import LLMFactory
    
    llm = LLMFactory.create_llm()
    claim = "The A380 can fly backwards using reverse thrust"
    
    result = check_claim(claim, llm)
    
    # Create test case
    test_case = LLMTestCase(
        input=claim,
        actual_output=f"{result['verdict']}: {result['reasoning']}"
    )
    
    # Test relevancy
    relevancy_metric = AnswerRelevancyMetric(threshold=0.8)
    assert relevancy_metric.measure(test_case)
    
def test_aviation_accuracy():
    """Test aviation fact accuracy using custom metric"""
    aviation_accuracy = GEval(
        name="Aviation Fact Accuracy",
        criteria="The verdict correctly identifies false aviation claims and provides accurate technical reasoning",
        evaluation_params=["input", "output"]
    )
    
    test_cases = [
        LLMTestCase(
            input="Jet engines work by burning fuel in space",
            actual_output="BS: Jet engines need oxygen from air to burn fuel, which doesn't exist in space"
        ),
        LLMTestCase(
            input="The Boeing 787 uses composite materials",
            actual_output="LEGITIMATE: The 787 extensively uses carbon fiber composites"
        )
    ]
    
    for test_case in test_cases:
        score = aviation_accuracy.measure(test_case)
        assert score > 0.7, f"Aviation accuracy too low: {score}"
```

## 5. Performance Optimization

```python
# Optional: Caching for development/testing
from functools import lru_cache

@lru_cache(maxsize=100)
def check_claim_cached(claim: str, llm_type: str) -> Dict[str, Any]:
    """Cached version for development - DO NOT use in production"""
    llm = LLMFactory.create_llm()
    return check_claim(claim, llm)
```