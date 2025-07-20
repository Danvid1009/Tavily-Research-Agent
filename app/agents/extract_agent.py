import asyncio
import logging
import json
from typing import List, Dict, Any
import httpx
from ..models.response import Document, ExtractedClause
from ..config import settings

logger = logging.getLogger(__name__)

class ExtractAgent:
    """Agent responsible for extracting key legal clauses from documents using Ollama."""
    
    def __init__(self):
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"
        self.model = settings.ollama_model
        self.max_length = settings.max_extraction_length
    
    async def extract_clauses(self, documents: List[Document]) -> List[ExtractedClause]:
        """
        Extract key legal clauses from documents using Ollama.
        
        Args:
            documents: List of documents to extract clauses from
            
        Returns:
            List of extracted clauses
        """
        try:
            logger.info(f"Starting clause extraction from {len(documents)} documents")
            
            all_clauses = []
            
            # Process documents in batches to avoid overwhelming the LLM
            for i, document in enumerate(documents):
                logger.info(f"Processing document {i+1}/{len(documents)}: {document.title}")
                
                # Extract clauses from this document
                document_clauses = await self._extract_from_document(document)
                all_clauses.extend(document_clauses)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"Extracted {len(all_clauses)} clauses total")
            return all_clauses
            
        except Exception as e:
            logger.error(f"Error in extract agent: {e}")
            raise
    
    async def _extract_from_document(self, document: Document) -> List[ExtractedClause]:
        """Extract clauses from a single document."""
        try:
            # Prepare the prompt for clause extraction
            prompt = self._create_extraction_prompt(document)
            
            # Get response from Ollama
            response = await self._call_ollama(prompt)
            
            # Parse the response
            clauses = self._parse_extraction_response(response, document)
            
            return clauses
            
        except Exception as e:
            logger.error(f"Error extracting from document {document.title}: {e}")
            return []
    
    def _create_extraction_prompt(self, document: Document) -> str:
        """Create a prompt for clause extraction."""
        prompt = f"""
You are a legal expert specializing in AI policy analysis. Your task is to extract key legal clauses from the following document.

Document Title: {document.title}
Source: {document.source}
Region: {document.region or 'Unknown'}

Document Content:
{document.content[:self.max_length]}

Please extract the most important legal clauses, requirements, prohibitions, definitions, and regulatory provisions from this document. For each clause, provide:

1. The exact clause text
2. The type of clause (requirement, prohibition, definition, enforcement, etc.)
3. The topic or category it belongs to (safety, privacy, transparency, etc.)
4. Key entities mentioned (organizations, systems, etc.)

Focus on clauses that are:
- Legally binding or regulatory in nature
- Specific and actionable
- Related to AI system requirements or restrictions
- Important for compliance or enforcement

Format your response as a JSON array with the following structure:
[
  {{
    "clause_text": "exact text of the clause",
    "clause_type": "requirement|prohibition|definition|enforcement|other",
    "topic": "safety|privacy|transparency|accountability|governance|other",
    "key_entities": ["entity1", "entity2"],
    "confidence": 0.95
  }}
]

Only include clauses that are clearly stated in the document. If no relevant clauses are found, return an empty array [].
"""
        return prompt
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to get extraction results."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extraction
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
    
    def _parse_extraction_response(self, response: str, document: Document) -> List[ExtractedClause]:
        """Parse the Ollama response into ExtractedClause objects."""
        clauses = []
        
        try:
            # Try to extract JSON from the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON array found in response for document {document.title}")
                return clauses
            
            json_str = response[json_start:json_end]
            extracted_data = json.loads(json_str)
            
            for item in extracted_data:
                try:
                    clause = ExtractedClause(
                        clause_text=item.get("clause_text", ""),
                        clause_type=item.get("clause_type", "other"),
                        topic=item.get("topic", "other"),
                        jurisdiction=document.region or "Unknown",
                        document_source=document.title,
                        confidence_score=item.get("confidence", 0.8),
                        key_entities=item.get("key_entities", [])
                    )
                    
                    # Only include clauses with sufficient content
                    if len(clause.clause_text.strip()) > 10:
                        clauses.append(clause)
                        
                except Exception as e:
                    logger.warning(f"Error parsing clause item: {e}")
                    continue
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response for document {document.title}: {e}")
            # Fallback: try to extract clauses using simple text parsing
            clauses = self._fallback_extraction(response, document)
        
        return clauses
    
    def _fallback_extraction(self, response: str, document: Document) -> List[ExtractedClause]:
        """Fallback method for extracting clauses when JSON parsing fails."""
        clauses = []
        
        # Simple pattern matching for clause extraction
        lines = response.split('\n')
        current_clause = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('"clause_text"') or line.startswith('clause_text'):
                # Extract clause text
                text_start = line.find('"', line.find('"') + 1) + 1
                text_end = line.rfind('"')
                if text_start > 0 and text_end > text_start:
                    current_clause = line[text_start:text_end]
                    
                    # Create a basic clause object
                    if len(current_clause) > 10:
                        clause = ExtractedClause(
                            clause_text=current_clause,
                            clause_type="requirement",  # Default type
                            topic="general",  # Default topic
                            jurisdiction=document.region or "Unknown",
                            document_source=document.title,
                            confidence_score=0.6  # Lower confidence for fallback
                        )
                        clauses.append(clause)
        
        return clauses
    
    async def validate_clauses(self, clauses: List[ExtractedClause]) -> List[ExtractedClause]:
        """Validate and filter extracted clauses for quality."""
        validated_clauses = []
        
        for clause in clauses:
            # Basic validation checks
            if (len(clause.clause_text.strip()) > 20 and 
                clause.confidence_score and clause.confidence_score > 0.5):
                validated_clauses.append(clause)
        
        logger.info(f"Validated {len(validated_clauses)} out of {len(clauses)} clauses")
        return validated_clauses 