import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from bson import ObjectId
from datetime import datetime

from ..models.query import ResearchQuery, ResearchQueryDB, QueryStatus
from ..models.response import ResearchResult
from ..workflow.research_workflow import ResearchWorkflow
from ..database import database

logger = logging.getLogger(__name__)

router = APIRouter()
workflow = ResearchWorkflow()

@router.post("/research", response_model=dict)
async def submit_research_query(
    query: ResearchQuery,
    background_tasks: BackgroundTasks
):
    """
    Submit a new research query for processing.
    
    The query will be processed asynchronously using the 4-agent workflow:
    1. Search Agent - Find relevant documents
    2. Extract Agent - Extract legal clauses
    3. Compare Agent - Compare across jurisdictions
    4. Summarize Agent - Generate summary and recommendations
    """
    try:
        # Create database record
        db_query = ResearchQueryDB(**query.dict())
        
        # Save to database
        collection = database.get_collection("research_queries")
        result = await collection.insert_one(db_query.dict(by_alias=True))
        db_query.id = str(result.inserted_id)
        
        # Start background processing
        background_tasks.add_task(process_research_query, db_query.id, query)
        
        return {
            "message": "Research query submitted successfully",
            "query_id": db_query.id,
            "status": "processing",
            "estimated_completion": "5-10 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error submitting research query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/{query_id}", response_model=ResearchResult)
