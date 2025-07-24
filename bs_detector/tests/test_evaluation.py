"""
Tests for the evaluation framework (Iteration 3)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from modules.m4_evaluation import (
    AviationClaim,
    EvaluationResult,
    BSDetectionAccuracy,
    ConfidenceCalibration,
    ReasoningQuality,
    BSDetectorEvaluator,
    evaluate_baseline,
    evaluate_langgraph,
    compare_all_iterations
)
from deepeval.test_case import LLMTestCase


class TestDataModels:
    """Test data models for evaluation"""
    
    def test_aviation_claim_creation(self):
        """Test creating an aviation claim"""
        claim = AviationClaim(
            id="test_001",
            claim="Test claim",
            verdict="LEGITIMATE",
            difficulty="easy",
            category="test",
            explanation="Test explanation",
            needs_evidence=False,
            expected_confidence=90
        )
        
        assert claim.id == "test_001"
        assert claim.verdict == "LEGITIMATE"
        assert claim.difficulty == "easy"
    
    def test_evaluation_result_creation(self):
        """Test creating evaluation result"""
        result = EvaluationResult(
            iteration="Test",
            total_claims=10,
            correct=8,
            accuracy=0.8,
            easy_accuracy=0.9,
            medium_accuracy=0.8,
            hard_accuracy=0.6,
            category_accuracy={"test": 0.8},
            avg_confidence=75.0,
            avg_confidence_when_correct=85.0,
            avg_confidence_when_wrong=45.0,
            avg_response_time=1.5
        )
        
        assert result.accuracy == 0.8
        assert result.easy_accuracy == 0.9
        assert result.avg_confidence == 75.0


class TestCustomMetrics:
    """Test custom DeepEval metrics"""
    
    def test_bs_detection_accuracy_metric(self):
        """Test BS detection accuracy metric"""
        metric = BSDetectionAccuracy()
        
        # Test correct prediction
        test_case = LLMTestCase(
            input="Test claim",
            actual_output="LEGITIMATE",
            expected_output="LEGITIMATE"
        )
        score = metric.measure(test_case)
        
        assert score == 1.0
        assert metric.is_successful()
        assert "matches ground truth" in metric.reason
        
        # Test incorrect prediction
        test_case_wrong = LLMTestCase(
            input="Test claim",
            actual_output="BS",
            expected_output="LEGITIMATE"
        )
        score_wrong = metric.measure(test_case_wrong)
        
        assert score_wrong == 0.0
        assert not metric.is_successful()
    
    def test_confidence_calibration_metric(self):
        """Test confidence calibration metric"""
        metric = ConfidenceCalibration()
        
        # Test high confidence when correct
        test_case = LLMTestCase(
            input="Test claim",
            actual_output="LEGITIMATE",
            expected_output="LEGITIMATE"
        )
        test_case.metadata = {"confidence": 85}
        score = metric.measure(test_case)
        
        assert score == 1.0
        assert metric.is_successful()
        
        # Test low confidence when wrong (good calibration)
        test_case_calibrated = LLMTestCase(
            input="Test claim",
            actual_output="BS",
            expected_output="LEGITIMATE"
        )
        test_case_calibrated.metadata = {"confidence": 30}
        score_calibrated = metric.measure(test_case_calibrated)
        
        assert score_calibrated == 1.0
        assert metric.is_successful()
        
        # Test high confidence when wrong (bad calibration)
        test_case_bad = LLMTestCase(
            input="Test claim",
            actual_output="BS",
            expected_output="LEGITIMATE"
        )
        test_case_bad.metadata = {"confidence": 90}
        score_bad = metric.measure(test_case_bad)
        
        assert score_bad < 0.5
        assert not metric.is_successful()
    
    @patch('modules.m4_evaluation.LLMFactory.create_llm')
    def test_reasoning_quality_metric(self, mock_llm):
        """Test reasoning quality metric"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "0.8"
        mock_llm.return_value.invoke.return_value = mock_response
        
        metric = ReasoningQuality()
        
        test_case = LLMTestCase(
            input="The Boeing 747 has four engines",
            actual_output="LEGITIMATE",
            expected_output="LEGITIMATE"
        )
        test_case.metadata = {"reasoning": "Boeing 747 is a four-engine wide-body aircraft"}
        
        score = metric.measure(test_case)
        
        assert score == 0.8
        assert metric.is_successful()
        
        # Verify LLM was called with proper prompt
        mock_llm.return_value.invoke.assert_called_once()
        call_args = mock_llm.return_value.invoke.call_args[0][0]
        assert "Boeing 747" in call_args
        assert "LEGITIMATE" in call_args


