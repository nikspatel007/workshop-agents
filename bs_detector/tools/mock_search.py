"""
Mock search tool for workshop consistency.
Returns predictable aviation facts without external dependencies.
"""

from typing import List, Dict, Any


def search_aviation_facts(query: str) -> List[Dict[str, Any]]:
    """
    Mock search that returns aviation facts.
    Used for consistent workshop experience.
    """
    # Simple keyword-based responses
    mock_data = {
        "747": [
            {"fact": "The Boeing 747 has 4 engines", "confidence": 1.0},
            {"fact": "The 747 first flew in 1969", "confidence": 1.0}
        ],
        "concorde": [
            {"fact": "The Concorde could fly at Mach 2.04", "confidence": 1.0},
            {"fact": "The Concorde was retired in 2003", "confidence": 1.0}
        ],
        "default": [
            {"fact": "Commercial pilots need an ATP license", "confidence": 0.9},
            {"fact": "Modern aircraft have multiple redundant systems", "confidence": 0.9}
        ]
    }
    
    # Find matching facts
    query_lower = query.lower()
    for key, facts in mock_data.items():
        if key in query_lower:
            return facts
    
    return mock_data["default"]