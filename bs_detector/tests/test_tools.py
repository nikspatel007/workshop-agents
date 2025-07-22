"""
Tests for tool integration (Iteration 4)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from modules.m4_tools import (
    BSDetectorState,
    initial_check_node,
    generate_queries_node,
    search_web_node,
    analyze_evidence_node,
    revise_verdict_node,
    format_output_node,
    route_after_initial_check,
    check_claim_with_tools,
    create_bs_detector_with_tools
)
from tools.search_tool import (
    WebSearchTool,
    generate_search_queries,
    search_for_evidence
)


class TestSearchTool:
    """Test the web search tool"""
    
    def test_generate_search_queries(self):
        """Test query generation from claims"""
        claim = "The Boeing 747 has four engines"
        queries = generate_search_queries(claim, num_queries=3)
        
        assert len(queries) == 3
        assert claim in queries  # Direct claim should be first
        assert any("fact check" in q for q in queries)  # Should have fact-check version
    
    def test_generate_queries_with_entities(self):
        """Test query generation extracts entities"""
        claim = "SpaceX was founded by Elon Musk in 2002"
        queries = generate_search_queries(claim)
        
        # Should extract SpaceX and Elon as entities
        assert any("SpaceX" in q and "Elon" in q for q in queries)
    
    @patch('tools.search_tool.DuckDuckGoSearchRun')
    def test_web_search_tool(self, mock_search):
        """Test WebSearchTool functionality"""
        # Mock search results
        mock_search_instance = Mock()
        mock_search_instance.invoke.return_value = "SpaceX was founded in 2002. It is a space company. Founded by Elon Musk."
        mock_search.return_value = mock_search_instance
        
        tool = WebSearchTool()
        result = tool.search_web("SpaceX founding date")
        
        assert result["success"] == True
        assert result["query"] == "SpaceX founding date"
        assert result["results"] is not None
        assert result["error"] is None
    
    @patch('tools.search_tool.DuckDuckGoSearchRun')
    def test_search_error_handling(self, mock_search):
        """Test search error handling"""
        mock_search_instance = Mock()
        mock_search_instance.invoke.side_effect = Exception("Network error")
        mock_search.return_value = mock_search_instance
        
        tool = WebSearchTool()
        result = tool.search_web("test query")
        
        assert result["success"] == False
        assert result["error"] == "Network error"
    
    def test_extract_facts(self):
        """Test fact extraction from search results"""
        tool = WebSearchTool()
        
        search_results = [
            {
                "success": True,
                "results": "The Boeing 747 has four engines. It is a wide-body aircraft. First flew in 1969."
            },
            {
                "success": True,
                "results": "Boeing 747 is called the Queen of the Skies. It has a distinctive hump."
            }
        ]
        
        facts = tool.extract_facts(search_results)
        
        assert len(facts) > 0
        assert any("four engines" in fact for fact in facts)
        assert len(facts) <= 10  # Should limit facts


class TestToolNodes:
    """Test individual nodes in the tool-enhanced graph"""
    
    @patch('modules.m4_tools.LLMFactory.create_llm')
    @patch('modules.m4_tools.check_claim')
    def test_initial_check_node(self, mock_check_claim, mock_llm):
        """Test initial check node"""
        # Mock baseline check
        mock_check_claim.return_value = {
            "verdict": "LEGITIMATE",
            "confidence": 65,  # Low confidence
            "reasoning": "Seems plausible"
        }
        
        state = BSDetectorState(claim="Test claim")
        result = initial_check_node(state)
        
        assert result["initial_verdict"] == "LEGITIMATE"
        assert result["initial_confidence"] == 65
        assert result["needs_search"] == True  # Should search due to low confidence
    
    def test_generate_queries_node(self):
        """Test query generation node"""
        state = BSDetectorState(claim="The Concorde could fly at Mach 2")
        result = generate_queries_node(state)
        
        assert "search_queries" in result
        assert len(result["search_queries"]) > 0
        assert any("Concorde" in q for q in result["search_queries"])
    
    @patch('modules.m4_tools.WebSearchTool')
    def test_search_web_node(self, mock_tool_class):
        """Test web search node"""
        # Mock search tool
        mock_tool = Mock()
        mock_tool.search_multiple.return_value = [
            {"success": True, "results": "Concorde flew at Mach 2.04", "query": "Concorde speed"}
        ]
        mock_tool.extract_facts.return_value = ["Concorde flew at Mach 2.04"]
        mock_tool_class.return_value = mock_tool
        
        state = BSDetectorState(
            claim="Concorde speed",
            search_queries=["Concorde speed", "Concorde Mach"]
        )
        result = search_web_node(state)
        
        assert result["used_search"] == True
        assert len(result["extracted_facts"]) > 0
        assert len(result["sources_used"]) > 0
    
    @patch('modules.m4_tools.LLMFactory.create_llm')
    def test_analyze_evidence_node(self, mock_llm):
        """Test evidence analysis node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = """
        SUMMARY: Evidence confirms Concorde could fly at Mach 2.04
        ASSESSMENT: SUPPORTS
        KEY FACTS: Concorde cruise speed was Mach 2.04
        """
        mock_llm.return_value.invoke.return_value = mock_response
        
        state = BSDetectorState(
            claim="Concorde could fly at Mach 2",
            extracted_facts=["Concorde flew at Mach 2.04", "Cruise speed was supersonic"]
        )
        result = analyze_evidence_node(state)
        
        assert "evidence_summary" in result
        assert result["evidence_supports_claim"] == True  # Should detect SUPPORTS
    
    def test_revise_verdict_node_confirm(self):
        """Test verdict revision when evidence confirms"""
        state = BSDetectorState(
            claim="Test claim",
            initial_verdict="LEGITIMATE",
            initial_confidence=65,
            initial_reasoning="Seems right",
            evidence_supports_claim=True,
            evidence_summary="Evidence confirms this"
        )
        
        result = revise_verdict_node(state)
        
        assert result["final_verdict"] == "LEGITIMATE"
        assert result["final_confidence"] > 65  # Should increase confidence
        assert "Evidence" in result["final_reasoning"]
    
    def test_revise_verdict_node_contradict(self):
        """Test verdict revision when evidence contradicts"""
        state = BSDetectorState(
            claim="Test claim",
            initial_verdict="LEGITIMATE",
            initial_confidence=65,
            initial_reasoning="Seems right",
            evidence_supports_claim=False,
            evidence_summary="Evidence refutes this"
        )
        
        result = revise_verdict_node(state)
        
        assert result["final_verdict"] == "BS"  # Should flip verdict
        assert result["final_confidence"] == 80
        assert "evidence indicates otherwise" in result["final_reasoning"]
    
    def test_format_output_node(self):
        """Test output formatting"""
        state = BSDetectorState(
            claim="Test",
            initial_verdict="BS",
            initial_confidence=85,
            initial_reasoning="Initial reason",
            final_verdict="LEGITIMATE",
            final_confidence=90,
            final_reasoning="Updated reason",
            used_search=True,
            sources_used=["query1", "query2"]
        )
        
        result = format_output_node(state)
        
        assert result["final_verdict"] == "LEGITIMATE"  # Uses final when search used
        assert result["final_confidence"] == 90
        assert "Sources consulted" in result["final_reasoning"]