class TestBSDetectorEvaluator:
    """Test the main evaluator class"""
    
    @pytest.fixture
    def evaluator(self, tmp_path):
        """Create evaluator with test dataset"""
        # Create test dataset
        test_data = {
            "metadata": {
                "version": "1.0",
                "categories": ["test"]
            },
            "claims": [
                {
                    "id": "test_001",
                    "claim": "Test claim 1",
                    "verdict": "LEGITIMATE",
                    "difficulty": "easy",
                    "category": "test",
                    "explanation": "Test",
                    "needs_evidence": False,
                    "expected_confidence": 90
                },
                {
                    "id": "test_002",
                    "claim": "Test claim 2",
                    "verdict": "BS",
                    "difficulty": "medium",
                    "category": "test",
                    "explanation": "Test",
                    "needs_evidence": True,
                    "expected_confidence": 70
                }
            ]
        }
        
        # Write test dataset
        dataset_path = tmp_path / "test_dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(test_data, f)
        
        return BSDetectorEvaluator(str(dataset_path))
    
    def test_load_dataset(self, evaluator):
        """Test loading dataset"""
        assert len(evaluator.claims) == 2
        assert evaluator.claims[0].id == "test_001"
        assert evaluator.claims[1].verdict == "BS"
    
    @patch('modules.m4_evaluation.LLMFactory.create_llm')
    def test_evaluate_detector(self, mock_llm, evaluator):
        """Test evaluating a detector"""
        # Mock detector function
        def mock_detector(claim, llm=None):
            if "claim 1" in claim:
                return {
                    "verdict": "LEGITIMATE",
                    "confidence": 85,
                    "reasoning": "Test reasoning"
                }
            else:
                return {
                    "verdict": "LEGITIMATE",  # Wrong!
                    "confidence": 60,
                    "reasoning": "Test reasoning 2"
                }
        
        # Run evaluation
        result = evaluator.evaluate_detector(
            mock_detector,
            "Test Detector"
        )
        
        assert result.iteration == "Test Detector"
        assert result.total_claims == 2
        assert result.correct == 1
        assert result.accuracy == 0.5
        assert result.avg_confidence == 72.5
    
    def test_evaluate_subset(self, evaluator):
        """Test evaluating on subset"""
        # Mock detector that always returns LEGITIMATE
        def mock_detector(claim, llm=None):
            return {"verdict": "LEGITIMATE", "confidence": 80}
        
        # Evaluate only easy claims
        result = evaluator.evaluate_detector(
            mock_detector,
            "Test Easy",
            subset="easy"
        )
        
        assert result.total_claims == 1  # Only 1 easy claim
        assert result.correct == 1
        assert result.accuracy == 1.0
    
    @patch('modules.m4_evaluation.LLMFactory.create_llm')
    def test_run_deepeval_tests(self, mock_llm, evaluator, capsys):
        """Test running DeepEval tests"""
        # Mock detector
        def mock_detector(claim, llm=None):
            return {
                "verdict": "LEGITIMATE",
                "confidence": 85,
                "reasoning": "Good reasoning"
            }
        
        # Mock LLM for reasoning quality
        mock_response = Mock()
        mock_response.content = "0.8"
        mock_llm.return_value.invoke.return_value = mock_response
        
        # Run tests
        evaluator.run_deepeval_tests(mock_detector, "Test")
        
        # Check output
        captured = capsys.readouterr()
        assert "Running DeepEval tests" in captured.out
        assert "BS Detection Accuracy" in captured.out
        assert "Confidence Calibration" in captured.out
        assert "Reasoning Quality" in captured.out
    
    def test_compare_iterations(self, evaluator, capsys):
        """Test comparing iterations"""
        # Add some results
        evaluator.results["Iteration 1"] = EvaluationResult(
            iteration="Iteration 1",
            total_claims=10,
            correct=7,
            accuracy=0.7,
            easy_accuracy=0.9,
            medium_accuracy=0.7,
            hard_accuracy=0.5,
            category_accuracy={"test": 0.7},
            avg_confidence=75.0,
            avg_confidence_when_correct=85.0,
            avg_confidence_when_wrong=50.0,
            avg_response_time=1.0
        )
        
        evaluator.results["Iteration 2"] = EvaluationResult(
            iteration="Iteration 2",
            total_claims=10,
            correct=8,
            accuracy=0.8,
            easy_accuracy=0.95,
            medium_accuracy=0.8,
            hard_accuracy=0.6,
            category_accuracy={"test": 0.8},
            avg_confidence=78.0,
            avg_confidence_when_correct=88.0,
            avg_confidence_when_wrong=45.0,
            avg_response_time=1.2
        )
        
        # Compare
        evaluator.compare_iterations()
        
        # Check output
        captured = capsys.readouterr()
        assert "Iteration Comparison" in captured.out
        assert "70.0%" in captured.out  # Iteration 1 accuracy
        assert "80.0%" in captured.out  # Iteration 2 accuracy
        assert "Improvement: 10.0%" in captured.out


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('modules.m4_evaluation.BSDetectorEvaluator')
    def test_evaluate_baseline(self, mock_evaluator_class):
        """Test evaluate_baseline function"""
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        
        # Call function
        evaluate_baseline()
        
        # Verify evaluator was created and used
        mock_evaluator_class.assert_called_once()
        mock_evaluator.evaluate_detector.assert_called_once()
        
        # Check correct function was passed
        call_args = mock_evaluator.evaluate_detector.call_args
        assert "Baseline" in call_args[0][1]
    
    @patch('modules.m4_evaluation.BSDetectorEvaluator')
    def test_evaluate_langgraph(self, mock_evaluator_class):
        """Test evaluate_langgraph function"""
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        
        # Call function
        evaluate_langgraph()
        
        # Verify evaluator was created and used
        mock_evaluator_class.assert_called_once()
        mock_evaluator.evaluate_detector.assert_called_once()
        
        # Check correct function was passed
        call_args = mock_evaluator.evaluate_detector.call_args
        assert "LangGraph" in call_args[0][1]
    
    @patch('modules.m4_evaluation.BSDetectorEvaluator')
    def test_compare_all_iterations(self, mock_evaluator_class):
        """Test compare_all_iterations function"""
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        
        # Call function
        compare_all_iterations()
        
        # Verify correct sequence of calls
        assert mock_evaluator.evaluate_detector.call_count == 2
        mock_evaluator.compare_iterations.assert_called_once()
        mock_evaluator.run_deepeval_tests.assert_called_once()


class TestErrorHandling:
    """Test error handling in evaluation"""
    
    def test_detector_error_handling(self, tmp_path):
        """Test handling detector errors"""
        # Create minimal dataset
        test_data = {
            "metadata": {"categories": ["test"]},
            "claims": [{
                "id": "test_001",
                "claim": "Test",
                "verdict": "LEGITIMATE",
                "difficulty": "easy",
                "category": "test",
                "explanation": "Test",
                "needs_evidence": False,
                "expected_confidence": 90
            }]
        }
        
        dataset_path = tmp_path / "test_dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(test_data, f)
        
        evaluator = BSDetectorEvaluator(str(dataset_path))
        
        # Detector that raises error
        def error_detector(claim, llm=None):
            raise Exception("Detector failed!")
        
        # Should handle error gracefully
        result = evaluator.evaluate_detector(error_detector, "Error Test")
        
        assert result.total_claims == 1
        assert result.correct == 0
        assert result.accuracy == 0.0
        assert result.claim_results[0]['predicted'] == 'ERROR'