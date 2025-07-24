"""
Tests for production evaluation system (unknown data)
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from modules.m4_production_evaluation import (
    ProductionEvaluator,
    ProductionMetrics,
    LLMJudge,
    ConsistencyChecker,
    DriftDetector,
    EvaluationCase
)


class TestLLMJudge:
    """Test LLM-as-judge functionality"""
    
    @patch('modules.m4_production_evaluation.LLMFactory.create_llm')
    def test_evaluate_reasoning_quality(self, mock_llm):
        """Test reasoning quality evaluation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "0.8"
        mock_llm.return_value.invoke.return_value = mock_response
        
        judge = LLMJudge()
        score = judge.evaluate_reasoning_quality(
            claim="The Boeing 747 has four engines",
            verdict="LEGITIMATE",
            reasoning="The Boeing 747 is a four-engine wide-body aircraft"
        )
        
        assert score == 0.8
        assert 0 <= score <= 1
    
    @patch('modules.m4_production_evaluation.LLMFactory.create_llm')
    def test_evaluate_claim_plausibility(self, mock_llm):
        """Test claim plausibility evaluation"""
        mock_response = Mock()
        mock_response.content = "0.9"
        mock_llm.return_value.invoke.return_value = mock_response
        
        judge = LLMJudge()
        score = judge.evaluate_claim_plausibility(
            claim="The moon is made of cheese",
            verdict="BS"
        )
        
        assert score == 0.9
    
    @patch('modules.m4_production_evaluation.LLMFactory.create_llm')
    def test_llm_judge_error_handling(self, mock_llm):
        """Test error handling returns default score"""
        mock_llm.return_value.invoke.side_effect = Exception("LLM error")
        
        judge = LLMJudge()
        score = judge.evaluate_reasoning_quality("claim", "verdict", "reasoning")
        
        assert score == 0.5  # Default middle score


class TestConsistencyChecker:
    """Test consistency checking across evaluations"""
    
    def test_empty_history(self):
        """Test consistency with no history"""
        checker = ConsistencyChecker()
        score = checker.check_consistency("New claim", {"verdict": "BS"})
        
        assert score == 0.5  # Default when no history
    
    def test_consistent_verdicts(self):
        """Test consistency with similar claims"""
        checker = ConsistencyChecker()
        
        # Add similar aviation claims
        checker.add_evaluation(
            "The Boeing 747 has four engines",
            {"verdict": "LEGITIMATE", "confidence": 95}
        )
        checker.add_evaluation(
            "The Boeing 777 has two engines", 
            {"verdict": "LEGITIMATE", "confidence": 90}
        )
        
        # Check consistency for similar claim
        score = checker.check_consistency(
            "The Boeing 787 has two engines",
            {"verdict": "LEGITIMATE", "confidence": 92}
        )
        
        assert score > 0.5  # Should be consistent
    
    def test_inconsistent_verdicts(self):
        """Test inconsistency detection"""
        checker = ConsistencyChecker()
        
        # Add claims about aircraft
        checker.add_evaluation(
            "Commercial planes can fly backwards",
            {"verdict": "BS", "confidence": 95}
        )
        
        # Opposite verdict for similar claim
        score = checker.check_consistency(
            "Passenger planes can fly backwards",
            {"verdict": "LEGITIMATE", "confidence": 90}
        )
        
        assert score <= 0.5  # Should be inconsistent


class TestDriftDetector:
    """Test domain and drift detection"""
    
    def test_domain_detection(self):
        """Test detecting claim domains"""
        detector = DriftDetector()
        
        # Test various domains
        test_cases = [
            ("The Boeing 747 has four engines", "aviation"),
            ("Python code can be optimized using AI", "technology"),
            ("The patient needs immediate treatment", "medical"),
            ("Stock market crashed today", "finance"),
            ("The sky is blue", "general")
        ]
        
        for claim, expected_domain in test_cases:
            domain, confidence = detector.detect_domain(claim)
            assert domain in detector.known_domains
            if expected_domain != "general":
                assert domain == expected_domain
    
    def test_anomaly_detection(self):
        """Test anomaly score calculation"""
        detector = DriftDetector()
        
        # Normal aviation claim
        normal_score = detector.calculate_anomaly_score(
            "The Boeing 747 has four engines",
            "aviation"
        )
        assert normal_score < 0.7  # Adjusted threshold
        
        # Very short claim
        short_score = detector.calculate_anomaly_score(
            "BS",
            "general"
        )
        assert short_score >= 0.7
        
        # Out of domain claim
        ood_score = detector.calculate_anomaly_score(
            "Quantum flux capacitor enables time travel",
            "general"
        )
        assert ood_score >= 0.5


