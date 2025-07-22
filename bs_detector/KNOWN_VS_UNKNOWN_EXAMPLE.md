# Known vs Unknown Data: A Concrete Example

## Scenario 1: Known Data (What we have in m3_evaluation.py)

```python
# From our dataset - WE KNOW THE ANSWER
known_claim = {
    "claim": "The Boeing 747 has four engines",
    "ground_truth": "LEGITIMATE"  # ← We know this is true!
}

# Detector processes it (without seeing the answer)
detector_result = {
    "verdict": "LEGITIMATE",
    "confidence": 95,
    "reasoning": "The Boeing 747 is a four-engine wide-body aircraft..."
}

# Evaluation is simple:
accuracy = (detector_result["verdict"] == known_claim["ground_truth"])  # True ✅
# We can definitively say: "The detector got this right!"
```

## Scenario 2: Unknown Data (Real-world usage)

```python
# Someone asks about a new claim - NO GROUND TRUTH
unknown_claim = "The new Boom Supersonic jet will be quieter than Concorde"

# Detector processes it
detector_result = {
    "verdict": "LEGITIMATE",
    "confidence": 75,
    "reasoning": "Boom Supersonic claims their aircraft uses modern engine technology and shaped sonic boom demonstration that should reduce noise..."
}

# Now what? We CAN'T calculate accuracy because we don't know the truth!
# accuracy = detector_result["verdict"] == ???  # No ground truth!
```

## What We CAN Measure on Unknown Data

### 1. Reasoning Quality Check
```python
def evaluate_reasoning(result):
    # Check: Does the reasoning support the verdict?
    reasoning = result['reasoning']
    verdict = result['verdict']
    
    # Use another LLM to judge
    quality_prompt = f"""
    Does this reasoning logically support the verdict?
    Verdict: {verdict}
    Reasoning: {reasoning}
    Score 0-1.
    """
    
    quality_score = llm_judge(quality_prompt)  # Let's say: 0.8
    return quality_score
```

### 2. Confidence Calibration Check
```python
def evaluate_confidence_appropriateness(result):
    # Check: Does confidence match the certainty in reasoning?
    
    uncertain_phrases = ["might be", "possibly", "claims", "should"]
    certain_phrases = ["definitely", "certainly", "proven", "confirmed"]
    
    uncertainty_count = sum(1 for phrase in uncertain_phrases if phrase in result['reasoning'])
    certainty_count = sum(1 for phrase in certain_phrases if phrase in result['reasoning'])
    
    # High confidence (75%) with uncertain language = problem
    if result['confidence'] > 70 and uncertainty_count > certainty_count:
        return 0.3  # Poor calibration
    else:
        return 0.9  # Good calibration
```

### 3. Consistency Check
```python
def evaluate_consistency(claim, result):
    # Find similar claims we've evaluated before
    similar_evaluated = [
        {"claim": "Concorde was louder than modern jets", "verdict": "LEGITIMATE"},
        {"claim": "Supersonic jets are always quieter", "verdict": "BS"}
    ]
    
    # Does our verdict align with patterns?
    # If we said "LEGITIMATE" for quieter supersonic jet, that's consistent
    return 0.85  # Reasonably consistent
```

## The Complete Picture

### Known Data Evaluation (Test Set)
```
Claim → Detector → Verdict → Compare with Truth → Accuracy ✅
                                    ↑
                            We have this!
```

### Unknown Data Evaluation (Production)
```
Claim → Detector → Verdict → ??? No Truth ???
                      ↓
                  Instead measure:
                  - Reasoning quality
                  - Confidence calibration  
                  - Consistency
                  - Anomaly detection
                      ↓
                  Trust Score (0-1)
                      ↓
                  If low → Human Review
```

## Real Example: How It Would Work

```python
class ProductionBSEvaluator:
    def evaluate_unknown_claim(self, claim):
        # 1. Run detector
        result = bs_detector(claim)
        
        # 2. Calculate quality metrics (no ground truth needed!)
        metrics = {
            'reasoning_quality': self.evaluate_reasoning(result),  # 0.8
            'confidence_calibration': self.evaluate_confidence(result),  # 0.9
            'consistency': self.evaluate_consistency(claim, result),  # 0.85
            'anomaly_score': self.check_if_unusual_claim(claim)  # 0.7
        }
        
        # 3. Overall trust score
        trust_score = sum(metrics.values()) / len(metrics)  # 0.81
        
        # 4. Decision
        if trust_score > 0.8:
            return {
                'verdict': result['verdict'],
                'confidence': result['confidence'],
                'trust_score': trust_score,
                'action': 'ACCEPT'
            }
        elif trust_score > 0.6:
            return {
                'verdict': result['verdict'],
                'confidence': result['confidence'] * 0.8,  # Reduce confidence
                'trust_score': trust_score,
                'action': 'ACCEPT_WITH_CAUTION'
            }
        else:
            return {
                'verdict': 'NEEDS_REVIEW',
                'trust_score': trust_score,
                'action': 'HUMAN_REVIEW_REQUIRED'
            }
```

## The Bottom Line

1. **m3_evaluation.py** works great for known data - it tells us our detector is ~75% accurate
2. For unknown data, we'd need a different approach - measuring quality signals instead of accuracy
3. We can never be 100% sure about unknown claims, but we can measure confidence in our answer
4. Low trust scores → human review (that's why Iteration 5 adds human-in-the-loop!)

Think of it like:
- **Known data**: Taking a practice test where you check answers against the answer key
- **Unknown data**: Taking the real test where you gauge confidence by how well you explained your reasoning