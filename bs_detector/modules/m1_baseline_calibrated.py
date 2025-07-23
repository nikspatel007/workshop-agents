"""
Calibrated baseline BS detector with better confidence scoring
"""

from langchain.schema import SystemMessage, HumanMessage
from typing import Dict

def check_claim_calibrated(claim: str, llm) -> Dict[str, any]:
    """
    Check if a claim is BS with calibrated confidence scoring.
    
    The key improvement is asking the LLM to explicitly consider uncertainty factors
    and provide a calibrated confidence score.
    """
    
    system_prompt = """You are an expert fact-checker evaluating claims about aviation and aerospace.

Your task is to determine if a claim is LEGITIMATE or BS (false/misleading) and provide a CALIBRATED confidence score.

IMPORTANT: For confidence scoring, explicitly consider these uncertainty factors:
1. How recent is the claim? (Recent events = lower confidence)
2. How specific are the facts? (Specific numbers/dates = need verification)
3. Is this common knowledge or specialized? (Specialized = lower confidence)
4. Could this have changed recently? (Dynamic topics = lower confidence)
5. Is this opinion or fact? (Opinions = lower confidence on factuality)

Confidence Scale:
- 90-100%: Absolutely certain (basic facts like "planes have wings")
- 70-89%: Very confident (well-known historical facts)
- 50-69%: Moderately confident (specialized knowledge, needs verification)
- 30-49%: Low confidence (recent events, specific claims, uncertain)
- 0-29%: Very uncertain (future predictions, rumors, unverifiable)

Structure your response EXACTLY as:
VERDICT: [LEGITIMATE or BS]
CONFIDENCE: [0-100]
UNCERTAINTY_FACTORS: [List factors that reduce your confidence]
REASONING: [Your detailed explanation]"""

    human_prompt = f"""Evaluate this claim: "{claim}"

Remember to:
1. First identify uncertainty factors
2. Then set confidence accordingly
3. Be honest about what you don't know for certain"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Parse response
    lines = response.content.strip().split('\n')
    verdict = None
    confidence = None
    uncertainty_factors = []
    reasoning = ""
    
    parsing_reasoning = False
    parsing_factors = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = int(line.split(":", 1)[1].strip())
            except:
                confidence = 50  # Default if parsing fails
        elif line.startswith("UNCERTAINTY_FACTORS:"):
            parsing_factors = True
            parsing_reasoning = False
            factors_text = line.split(":", 1)[1].strip()
            if factors_text:
                uncertainty_factors.append(factors_text)
        elif line.startswith("REASONING:"):
            parsing_factors = False
            parsing_reasoning = True
            reasoning = line.split(":", 1)[1].strip()
        elif parsing_factors and line:
            uncertainty_factors.append(line)
        elif parsing_reasoning:
            reasoning += " " + line
    
    # Ensure valid values
    if verdict not in ["LEGITIMATE", "BS"]:
        verdict = "UNCERTAIN"
    if confidence is None:
        confidence = 50
    
    return {
        "verdict": verdict,
        "confidence": confidence,
        "uncertainty_factors": uncertainty_factors,
        "reasoning": reasoning.strip()
    }


def check_claim_with_categories(claim: str, llm) -> Dict[str, any]:
    """
    Alternative approach: Categorize claim first, then apply appropriate confidence.
    """
    
    categorization_prompt = """Categorize this claim into ONE of these types:
1. BASIC_FACT: Universal truths (e.g., "water is wet")
2. HISTORICAL: Past events with dates/facts (e.g., "Boeing 747 first flew in 1969")
3. TECHNICAL: Specific technical details (e.g., "engine thrust is 50,000 lbs")
4. RECENT: Events from last 2 years (e.g., "launched last month")
5. FUTURE: Predictions or planned events (e.g., "will launch next year")
6. OPINION: Subjective statements (e.g., "best aircraft")
7. UNCERTAIN: Rumors, maybes, unverified (e.g., "might be developing")

Claim: "{claim}"

Response format:
CATEGORY: [category]
JUSTIFICATION: [why this category]"""
    
    messages = [
        SystemMessage(content="You categorize claims about aviation and aerospace."),
        HumanMessage(content=categorization_prompt.format(claim=claim))
    ]
    
    cat_response = llm.invoke(messages)
    
    # Parse category
    category = "UNCERTAIN"
    for line in cat_response.content.split('\n'):
        if line.startswith("CATEGORY:"):
            category = line.split(":", 1)[1].strip()
            break
    
    # Set confidence based on category
    category_confidence = {
        "BASIC_FACT": 95,
        "HISTORICAL": 85,
        "TECHNICAL": 60,  # Needs verification
        "RECENT": 40,     # Definitely needs search
        "FUTURE": 35,     # Very uncertain
        "OPINION": 70,    # Can judge but subjective
        "UNCERTAIN": 30   # Needs search
    }
    
    # Now check the claim with category-aware confidence
    base_confidence = category_confidence.get(category, 50)
    
    # Get verdict
    check_prompt = f"""Evaluate if this claim is LEGITIMATE or BS: "{claim}"

This is a {category} type claim, so base confidence should be around {base_confidence}%.
Adjust up/down by up to 15% based on your specific knowledge.

Response format:
VERDICT: [LEGITIMATE or BS]
CONFIDENCE: [{base_confidence-15} to {base_confidence+15}]
REASONING: [explanation]"""
    
    messages = [
        SystemMessage(content="You are a fact-checker for aviation claims."),
        HumanMessage(content=check_prompt)
    ]
    
    check_response = llm.invoke(messages)
    
    # Parse response
    lines = check_response.content.strip().split('\n')
    verdict = "UNCERTAIN"
    confidence = base_confidence
    reasoning = ""
    
    for line in lines:
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = int(line.split(":", 1)[1].strip())
            except:
                confidence = base_confidence
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
    
    return {
        "verdict": verdict,
        "confidence": confidence,
        "category": category,
        "reasoning": reasoning
    }