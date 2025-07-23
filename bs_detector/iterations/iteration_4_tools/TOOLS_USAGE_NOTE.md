# Important Note: Tool Usage in Iteration 4

## The Challenge (SOLVED!)
The web search tool was rarely triggered with the default 70% confidence threshold because LLMs are typically 90-95% confident on most claims.

## Solution: Calibrated Confidence Scoring
We implemented a category-based confidence calibration mechanism that:
1. First categorizes the claim type
2. Assigns appropriate confidence based on category
3. Ensures tools are triggered when actually needed

## How It Works

### Claim Categories and Confidence Levels
- **BASIC_FACT** (95%): Universal truths like "planes have wings"
- **HISTORICAL** (85%): Past events like "Wright brothers 1903"  
- **TECHNICAL** (60%): Specific details that need verification
- **RECENT** (40%): Events from last 2 years - needs search
- **FUTURE** (35%): Predictions - very uncertain
- **OPINION** (70%): Subjective statements
- **UNCERTAIN** (30%): Rumors, "might be" - needs search

### Implementation
```python
# The system now uses calibrated confidence
from modules.m1_baseline_calibrated import check_claim_with_categories

# This automatically categorizes and assigns appropriate confidence
result = check_claim_with_tools("SpaceX launched 50 missions last month")
# Category: RECENT, Confidence: ~40% → Triggers search!
```

## Results
With the default 70% threshold:
- ✅ RECENT claims (40%) trigger search
- ✅ FUTURE claims (35%) trigger search  
- ✅ UNCERTAIN claims (30%) trigger search
- ✅ TECHNICAL claims (60%) trigger search
- ❌ BASIC_FACT (95%) and HISTORICAL (85%) don't trigger (as expected)

## Example Usage
```python
# These now trigger search automatically
claims = [
    "Tesla delivered 500,000 cars last quarter",      # RECENT → ~40%
    "The Boeing 797 will launch in 2025",            # FUTURE → ~35%
    "The F-35 costs $80 million per unit",           # TECHNICAL → ~60%
    "Some airlines might be testing AI pilots"        # UNCERTAIN → ~30%
]

for claim in claims:
    result = check_claim_with_tools(claim)
    # All will use web search with default 70% threshold!
```

## Key Benefits
1. **No manual threshold adjustment needed** - works with default 70%
2. **Appropriate tool usage** - searches when uncertainty is real
3. **Cost-effective** - doesn't search for obvious facts
4. **Production-ready** - based on claim characteristics

## Takeaway
By implementing proper confidence calibration, we solved the overconfidence problem and made tool usage automatic and intelligent. The system now correctly identifies when external verification is needed!