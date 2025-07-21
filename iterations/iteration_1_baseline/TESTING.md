# Iteration 1: Testing Guide

## Test Overview
This iteration tests the baseline BS detector's ability to classify aviation claims using a single LLM call.

## Running Tests

### 1. Unit Tests
```bash
# Run baseline tests
pytest tests/test_baseline.py -v

# Run with coverage
pytest tests/test_baseline.py --cov=modules.m1_baseline

# Run DeepEval tests
pytest tests/test_baseline_deepeval.py -v
```

### 2. Interactive Testing

#### Quick Test Script
```python
# test_quick.py
from modules.m1_baseline import check_claim
from config.llm_factory import LLMFactory

llm = LLMFactory.create_llm()

# Test claims
claims = [
    "The Concorde could fly at Mach 2",  # Legitimate
    "Boeing 747s have 6 engines",  # BS - they have 4
    "Pilots can eject from commercial aircraft",  # BS
    "Jet fuel is basically kerosene",  # Legitimate
]

for claim in claims:
    print(f"\nClaim: {claim}")
    result = check_claim(claim, llm)
    print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
    print(f"Reasoning: {result['reasoning']}")
```

### 3. Performance Testing

```python
# test_performance.py
import time
import statistics
from modules.m1_baseline import check_claim
from config.llm_factory import LLMFactory

llm = LLMFactory.create_llm()

# Test claims for performance
test_set = [
    "The A380 is the largest passenger aircraft",
    "Helicopters can fly upside down indefinitely",
    "Aircraft black boxes are actually orange",
    "Commercial jets can break the sound barrier",
    "Autopilot can handle all phases of flight",
]

times = []
for claim in test_set * 2:  # Run twice to account for warmup
    start = time.time()
    result = check_claim(claim, llm)
    elapsed = time.time() - start
    times.append(elapsed)
    
    if result["verdict"] == "ERROR":
        print(f"Error on claim: {claim}")
        print(f"Error: {result['error']}")

# Calculate statistics
print(f"\nPerformance Statistics:")
print(f"Average: {statistics.mean(times):.2f}s")
print(f"Median: {statistics.median(times):.2f}s")
print(f"Max: {max(times):.2f}s")
print(f"Min: {min(times):.2f}s")
print(f"Target: < 2.0s ✓" if max(times) < 2.0 else "Target: < 2.0s ✗")
```

## Validation Checklist

### Functionality Tests
- [ ] Correctly identifies obvious BS claims
- [ ] Correctly identifies legitimate claims
- [ ] Confidence scores are reasonable (not always 0 or 100)
- [ ] Reasoning is relevant to aviation
- [ ] Empty claims return error
- [ ] Very long claims are truncated
- [ ] Malformed LLM responses handled gracefully

### Edge Cases
- [ ] Claims with numbers: "The 747 has 4 engines"
- [ ] Technical jargon: "TCAS provides collision avoidance"
- [ ] Ambiguous claims: "Planes are getting bigger"
- [ ] Non-aviation claims: "Cars can fly"
- [ ] Mixed truth claims: "747s have 4 engines and can fly to Mars"

### Response Quality
- [ ] Verdict is always BS or LEGITIMATE (or ERROR)
- [ ] Confidence is integer 0-100
- [ ] Reasoning is concise (1-2 sentences)
- [ ] Aviation terminology used correctly
- [ ] No hallucination of facts

## Test Data Categories

### Legitimate Claims (Should return LEGITIMATE)
```python
legitimate_claims = [
    "The Boeing 747 has four turbofan engines",
    "Pilots undergo years of training",
    "Aircraft aluminum is lightweight but strong",
    "The Concorde was a supersonic passenger jet",
    "Air traffic control guides planes safely",
]
```

### BS Claims (Should return BS)
```python
bs_claims = [
    "Passenger planes can fly to the moon",
    "Pilots control chemtrails from the cockpit",
    "Jets can hover like helicopters",
    "Windows can be opened during flight",
    "Planes refuel by scooping ocean water",
]
```

### Tricky Claims (Test nuance)
```python
tricky_claims = [
    "All pilots must have perfect vision",  # BS - corrective lenses allowed
    "Autopilot can land planes",  # Legitimate - with autoland systems
    "Turbulence has never caused a crash",  # Debatable
    "Phones interfere with navigation",  # Mostly BS but historically based
]
```

## DeepEval Metrics

### Answer Relevancy Test
```python
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(threshold=0.8)

# Test that reasoning relates to the claim
test_case = LLMTestCase(
    input="Can helicopters fly upside down?",
    actual_output="BS: Helicopters cannot sustain inverted flight..."
)

score = metric.measure(test_case)
print(f"Relevancy score: {score}")
```

### Consistency Test
```python
# Run same claim multiple times
claim = "The SR-71 was the fastest jet"
results = []

for i in range(5):
    result = check_claim(claim, llm)
    results.append(result["verdict"])

# Check consistency
if len(set(results)) == 1:
    print("✓ Consistent verdicts")
else:
    print("✗ Inconsistent verdicts:", results)
```

## Common Issues and Solutions

### Issue: Timeout errors
**Solution**: Increase timeout in LLM factory
```python
llm = LLMFactory.create_llm(request_timeout=30)
```

### Issue: Parsing failures
**Solution**: Check LLM response format
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Issue: Low confidence scores
**Solution**: Adjust prompt to be more decisive
```python
# In prompt: "Be confident in your assessment"
```

### Issue: Inconsistent verdicts
**Solution**: Add examples to prompt
```python
# In prompt: "Example: 'Planes fly to moon' = BS"
```

## Success Metrics

### Accuracy Targets
- Obvious BS claims: 95%+ correct
- Obvious legitimate claims: 95%+ correct
- Tricky claims: 70%+ correct
- Overall accuracy: 85%+

### Performance Targets
- Average response time: < 1.5s
- Max response time: < 2.0s
- Error rate: < 5%
- Parse failure rate: < 2%

### Quality Targets
- Reasoning mentions specific aviation facts: 80%+
- Confidence correlates with correctness: 70%+
- Consistent verdicts for same claim: 90%+

## Next Steps
If all tests pass, you're ready for Iteration 2 where we'll wrap this in a proper agent structure!