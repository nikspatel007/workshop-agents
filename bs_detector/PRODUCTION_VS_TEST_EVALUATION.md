# Production vs Test Evaluation: The Complete Picture

## The Two Types of Evaluation

### 1. Test Set Evaluation (What we had in m3_evaluation.py)
```python
# We KNOW the answer
claim = "The Boeing 747 has four engines"
ground_truth = "LEGITIMATE"

# Run detector
result = detector(claim)  # Returns: {"verdict": "LEGITIMATE", ...}

# Simple comparison
accuracy = (result["verdict"] == ground_truth)  # True ✅
```

**Pros:**
- Exact accuracy measurement
- Easy to understand
- Good for development

**Cons:**
- Only works with labeled data
- Doesn't work in production
- Limited to specific domains

### 2. Production Evaluation (What we built in m3_production_evaluation.py)
```python
# We DON'T KNOW the answer
claim = "The new XYZ technology will revolutionize computing"
ground_truth = ???  # We don't know!

# Run detector
result = detector(claim)

# Evaluate quality instead of accuracy
metrics = ProductionEvaluator().evaluate(claim, result)
trust_score = metrics.trust_score  # 0.73
needs_review = metrics.requires_human_review  # True if uncertain
```

**Pros:**
- Works on ANY claim
- No ground truth needed
- Identifies uncertain cases
- Detects drift and anomalies

**Cons:**
- Can't measure exact accuracy
- More complex metrics
- Requires careful interpretation

## How Production Evaluation Works

### 1. LLM-as-Judge
Another LLM evaluates the quality of reasoning:
```python
prompt = """
Does this reasoning support the verdict?
Claim: {claim}
Verdict: {verdict}
Reasoning: {reasoning}
Score 0-1.
"""
quality_score = llm_judge(prompt)
```

### 2. Confidence Calibration
Checks if confidence matches the language:
```python
# High confidence (90%) but uncertain language = BAD
reasoning = "This might possibly be true, perhaps"
confidence = 90
calibration_score = 0.3  # Poor calibration

# High confidence (90%) with certain language = GOOD  
reasoning = "This is definitely true because..."
confidence = 90
calibration_score = 0.9  # Good calibration
```

### 3. Consistency Checking
Similar claims should get similar verdicts:
```python
history = [
    {"claim": "Planes can fly backwards", "verdict": "BS"},
    {"claim": "Jets can fly in reverse", "verdict": "BS"}
]

new_claim = "Aircraft can fly backwards"
new_verdict = "LEGITIMATE"  # Inconsistent!
consistency_score = 0.2  # Low score
```

### 4. Drift Detection
Identifies out-of-domain or unusual claims:
```python
# Aviation detector gets medical claim
claim = "This drug cures cancer"
domain = "medical"  # Not aviation!
anomaly_score = 0.8  # High - out of domain

# Normal aviation claim
claim = "The 747 has four engines"  
domain = "aviation"
anomaly_score = 0.1  # Low - normal claim
```

## When to Use Each

### Use Test Set Evaluation When:
- Developing and improving your agent
- Comparing different versions
- Setting performance baselines
- You have labeled data

### Use Production Evaluation When:
- Running in the real world
- No ground truth available
- Need to identify uncertain cases
- Monitoring for drift

## Real-World Example

```python
# In Development
test_evaluator = BSDetectorEvaluator()
accuracy = test_evaluator.evaluate(detector, test_set)
print(f"Test accuracy: {accuracy:.1%}")  # 85%

# In Production
prod_evaluator = ProductionEvaluator()

for claim in real_world_claims:
    result = detector(claim)
    metrics = prod_evaluator.evaluate(claim, result)
    
    if metrics.requires_human_review:
        send_to_human_queue(claim, result, metrics)
    else:
        accept_result(result)
```

## The Key Insight

**Test evaluation** answers: "How accurate is my detector?"
**Production evaluation** answers: "Can I trust this specific result?"

You need BOTH:
1. Test evaluation to build a good detector
2. Production evaluation to use it safely in the real world

## Metrics Comparison

| Metric | Test Evaluation | Production Evaluation |
|--------|----------------|---------------------|
| Accuracy | ✅ Exact percentage | ❌ Not available |
| Reasoning Quality | ✅ Via DeepEval | ✅ Via LLM Judge |
| Confidence Calibration | ✅ Compare with truth | ✅ Compare with language |
| Consistency | ❌ Not needed | ✅ Critical |
| Drift Detection | ❌ Not applicable | ✅ Essential |
| Human Review Trigger | ❌ Not needed | ✅ Built-in |

## Best Practices

1. **Start with test evaluation** to build a good baseline
2. **Add production evaluation** before deploying
3. **Monitor both** in production:
   - Production metrics for individual decisions
   - Periodic test evaluation on new labeled data
4. **Use human review** for low-trust cases
5. **Track drift** to know when to retrain

The production evaluator is what makes AI agents safe and reliable in the real world!