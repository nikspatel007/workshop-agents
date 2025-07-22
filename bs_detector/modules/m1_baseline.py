"""
Simple BS detector using single LLM call with structured output.
This module provides baseline claim verification functionality using Pydantic models.
"""

import logging
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.llm_factory import LLMFactory

# Set up logging
logger = logging.getLogger(__name__)


class BSDetectorOutput(BaseModel):
    """Structured output for BS detection results"""
    verdict: str = Field(
        description="BS or LEGITIMATE - whether the claim is false or true"
    )
    confidence: int = Field(
        description="Confidence percentage from 0 to 100",
        ge=0,
        le=100
    )
    reasoning: str = Field(
        description="Brief explanation for the verdict in 1-2 sentences"
    )


def check_claim(claim: str, llm) -> dict:
    """
    Check if an aviation claim is BS or legitimate using structured output.
    
    Args:
        claim: The aviation claim to verify
        llm: Language model instance from LLMFactory (must support structured output)
        
    Returns:
        Dictionary with verdict, confidence, reasoning, and optional error
    """
    try:
        # Validate input
        if not claim or not claim.strip():
            return {
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": "Empty claim provided",
                "error": "Invalid input"
            }
        
        # Truncate very long claims
        if len(claim) > 500:
            claim = claim[:500] + "..."
        
        # Create prompt
        system_prompt = """You are an aviation expert and fact-checker. Your job is to determine if claims about aviation are BS (false/ridiculous) or LEGITIMATE (true/reasonable).

Remember:
- BS means the claim is false, impossible, or ridiculous
- LEGITIMATE means the claim is true, possible, or reasonable
- Be specific about aviation facts in your reasoning
- Keep reasoning to 1-2 sentences"""

        user_prompt = f"Analyze this aviation claim: {claim}"
        
        # Get structured output from LLM
        logger.debug(f"Checking claim: {claim[:50]}...")
        
        # Create structured LLM
        structured_llm = llm.with_structured_output(BSDetectorOutput)
        
        # Get response
        response = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # Convert Pydantic model to dict
        result = response.model_dump()
        
        # Validate verdict (should already be valid from Pydantic, but double-check)
        if result["verdict"] not in ["BS", "LEGITIMATE"]:
            logger.warning(f"Invalid verdict: {result['verdict']}")
            result["verdict"] = "ERROR"
            result["error"] = "Invalid verdict returned"
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking claim: {str(e)}")
        return {
            "verdict": "ERROR",
            "confidence": 0,
            "reasoning": "Failed to analyze claim",
            "error": str(e)
        }


def check_claim_batch(claims: list[str], llm) -> list[dict]:
    """
    Check multiple claims (for testing purposes).
    
    Args:
        claims: List of claims to check
        llm: Language model instance
        
    Returns:
        List of results for each claim
    """
    results = []
    for claim in claims:
        result = check_claim(claim, llm)
        result["claim"] = claim  # Include original claim
        results.append(result)
    return results


# Example usage
if __name__ == "__main__":
    # Demo the structured output
    llm = LLMFactory.create_llm()
    
    test_claims = [
        "The Boeing 747 has four engines",
        "Commercial planes can fly to the moon"
    ]
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        result = check_claim(claim, llm)
        print(f"Result: {result}")