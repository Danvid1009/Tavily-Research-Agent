import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..agents import SearchAgent, ExtractAgent, CompareAgent, SummarizeAgent
from ..models.query import ResearchQuery, QueryStatus
from ..models.response import Document, ExtractedClause, Comparison, Summary, ResearchResult

logger = logging.getLogger(__name__)

class ResearchWorkflow:
    """LangGraph workflow for orchestrating the 4-agent research process."""
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.extract_agent = ExtractAgent()
        self.compare_agent = CompareAgent()
        self.summarize_agent = SummarizeAgent()
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        
        # Define the state structure
        workflow = StateGraph({
            "query": str,
            "regions": List[str],
            "document_types": List[str],
            "max_documents": int,
            "status": str,
            "progress": Dict[str, float],
            "documents": List[Document],
            "clauses": List[ExtractedClause],
            "comparisons": List[Comparison],
            "summary": Summary,
            "result": ResearchResult,
            "error": str
        })
        
        # Add nodes for each agent
        workflow.add_node("search", self._search_node)
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("compare", self._compare_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the workflow edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "extract")
        workflow.add_edge("extract", "compare")
        workflow.add_edge("compare", "summarize")
        workflow.add_edge("summarize", "finalize")
        workflow.add_edge("finalize", END)
        
        # Add conditional edges for error handling
        workflow.add_conditional_edges(
            "search",
            self._should_continue,
            {
                "continue": "extract",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "extract",
            self._should_continue,
            {
                "continue": "compare",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "compare",
            self._should_continue,
            {
                "continue": "summarize",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "summarize",
            self._should_continue,
            {
                "continue": "finalize",
                "error": END
            }
        )
        
        # Compile the workflow
        return workflow.compile(checkpointer=MemorySaver())
    
    async def _search_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search agent node."""
        try:
            logger.info("Starting search phase")
            
            # Update status and progress
            state["status"] = QueryStatus.SEARCHING
            state["progress"]["search_agent"] = 0.0
            
            # Perform search
            documents = await self.search_agent.search_documents(
                query=state["query"],
                regions=state.get("regions"),
                document_types=state.get("document_types")
            )
            
            # Limit documents if specified
            if state.get("max_documents"):
                documents = documents[:state["max_documents"]]
            
            # Update state
            state["documents"] = documents
            state["progress"]["search_agent"] = 1.0
            
            logger.info(f"Search completed: found {len(documents)} documents")
            return state
            
        except Exception as e:
            logger.error(f"Error in search node: {e}")
            state["error"] = f"Search failed: {str(e)}"
            state["status"] = QueryStatus.FAILED
            return state
    
    async def _extract_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract agent node."""
        try:
            logger.info("Starting extraction phase")
            
            # Update status and progress
            state["status"] = QueryStatus.EXTRACTING
            state["progress"]["extract_agent"] = 0.0
            
            # Extract clauses from documents
            clauses = await self.extract_agent.extract_clauses(state["documents"])
            
            # Validate clauses
            validated_clauses = await self.extract_agent.validate_clauses(clauses)
            
            # Update state
            state["clauses"] = validated_clauses
            state["progress"]["extract_agent"] = 1.0
            
            logger.info(f"Extraction completed: extracted {len(validated_clauses)} clauses")
            return state
            
        except Exception as e:
            logger.error(f"Error in extract node: {e}")
            state["error"] = f"Extraction failed: {str(e)}"
            state["status"] = QueryStatus.FAILED
            return state
    
    async def _compare_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare agent node."""
        try:
            logger.info("Starting comparison phase")
            
            # Update status and progress
            state["status"] = QueryStatus.COMPARING
            state["progress"]["compare_agent"] = 0.0
            
            # Compare clauses across jurisdictions
            comparisons = await self.compare_agent.compare_clauses(state["clauses"])
            
            # Update state
            state["comparisons"] = comparisons
            state["progress"]["compare_agent"] = 1.0
            
            logger.info(f"Comparison completed: generated {len(comparisons)} comparisons")
            return state
            
        except Exception as e:
            logger.error(f"Error in compare node: {e}")
            state["error"] = f"Comparison failed: {str(e)}"
            state["status"] = QueryStatus.FAILED
            return state
    
    async def _summarize_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize agent node."""
        try:
            logger.info("Starting summarization phase")
            
            # Update status and progress
            state["status"] = QueryStatus.SUMMARIZING
            state["progress"]["summarize_agent"] = 0.0
            
            # Generate summary
            summary = await self.summarize_agent.generate_summary(
                query=state["query"],
                documents=state["documents"],
                clauses=state["clauses"],
                comparisons=state["comparisons"]
            )
            
            # Update state
            state["summary"] = summary
            state["progress"]["summarize_agent"] = 1.0
            
            logger.info("Summarization completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in summarize node: {e}")
            state["error"] = f"Summarization failed: {str(e)}"
            state["status"] = QueryStatus.FAILED
            return state
    
    async def _finalize_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the research result."""
        try:
            logger.info("Finalizing research result")
            
            # Create the final research result
            result = ResearchResult(
                query=state["query"],
                documents=state["documents"],
                extracted_clauses=state["clauses"],
                comparisons=state["comparisons"],
                summary=state["summary"],
                metadata={
                    "regions": state.get("regions"),
                    "document_types": state.get("document_types"),
                    "max_documents": state.get("max_documents"),
                    "workflow_version": "1.0"
                },
                completed_at=datetime.utcnow()
            )
            
            # Update state
            state["result"] = result
            state["status"] = QueryStatus.COMPLETED
            
            logger.info("Research workflow completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in finalize node: {e}")
            state["error"] = f"Finalization failed: {str(e)}"
            state["status"] = QueryStatus.FAILED
            return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if the workflow should continue or end due to error."""
        if state.get("error"):
            return "error"
        return "continue"
    
    async def run_research(self, research_query: ResearchQuery, 
                          config: Dict[str, Any] = None) -> ResearchResult:
        """
        Run the complete research workflow.
        
        Args:
            research_query: The research query to process
            config: Optional configuration overrides
            
        Returns:
            ResearchResult object with complete analysis
        """
        try:
            logger.info(f"Starting research workflow for query: {research_query.query}")
            
            # Prepare initial state
            initial_state = {
                "query": research_query.query,
                "regions": research_query.regions or [],
                "document_types": research_query.document_types or [],
                "max_documents": research_query.max_documents or 10,
                "status": QueryStatus.PENDING,
                "progress": {
                    "search_agent": 0.0,
                    "extract_agent": 0.0,
                    "compare_agent": 0.0,
                    "summarize_agent": 0.0
                },
                "documents": [],
                "clauses": [],
                "comparisons": [],
                "summary": None,
                "result": None,
                "error": None
            }
            
            # Apply any configuration overrides
            if config:
                initial_state.update(config)
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("error"):
                raise Exception(f"Workflow failed: {final_state['error']}")
            
            # Return the result
            return final_state["result"]
            
        except Exception as e:
            logger.error(f"Research workflow failed: {e}")
            raise
    
    async def get_progress(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current progress of a running workflow."""
        try:
            # Get the current state from the workflow
            current_state = await self.workflow.aget_state(config)
            return {
                "status": current_state.get("status"),
                "progress": current_state.get("progress", {}),
                "error": current_state.get("error")
            }
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return {"status": "unknown", "progress": {}, "error": str(e)} 