"""
Pydantic models for node updates in LangGraph.
These models ensure type safety for state updates from nodes.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class RouterUpdate(BaseModel):
    """Update model for router node"""
    claim_type: Literal["technical", "historical", "current_event", "general"]
    confidence_level: Literal["high", "medium", "low"]


class ExpertUpdate(BaseModel):
    """Update model for expert nodes"""
    verdict: Literal["BS", "LEGITIMATE", "UNCERTAIN"]
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    analyzing_agent: str


class ToolUpdate(BaseModel):
    """Update model for tool-using nodes"""
    search_performed: bool = False
    search_results: Optional[List[Dict[str, Any]]] = None
    tools_used: List[str] = Field(default_factory=list)


class UncertaintyUpdate(BaseModel):
    """Update model for uncertainty detector node"""
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    human_review_request: Optional[Dict[str, Any]] = None


class HumanReviewUpdate(BaseModel):
    """Update model for human review node"""
    human_feedback: Optional[Dict[str, Any]] = None
    verdict: Optional[Literal["BS", "LEGITIMATE", "UNCERTAIN"]] = None
    confidence: Optional[int] = Field(default=None, ge=0, le=100)
    reasoning: Optional[str] = None


class FinalResultUpdate(BaseModel):
    """Update model for final result formatting"""
    result: Dict[str, Any]


class ErrorUpdate(BaseModel):
    """Update model for error states"""
    error: str
    retry_count: Optional[int] = None