# Iteration 1: Baseline Tasks

## Core Implementation
- [ ] Create `modules/m1_baseline.py`
- [ ] Implement `check_claim()` function
- [ ] Add comprehensive docstring
- [ ] Include type hints for all parameters
- [ ] Return structured dictionary response

## Prompt Engineering
- [ ] Design aviation-focused prompt template
- [ ] Include clear instructions for verdict format
- [ ] Request confidence percentage
- [ ] Ask for brief reasoning
- [ ] Test with various claim types

## Response Parsing
- [ ] Implement `parse_response()` helper function
- [ ] Extract verdict (BS/LEGITIMATE)
- [ ] Parse confidence percentage (0-100)
- [ ] Extract reasoning text
- [ ] Handle malformed responses

## Error Handling
- [ ] Catch LLM timeout errors
- [ ] Handle empty responses
- [ ] Provide default values for parse failures
- [ ] Log errors appropriately
- [ ] Return error in structured format

## Testing
- [ ] Create `tests/test_baseline.py`
- [ ] Test obvious BS claims
- [ ] Test legitimate claims
- [ ] Test edge cases (empty, very long)
- [ ] Test error conditions
- [ ] Measure response times

## Notebook Demo
- [ ] Create `notebooks/01_Baseline.ipynb`
- [ ] Import and setup section
- [ ] Demo with example claims
- [ ] Visualize results
- [ ] Performance analysis
- [ ] Failure mode exploration

## Documentation
- [ ] Document prompt template rationale
- [ ] Explain parsing approach
- [ ] List known limitations
- [ ] Provide usage examples
- [ ] Include troubleshooting guide

## Performance Testing
- [ ] Measure average response time
- [ ] Test with 10 different claims
- [ ] Document consistency of results
- [ ] Identify failure patterns
- [ ] Create performance baseline

## DeepEval Integration
- [ ] Create test case for BS detection
- [ ] Implement answer relevancy check
- [ ] Test confidence calibration
- [ ] Document evaluation results
- [ ] Create baseline metrics