class TestRouting:
    """Test routing logic"""
    
    def test_route_after_initial_check_high_confidence(self):
        """Test routing with high confidence"""
        state = BSDetectorState(
            claim="Test",
            needs_search=False
        )
        
        route = route_after_initial_check(state)
        assert route == "format_output"
    
    def test_route_after_initial_check_low_confidence(self):
        """Test routing with low confidence"""
        state = BSDetectorState(
            claim="Test",
            needs_search=True
        )
        
        route = route_after_initial_check(state)
        assert route == "generate_queries"


class TestEndToEnd:
    """Test complete tool-enhanced detection"""
    
    @patch('modules.m4_tools.check_claim')
    @patch('modules.m4_tools.WebSearchTool')
    @patch('modules.m4_tools.LLMFactory.create_llm')
    def test_check_claim_with_tools_high_confidence(self, mock_llm, mock_tool_class, mock_check):
        """Test claim with high confidence (skip search)"""
        # Mock high confidence baseline result
        mock_check.return_value = {
            "verdict": "LEGITIMATE",
            "confidence": 90,
            "reasoning": "Obviously true"
        }
        
        result = check_claim_with_tools("Water is wet")
        
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] == 90
        assert result["used_search"] == False
        
        # Search tool should not be called
        mock_tool_class.assert_not_called()
    
    @patch('modules.m4_tools.check_claim')
    @patch('modules.m4_tools.WebSearchTool')
    @patch('modules.m4_tools.LLMFactory.create_llm')
    def test_check_claim_with_tools_low_confidence(self, mock_llm, mock_tool_class, mock_check):
        """Test claim with low confidence (trigger search)"""
        # Mock low confidence baseline result
        mock_check.return_value = {
            "verdict": "LEGITIMATE",
            "confidence": 50,
            "reasoning": "Not sure"
        }
        
        # Mock search tool
        mock_tool = Mock()
        mock_tool.search_multiple.return_value = [
            {"success": True, "results": "Evidence supports claim"}
        ]
        mock_tool.extract_facts.return_value = ["Supporting fact"]
        mock_tool_class.return_value = mock_tool
        
        # Mock evidence analysis
        mock_response = Mock()
        mock_response.content = "ASSESSMENT: SUPPORTS"
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = check_claim_with_tools("Complex claim")
        
        assert result["used_search"] == True
        assert result["confidence"] >= 40  # Should be at least 40
        mock_tool_class.assert_called_once()
    
    def test_create_graph(self):
        """Test graph creation"""
        app = create_bs_detector_with_tools()
        
        # Check graph structure
        assert app is not None
        
        # Get graph for inspection
        graph = app.get_graph()
        nodes = graph.nodes
        
        # Verify all nodes present
        expected_nodes = [
            "initial_check",
            "generate_queries", 
            "search_web",
            "analyze_evidence",
            "revise_verdict",
            "format_output"
        ]
        
        for node in expected_nodes:
            assert node in nodes


class TestErrorHandling:
    """Test error handling in tool integration"""
    
    @patch('modules.m4_tools.check_claim')
    def test_initial_check_error(self, mock_check):
        """Test handling of initial check errors"""
        mock_check.side_effect = Exception("LLM error")
        
        state = BSDetectorState(claim="Test")
        result = initial_check_node(state)
        
        assert "error" in result
        assert result["needs_search"] == True  # Should try search on error
    
    @patch('modules.m4_tools.WebSearchTool')
    def test_search_failure_handling(self, mock_tool_class):
        """Test handling of search failures"""
        mock_tool = Mock()
        mock_tool.search_multiple.side_effect = Exception("Network error")
        mock_tool_class.return_value = mock_tool
        
        state = BSDetectorState(
            claim="Test",
            search_queries=["query"]
        )
        result = search_web_node(state)
        
        assert "error" in result
        assert result["used_search"] == True
    
    def test_no_evidence_handling(self):
        """Test handling when no evidence found"""
        state = BSDetectorState(
            claim="Test",
            extracted_facts=[]  # No facts found
        )
        
        result = analyze_evidence_node(state)
        
        assert result["evidence_summary"] == "No evidence found through search."
        assert result["evidence_supports_claim"] is None