async def get_research_result(query_id: str):
    """Get the results of a completed research query."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(query_id):
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        # Get research result from database
        collection = database.get_collection("research_results")
        result = await collection.find_one({"_id": ObjectId(query_id)})
        
        if not result:
            raise HTTPException(status_code=404, detail="Research result not found")
        
        # Convert ObjectId to string
        result["_id"] = str(result["_id"])
        
        return ResearchResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting research result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/{query_id}/status", response_model=dict)
async def get_research_status(query_id: str):
    """Get the current status and progress of a research query."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(query_id):
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        # Get query status from database
        collection = database.get_collection("research_queries")
        query = await collection.find_one({"_id": ObjectId(query_id)})
        
        if not query:
            raise HTTPException(status_code=404, detail="Research query not found")
        
        return {
            "query_id": query_id,
            "status": query.get("status", "unknown"),
            "progress": query.get("progress", {}),
            "created_at": query.get("created_at"),
            "updated_at": query.get("updated_at"),
            "error_message": query.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting research status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research", response_model=List[dict])
async def list_research_queries(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[QueryStatus] = Query(default=None)
):
    """List all research queries with optional filtering."""
    try:
        collection = database.get_collection("research_queries")
        
        # Build filter
        filter_query = {}
        if status:
            filter_query["status"] = status
        
        # Get queries
        cursor = collection.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
        queries = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for query in queries:
            query["_id"] = str(query["_id"])
        
        return queries
        
    except Exception as e:
        logger.error(f"Error listing research queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/research/{query_id}")
async def delete_research_query(query_id: str):
    """Delete a research query and its results."""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(query_id):
            raise HTTPException(status_code=400, detail="Invalid query ID")
        
        # Delete from both collections
        queries_collection = database.get_collection("research_queries")
        results_collection = database.get_collection("research_results")
        
        # Check if query exists
        query = await queries_collection.find_one({"_id": ObjectId(query_id)})
        if not query:
            raise HTTPException(status_code=404, detail="Research query not found")
        
        # Delete query and result
        await queries_collection.delete_one({"_id": ObjectId(query_id)})
        await results_collection.delete_one({"_id": ObjectId(query_id)})
        
        return {"message": "Research query deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting research query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/{query_id}/export")
async def export_research_result(query_id: str, format: str = Query(default="json", regex="^(json|markdown)$")):
    """Export research results in different formats."""
    try:
        # Get research result
        collection = database.get_collection("research_results")
        result = await collection.find_one({"_id": ObjectId(query_id)})
        
        if not result:
            raise HTTPException(status_code=404, detail="Research result not found")
        
        # Convert ObjectId to string
        result["_id"] = str(result["_id"])
        research_result = ResearchResult(**result)
        
        if format == "json":
            return research_result.dict()
        elif format == "markdown":
            return generate_markdown_report(research_result)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting research result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_research_query(query_id: str, query: ResearchQuery):
    """Background task to process a research query using the workflow."""
    try:
        logger.info(f"Starting background processing for query {query_id}")
        
        # Update status to processing
        collection = database.get_collection("research_queries")
        await collection.update_one(
            {"_id": ObjectId(query_id)},
            {
                "$set": {
                    "status": QueryStatus.SEARCHING,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Run the research workflow
        result = await workflow.run_research(query)
        
        # Save result to database
        results_collection = database.get_collection("research_results")
        result_dict = result.dict()
        result_dict["_id"] = ObjectId(query_id)
        await results_collection.insert_one(result_dict)
        
        # Update query status to completed
        await collection.update_one(
            {"_id": ObjectId(query_id)},
            {
                "$set": {
                    "status": QueryStatus.COMPLETED,
                    "updated_at": datetime.utcnow(),
                    "progress": {
                        "search_agent": 1.0,
                        "extract_agent": 1.0,
                        "compare_agent": 1.0,
                        "summarize_agent": 1.0
                    }
                }
            }
        )
        
        logger.info(f"Background processing completed for query {query_id}")
        
    except Exception as e:
        logger.error(f"Error in background processing for query {query_id}: {e}")
        
        # Update status to failed
        try:
            collection = database.get_collection("research_queries")
            await collection.update_one(
                {"_id": ObjectId(query_id)},
                {
                    "$set": {
                        "status": QueryStatus.FAILED,
                        "error_message": str(e),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as update_error:
            logger.error(f"Error updating failed status: {update_error}")

def generate_markdown_report(result: ResearchResult) -> str:
    """Generate a markdown report from research results."""
    markdown = f"""# AI Policy Research Report

## Query
{result.query}

## Executive Summary
{result.summary.executive_summary}

## Key Findings
"""
    
    for i, finding in enumerate(result.summary.key_findings, 1):
        markdown += f"{i}. {finding}\n"
    
    markdown += "\n## Policy Recommendations\n"
    for i, recommendation in enumerate(result.summary.recommendations, 1):
        markdown += f"{i}. {recommendation}\n"
    
    markdown += f"\n## Documents Analyzed\n"
    for doc in result.documents:
        markdown += f"- **{doc.title}** ({doc.source}) - {doc.region}\n"
    
    markdown += f"\n## Extracted Clauses\n"
    for clause in result.extracted_clauses:
        markdown += f"- **{clause.topic.title()}** ({clause.jurisdiction}): {clause.clause_text[:200]}...\n"
    
    markdown += f"\n## Comparative Analysis\n"
    for comparison in result.comparisons:
        markdown += f"\n### {comparison.topic.title()}\n"
        markdown += f"Jurisdictions: {', '.join(comparison.jurisdictions_compared)}\n"
        markdown += f"Similarity Score: {comparison.comparison_score:.2f}\n"
        
        if comparison.similarities:
            markdown += "\n**Similarities:**\n"
            for similarity in comparison.similarities:
                markdown += f"- {similarity}\n"
        
        if comparison.differences:
            markdown += "\n**Differences:**\n"
            for difference in comparison.differences:
                markdown += f"- {difference}\n"
        
        if comparison.gaps:
            markdown += "\n**Regulatory Gaps:**\n"
            for gap in comparison.gaps:
                markdown += f"- {gap}\n"
    
    markdown += f"\n## Methodology\n{result.summary.methodology}\n"
    
    if result.summary.limitations:
        markdown += "\n## Limitations\n"
        for limitation in result.summary.limitations:
            markdown += f"- {limitation}\n"
    
    markdown += f"\n---\n*Report generated on {result.completed_at}*"
    
    return markdown 