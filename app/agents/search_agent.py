import asyncio
import logging
from typing import List, Dict, Any
from tavily import TavilyClient
from ..models.response import Document
from ..config import settings

logger = logging.getLogger(__name__)

class SearchAgent:
    """Agent responsible for searching and retrieving AI policy documents."""
    
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)
        self.max_results = settings.max_search_results
    
    async def search_documents(self, query: str, regions: List[str] = None, 
                             document_types: List[str] = None) -> List[Document]:
        """
        Search for AI policy documents using Tavily API.
        
        Args:
            query: The research query
            regions: Specific regions to focus on
            document_types: Types of documents to search for
            
        Returns:
            List of relevant documents
        """
        try:
            logger.info(f"Starting document search for query: {query}")
            
            # Build search query with region and document type filters
            search_query = self._build_search_query(query, regions, document_types)
            
            # Perform search with Tavily
            search_results = await self._perform_search(search_query)
            
            # Convert results to Document objects
            documents = await self._process_search_results(search_results, regions)
            
            logger.info(f"Found {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error in search agent: {e}")
            raise
    
    def _build_search_query(self, query: str, regions: List[str] = None, 
                           document_types: List[str] = None) -> str:
        """Build an optimized search query."""
        search_terms = [query]
        
        # Add region-specific terms
        if regions:
            region_terms = []
            for region in regions:
                if region.upper() == "EU":
                    region_terms.extend(["European Union", "EU", "European Commission"])
                elif region.upper() == "US":
                    region_terms.extend(["United States", "US", "USA", "federal"])
                elif region.upper() == "UK":
                    region_terms.extend(["United Kingdom", "UK", "British"])
                else:
                    region_terms.append(region)
            search_terms.extend(region_terms)
        
        # Add document type terms
        if document_types:
            type_terms = []
            for doc_type in document_types:
                if doc_type == "legislation":
                    type_terms.extend(["legislation", "law", "act", "regulation"])
                elif doc_type == "policy_framework":
                    type_terms.extend(["policy", "framework", "guidelines", "strategy"])
                elif doc_type == "white_paper":
                    type_terms.extend(["white paper", "whitepaper", "report"])
                else:
                    type_terms.append(doc_type)
            search_terms.extend(type_terms)
        
        # Add AI-specific terms
        ai_terms = ["artificial intelligence", "AI", "machine learning", "algorithm"]
        search_terms.extend(ai_terms)
        
        return " ".join(search_terms)
    
    async def _perform_search(self, search_query: str) -> List[Dict[str, Any]]:
        """Perform the actual search using Tavily API."""
        try:
            # Configure search parameters for academic and legal sources
            search_params = {
                "query": search_query,
                "search_depth": "advanced",
                "include_domains": [
                    "europa.eu", "ec.europa.eu", "whitehouse.gov", "congress.gov",
                    "gov.uk", "parliament.uk", "oecd.org", "un.org", "wto.org",
                    "academic.oup.com", "springer.com", "ieee.org", "arxiv.org"
                ],
                "exclude_domains": ["twitter.com", "facebook.com", "instagram.com"],
                "max_results": self.max_results,
                "include_answer": False,
                "include_raw_content": True,
                "include_images": False
            }
            
            # Perform search
            response = self.client.search(**search_params)
            
            if not response or "results" not in response:
                logger.warning("No search results returned from Tavily")
                return []
            
            return response["results"]
            
        except Exception as e:
            logger.error(f"Error performing Tavily search: {e}")
            raise
    
    async def _process_search_results(self, results: List[Dict[str, Any]], 
                                    regions: List[str] = None) -> List[Document]:
        """Process search results into Document objects."""
        documents = []
        
        for result in results:
            try:
                # Extract region from content or URL if not specified
                region = self._extract_region(result, regions)
                
                # Create Document object
                document = Document(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    content=result.get("content", ""),
                    source=result.get("source", "Unknown"),
                    region=region,
                    document_type=self._classify_document_type(result),
                    relevance_score=self._calculate_relevance_score(result)
                )
                
                documents.append(document)
                
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue
        
        # Sort by relevance score
        documents.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        return documents
    
    def _extract_region(self, result: Dict[str, Any], regions: List[str] = None) -> str:
        """Extract region information from search result."""
        if regions and len(regions) == 1:
            return regions[0]
        
        content = result.get("content", "").lower()
        url = result.get("url", "").lower()
        
        # Check for region indicators in content and URL
        if any(term in content or term in url for term in ["european union", "eu", "europa"]):
            return "EU"
        elif any(term in content or term in url for term in ["united states", "us", "usa", "federal"]):
            return "US"
        elif any(term in content or term in url for term in ["united kingdom", "uk", "british"]):
            return "UK"
        
        return "Global" if regions is None else regions[0] if regions else "Unknown"
    
    def _classify_document_type(self, result: Dict[str, Any]) -> str:
        """Classify the type of document based on content and source."""
        content = result.get("content", "").lower()
        url = result.get("url", "").lower()
        
        if any(term in content or term in url for term in ["act", "regulation", "law", "legislation"]):
            return "legislation"
        elif any(term in content or term in url for term in ["policy", "framework", "guidelines"]):
            return "policy_framework"
        elif any(term in content or term in url for term in ["white paper", "whitepaper", "report"]):
            return "white_paper"
        else:
            return "other"
    
    def _calculate_relevance_score(self, result: Dict[str, Any]) -> float:
        """Calculate a relevance score for the document."""
        score = 0.0
        
        # Base score from Tavily (if available)
        if "score" in result:
            score += float(result["score"]) * 0.5
        
        # Boost for official sources
        url = result.get("url", "").lower()
        if any(domain in url for domain in ["europa.eu", "whitehouse.gov", "gov.uk"]):
            score += 0.3
        
        # Boost for recent documents
        if "published_date" in result:
            score += 0.1
        
        # Boost for comprehensive content
        content_length = len(result.get("content", ""))
        if content_length > 1000:
            score += 0.1
        
        return min(score, 1.0) 