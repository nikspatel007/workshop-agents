"""
Tests for Human-in-the-Loop functionality (Iteration 5)
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from modules.m5_human_in_loop import (
    HumanReviewRequest,
    HumanFeedback,
    HumanInLoopState,
    calculate_uncertainty,
    uncertainty_detector_node,
    human_review_node,
    create_human_in_loop_bs_detector,
    check_claim_with_human_in_loop,
    interactive_human_input
)


class TestHumanReviewRequest:
    """Test HumanReviewRequest functionality"""
    
    def test_create_review_request(self):
        """Test creating a human review request"""
        request = HumanReviewRequest(
            claim="Test claim",
            ai_verdict="BS",
            ai_confidence=40,
            ai_reasoning="Low confidence detection",
            uncertainty_reasons=["Low confidence: 40%"]
        )
        
        assert request.claim == "Test claim"
        assert request.ai_verdict == "BS"
        assert request.ai_confidence == 40
        assert len(request.uncertainty_reasons) == 1
    
    def test_format_for_human(self):
        """Test formatting review request for human display"""
        request = HumanReviewRequest(
            claim="The moon is made of cheese",
            ai_verdict="BS",
            ai_confidence=30,
            uncertainty_reasons=["Very low confidence"],
            expert_opinions={
                "General Expert": {
                    "verdict": "BS",
                    "confidence": 30,
                    "reasoning": "Scientifically impossible"
                }
            }
        )
        
        formatted = request.format_for_human()
        
        assert "HUMAN REVIEW REQUESTED" in formatted
        assert "The moon is made of cheese" in formatted
        assert "Very low confidence" in formatted
        assert "General Expert" in formatted
        assert "Scientifically impossible" in formatted


class TestUncertaintyCalculation:
    """Test uncertainty calculation"""
    
    def test_high_confidence_low_uncertainty(self):
        """Test that high confidence results in low uncertainty"""
        state = HumanInLoopState(
            claim="Test",
            verdict="LEGITIMATE",
            confidence=95
        )
        
        uncertainty = calculate_uncertainty(state)
        assert uncertainty < 0.3
    
    def test_low_confidence_high_uncertainty(self):
        """Test that low confidence results in high uncertainty"""
        state = HumanInLoopState(
            claim="Test",
            verdict="BS",
            confidence=30
        )
        
        uncertainty = calculate_uncertainty(state)
        assert uncertainty >= 0.4
    
    def test_expert_disagreement_increases_uncertainty(self):
        """Test that expert disagreement increases uncertainty"""
        state = HumanInLoopState(
            claim="Test",
            verdict="BS",
            confidence=70,
            expert_opinions={
                "Expert1": {"verdict": "BS"},
                "Expert2": {"verdict": "LEGITIMATE"}
            }
        )
        
        uncertainty = calculate_uncertainty(state)
        assert uncertainty >= 0.3
    
    def test_current_event_without_search(self):
        """Test uncertainty for current events without search"""
        state = HumanInLoopState(
            claim="Test",
            claim_type="current_event",
            confidence=80,
            search_performed=False
        )
        
        uncertainty = calculate_uncertainty(state)
        assert uncertainty > 0


class TestUncertaintyDetectorNode:
    """Test uncertainty detector node"""
    
    def test_high_uncertainty_triggers_review(self):
        """Test that high uncertainty triggers human review"""
        state = HumanInLoopState(
            claim="Uncertain claim",
            verdict="BS",
            confidence=30
        )
        
        updates = uncertainty_detector_node(state)
        
        assert updates["needs_human_review"] == True
        assert updates["human_review_request"] is not None
        assert len(updates["review_reasons"]) > 0
    
    def test_low_uncertainty_no_review(self):
        """Test that low uncertainty doesn't trigger review"""
        state = HumanInLoopState(
            claim="Clear claim",
            verdict="LEGITIMATE",
            confidence=95
        )
        
        updates = uncertainty_detector_node(state)
        
        assert updates["needs_human_review"] == False
    
    def test_review_reasons_tracked(self):
        """Test that review reasons are properly tracked"""
        state = HumanInLoopState(
            claim="Test",
            verdict="BS",
            confidence=40,
            expert_disagreement=True
        )
        
        updates = uncertainty_detector_node(state)
        
        reasons = updates["review_reasons"]
        assert any("low confidence" in r.lower() for r in reasons)


class TestHumanReviewNode:
    """Test human review node"""
    
    @patch('time.sleep')
    def test_simulated_human_feedback(self, mock_sleep):
        """Test simulated human feedback"""
        state = HumanInLoopState(
            claim="Test claim",
            human_review_request=HumanReviewRequest(
                claim="Test claim",
                ai_verdict="BS",
                ai_confidence=40
            )
        )
        
        updates = human_review_node(state)
        
        assert updates["human_feedback"] is not None
        assert updates["verdict"] == "UNCERTAIN"
        assert updates["confidence"] == 60
        assert "Human review" in updates["reasoning"]
    
    def test_custom_human_handler(self):
        """Test custom human input handler"""
        def mock_handler(request):
            return HumanFeedback(
                verdict="LEGITIMATE",
                confidence=85,
                reasoning="Human verified as true"
            )
        
        state = HumanInLoopState(
            claim="Test claim",
            human_review_request=HumanReviewRequest(
                claim="Test claim",
                ai_verdict="BS",
                ai_confidence=40
            )
        )
        state._human_input_handler = mock_handler
        
        updates = human_review_node(state)
        
        assert updates["verdict"] == "LEGITIMATE"
        assert updates["confidence"] == 85


