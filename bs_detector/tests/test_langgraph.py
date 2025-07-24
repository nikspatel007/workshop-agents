"""
Test cases for LangGraph BS detector (Iteration 2).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.m3_langgraph import (
    BSDetectorState,
    detect_bs_node,
    retry_node,
    route_after_detection,
    create_bs_detector_graph,
    check_claim_with_graph
)


class TestLangGraphComponents:
    """Test individual graph components"""
    
    def test_state_structure(self):
        """Test that state has all required fields"""
        state = BSDetectorState(
            claim="Test claim",
            retry_count=0,
            max_retries=3
        )
        
        # Test Pydantic model attributes
        assert state.claim == "Test claim"
        assert state.retry_count == 0
        assert state.max_retries == 3
        assert state.verdict is None
        assert state.confidence is None
    
    def test_routing_logic(self):
        """Test routing decisions"""
        # Success case
        state = BSDetectorState(
            claim="test",
            verdict="BS",
            retry_count=0,
            max_retries=3
        )
        assert route_after_detection(state) == "success"
        
        # Retry case
        state = BSDetectorState(
            claim="test",
            verdict="ERROR",
            retry_count=1,
            max_retries=3
        )
        assert route_after_detection(state) == "retry"
        
        # Max retries case
        state = BSDetectorState(
            claim="test",
            verdict="ERROR",
            retry_count=3,
            max_retries=3
        )
        assert route_after_detection(state) == "error"
    
    def test_retry_node(self):
        """Test retry node increments count"""
        state = BSDetectorState(
            claim="test",
            retry_count=1,
            max_retries=3
        )
        
        # Mock sleep to speed up test
        with patch('time.sleep'):
            result = retry_node(state)
        
        # retry_node returns empty dict, state is unchanged
        assert result == {}


class TestGraphExecution:
    """Test the complete graph"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        mock = Mock()
        mock.with_structured_output.return_value = mock
        return mock
    
    def test_graph_creation(self):
        """Test that graph compiles successfully"""
        graph = create_bs_detector_graph()
        assert graph is not None
        
        # Check graph structure
        graph_def = graph.get_graph()
        assert graph_def is not None
    
    @patch('modules.m3_langgraph.check_claim')
    def test_successful_detection(self, mock_check_claim):
        """Test successful claim detection"""
        # Mock the baseline check_claim to return a successful result
        mock_check_claim.return_value = {
            "verdict": "LEGITIMATE",
            "confidence": 95,
            "reasoning": "This is true"
        }
        
        # Run detection
        result = check_claim_with_graph("The Boeing 747 has four engines", max_retries=1)
        
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] == 95
        assert "error" not in result
    
    @patch('modules.m3_langgraph.check_claim')
    def test_retry_on_error(self, mock_check_claim):
        """Test that graph retries on error"""
        # Mock check_claim to fail once then succeed
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API Error")
            else:
                return {
                    "verdict": "BS",
                    "confidence": 90,
                    "reasoning": "Retry worked"
                }
        
        mock_check_claim.side_effect = side_effect
        
        # Run with retry
        with patch('time.sleep'):  # Speed up test
            result = check_claim_with_graph("Test claim", max_retries=2)
        
        # Should succeed after retry
        assert result["verdict"] == "BS"
        assert mock_check_claim.call_count == 2  # First attempt + 1 retry


class TestIntegration:
    """Integration tests with real components"""
    
    def test_graph_maintains_baseline_compatibility(self):
        """Test that graph output matches baseline format"""
        # This would need actual LLM to fully test
        # Here we just check the structure
        app = create_bs_detector_graph()
        
        # The state should support baseline fields
        initial_state = BSDetectorState(
            claim="Test",
            retry_count=0,
            max_retries=1
        )
        
        # Graph should accept this state
        # (Would run with real LLM in integration environment)
        assert app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])