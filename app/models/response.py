from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Document(BaseModel):
    """Model for a document found by the search agent."""
    
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    content: str = Field(..., description="Document content or summary")
    source: str = Field(..., description="Source of the document")
    region: Optional[str] = Field(default=None, description="Geographic region")
    document_type: Optional[str] = Field(default=None, description="Type of document")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score")

class ExtractedClause(BaseModel):
    """Model for a legal clause extracted from a document."""
    
    clause_text: str = Field(..., description="The extracted clause text")
    clause_type: str = Field(..., description="Type of clause (e.g., 'requirement', 'prohibition', 'definition')")
    topic: str = Field(..., description="Topic or category of the clause")
    jurisdiction: str = Field(..., description="Jurisdiction the clause applies to")
    document_source: str = Field(..., description="Source document")
    confidence_score: Optional[float] = Field(default=None, description="Extraction confidence score")
    key_entities: Optional[List[str]] = Field(default=None, description="Key entities mentioned in the clause")

class Comparison(BaseModel):
    """Model for comparison results between jurisdictions."""
    
    topic: str = Field(..., description="Topic being compared")
    similarities: List[str] = Field(default_factory=list, description="Similarities found")
    differences: List[str] = Field(default_factory=list, description="Differences found")
    gaps: List[str] = Field(default_factory=list, description="Regulatory gaps identified")
    jurisdictions_compared: List[str] = Field(..., description="Jurisdictions compared")
    comparison_score: Optional[float] = Field(default=None, description="Similarity score")

class Summary(BaseModel):
    """Model for the final research summary."""
    
    executive_summary: str = Field(..., description="Executive summary of findings")
    key_findings: List[str] = Field(..., description="Key findings from the research")
    recommendations: List[str] = Field(..., description="Policy recommendations")
    methodology: str = Field(..., description="Description of the research methodology")
    limitations: List[str] = Field(default_factory=list, description="Research limitations")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ResearchResult(BaseModel):
    """Complete research result model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    query: str = Field(..., description="Original research query")
    documents: List[Document] = Field(default_factory=list, description="Documents found")
    extracted_clauses: List[ExtractedClause] = Field(default_factory=list, description="Extracted legal clauses")
    comparisons: List[Comparison] = Field(default_factory=list, description="Comparison results")
    summary: Optional[Summary] = Field(default=None, description="Final summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "query": "Compare AI safety regulations in EU vs US",
                "documents": [
                    {
                        "title": "EU AI Act",
                        "url": "https://example.com/eu-ai-act",
                        "content": "The EU AI Act establishes...",
                        "source": "European Commission",
                        "region": "EU"
                    }
                ],
                "extracted_clauses": [
                    {
                        "clause_text": "High-risk AI systems must undergo conformity assessment",
                        "clause_type": "requirement",
                        "topic": "safety_assessment",
                        "jurisdiction": "EU",
                        "document_source": "EU AI Act"
                    }
                ],
                "comparisons": [
                    {
                        "topic": "safety_assessment",
                        "similarities": ["Both require some form of assessment"],
                        "differences": ["EU has mandatory assessment, US has voluntary"],
                        "gaps": ["US lacks comprehensive safety framework"],
                        "jurisdictions_compared": ["EU", "US"]
                    }
                ],
                "summary": {
                    "executive_summary": "The EU has more comprehensive AI safety regulations...",
                    "key_findings": ["EU has stricter requirements", "US takes voluntary approach"],
                    "recommendations": ["US should consider mandatory safety assessments"]
                }
            }
        } 