class TestGraphIntegration:
    """Test full graph integration"""
    
    def test_create_graph(self):
        """Test graph creation"""
        app = create_human_in_loop_bs_detector()
        
        assert app is not None
        
        # Check nodes exist
        graph = app.get_graph()
        nodes = graph.nodes
        
        expected_nodes = [
            "router",
            "technical_expert",
            "historical_expert",
            "current_events_expert",
            "general_expert",
            "uncertainty_detector",
            "human_review",
            "format_output"
        ]
        
        for node in expected_nodes:
            assert node in nodes
    
    @patch('modules.m5_human_in_loop.LLMFactory.create_llm')
    def test_high_confidence_claim_no_review(self, mock_llm):
        """Test that high confidence claims don't trigger review"""
        # Mock LLM responses
        mock_llm_instance = Mock()
        
        # Router response
        router_response = Mock()
        router_response.content = "CLAIM_TYPE: technical\nCONFIDENCE_LEVEL: high"
        
        # Expert response
        expert_response = Mock()
        expert_response.content = "VERDICT: LEGITIMATE\nCONFIDENCE: 95\nREASONING: Clear technical fact"
        
        mock_llm_instance.invoke.side_effect = [router_response, expert_response]
        mock_llm.return_value = mock_llm_instance
        
        result = check_claim_with_human_in_loop("The Boeing 747 has four engines")
        
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] == 95
        assert result["human_reviewed"] == False
    
    @patch('modules.m5_human_in_loop.LLMFactory.create_llm')
    @patch('time.sleep')
    def test_low_confidence_triggers_review(self, mock_sleep, mock_llm):
        """Test that low confidence triggers human review"""
        # Mock LLM responses
        mock_llm_instance = Mock()
        
        # Router response
        router_response = Mock()
        router_response.content = "CLAIM_TYPE: general\nCONFIDENCE_LEVEL: low"
        
        # Expert response with low confidence
        expert_response = Mock()
        expert_response.content = "VERDICT: BS\nCONFIDENCE: 30\nREASONING: Very uncertain"
        
        mock_llm_instance.invoke.side_effect = [router_response, expert_response]
        mock_llm.return_value = mock_llm_instance
        
        result = check_claim_with_human_in_loop("Some uncertain claim")
        
        assert result["human_reviewed"] == True
        assert result["uncertainty_score"] > 0.4
        assert result.get("human_feedback") is not None


class TestHumanFeedback:
    """Test human feedback model"""
    
    def test_valid_feedback(self):
        """Test creating valid human feedback"""
        feedback = HumanFeedback(
            verdict="BS",
            confidence=90,
            reasoning="Clearly false based on evidence",
            additional_context="Checked multiple sources",
            sources=["source1", "source2"]
        )
        
        assert feedback.verdict == "BS"
        assert feedback.confidence == 90
        assert feedback.reasoning == "Clearly false based on evidence"
        assert len(feedback.sources) == 2
    
    def test_feedback_validation(self):
        """Test feedback validation"""
        # Test invalid confidence
        with pytest.raises(ValueError):
            HumanFeedback(
                verdict="BS",
                confidence=150,  # Invalid
                reasoning="Test"
            )
        
        # Test invalid verdict
        with pytest.raises(ValueError):
            HumanFeedback(
                verdict="MAYBE",  # Invalid
                confidence=50,
                reasoning="Test"
            )


class TestMetrics:
    """Test metrics tracking"""
    
    def test_uncertainty_score_calculation(self):
        """Test that uncertainty scores are properly calculated"""
        test_cases = [
            # (confidence, expected_min_uncertainty)
            (95, 0.0),
            (70, 0.0),
            (50, 0.2),
            (40, 0.4),
            (20, 0.4),
        ]
        
        for confidence, expected_min in test_cases:
            state = HumanInLoopState(
                claim="Test",
                confidence=confidence,
                verdict="BS"
            )
            uncertainty = calculate_uncertainty(state)
            assert uncertainty >= expected_min
    
    def test_review_trigger_tracking(self):
        """Test that review triggers are properly identified"""
        state = HumanInLoopState(
            claim="Test",
            verdict="BS",
            confidence=30,
            expert_disagreement=True,
            claim_type="current_event",
            search_performed=False
        )
        
        updates = uncertainty_detector_node(state)
        reasons = updates["review_reasons"]
        
        # Should have multiple reasons
        assert len(reasons) >= 2
        assert any("low confidence" in r.lower() for r in reasons)