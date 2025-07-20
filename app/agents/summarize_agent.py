import asyncio
import logging
import json
from typing import List, Dict, Any
import httpx
from ..models.response import Document, ExtractedClause, Comparison, Summary
from ..config import settings

logger = logging.getLogger(__name__)

class SummarizeAgent:
    """Agent responsible for generating executive summaries and recommendations."""
    
    def __init__(self):
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"
        self.model = settings.ollama_model
    
    async def generate_summary(self, query: str, documents: List[Document], 
                             clauses: List[ExtractedClause], 
                             comparisons: List[Comparison]) -> Summary:
        """
        Generate a comprehensive executive summary and recommendations.
        
        Args:
            query: Original research query
            documents: Documents analyzed
            clauses: Extracted clauses
            comparisons: Comparison results
            
        Returns:
            Summary object with executive summary and recommendations
        """
        try:
            logger.info("Starting summary generation")
            
            # Prepare the summary prompt
            prompt = self._create_summary_prompt(query, documents, clauses, comparisons)
            
            # Get summary from Ollama
            response = await self._call_ollama(prompt)
            
            # Parse the summary response
            summary = self._parse_summary_response(response, query, documents, clauses, comparisons)
            
            logger.info("Summary generation completed")
            return summary
            
        except Exception as e:
            logger.error(f"Error in summarize agent: {e}")
            raise
    
    def _create_summary_prompt(self, query: str, documents: List[Document], 
                             clauses: List[ExtractedClause], 
                             comparisons: List[Comparison]) -> str:
        """Create a comprehensive prompt for summary generation."""
        
        # Prepare document summary
        doc_summary = self._summarize_documents(documents)
        
        # Prepare clause summary
        clause_summary = self._summarize_clauses(clauses)
        
        # Prepare comparison summary
        comparison_summary = self._summarize_comparisons(comparisons)
        
        prompt = f"""
You are a senior policy analyst specializing in AI regulation. Your task is to create a comprehensive executive summary and policy recommendations based on the following research:

ORIGINAL QUERY: {query}

RESEARCH CONTEXT:
{doc_summary}

KEY FINDINGS FROM DOCUMENTS:
{clause_summary}

COMPARATIVE ANALYSIS:
{comparison_summary}

Please provide a comprehensive analysis in the following JSON format:

{{
  "executive_summary": "A 2-3 paragraph executive summary highlighting the most important findings and implications",
  "key_findings": [
    "Finding 1: Description of a key insight",
    "Finding 2: Description of another key insight",
    "Finding 3: Description of a third key insight"
  ],
  "recommendations": [
    "Recommendation 1: Specific, actionable policy recommendation",
    "Recommendation 2: Another specific recommendation",
    "Recommendation 3: A third recommendation"
  ],
  "methodology": "Brief description of the research methodology used",
  "limitations": [
    "Limitation 1: Description of research limitation",
    "Limitation 2: Another limitation"
  ]
}}

Guidelines:
- The executive summary should be accessible to policymakers and executives
- Key findings should highlight the most significant regulatory differences and similarities
- Recommendations should be specific, actionable, and evidence-based
- Focus on practical implications for AI development and deployment
- Consider both immediate and long-term policy implications
- Acknowledge limitations and uncertainties in the analysis

Make the summary professional, balanced, and useful for decision-making.
"""
        return prompt
    
    def _summarize_documents(self, documents: List[Document]) -> str:
        """Create a summary of the documents analyzed."""
        if not documents:
            return "No documents were analyzed."
        
        summary = f"Analyzed {len(documents)} documents from the following sources:\n"
        
        # Group by region
        regions = {}
        for doc in documents:
            region = doc.region or "Unknown"
            if region not in regions:
                regions[region] = []
            regions[region].append(doc)
        
        for region, docs in regions.items():
            summary += f"\n{region} ({len(docs)} documents):\n"
            for doc in docs[:3]:  # Show top 3 per region
                summary += f"- {doc.title} ({doc.source})\n"
            if len(docs) > 3:
                summary += f"- ... and {len(docs) - 3} more\n"
        
        return summary
    
    def _summarize_clauses(self, clauses: List[ExtractedClause]) -> str:
        """Create a summary of the extracted clauses."""
        if not clauses:
            return "No legal clauses were extracted."
        
        summary = f"Extracted {len(clauses)} legal clauses across the following topics:\n"
        
        # Group by topic
        topics = {}
        for clause in clauses:
            topic = clause.topic
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(clause)
        
        for topic, topic_clauses in topics.items():
            summary += f"\n{topic.title()} ({len(topic_clauses)} clauses):\n"
            for clause in topic_clauses[:2]:  # Show top 2 per topic
                summary += f"- {clause.clause_text[:100]}...\n"
            if len(topic_clauses) > 2:
                summary += f"- ... and {len(topic_clauses) - 2} more\n"
        
        return summary
    
    def _summarize_comparisons(self, comparisons: List[Comparison]) -> str:
        """Create a summary of the comparison results."""
        if not comparisons:
            return "No comparative analysis was performed."
        
        summary = f"Comparative analysis across {len(comparisons)} topics:\n"
        
        for comparison in comparisons:
            summary += f"\n{comparison.topic.title()}:\n"
            summary += f"- Jurisdictions compared: {', '.join(comparison.jurisdictions_compared)}\n"
            summary += f"- Similarity score: {comparison.comparison_score:.2f}\n"
            
            if comparison.similarities:
                summary += f"- Key similarities: {len(comparison.similarities)} found\n"
            if comparison.differences:
                summary += f"- Key differences: {len(comparison.differences)} found\n"
            if comparison.gaps:
                summary += f"- Regulatory gaps: {len(comparison.gaps)} identified\n"
        
        return summary
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to get summary results."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for summary
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for consistent summaries
                        "top_p": 0.9,
                        "num_predict": 4096  # Longer response for comprehensive summary
                    }
                }
                
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    def _parse_summary_response(self, response: str, query: str, documents: List[Document], 
                              clauses: List[ExtractedClause], 
                              comparisons: List[Comparison]) -> Summary:
        """Parse the Ollama response into a Summary object."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON object found in summary response")
                return self._create_fallback_summary(query, documents, clauses, comparisons)
            
            json_str = response[json_start:json_end]
            summary_data = json.loads(json_str)
            
            summary = Summary(
                executive_summary=summary_data.get("executive_summary", ""),
                key_findings=summary_data.get("key_findings", []),
                recommendations=summary_data.get("recommendations", []),
                methodology=summary_data.get("methodology", ""),
                limitations=summary_data.get("limitations", [])
            )
            
            return summary
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON summary response: {e}")
            return self._create_fallback_summary(query, documents, clauses, comparisons)
    
    def _create_fallback_summary(self, query: str, documents: List[Document], 
                               clauses: List[ExtractedClause], 
                               comparisons: List[Comparison]) -> Summary:
        """Create a fallback summary when parsing fails."""
        
        # Basic executive summary
        executive_summary = f"""
