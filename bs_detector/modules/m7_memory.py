"""
Module 7: Memory-Enhanced BS Detection

This module adds memory capabilities without external dependencies:
1. In-memory storage of claims and verdicts
2. Simple pattern matching for related claims
3. Context retrieval based on entity matching
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
import re
from collections import defaultdict

from modules.m6_human_in_loop_simple import HumanInLoopState
from config.llm_factory import LLMFactory


# Global in-memory storage (for workshop simplicity)
MEMORY_STORE = {
    "claims": [],
    "entities": defaultdict(list),
    "patterns": defaultdict(int)
}


class MemoryEnhancedState(HumanInLoopState):
    """State with memory capabilities"""
    memory_context: Optional[str] = None
    similar_claims: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_entities: List[str] = Field(default_factory=list)


class SimpleMemoryManager:
    """Manages memory operations with in-memory storage"""
    
    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """Simple entity extraction using regex patterns"""
        entities = []
        
        # Pattern for capitalized words (proper nouns)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(proper_nouns)
        
        # Pattern for acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        entities.extend(acronyms)
        
        # Pattern for numbers with units (e.g., "747", "A380")
        alphanumeric = re.findall(r'\b[A-Z]\d+\b|\b\d+[A-Z]\b', text)
        entities.extend(alphanumeric)
        
        # Remove duplicates and common words
        entities = list(set(entities))
        common_words = {"The", "This", "That", "These", "Those", "Is", "Are", "Was", "Were"}
        entities = [e for e in entities if e not in common_words]
        
        return entities
    
    @staticmethod
    def store_claim(claim: str, verdict: str, confidence: int, reasoning: str):
        """Store a claim and its verdict in memory"""
        entities = SimpleMemoryManager.extract_entities(claim)
        
        claim_record = {
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in claims list
        MEMORY_STORE["claims"].append(claim_record)
        
        # Index by entities
        for entity in entities:
            MEMORY_STORE["entities"][entity].append(len(MEMORY_STORE["claims"]) - 1)
        
        # Track patterns in false claims
        if verdict == "BS":
            # Extract key phrases
            key_phrases = re.findall(r'\b(?:quantum|perpetual|anti-gravity|light speed|time travel)\b', claim.lower())
            for phrase in key_phrases:
                MEMORY_STORE["patterns"][phrase] += 1
    
    @staticmethod
    def retrieve_context(claim: str) -> Dict[str, Any]:
        """Retrieve relevant context for a claim"""
        entities = SimpleMemoryManager.extract_entities(claim)
        
        # Find related claims
        related_indices = set()
        for entity in entities:
            related_indices.update(MEMORY_STORE["entities"].get(entity, []))
        
        similar_claims = []
        for idx in related_indices:
            if idx < len(MEMORY_STORE["claims"]):
                similar_claims.append(MEMORY_STORE["claims"][idx])
        
        # Check for known BS patterns
        bs_patterns = []
        claim_lower = claim.lower()
        for pattern, count in MEMORY_STORE["patterns"].items():
            if pattern in claim_lower and count >= 2:
                bs_patterns.append(pattern)
        
        # Build context string
        context_parts = []
        
        if similar_claims:
            context_parts.append("Related previous claims:")
            for sc in similar_claims[:3]:  # Limit to 3
                context_parts.append(f"- {sc['claim']}: {sc['verdict']} ({sc['confidence']}%)")
        
        if bs_patterns:
            context_parts.append(f"\\nWarning: Contains known BS patterns: {', '.join(bs_patterns)}")
        
        return {
            "memory_context": "\\n".join(context_parts) if context_parts else None,
            "similar_claims": similar_claims[:3],
            "extracted_entities": entities
        }


def memory_enhanced_check(claim: str, llm) -> Dict[str, Any]:
    """Check a claim with memory enhancement"""
    # Retrieve context
    context = SimpleMemoryManager.retrieve_context(claim)
    
    # Build enhanced prompt
    system_prompt = """You are an aviation fact checker with access to previous claims.
Analyze the claim and determine if it's BS or LEGITIMATE."""
    
    if context["memory_context"]:
        system_prompt += f"\n\n{context['memory_context']}"
    
    # Use structured output
    from modules.m2_prompt_engineering import BSDetectionResult
    llm_with_structure = llm.with_structured_output(BSDetectionResult)
    
    try:
        result = llm_with_structure.invoke(f"{system_prompt}\n\nClaim: {claim}")
        
        # Store in memory
        SimpleMemoryManager.store_claim(
            claim,
            result.verdict,
            result.confidence,
            result.reasoning
        )
        
        # Return enhanced result
        return {
            "verdict": result.verdict,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "memory_context": context["memory_context"],
            "related_entities": context["extracted_entities"],
            "similar_claims": len(context["similar_claims"])
        }
        
    except Exception as e:
        # Fallback
        response = llm.invoke(f"{system_prompt}\n\nClaim: {claim}")
        verdict = "BS" if "bs" in response.content.lower() else "LEGITIMATE"
        
        SimpleMemoryManager.store_claim(claim, verdict, 70, response.content[:200])
        
        return {
            "verdict": verdict,
            "confidence": 70,
            "reasoning": response.content[:200],
            "memory_context": context["memory_context"],
            "related_entities": context["extracted_entities"]
        }


def interactive_demo():
    """Demo showing simple memory in action"""
    print("🧠 BS Detector with Simple Memory")
    print("=" * 50)
    
    llm = LLMFactory.create_llm()
    
    # Test sequence
    test_claims = [
        "The Boeing 747 has four engines",
        "The Boeing 747 can fly at Mach 2",  # Should remember 747
        "Quantum engines can achieve light speed",
        "Another quantum drive breaks physics laws",  # Should detect pattern
    ]
    
    for i, claim in enumerate(test_claims):
        print(f"\n{'='*40}")
        print(f"Claim {i+1}: {claim}")
        
        result = memory_enhanced_check(claim, llm)
        
        print(f"Verdict: {result['verdict']} ({result['confidence']}%)")
        
        if result.get('memory_context'):
            print(f"\n📝 Memory Context:")
            print(result['memory_context'])
        
        if result.get('related_entities'):
            print(f"\n🔗 Entities: {', '.join(result['related_entities'])}")
    
    # Show memory stats
    print(f"\n\n📊 Memory Statistics:")
    print(f"Total claims stored: {len(MEMORY_STORE['claims'])}")
    print(f"Unique entities tracked: {len(MEMORY_STORE['entities'])}")
    print(f"BS patterns detected: {dict(MEMORY_STORE['patterns'])}")


# Clear memory function for testing
def clear_memory():
    """Clear all stored memory"""
    MEMORY_STORE["claims"].clear()
    MEMORY_STORE["entities"].clear()
    MEMORY_STORE["patterns"].clear()


if __name__ == "__main__":
    interactive_demo()