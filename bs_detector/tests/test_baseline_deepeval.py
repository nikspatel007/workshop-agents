"""
DeepEval tests for baseline BS detector.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import deepeval
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import AnswerRelevancyMetric, GEval
    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False


@pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="DeepEval not installed")
@pytest.mark.skip(reason="DeepEval tests are optional - focus on core functionality")
class TestBaselineDeepEval:
    """DeepEval tests for baseline BS detector - OPTIONAL"""
    
    def test_bs_detection_relevancy(self):
        """Test that BS detection provides relevant analysis"""
        from modules.m1_baseline import check_claim
        from config.llm_factory import LLMFactory
        
        try:
            llm = LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
        
        claim = "The A380 can fly backwards using reverse thrust"
        result = check_claim(claim, llm)
        
        # Create test case
        test_case = LLMTestCase(
            input=claim,
            actual_output=f"{result['verdict']}: {result['reasoning']}"
        )
        
        # Test relevancy
        relevancy_metric = AnswerRelevancyMetric(threshold=0.8)
        score = relevancy_metric.measure(test_case)
        assert score >= 0.8, f"Relevancy score {score} is below threshold"
    
    def test_aviation_accuracy(self):
        """Test aviation fact accuracy using custom metric"""
        from modules.m1_baseline import check_claim
        from config.llm_factory import LLMFactory
        
        try:
            llm = LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
        
        # Define custom metric
        aviation_accuracy = GEval(
            name="Aviation Fact Accuracy",
            criteria="The verdict correctly identifies false aviation claims and provides accurate technical reasoning",
            evaluation_params=["input", "output"],
            threshold=0.7
        )
        
        # Test cases with known correct answers
        test_cases = [
            {
                "claim": "Jet engines work by burning fuel in space",
                "expected_verdict": "BS",
                "expected_reasoning": "need oxygen"
            },
            {
                "claim": "The Boeing 787 uses composite materials",
                "expected_verdict": "LEGITIMATE",
                "expected_reasoning": "composite"
            }
        ]
        
        for test in test_cases:
            result = check_claim(test["claim"], llm)
            
            # Create test case
            test_case = LLMTestCase(
                input=test["claim"],
                actual_output=f"{result['verdict']}: {result['reasoning']}"
            )
            
            # Measure accuracy
            score = aviation_accuracy.measure(test_case)
            assert score >= 0.7, f"Aviation accuracy {score} below threshold for: {test['claim']}"
            
            # Also check verdict matches expectation
            assert result['verdict'] == test['expected_verdict'], \
                f"Expected {test['expected_verdict']}, got {result['verdict']}"
    
    def test_confidence_calibration(self):
        """Test that confidence scores are well-calibrated"""
        from modules.m1_baseline import check_claim
        from config.llm_factory import LLMFactory
        
        try:
            llm = LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
        
        # Test obvious cases that should have high confidence
        high_confidence_claims = [
            ("The moon is made of cheese", "BS"),
            ("Water boils at 100°C at sea level", "LEGITIMATE")
        ]
        
        for claim, expected_verdict in high_confidence_claims:
            result = check_claim(claim, llm)
            
            # For obvious cases, confidence should be high
            if result['verdict'] == expected_verdict:
                assert result['confidence'] >= 80, \
                    f"Confidence {result['confidence']}% too low for obvious claim: {claim}"
    
    def test_reasoning_quality(self):
        """Test quality of reasoning using custom metric"""
        from modules.m1_baseline import check_claim
        from config.llm_factory import LLMFactory
        
        try:
            llm = LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
        
        # Define reasoning quality metric
        reasoning_quality = GEval(
            name="Reasoning Quality",
            criteria="""The reasoning should:
            1. Be specific to aviation when relevant
            2. Cite technical facts or principles
            3. Be concise but informative
            4. Directly address why the claim is BS or LEGITIMATE""",
            evaluation_params=["input", "output"],
            threshold=0.75
        )
        
        claim = "Helicopters can hover because they create lift differently than airplanes"
        result = check_claim(claim, llm)
        
        test_case = LLMTestCase(
            input=claim,
            actual_output=result['reasoning']
        )
        
        score = reasoning_quality.measure(test_case)
        assert score >= 0.75, f"Reasoning quality {score} below threshold"