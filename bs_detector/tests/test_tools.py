"""
Tests for tool integration (Iteration 4) - Multi-Agent System
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from modules.m4_tools import (
    ToolEnhancedState,
    WebSearchResult,
    search_for_information,
    current_events_expert_with_tools_node,
    create_tool_enhanced_bs_detector,
    check_claim_with_tools
)
from modules.m3_routing import (
    MultiAgentState,
    router_node,
    technical_expert_node,
    historical_expert_node,
    general_expert_node
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


class TestMultiAgentRouting:
    """Test multi-agent routing system"""
    
    @patch('modules.m3_routing.LLMFactory.create_llm')
    def test_router_node(self, mock_llm):
        """Test router correctly classifies claims"""
        # Mock LLM response for technical claim
        mock_response = Mock()
        mock_response.content = "CLAIM_TYPE: technical\nCONFIDENCE_LEVEL: high"
        mock_llm.return_value.invoke.return_value = mock_response
        
        state = MultiAgentState(claim="The F-22 can fly at Mach 2.2")
        result = router_node(state)
        
        assert result["claim_type"] == "technical"
        assert result["confidence_level"] == "high"
    
    @patch('modules.m3_routing.LLMFactory.create_llm')
    def test_router_current_events(self, mock_llm):
        """Test router identifies current events"""
        mock_response = Mock()
        mock_response.content = "CLAIM_TYPE: current_event\nCONFIDENCE_LEVEL: medium"
        mock_llm.return_value.invoke.return_value = mock_response
        
        state = MultiAgentState(claim="Apple announced new products yesterday")
        result = router_node(state)
        
        assert result["claim_type"] == "current_event"


class TestToolIntegration:
    """Test tool integration with current events expert"""
    
    @patch('modules.m4_tools.WebSearchTool')
    def test_search_for_information_tool(self, mock_tool_class):
        """Test the search_for_information tool function"""
        # Mock search tool
        mock_tool = Mock()
        mock_tool.search_web.return_value = {
            "success": True,
            "query": "test query",
            "results": "Some results"
        }
        mock_tool.extract_facts.return_value = ["Fact 1", "Fact 2"]
        mock_tool_class.return_value = mock_tool
        
        result = search_for_information("test query")
        import json
        result_data = json.loads(result)  # It returns JSON string
        
        assert result_data["search_successful"] == True
        assert len(result_data["facts"]) == 2
    
    @patch('modules.m4_tools.LLMFactory.create_llm')
    def test_current_events_expert_no_tools(self, mock_llm):
        """Test current events expert when tools not needed"""
        # Mock LLM without tool calls
        mock_response = Mock()
        mock_response.content = "VERDICT: LEGITIMATE\nCONFIDENCE: 95\nREASONING: Historical fact"
        mock_response.tool_calls = []
        
        mock_llm_instance = Mock()
        mock_llm_instance.bind_tools.return_value.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        state = ToolEnhancedState(claim="World War II ended in 1945")
        result = current_events_expert_with_tools_node(state)
        
        assert result["verdict"] == "LEGITIMATE"
        assert result["confidence"] == 95
        assert result["search_performed"] == False
        assert result["tools_used"] == []
    
    @patch('modules.m4_tools.LLMFactory.create_llm')
    @patch('modules.m4_tools.search_for_information')
    def test_current_events_expert_with_tools(self, mock_search_tool, mock_llm):
        """Test current events expert using tools"""
        # Mock tool call
        tool_call = {
            "name": "search_for_information",
            "args": {"query": "SpaceX launches yesterday"},
            "id": "call_123"
        }
        
        # Mock initial response with tool call
        mock_initial_response = Mock()
        mock_initial_response.content = "Need to search"
        mock_initial_response.tool_calls = [tool_call]
        
        # Mock final response after tool use
        mock_final_response = Mock()
        mock_final_response.content = "VERDICT: BS\nCONFIDENCE: 90\nREASONING: No launches found"
        
        # Mock search tool
        mock_search_tool.invoke.return_value = '{"query": "SpaceX launches yesterday", "facts": ["No launches"], "search_successful": true}'
        
        # Setup LLM mock
        mock_llm_instance = Mock()
        mock_llm_with_tools = Mock()
        mock_llm_with_tools.invoke.side_effect = [mock_initial_response, mock_final_response]
        mock_llm_instance.bind_tools.return_value = mock_llm_with_tools
        mock_llm.return_value = mock_llm_instance
        
        state = ToolEnhancedState(claim="SpaceX launched 5 rockets yesterday")
        result = current_events_expert_with_tools_node(state)
        
        assert result["verdict"] == "BS"
        assert result["confidence"] == 90
        assert result["search_performed"] == True
        assert "search_for_information" in result["tools_used"]


class TestGraphStructure:
    """Test graph structure and components"""
    
    def test_create_graph(self):
        """Test graph creation"""
        app = create_tool_enhanced_bs_detector()
        
        # Check graph structure
        assert app is not None
        
        # Get graph for inspection
        graph = app.get_graph()
        nodes = graph.nodes
        
        # Verify all nodes present
        expected_nodes = [
            "router",
            "technical_expert",
            "historical_expert", 
            "current_events_expert",
            "general_expert"
        ]
        
        for node in expected_nodes:
            assert node in nodes
    
    def test_state_structure(self):
        """Test the enhanced state includes all necessary fields"""
        state = ToolEnhancedState(claim="Test claim")
        
        # Check inherited fields
        assert state.claim == "Test claim"
        assert state.claim_type is None
        assert state.verdict is None
        
        # Check tool-specific fields
        assert state.search_performed == False
        assert state.search_results is None
        assert state.tools_used == []
        assert state.messages == []


class TestErrorHandling:
    """Test error handling in multi-agent system"""
    
    @patch('modules.m3_routing.LLMFactory.create_llm')
    def test_router_error_defaults_to_general(self, mock_llm):
        """Test router defaults to general on error"""
        mock_llm.return_value.invoke.side_effect = Exception("LLM error")
        
        state = MultiAgentState(claim="Test claim")
        result = router_node(state)
        
        # Should default to general
        assert result["claim_type"] == "general"
        assert result["confidence_level"] == "medium"
    
    @patch('modules.m4_tools.WebSearchTool')
    def test_search_tool_error_handling(self, mock_tool_class):
        """Test search tool handles errors gracefully"""
        mock_tool = Mock()
        mock_tool.search_web.side_effect = Exception("Network error")
        mock_tool_class.return_value = mock_tool
        
        result = search_for_information("test query")
        result_data = json.loads(result)
        
        assert result_data["search_successful"] == False
        assert "Network error" in result_data["error"]