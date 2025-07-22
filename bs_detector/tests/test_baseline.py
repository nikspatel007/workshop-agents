"""
Test cases for baseline BS detector.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.m1_baseline import check_claim, BSDetectorOutput
from config.llm_factory import LLMFactory


class TestPydanticModel:
    """Test cases for Pydantic model"""
    
    def test_bs_detector_output_model(self):
        """Test the BSDetectorOutput Pydantic model"""
        # Test valid model creation
        output = BSDetectorOutput(
            verdict="BS",
            confidence=95,
            reasoning="This is clearly false"
        )
        assert output.verdict == "BS"
        assert output.confidence == 95
        assert output.reasoning == "This is clearly false"
        
        # Test model validation
        from pydantic import ValidationError
        
        # Test confidence bounds
        with pytest.raises(ValidationError):
            BSDetectorOutput(verdict="BS", confidence=150, reasoning="test")
        
        with pytest.raises(ValidationError):
            BSDetectorOutput(verdict="BS", confidence=-10, reasoning="test")
        
        # Test model dump
        data = output.model_dump()
        assert data["verdict"] == "BS"
        assert data["confidence"] == 95
        assert data["reasoning"] == "This is clearly false"


class TestBaseline:
    """Test cases for baseline BS detector"""
    
    @pytest.fixture
    def llm(self):
        """Create LLM instance for testing"""
        try:
            return LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
    
    def test_obvious_bs_claim(self, llm):
        """Test detection of obvious BS claim"""
        result = check_claim(
            "Commercial airplanes can fly to the moon",
            llm
        )
        assert result["verdict"] == "BS"
        assert result["confidence"] > 70  # Lower threshold for different models
        # Check for various keywords that might appear in the reasoning
        reasoning_lower = result["reasoning"].lower()
        expected_keywords = ["moon", "space", "atmosphere", "orbit", "commercial", "impossible", "cannot"]
        assert any(keyword in reasoning_lower for keyword in expected_keywords), \
            f"Expected aviation-related reasoning, got: {result['reasoning']}"
    
    def test_legitimate_claim(self, llm):
        """Test detection of legitimate claim"""
        result = check_claim(
            "The Boeing 747 has four jet engines",
            llm
        )
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] > 60  # Lower threshold for different models
        assert len(result["reasoning"]) > 10
    
    def test_empty_claim(self, llm):
        """Test handling of empty claim"""
        result = check_claim("", llm)
        assert result["verdict"] == "ERROR"
        assert result["error"] == "Invalid input"
    
    def test_long_claim_truncation(self, llm):
        """Test that very long claims are truncated"""
        long_claim = "The airplane " + ("can fly very high " * 100)
        result = check_claim(long_claim, llm)
        # Should still get a valid response
        assert result["verdict"] in ["BS", "LEGITIMATE", "ERROR"]
        assert "confidence" in result
    
    def test_structured_output_format(self, llm):
        """Test that structured output returns expected format"""
        result = check_claim("Helicopters can hover in place", llm)
        
        # Check all required fields are present
        assert "verdict" in result
        assert "confidence" in result
        assert "reasoning" in result
        
        # Check types
        assert isinstance(result["verdict"], str)
        assert isinstance(result["confidence"], int)
        assert isinstance(result["reasoning"], str)
        
        # Check confidence is within bounds
        assert 0 <= result["confidence"] <= 100


class TestBatchProcessing:
    """Test batch claim processing"""
    
    @pytest.fixture
    def llm(self):
        """Create LLM instance for testing"""
        try:
            return LLMFactory.create_llm()
        except Exception:
            pytest.skip("No LLM provider available")
    
    def test_check_claim_batch(self, llm):
        """Test batch processing of claims"""
        from modules.m1_baseline import check_claim_batch
        
        claims = [
            "The Boeing 747 has four engines",
            "Planes can fly to Mars",
            "Pilots need licenses"
        ]
        
        results = check_claim_batch(claims, llm)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert "verdict" in result
            assert "confidence" in result
            assert "reasoning" in result
            assert result["claim"] == claims[i]