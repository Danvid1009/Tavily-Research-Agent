import asyncio
import logging
import json
from typing import List, Dict, Any, Set
import httpx
from collections import defaultdict
from ..models.response import ExtractedClause, Comparison
from ..config import settings

logger = logging.getLogger(__name__)

class CompareAgent:
    """Agent responsible for comparing extracted clauses across jurisdictions."""
    
    def __init__(self):
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"
        self.model = settings.ollama_model
        self.batch_size = settings.comparison_batch_size
    
    async def compare_clauses(self, clauses: List[ExtractedClause]) -> List[Comparison]:
        """
        Compare extracted clauses across different jurisdictions.
        
        Args:
            clauses: List of extracted clauses from different jurisdictions
            
        Returns:
            List of comparison results
        """
        try:
            logger.info(f"Starting clause comparison for {len(clauses)} clauses")
            
            # Group clauses by topic and jurisdiction
            grouped_clauses = self._group_clauses(clauses)
            
            # Generate comparisons for each topic
            comparisons = []
            for topic, jurisdiction_clauses in grouped_clauses.items():
                if len(jurisdiction_clauses) > 1:  # Only compare if we have multiple jurisdictions
                    comparison = await self._compare_topic(topic, jurisdiction_clauses)
                    if comparison:
                        comparisons.append(comparison)
            
            logger.info(f"Generated {len(comparisons)} comparisons")
            return comparisons
            
        except Exception as e:
            logger.error(f"Error in compare agent: {e}")
            raise
    
    def _group_clauses(self, clauses: List[ExtractedClause]) -> Dict[str, Dict[str, List[ExtractedClause]]]:
        """Group clauses by topic and jurisdiction."""
        grouped = defaultdict(lambda: defaultdict(list))
        
        for clause in clauses:
            topic = clause.topic.lower()
            jurisdiction = clause.jurisdiction
            grouped[topic][jurisdiction].append(clause)
        
        return grouped
    
    async def _compare_topic(self, topic: str, jurisdiction_clauses: Dict[str, List[ExtractedClause]]) -> Comparison:
        """Compare clauses for a specific topic across jurisdictions."""
        try:
            # Prepare the comparison prompt
            prompt = self._create_comparison_prompt(topic, jurisdiction_clauses)
            
            # Get comparison from Ollama
            response = await self._call_ollama(prompt)
            
            # Parse the comparison result
            comparison = self._parse_comparison_response(response, topic, jurisdiction_clauses)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing topic {topic}: {e}")
            return None
    
    def _create_comparison_prompt(self, topic: str, jurisdiction_clauses: Dict[str, List[ExtractedClause]]) -> str:
        """Create a prompt for comparing clauses across jurisdictions."""
        
        # Build the context with clauses from each jurisdiction
        context_parts = []
        for jurisdiction, clauses in jurisdiction_clauses.items():
            jurisdiction_text = f"\n=== {jurisdiction} ===\n"
            for i, clause in enumerate(clauses[:3]):  # Limit to top 3 clauses per jurisdiction
                jurisdiction_text += f"{i+1}. {clause.clause_text}\n"
            context_parts.append(jurisdiction_text)
        
        context = "".join(context_parts)
        jurisdictions = list(jurisdiction_clauses.keys())
        
        prompt = f"""
You are a legal expert specializing in comparative AI policy analysis. Your task is to compare AI policy clauses across different jurisdictions for the topic: {topic}.

Context - Clauses from different jurisdictions:
{context}

Please analyze the similarities, differences, and regulatory gaps between these jurisdictions for the topic of {topic}.

Consider:
1. Similarities in approach, requirements, or principles
2. Key differences in regulatory approach, stringency, or scope
3. Regulatory gaps where one jurisdiction has requirements that others lack
4. Implications of these differences for AI development and deployment

Format your response as JSON with the following structure:
{{
  "similarities": [
    "Similarity 1 description",
    "Similarity 2 description"
  ],
  "differences": [
    "Difference 1 description",
    "Difference 2 description"
  ],
  "gaps": [
    "Gap 1 description",
    "Gap 2 description"
  ],
  "comparison_score": 0.75
}}

The comparison_score should be a number between 0 and 1 indicating how similar the approaches are (1 = very similar, 0 = very different).

Focus on actionable insights that policymakers can use to understand regulatory differences.
"""
        return prompt
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to get comparison results."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Moderate temperature for balanced analysis
                        "top_p": 0.9,
                        "num_predict": 2048
                    }
                }
                
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    def _parse_comparison_response(self, response: str, topic: str, 
                                 jurisdiction_clauses: Dict[str, List[ExtractedClause]]) -> Comparison:
        """Parse the Ollama response into a Comparison object."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON object found in comparison response for topic {topic}")
                return self._create_fallback_comparison(topic, jurisdiction_clauses)
            
            json_str = response[json_start:json_end]
            comparison_data = json.loads(json_str)
            
            comparison = Comparison(
                topic=topic,
                similarities=comparison_data.get("similarities", []),
                differences=comparison_data.get("differences", []),
                gaps=comparison_data.get("gaps", []),
                jurisdictions_compared=list(jurisdiction_clauses.keys()),
                comparison_score=comparison_data.get("comparison_score", 0.5)
            )
            
            return comparison
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON comparison response for topic {topic}: {e}")
            return self._create_fallback_comparison(topic, jurisdiction_clauses)
    
    def _create_fallback_comparison(self, topic: str, 
                                  jurisdiction_clauses: Dict[str, List[ExtractedClause]]) -> Comparison:
        """Create a fallback comparison when parsing fails."""
        jurisdictions = list(jurisdiction_clauses.keys())
        
        # Simple fallback analysis
        similarities = [f"All jurisdictions have some form of {topic} regulation"]
        differences = [f"Different jurisdictions approach {topic} with varying levels of detail"]
        gaps = [f"Some jurisdictions may lack comprehensive {topic} frameworks"]
        
        return Comparison(
            topic=topic,
            similarities=similarities,
            differences=differences,
            gaps=gaps,
            jurisdictions_compared=jurisdictions,
            comparison_score=0.5
        )
    
    async def calculate_similarity_scores(self, clauses: List[ExtractedClause]) -> Dict[str, float]:
        """Calculate similarity scores between jurisdictions based on clause overlap."""
        jurisdiction_clauses = defaultdict(list)
        
        # Group clauses by jurisdiction
        for clause in clauses:
            jurisdiction_clauses[clause.jurisdiction].append(clause)
        
        jurisdictions = list(jurisdiction_clauses.keys())
        similarity_scores = {}
        
        # Calculate pairwise similarities
        for i, j1 in enumerate(jurisdictions):
            for j2 in jurisdictions[i+1:]:
                score = self._calculate_jurisdiction_similarity(
                    jurisdiction_clauses[j1], 
                    jurisdiction_clauses[j2]
                )
                similarity_scores[f"{j1}_vs_{j2}"] = score
        
        return similarity_scores
    
    def _calculate_jurisdiction_similarity(self, clauses1: List[ExtractedClause], 
                                         clauses2: List[ExtractedClause]) -> float:
        """Calculate similarity between two jurisdictions based on clause topics and types."""
        if not clauses1 or not clauses2:
            return 0.0
        
        # Extract topics and types from clauses
        topics1 = set(clause.topic.lower() for clause in clauses1)
        topics2 = set(clause.topic.lower() for clause in clauses2)
        
        types1 = set(clause.clause_type.lower() for clause in clauses1)
        types2 = set(clause.clause_type.lower() for clause in clauses2)
        
        # Calculate Jaccard similarity for topics and types
        topic_similarity = len(topics1 & topics2) / len(topics1 | topics2) if topics1 | topics2 else 0
        type_similarity = len(types1 & types2) / len(types1 | types2) if types1 | types2 else 0
        
        # Weighted average
        return (topic_similarity * 0.7) + (type_similarity * 0.3)
    
    async def identify_regulatory_gaps(self, clauses: List[ExtractedClause]) -> List[str]:
        """Identify regulatory gaps by finding topics covered in some jurisdictions but not others."""
        jurisdiction_topics = defaultdict(set)
        
        # Collect topics by jurisdiction
        for clause in clauses:
            jurisdiction_topics[clause.jurisdiction].add(clause.topic.lower())
        
        all_topics = set()
        for topics in jurisdiction_topics.values():
            all_topics.update(topics)
        
        gaps = []
        jurisdictions = list(jurisdiction_topics.keys())
        
        # Find topics that are missing in some jurisdictions
        for topic in all_topics:
            jurisdictions_with_topic = [
                j for j in jurisdictions 
                if topic in jurisdiction_topics[j]
            ]
            
            if len(jurisdictions_with_topic) < len(jurisdictions):
                missing_jurisdictions = [
                    j for j in jurisdictions 
                    if j not in jurisdictions_with_topic
                ]
                gaps.append(f"Topic '{topic}' is missing in jurisdictions: {', '.join(missing_jurisdictions)}")
        
        return gaps 