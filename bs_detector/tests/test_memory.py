"""
Test cases for memory-enhanced BS detection (Module 7)
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.m7_memory import (
    SimpleMemoryManager,
    memory_enhanced_check,
    clear_memory,
    MEMORY_STORE
)
from unittest.mock import Mock, patch


class TestSimpleMemoryManager:
    """Test the simple memory manager"""
    
    def setup_method(self):
        """Clear memory before each test"""
        clear_memory()
    
    def test_entity_extraction(self):
        """Test entity extraction from claims"""
        test_cases = [
            ("The Boeing 747 has four engines", ["Boeing", "747"]),
            ("NASA launched Apollo 11 in 1969", ["NASA", "Apollo"]),
            ("The A380 is made by Airbus", ["A380", "Airbus"]),
        ]
        
        for claim, expected_entities in test_cases:
            entities = SimpleMemoryManager.extract_entities(claim)
            for expected in expected_entities:
                assert expected in entities, f"Expected {expected} in {entities}"
    
    def test_memory_storage(self):
        """Test storing claims in memory"""
        claim = "The Boeing 747 has four engines"
        verdict = "LEGITIMATE"
        confidence = 95
        reasoning = "This is correct"
        
        SimpleMemoryManager.store_claim(claim, verdict, confidence, reasoning)
        
        # Check storage
        assert len(MEMORY_STORE["claims"]) == 1
        stored = MEMORY_STORE["claims"][0]
        assert stored["claim"] == claim
        assert stored["verdict"] == verdict
        assert stored["confidence"] == confidence
        
        # Check entity indexing
        assert "Boeing" in MEMORY_STORE["entities"]
        assert "747" in MEMORY_STORE["entities"]
    
    def test_pattern_detection(self):
        """Test BS pattern detection"""
        bs_claims = [
            "A quantum engine can achieve light speed",
            "Another quantum device breaks physics",
            "Quantum technology defies all laws"
        ]
        
        for claim in bs_claims:
            SimpleMemoryManager.store_claim(claim, "BS", 90, "Impossible")
        
        # Check pattern detection
        assert MEMORY_STORE["patterns"]["quantum"] == 3
    
    def test_context_retrieval(self):
        """Test retrieving relevant context"""
        # Store some claims first
        SimpleMemoryManager.store_claim(
            "The Boeing 747 has four engines",
            "LEGITIMATE", 95, "Correct"
        )
        SimpleMemoryManager.store_claim(
            "The 747 first flew in 1969",
            "LEGITIMATE", 90, "Historical fact"
        )
        
        # Retrieve context for related claim
        context = SimpleMemoryManager.retrieve_context("The 747 can fly at Mach 2")
        
        assert context["memory_context"] is not None
        assert "747" in context["extracted_entities"]
        assert len(context["similar_claims"]) > 0


class TestMemoryEnhancedCheck:
    """Test the memory-enhanced checking function"""
    
    def setup_method(self):
        """Clear memory and create mock LLM"""
        clear_memory()
        self.mock_llm = Mock()
    
    def test_basic_memory_check(self):
        """Test basic memory-enhanced checking"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.verdict = "LEGITIMATE"
        mock_response.confidence = 95
        mock_response.reasoning = "This is correct"
        mock_response.evidence = ["Evidence 1"]
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result = memory_enhanced_check("The Boeing 747 has four engines", self.mock_llm)
        
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] == 95
        assert "related_entities" in result
    
    def test_memory_context_usage(self):
        """Test that memory context is used in subsequent checks"""
        # First claim
        mock_response1 = Mock()
        mock_response1.verdict = "BS"
        mock_response1.confidence = 99
        mock_response1.reasoning = "Impossible"
        mock_response1.evidence = []
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_response1
        result1 = memory_enhanced_check("A quantum engine achieves light speed", self.mock_llm)
        
        # Second similar claim should have context
        context = SimpleMemoryManager.retrieve_context("Another quantum device breaks physics")
        assert context["memory_context"] is not None
        
        # Should detect pattern after multiple BS claims
        memory_enhanced_check("Quantum perpetual motion discovered", self.mock_llm)
        memory_enhanced_check("Quantum anti-gravity achieved", self.mock_llm)
        
        context = SimpleMemoryManager.retrieve_context("New quantum breakthrough")
        assert "quantum" in context["memory_context"].lower()


class TestMemoryPersistence:
    """Test memory persistence across sessions"""
    
    def test_memory_accumulation(self):
        """Test that memory accumulates over multiple checks"""
        clear_memory()
        mock_llm = Mock()
        
        # Mock structured output
        mock_llm.with_structured_output.return_value = mock_llm
        
        claims = [
            ("Claim 1", "LEGITIMATE", 90),
            ("Claim 2", "BS", 95),
            ("Claim 3", "LEGITIMATE", 85),
        ]
        
        for claim_text, verdict, confidence in claims:
            mock_response = Mock()
            mock_response.verdict = verdict
            mock_response.confidence = confidence
            mock_response.reasoning = f"Reasoning for {claim_text}"
            mock_response.evidence = []
            
            mock_llm.invoke.return_value = mock_response
            memory_enhanced_check(claim_text, mock_llm)
        
        # Check accumulation
        assert len(MEMORY_STORE["claims"]) == 3
        
        # Check verdicts are stored correctly
        verdicts = [c["verdict"] for c in MEMORY_STORE["claims"]]
        assert verdicts == ["LEGITIMATE", "BS", "LEGITIMATE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])