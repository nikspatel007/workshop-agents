# Code Walkthrough: How m3_evaluation.py Actually Works

## The Evaluation Flow

Let me trace through exactly what happens when you run an evaluation:

### Step 1: Load the Known Dataset

```python
class BSDetectorEvaluator:
    def __init__(self, dataset_path):
        self.claims = self._load_dataset()  # Loads 30 claims with ground truth
        
    def _load_dataset(self):
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        
        # Each claim has:
        # - claim: "The Boeing 747 has four engines"
        # - verdict: "LEGITIMATE"  <-- THE ANSWER KEY
        # - difficulty: "easy"
        # - expected_confidence: 95
```

### Step 2: Run Evaluation

```python
def evaluate_detector(self, detector_func, iteration_name):
    results = []
    
    for claim in self.claims:
        # 1. Run the detector (it doesn't know the answer!)
        result = detector_func(claim.claim)
        # Returns: {"verdict": "LEGITIMATE", "confidence": 90, "reasoning": "..."}
        
        # 2. Compare with ground truth
        is_correct = (result['verdict'] == claim.verdict)
        
        # 3. Store detailed results
        results.append({
            'claim': claim.claim,
            'expected': claim.verdict,      # Ground truth
            'predicted': result['verdict'],  # What detector said
            'correct': is_correct,
            'confidence': result['confidence'],
            'reasoning': result['reasoning']
        })
```

### Step 3: Calculate Metrics

```python
# After testing all claims:
accuracy = sum(r['correct'] for r in results) / len(results)

# Break down by difficulty
easy_claims = [r for r in results if r['difficulty'] == 'easy']
easy_accuracy = sum(r['correct'] for r in easy_claims) / len(easy_claims)

# Confidence analysis
correct_results = [r for r in results if r['correct']]
avg_confidence_when_correct = sum(r['confidence'] for r in correct_results) / len(correct_results)
```

## The DeepEval Integration

### Custom Metric Example: Confidence Calibration

```python
class ConfidenceCalibration(BaseMetric):
    def measure(self, test_case):
        confidence = test_case.metadata['confidence']
        is_correct = test_case.actual_output == test_case.expected_output
        
        # Scoring logic:
        if is_correct and confidence >= 70:
            return 1.0  # Good: confident and correct
        elif not is_correct and confidence < 50:
            return 1.0  # Good: uncertain and wrong
        else:
            # Bad: confident but wrong OR uncertain but correct
            return 0.5
```

### Reasoning Quality (The Clever Part)

```python
class ReasoningQuality(BaseMetric):
    def measure(self, test_case):
        # This is where it gets interesting!
        # We use an LLM to judge another LLM's reasoning
        
        prompt = f"""
        Evaluate this BS detection reasoning:
        
        Claim: {test_case.input}
        Verdict: {test_case.actual_output}
        Reasoning: {test_case.metadata['reasoning']}
        
        Score 0-1 based on:
        - Logical consistency
        - Use of aviation knowledge
        - Evidence quality
        
        Return only a number.
        """
        
        score = float(self.llm.invoke(prompt).content)
        return score
```

## What About Unknown Data?

Here's what the current system **doesn't** do (but could):

```python
# Current system (only works with known answers):
def evaluate_known_claim(claim, ground_truth):
    result = detector(claim)
    accuracy = (result['verdict'] == ground_truth)
    return accuracy

# What we'd need for unknown claims:
def evaluate_unknown_claim(claim):
    result = detector(claim)
    
    # We can't measure accuracy, but we can measure:
    quality_scores = {
        'reasoning_coherence': check_reasoning_makes_sense(result['reasoning']),
        'confidence_appropriateness': check_confidence_matches_certainty(result),
        'factual_consistency': check_facts_are_correct(result['reasoning']),
        'pattern_consistency': compare_with_similar_claims(claim, result)
    }
    
    # Red flags that might indicate problems:
    red_flags = []
    if result['confidence'] > 95:
        red_flags.append("Suspiciously high confidence")
    if "not sure" in result['reasoning'] and result['confidence'] > 70:
        red_flags.append("Confidence doesn't match uncertainty in reasoning")
    
    return {
        'quality_scores': quality_scores,
        'red_flags': red_flags,
        'trust_level': sum(quality_scores.values()) / len(quality_scores)
    }
```

## The Reality Check

The current `m3_evaluation.py` is like a teacher grading a test with an answer key:
1. ✅ It knows the right answers (ground truth)
2. ✅ It can measure accuracy directly
3. ❌ It can't evaluate claims without known answers

For production use with unknown claims, you'd need:
1. **Behavioral metrics** (consistency, calibration)
2. **Quality metrics** (reasoning coherence, factual accuracy)
3. **Anomaly detection** (is this claim very different from training data?)
4. **Human review triggers** (when confidence is low or stakes are high)

## The Key Insight

**Known data evaluation** tells you:
- "This detector is 80% accurate on aviation claims we know the answer to"

**Unknown data evaluation** would tell you:
- "This detector seems to be reasoning coherently and is appropriately confident"
- "But we should flag this specific claim for human review because it's unusual"

The art is in building good proxy metrics that correlate with actual accuracy!