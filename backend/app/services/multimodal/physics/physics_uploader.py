"""
Physics Uploader

Uploads physics chunks to Pinecone 'physics' namespace.
"""

from pinecone import Pinecone
from typing import List, Dict, Tuple
import logging
import os
from tqdm import tqdm

logger = logging.getLogger(__name__)


class PhysicsUploader:
    """Upload physics chunks to Pinecone"""
    
    def __init__(self, api_key: str = None, index_name: str = "ncert-all-subjects"):
        """Initialize Pinecone connection"""
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name
        
        logger.info(f"🌲 Initializing Physics Uploader...")
        
        # Connect to Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
        
        logger.info(f"   Connected to index: {self.index_name}")
        logger.info(f"✅ Physics Uploader ready")
    
    def upload_chunks(
        self,
        chunks: List[Dict],
        namespace: str = "physics",
        batch_size: int = 100
    ) -> Dict:
        """
        Upload chunks to Pinecone
        
        Args:
            chunks: List of chunks with embeddings
            namespace: Pinecone namespace (default: physics)
            batch_size: Number of vectors per batch
        
        Returns:
            Upload statistics
        """
        logger.info(f"📤 Uploading {len(chunks)} chunks to namespace '{namespace}'...")
        
        # Convert chunks to Pinecone format
        vectors = self._prepare_vectors(chunks)
        
        # Upload in batches
        total_uploaded = 0
        failed = 0
        
        for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading batches"):
            batch = vectors[i:i+batch_size]
            
            try:
                self.index.upsert(
                    vectors=batch,
                    namespace=namespace
                )
                total_uploaded += len(batch)
                
            except Exception as e:
                logger.error(f"Failed to upload batch {i//batch_size}: {e}")
                failed += len(batch)
        
        # Get final statistics
        stats = self.index.describe_index_stats()
        namespace_stats = stats.namespaces.get(namespace, {})
        
        result = {
            'total_chunks': len(chunks),
            'uploaded': total_uploaded,
            'failed': failed,
            'namespace': namespace,
            'namespace_vector_count': namespace_stats.get('vector_count', 0)
        }
        
        logger.info(f"✅ Upload complete:")
        logger.info(f"   Total chunks: {result['total_chunks']}")
        logger.info(f"   Uploaded: {result['uploaded']}")
        logger.info(f"   Failed: {result['failed']}")
        logger.info(f"   Namespace '{namespace}' now has {result['namespace_vector_count']} vectors")
        
        return result
    
    def _prepare_vectors(self, chunks: List[Dict]) -> List[Tuple]:
        """
        Convert chunks to Pinecone vector format
        
        Format: (id, embedding, metadata)
        """
        vectors = []
        
        for chunk in chunks:
            # Extract embedding
            embedding = chunk.get('embedding')
            if embedding is None:
                logger.warning(f"Chunk {chunk.get('chunk_id')} missing embedding, skipping")
                continue
            
            # Convert to list if numpy array
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            # Prepare metadata (exclude embedding and large fields)
            metadata = {
                'content_type': chunk.get('content_type'),
                'class': chunk.get('metadata', {}).get('class'),
                'chapter': chunk.get('metadata', {}).get('chapter'),
                'page': chunk.get('metadata', {}).get('page'),
                'subject': chunk.get('metadata', {}).get('subject', 'physics'),
                'has_formula': str(chunk.get('has_formula', False)),
                'has_image': str(chunk.get('has_image', False)),
                'has_table': str(chunk.get('has_table', False)),
                'raw_text': chunk.get('raw_text', '')[:500],  # Truncate
            }
            
            # Add optional fields
            if chunk.get('latex_formula'):
                metadata['latex_formula'] = chunk.get('latex_formula')[:200]
            
            if chunk.get('diagram_path'):
                metadata['diagram_path'] = chunk.get('diagram_path')
            
            if chunk.get('step_number') is not None:
                metadata['step_number'] = chunk.get('step_number')
            
            if chunk.get('table_data'):
                metadata['table_data'] = chunk.get('table_data')[:300]
            
            # Create vector tuple
            vector = (
                chunk['chunk_id'],
                embedding,
                metadata
            )
            
            vectors.append(vector)
        
        return vectors
    
    def get_namespace_stats(self, namespace: str = "physics") -> Dict:
        """Get statistics for physics namespace"""
        stats = self.index.describe_index_stats()
        namespace_stats = stats.namespaces.get(namespace, {})
        
        return {
            'namespace': namespace,
            'vector_count': namespace_stats.get('vector_count', 0),
            'total_vectors': stats.total_vector_count,
            'dimension': stats.dimension
        }
    
    def delete_namespace(self, namespace: str = "physics"):
        """Delete all vectors in namespace"""
        logger.warning(f"⚠️  Deleting all vectors in namespace '{namespace}'...")
        
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"✅ Namespace '{namespace}' cleared")
        except Exception as e:
            logger.error(f"Failed to delete namespace: {e}")