This research analyzed AI policy documents in response to the query: "{query}". 
The analysis covered {len(documents)} documents and extracted {len(clauses)} legal clauses 
across {len(comparisons)} comparative topics. The research provides insights into 
regulatory approaches across different jurisdictions and identifies key policy differences.
"""
        
        # Basic key findings
        key_findings = [
            f"Analyzed {len(documents)} policy documents from multiple jurisdictions",
            f"Extracted {len(clauses)} legal clauses covering various regulatory topics",
            f"Identified {len(comparisons)} key areas of regulatory comparison"
        ]
        
        # Basic recommendations
        recommendations = [
            "Consider harmonizing regulatory approaches across jurisdictions",
            "Address identified regulatory gaps in policy frameworks",
            "Monitor emerging AI policy developments in key jurisdictions"
        ]
        
        # Basic methodology
        methodology = """
This research used a multi-agent AI system to:
1. Search for relevant AI policy documents using the Tavily API
2. Extract key legal clauses using local LLM analysis
3. Compare regulatory approaches across jurisdictions
4. Generate policy recommendations based on the analysis
"""
        
        # Basic limitations
        limitations = [
            "Analysis limited to publicly available documents",
            "Language barriers may affect document coverage",
            "Rapidly evolving nature of AI policy may affect currency of findings"
        ]
        
        return Summary(
            executive_summary=executive_summary.strip(),
            key_findings=key_findings,
            recommendations=recommendations,
            methodology=methodology.strip(),
            limitations=limitations
        )
    
    async def generate_policy_brief(self, summary: Summary) -> str:
        """Generate a formatted policy brief from the summary."""
        brief = f"""
# AI Policy Research Brief

## Executive Summary
{summary.executive_summary}

## Key Findings
"""
        
        for i, finding in enumerate(summary.key_findings, 1):
            brief += f"{i}. {finding}\n"
        
        brief += "\n## Policy Recommendations\n"
        for i, recommendation in enumerate(summary.recommendations, 1):
            brief += f"{i}. {recommendation}\n"
        
        brief += f"\n## Methodology\n{summary.methodology}\n"
        
        if summary.limitations:
            brief += "\n## Limitations\n"
            for limitation in summary.limitations:
                brief += f"- {limitation}\n"
        
        return brief 