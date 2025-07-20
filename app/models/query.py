from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class QueryStatus(str, Enum):
    """Status of a research query."""
    PENDING = "pending"
    SEARCHING = "searching"
    EXTRACTING = "extracting"
    COMPARING = "comparing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchQuery(BaseModel):
    """Model for research query requests."""
    
    query: str = Field(..., description="The research question or topic to investigate")
    regions: Optional[List[str]] = Field(default=None, description="Specific regions to focus on (e.g., ['EU', 'US'])")
    document_types: Optional[List[str]] = Field(default=None, description="Types of documents to search for")
    max_documents: Optional[int] = Field(default=10, description="Maximum number of documents to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Compare AI safety regulations in EU vs US",
                "regions": ["EU", "US"],
                "document_types": ["legislation", "policy_framework"],
                "max_documents": 10
            }
        }

class ResearchQueryDB(ResearchQuery):
    """Database model for research queries with additional fields."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    status: QueryStatus = Field(default=QueryStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    progress: dict = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "query": "Compare AI safety regulations in EU vs US",
                "regions": ["EU", "US"],
                "document_types": ["legislation", "policy_framework"],
                "max_documents": 10,
                "status": "pending",
                "progress": {
                    "search_agent": 0,
                    "extract_agent": 0,
                    "compare_agent": 0,
                    "summarize_agent": 0
                }
            }
        } 