"""
Shared utilities for BS Detector workshop
"""
import base64
import os
from IPython.display import Image


def render_mermaid_diagram(graph_definition: str) -> Image:
    """
    Render mermaid diagram in Jupyter using mermaid.ink API
    
    Args:
        graph_definition: Mermaid graph definition string
        
    Returns:
        IPython Image object for display
    """
    graph_bytes = graph_definition.encode("utf-8")
    base64_string = base64.b64encode(graph_bytes).decode("ascii")
    image_url = f"https://mermaid.ink/img/{base64_string}?type=png"
    return Image(url=image_url)


def setup_bedrock_env():
    """Set up environment for AWS Bedrock"""
    os.environ["DEFAULT_LLM_PROVIDER"] = "bedrock"
    os.environ["BEDROCK_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


def format_verdict(verdict: str, confidence: int, evidence: list = None) -> str:
    """
    Format BS detector verdict for consistent output
    
    Args:
        verdict: The verdict (BS, Not BS, Needs Review)
        confidence: Confidence percentage
        evidence: Optional list of evidence items
        
    Returns:
        Formatted verdict string
    """
    output = f"Verdict: {verdict}\nConfidence: {confidence}%"
    
    if evidence:
        output += "\n\nEvidence:"
        for i, item in enumerate(evidence, 1):
            output += f"\n{i}. {item}"
    
    return output