class TestProductionEvaluator:
    """Test main production evaluator"""
    
    @patch('modules.m4_production_evaluation.LLMFactory.create_llm')
    def test_evaluate_without_ground_truth(self, mock_llm):
        """Test evaluation without ground truth"""
        # Mock LLM responses
        mock_response = Mock()
        mock_response.content = "0.75"
        mock_llm.return_value.invoke.return_value = mock_response
        
        evaluator = ProductionEvaluator()
        
        # Test claim and result
        claim = "The Boeing 747 has four engines"
        detector_result = {
            "verdict": "LEGITIMATE",
            "confidence": 85,
            "reasoning": "The Boeing 747 is definitely a four-engine aircraft"
        }
        
        metrics = evaluator.evaluate(claim, detector_result)
        
        # Check metrics object
        assert isinstance(metrics, ProductionMetrics)
        assert 0 <= metrics.trust_score <= 1
        assert 0 <= metrics.reasoning_quality <= 1
        assert 0 <= metrics.anomaly_score <= 1
        assert isinstance(metrics.requires_human_review, bool)
    
    def test_confidence_calibration(self):
        """Test confidence calibration evaluation"""
        evaluator = ProductionEvaluator()
        
        # High confidence with certain language
        good_calibration = evaluator._evaluate_confidence_calibration(
            confidence=90,
            reasoning="This is definitely and certainly true",
            verdict="LEGITIMATE"
        )
        assert good_calibration > 0.7
        
        # High confidence with uncertain language
        bad_calibration = evaluator._evaluate_confidence_calibration(
            confidence=95,
            reasoning="This might possibly be true, perhaps",
            verdict="LEGITIMATE"
        )
        assert bad_calibration < 0.5
    
    def test_token_efficiency(self):
        """Test token efficiency calculation"""
        evaluator = ProductionEvaluator()
        
        # Good ratio
        good_efficiency = evaluator._calculate_token_efficiency(
            claim="Is this true?",
            reasoning="Based on analysis, this appears to be true because of X, Y, and Z factors."
        )
        assert good_efficiency > 0.7
        
        # Too brief
        brief_efficiency = evaluator._calculate_token_efficiency(
            claim="Is this a complex scientific claim that needs analysis?",
            reasoning="Yes."
        )
        assert brief_efficiency <= 0.5
        
        # Too verbose
        verbose_efficiency = evaluator._calculate_token_efficiency(
            claim="True?",
            reasoning=" ".join(["word"] * 100)  # 100 words for 1 word claim
        )
        assert verbose_efficiency <= 0.5
    
    @patch('modules.m4_production_evaluation.LLMFactory.create_llm')
    def test_human_review_triggers(self, mock_llm):
        """Test conditions that trigger human review"""
        mock_response = Mock()
        mock_response.content = "0.8"
        mock_llm.return_value.invoke.return_value = mock_response
        
        evaluator = ProductionEvaluator()
        
        # Low confidence should trigger review
        low_conf_result = {
            "verdict": "LEGITIMATE",
            "confidence": 30,  # Very low
            "reasoning": "Not sure about this"
        }
        metrics = evaluator.evaluate("Some claim", low_conf_result)
        assert metrics.requires_human_review
        
        # High anomaly should trigger review
        anomalous_claim = "XYZ123 quantum flux capacitor reverse polarity"
        normal_result = {
            "verdict": "BS",
            "confidence": 75,
            "reasoning": "This seems unlikely"
        }
        metrics = evaluator.evaluate(anomalous_claim, normal_result)
        # Anomaly score should be high for weird claim
        assert metrics.anomaly_score >= 0.5
    
    def test_evaluation_summary(self):
        """Test getting evaluation summary"""
        evaluator = ProductionEvaluator()
        
        # Add some evaluations
        from datetime import datetime
        for i in range(5):
            evaluator.evaluation_history.append({
                'timestamp': datetime.now(),
                'claim': f"Test claim {i}",
                'domain': 'test',
                'result': {"verdict": "BS"},
                'metrics': {
                    'trust_score': 0.7 + i * 0.05,
                    'anomaly_score': 0.3,
                    'response_time': 1.0,
                    'requires_human_review': i < 2
                }
            })
        
        summary = evaluator.get_evaluation_summary()
        
        assert summary['total_evaluations'] == 5
        assert 'avg_trust_score' in summary
        assert summary['human_review_rate'] == 0.4  # 2/5
        assert summary['domain_distribution']['test'] == 5
    
    def test_export_for_human_review(self):
        """Test exporting cases for human review"""
        evaluator = ProductionEvaluator()
        
        # Add evaluations with different review requirements
        from datetime import datetime
        evaluator.evaluation_history = [
            {
                'timestamp': datetime.now(),
                'claim': "Needs review",
                'result': {"verdict": "BS"},
                'metrics': {'requires_human_review': True}
            },
            {
                'timestamp': datetime.now(),
                'claim': "No review needed",
                'result': {"verdict": "LEGITIMATE"},
                'metrics': {'requires_human_review': False}
            }
        ]
        
        review_cases = evaluator.export_for_human_review()
        
        assert len(review_cases) == 1
        assert review_cases[0]['claim'] == "Needs review"


class TestProductionMetrics:
    """Test ProductionMetrics model"""
    
    def test_metrics_validation(self):
        """Test metrics validation"""
        # Valid metrics
        metrics = ProductionMetrics(
            reasoning_quality=0.8,
            confidence_calibration=0.7,
            consistency_score=0.9,
            claim_plausibility=0.85,
            logical_coherence=0.8,
            evidence_quality=0.75,
            domain_confidence=0.9,
            anomaly_score=0.2,
            response_time=1.5,
            token_efficiency=0.8,
            trust_score=0.82,
            requires_human_review=False
        )
        
        assert metrics.trust_score == 0.82
        
        # Test bounds
        with pytest.raises(ValueError):
            ProductionMetrics(
                reasoning_quality=1.5,  # > 1
                confidence_calibration=0.7,
                consistency_score=0.9,
                claim_plausibility=0.85,
                logical_coherence=0.8,
                evidence_quality=0.75,
                domain_confidence=0.9,
                anomaly_score=0.2,
                response_time=1.5,
                token_efficiency=0.8,
                trust_score=0.82,
                requires_human_review=False
            )