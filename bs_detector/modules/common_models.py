"""
Common Pydantic models used across all modules for structured output.
This ensures type safety and consistency across the entire application.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class BSDetectorResult(BaseModel):
    """Standard result model for BS detection"""
    verdict: Literal["BS", "LEGITIMATE", "UNCERTAIN", "ERROR"] = Field(
        description="The verdict on whether the claim is BS or legitimate"
    )
    confidence: int = Field(
        ge=0, 
        le=100,
        description="Confidence percentage from 0 to 100"
    )
    reasoning: str = Field(
        description="Explanation for the verdict"
    )
    claim_type: Optional[Literal["technical", "historical", "current_event", "general"]] = Field(
        default=None,
        description="Type of claim as determined by router"
    )
    analyzing_agent: Optional[str] = Field(
        default=None,
        description="Name of the agent that analyzed the claim"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )


class SearchResult(BaseModel):
    """Model for search results"""
    query: str
    results: Optional[str] = None
    facts: List[str] = Field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCallResult(BaseModel):
    """Model for tool call results"""
    tool_name: str
    tool_args: Dict[str, Any]
    result: Any
    success: bool = True
    error: Optional[str] = None


class ExpertOpinion(BaseModel):
    """Model for expert opinions"""
    expert_name: str
    verdict: Literal["BS", "LEGITIMATE", "UNCERTAIN"]
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)


class HumanReviewRequestModel(BaseModel):
    """Structured model for human review requests"""
    claim: str
    ai_verdict: Optional[Literal["BS", "LEGITIMATE", "UNCERTAIN"]] = None
    ai_confidence: Optional[int] = Field(default=None, ge=0, le=100)
    ai_reasoning: Optional[str] = None
    uncertainty_reasons: List[str] = Field(default_factory=list)
    expert_opinions: List[ExpertOpinion] = Field(default_factory=list)
    search_results: List[SearchResult] = Field(default_factory=list)
    request_time: datetime = Field(default_factory=datetime.now)


class HumanFeedbackModel(BaseModel):
    """Structured model for human feedback"""
    verdict: Literal["BS", "LEGITIMATE", "UNCERTAIN"]
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    additional_context: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    feedback_time: datetime = Field(default_factory=datetime.now)


class NodeUpdate(BaseModel):
    """Base model for node updates to state"""
    class Config:
        extra = "allow"  # Allow additional fields for flexibility