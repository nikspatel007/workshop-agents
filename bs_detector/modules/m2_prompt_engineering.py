"""
Module 2: Prompt Engineering for Better BS Detection

This module demonstrates various prompt engineering techniques:
- Structured prompts
- Few-shot learning
- Chain of thought reasoning
- Domain-specific prompts
"""

from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel


class BSDetectionResult(BaseModel):
    """Structured output for BS detection"""
    verdict: str = Field(description="BS or LEGITIMATE")
    confidence: int = Field(description="Confidence percentage 0-100", ge=0, le=100)
    reasoning: str = Field(description="Explanation of the verdict")
    evidence: list[str] = Field(description="Supporting evidence points")


def create_structured_prompt(claim: str) -> str:
    """Create a structured prompt for BS detection"""
    return f"""You are an aviation expert.

Analyze this claim: {claim}

Provide:
- Verdict: [TRUE/FALSE]
- Confidence: [0-100%]
- Evidence: 2 key facts
"""


def create_few_shot_prompt(claim: str) -> str:
    """Create a few-shot learning prompt"""
    return f"""Determine if aviation claims are BS or LEGITIMATE.

Examples:
Claim: "The Wright brothers first flew in 1903"
Verdict: LEGITIMATE (Historical fact)

Claim: "Helicopters fly by pushing air down"
Verdict: LEGITIMATE (Correct physics)

Claim: "Jets can hover vertically without special engines"
Verdict: BS (Requires VTOL capability)

Now analyze:
Claim: "{claim}"
Verdict:"""


def create_chain_of_thought_prompt(claim: str) -> str:
    """Create a chain-of-thought reasoning prompt"""
    return f"""Think step-by-step to determine if this claim is BS:

Claim: "{claim}"

Step 1: What does the claim assert?
Step 2: What physics/engineering principles apply?
Step 3: Is it technically possible?
Step 4: Final verdict

Let's work through each step:"""


def create_domain_specific_prompt(claim: str, domain: str = "general") -> str:
    """Create a domain-specific BS detection prompt"""
    return f"""You are an expert fact-checker specializing in {domain}.

Analyze this claim for accuracy: "{claim}"

Consider:
1. Known facts and data
2. Physical/technical feasibility
3. Logical consistency
4. Common misconceptions

Provide a structured analysis with verdict, confidence, and evidence."""


def check_claim_with_prompt_engineering(
    claim: str, 
    llm: BaseChatModel,
    technique: str = "structured"
) -> BSDetectionResult:
    """
    Check a claim using various prompt engineering techniques
    
    Args:
        claim: The claim to verify
        llm: Language model to use
        technique: Prompt technique to use (structured, few_shot, cot, domain)
        
    Returns:
        BSDetectionResult with verdict and analysis
    """
    # Select prompt based on technique
    if technique == "few_shot":
        prompt = create_few_shot_prompt(claim)
    elif technique == "cot":
        prompt = create_chain_of_thought_prompt(claim)
    elif technique == "domain":
        # Detect domain from claim content
        domain = "aviation" if any(word in claim.lower() for word in ["fly", "plane", "aircraft", "boeing"]) else "general"
        prompt = create_domain_specific_prompt(claim, domain)
    else:
        prompt = create_structured_prompt(claim)
    
    # Use structured output
    llm_with_structure = llm.with_structured_output(BSDetectionResult)
    
    try:
        result = llm_with_structure.invoke(prompt)
        return result
    except Exception as e:
        # Fallback for models that don't support structured output
        response = llm.invoke(prompt)
        # Parse response manually
        verdict = "BS" if "bs" in response.content.lower() or "false" in response.content.lower() else "LEGITIMATE"
        confidence = 70  # Default confidence
        
        return BSDetectionResult(
            verdict=verdict,
            confidence=confidence,
            reasoning=response.content[:200],
            evidence=["See reasoning above"]
        )