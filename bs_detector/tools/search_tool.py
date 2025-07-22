"""
Web search tool for fact-checking
"""

from typing import List, Dict
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


class WebSearchTool:
    """Wrapper for web search functionality"""
    
    def __init__(self, max_results: int = 3):
        """Initialize search tool
        
        Args:
            max_results: Maximum number of results per search
        """
        # Configure search wrapper
        search_wrapper = DuckDuckGoSearchAPIWrapper(
            max_results=max_results,
            region="en-us",
            safesearch="moderate",
            time="y"  # Last year
        )
        self.search = DuckDuckGoSearchRun(api_wrapper=search_wrapper)
        self.max_results = max_results
    
    def search_web(self, query: str) -> Dict[str, any]:
        """Perform web search
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with query and results
        """
        try:
            # Perform search
            results = self.search.invoke(query)
            
            return {
                "query": query,
                "results": results,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "query": query,
                "results": None,
                "success": False,
                "error": str(e)
            }
    
    def search_multiple(self, queries: List[str]) -> List[Dict[str, any]]:
        """Search multiple queries
        
        Args:
            queries: List of search queries
            
        Returns:
            List of search results
        """
        results = []
        for query in queries:
            result = self.search_web(query)
            results.append(result)
        return results
    
    def extract_facts(self, search_results: List[Dict]) -> List[str]:
        """Extract key facts from search results
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of extracted facts
        """
        facts = []
        
        for result in search_results:
            if result.get("success") and result.get("results"):
                # Split results into sentences and take first few
                sentences = result["results"].split(". ")
                # Take first 3 sentences from each result
                for sentence in sentences[:3]:
                    if len(sentence) > 20:  # Filter out short fragments
                        facts.append(sentence.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_facts = []
        for fact in facts:
            if fact.lower() not in seen:
                seen.add(fact.lower())
                unique_facts.append(fact)
        
        return unique_facts[:10]  # Limit to 10 facts total


def generate_search_queries(claim: str, num_queries: int = 3) -> List[str]:
    """Generate search queries from a claim
    
    Args:
        claim: The claim to fact-check
        num_queries: Number of queries to generate
        
    Returns:
        List of search queries
    """
    queries = []
    
    # Query 1: Direct claim search
    queries.append(claim)
    
    # Query 2: Fact-check version
    if num_queries >= 2:
        queries.append(f"fact check {claim}")
    
    # Query 3: Key entities + verification
    if num_queries >= 3:
        # Extract key terms (simple heuristic)
        words = claim.split()
        # Look for capitalized words (likely entities)
        entities = [w for w in words if w[0].isupper() and len(w) > 2]
        if entities:
            queries.append(f"{' '.join(entities[:2])} facts verification")
        else:
            # Fallback: truth about claim
            queries.append(f"truth about {claim[:50]}")
    
    return queries[:num_queries]


# Convenience functions
def search_for_evidence(claim: str) -> Dict[str, any]:
    """Search for evidence about a claim
    
    Args:
        claim: The claim to research
        
    Returns:
        Dictionary with queries, results, and extracted facts
    """
    tool = WebSearchTool()
    queries = generate_search_queries(claim)
    results = tool.search_multiple(queries)
    facts = tool.extract_facts(results)
    
    return {
        "claim": claim,
        "queries": queries,
        "search_results": results,
        "extracted_facts": facts,
        "num_facts": len(facts)
    }


if __name__ == "__main__":
    # Test the search tool
    print("Testing Web Search Tool")
    print("=" * 50)
    
    test_claims = [
        "The Boeing 797 will have folding wings",
        "The Concorde could fly at Mach 2.04",
        "Elon Musk founded SpaceX in 2002"
    ]
    
    tool = WebSearchTool()
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        print("-" * 40)
        
        # Generate queries
        queries = generate_search_queries(claim)
        print("Search queries:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
        
        # Search
        results = tool.search_multiple(queries[:1])  # Just first query for demo
        
        if results[0]["success"]:
            print("\nSearch results:")
            print(results[0]["results"][:200] + "...")
            
            # Extract facts
            facts = tool.extract_facts(results)
            print("\nExtracted facts:")
            for i, fact in enumerate(facts[:3], 1):
                print(f"  {i}. {fact}")
        else:
            print(f"Search failed: {results[0]['error']}")