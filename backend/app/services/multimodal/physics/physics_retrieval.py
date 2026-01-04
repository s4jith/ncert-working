"""
Physics Retrieval

Intelligent query parsing and retrieval for physics content.
"""

from pinecone import Pinecone
from typing import List, Dict, Optional
import logging
import os
import re

logger = logging.getLogger(__name__)


class PhysicsRetrieval:
    """Retrieve physics content with intelligent query parsing"""
    
    def __init__(
        self,
        embedder,
        api_key: str = None,
        index_name: str = "ncert-all-subjects"
    ):
        """Initialize retrieval system"""
        self.embedder = embedder
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name
        
        logger.info(f"🔍 Initializing Physics Retrieval...")
        
        # Connect to Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
        
        logger.info(f"✅ Physics Retrieval ready")
    
    def search(
        self,
        query: str,
        class_num: Optional[int] = None,
        top_k: int = 10,
        namespace: str = "physics"
    ) -> List[Dict]:
        """
        Search for physics content
        
        Args:
            query: Natural language query
            class_num: Filter by class (11 or 12)
            top_k: Number of results
            namespace: Pinecone namespace
        
        Returns:
            List of matched chunks with scores
        """
        logger.info(f"🔎 Searching: '{query}'")
        
        # Parse query to detect content types
        query_info = self._parse_query(query)
        logger.info(f"   Detected: {query_info['intent']}")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Build metadata filter
        metadata_filter = {'subject': 'physics'}
        
        if class_num:
            metadata_filter['class'] = class_num
        
        # Add content type filters based on query
        if query_info['content_types']:
            # If specific types detected, prioritize them
            # But don't strictly filter (allow semantic matches)
            pass
        
        # Search Pinecone
        try:
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k * 2,  # Get more, then re-rank
                namespace=namespace,
                filter=metadata_filter,
                include_metadata=True
            )
            
            matches = results.matches
            logger.info(f"   Found {len(matches)} matches")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        
        # Post-process and re-rank results
        processed_results = self._post_process_results(
            matches,
            query_info,
            top_k
        )
        
        return processed_results
    
    def _parse_query(self, query: str) -> Dict:
        """Parse query to detect intent and content types"""
        query_lower = query.lower()
        
        info = {
            'query': query,
            'intent': 'general',
            'content_types': [],
            'has_formula': False
        }
        
        # Detect content type requests
        if any(word in query_lower for word in ['formula', 'equation', 'expression']):
            info['content_types'].append('formula')
            info['intent'] = 'formula_search'
        
        if any(word in query_lower for word in ['law', 'principle', 'theorem']):
            info['content_types'].append('law')
            info['intent'] = 'law_search'
        
        if any(word in query_lower for word in ['derive', 'derivation', 'proof']):
            info['content_types'].append('derivation')
            info['intent'] = 'derivation_search'
        
        if any(word in query_lower for word in ['diagram', 'circuit', 'ray', 'figure']):
            info['content_types'].append('diagram')
            info['intent'] = 'diagram_search'
        
        if any(word in query_lower for word in ['solve', 'problem', 'numerical', 'calculate']):
            info['content_types'].extend(['numerical_question', 'solution_step'])
            info['intent'] = 'numerical_search'
        
        if any(word in query_lower for word in ['experiment', 'practical', 'activity']):
            info['content_types'].append('experiment')
            info['intent'] = 'experiment_search'
        
        if any(word in query_lower for word in ['table', 'data']):
            info['content_types'].append('table')
            info['intent'] = 'table_search'
        
        if any(word in query_lower for word in ['example', 'illustration']):
            info['content_types'].append('example')
            info['intent'] = 'example_search'
        
        # Detect physics formulas in query
        formula_patterns = [
            r'F\s*=\s*ma',
            r'V\s*=\s*IR',
            r'E\s*=\s*mc',
            r'PV\s*=\s*nRT',
            r'v\s*=\s*f',
            r'KE\s*=',
            r'PE\s*=',
        ]
        
        for pattern in formula_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                info['has_formula'] = True
                if 'formula' not in info['content_types']:
                    info['content_types'].append('formula')
                break
        
        # If no specific type, it's a concept search
        if not info['content_types']:
            info['content_types'].append('concept')
            info['intent'] = 'concept_search'
        
        return info
    
    def _post_process_results(
        self,
        matches: List,
        query_info: Dict,
        top_k: int
    ) -> List[Dict]:
        """Post-process and re-rank search results"""
        processed = []
        
        for match in matches:
            result = {
                'chunk_id': match.id,
                'score': match.score,
                'content_type': match.metadata.get('content_type'),
                'class': match.metadata.get('class'),
                'chapter': match.metadata.get('chapter'),
                'page': match.metadata.get('page'),
                'raw_text': match.metadata.get('raw_text', ''),
                'has_formula': match.metadata.get('has_formula') == 'True',
                'has_image': match.metadata.get('has_image') == 'True',
                'has_table': match.metadata.get('has_table') == 'True',
            }
            
            # Add optional fields
            if 'latex_formula' in match.metadata:
                result['latex_formula'] = match.metadata['latex_formula']
            
            if 'diagram_path' in match.metadata:
                result['diagram_path'] = match.metadata['diagram_path']
            
            if 'step_number' in match.metadata:
                result['step_number'] = match.metadata['step_number']
            
            if 'table_data' in match.metadata:
                result['table_data'] = match.metadata['table_data']
            
            processed.append(result)
        
        # Re-rank based on query intent
        if query_info['content_types']:
            processed = self._rerank_by_content_type(
                processed,
                query_info['content_types']
            )
        
        # Return top_k results
        return processed[:top_k]
    
    def _rerank_by_content_type(
        self,
        results: List[Dict],
        preferred_types: List[str]
    ) -> List[Dict]:
        """Boost results matching preferred content types"""
        
        for result in results:
            content_type = result['content_type']
            
            # Boost score if matches preferred type
            if content_type in preferred_types:
                result['score'] *= 1.2  # 20% boost
            
            # Additional boosts for specific features
            if 'formula' in preferred_types and result['has_formula']:
                result['score'] *= 1.1
            
            if 'diagram' in preferred_types and result['has_image']:
                result['score'] *= 1.1
            
            if 'table' in preferred_types and result['has_table']:
                result['score'] *= 1.1
        
        # Re-sort by adjusted scores
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def get_by_id(
        self,
        chunk_id: str,
        namespace: str = "physics"
    ) -> Optional[Dict]:
        """Fetch specific chunk by ID"""
        try:
            result = self.index.fetch(
                ids=[chunk_id],
                namespace=namespace
            )
            
            if chunk_id in result.vectors:
                vector_data = result.vectors[chunk_id]
                return {
                    'chunk_id': chunk_id,
                    'metadata': vector_data.metadata
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch chunk {chunk_id}: {e}")
            return None
