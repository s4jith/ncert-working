"""
Pinecone Vector Database Connection and Operations
Organized with subject-based NAMESPACES for efficient retrieval

Namespace Structure:
- mathematics: All math books from class 5-12
- science: All science books from class 5-12
- physics: Physics books (class 11-12)
- chemistry: Chemistry books (class 11-12)
- biology: Biology books (class 11-12)
- etc.
"""

import logging
from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

# Global instances
_pinecone_client = None
_pinecone_index = None
_embedding_model = None


def get_namespace(subject: str) -> str:
    """Convert subject name to namespace identifier"""
    if not subject:
        return "general"
    # Normalize: lowercase, replace spaces with underscore
    return subject.lower().replace(" ", "_").replace("-", "_")


def init_pinecone():
    """Initialize Pinecone connection and embedding model"""
    global _pinecone_client, _pinecone_index, _embedding_model
    
    try:
        # Check if API key is configured
        if not settings.PINECONE_API_KEY:
            logger.warning("Pinecone API key not configured - vector search disabled")
            return
        
        from pinecone import Pinecone
        
        # Initialize Pinecone client
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Connect to index
        _pinecone_index = _pinecone_client.Index(settings.PINECONE_INDEX_NAME)
        
        # Initialize embedding model
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        logger.info(f"Pinecone initialized with index: {settings.PINECONE_INDEX_NAME}")
        
    except Exception as e:
        logger.warning(f"Pinecone initialization skipped: {e}")


def close_pinecone():
    """Close Pinecone connection"""
    global _pinecone_client, _pinecone_index, _embedding_model
    _pinecone_client = None
    _pinecone_index = None
    _embedding_model = None
    logger.info("Pinecone connection closed")


async def check_pinecone_health() -> str:
    """Check Pinecone connection health"""
    try:
        if _pinecone_index is None:
            return "disconnected"
        stats = _pinecone_index.describe_index_stats()
        return f"connected ({stats.total_vector_count} vectors)"
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        return f"error: {str(e)}"


def get_embedding(text: str) -> List[float]:
    """Generate embedding vector for text"""
    if _embedding_model is None:
        raise RuntimeError("Embedding model not initialized")
    return _embedding_model.encode(text).tolist()


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts"""
    if _embedding_model is None:
        raise RuntimeError("Embedding model not initialized")
    return _embedding_model.encode(texts).tolist()


async def query_vectors(
    query_text: str,
    class_num: Optional[str] = None,
    subject: Optional[str] = None,
    chapter: Optional[str] = None,
    top_k: int = None
) -> List[Dict]:
    """
    Query Pinecone with subject-based namespace for efficient retrieval
    
    Args:
        query_text: The question/query text
        class_num: Filter by class (e.g., "5", "6", "Class 5")
        subject: Filter by subject - also determines namespace
        chapter: Filter by chapter
        top_k: Number of results to return
        
    Returns:
        List of matching documents with metadata and scores
    """
    if _pinecone_index is None:
        raise RuntimeError("Pinecone not initialized")
    
    top_k = top_k or settings.RAG_TOP_K
    
    # Generate query embedding
    query_embedding = get_embedding(query_text)
    
    # Build filter
    filter_dict = {}
    
    if class_num:
        # Normalize class number (handle "5", "Class 5", "class 5", etc.)
        class_normalized = class_num.lower().replace("class", "").strip()
        filter_dict["class_num"] = {"$in": [class_normalized, f"Class {class_normalized}", str(class_normalized)]}
    
    if chapter:
        filter_dict["chapter"] = {"$eq": chapter}
    
    # Determine namespace from subject
    namespace = get_namespace(subject) if subject else None
    
    try:
        all_results = []
        
        if namespace:
            # Query specific subject namespace
            results = _pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None,
                namespace=namespace
            )
            all_results.extend(results.matches)
        else:
            # Query default namespace and top subject namespaces
            namespaces_to_query = ["", "mathematics", "science", "physics", "chemistry", "biology", "english", "social_science"]
            for ns in namespaces_to_query:
                try:
                    results = _pinecone_index.query(
                        vector=query_embedding,
                        top_k=3,  # Get fewer from each namespace
                        include_metadata=True,
                        filter=filter_dict if filter_dict else None,
                        namespace=ns if ns else None
                    )
                    all_results.extend(results.matches)
                except:
                    pass  # Namespace might not exist
            
            # Sort by score and take top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            all_results = all_results[:top_k]
        
        # Format results
        formatted_results = []
        for match in all_results:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "class_num": match.metadata.get("class_num", ""),
                "subject": match.metadata.get("subject", ""),
                "chapter": match.metadata.get("chapter", ""),
                "source_file": match.metadata.get("source_file", ""),
                "page": match.metadata.get("page"),
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        raise


async def add_documents(
    chunks: List[Dict],
    standard: str,
    subject: str,
    chapter: str,
    source_file: str,
    batch_size: int = 100
) -> int:
    """
    Add document chunks to Pinecone with subject-based namespace
    
    Vectors are stored in namespaces based on subject:
    - Mathematics books -> 'mathematics' namespace
    - Science books -> 'science' namespace
    - Physics books -> 'physics' namespace
    - etc.
    
    This allows efficient retrieval when student asks subject-specific questions.
    
    Args:
        chunks: List of text chunks with optional page info
        standard: Class/Grade number (5-12)
        subject: Subject name (determines namespace)
        chapter: Chapter name
        source_file: Source filename
        batch_size: Batch size for upsert
        
    Returns:
        Number of vectors added
    """
    if _pinecone_index is None:
        raise RuntimeError("Pinecone not initialized")
    
    # Determine namespace from subject
    namespace = get_namespace(subject)
    logger.info(f"Adding {len(chunks)} vectors to namespace: {namespace}")
    
    vectors = []
    
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", chunk) if isinstance(chunk, dict) else chunk
        page = chunk.get("page") if isinstance(chunk, dict) else None
        
        embedding = get_embedding(text)
        
        # Create unique vector ID
        vector_id = f"{source_file}_{standard}_{chapter}_{i}".replace(" ", "_")
        
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "text": text[:8000],  # Pinecone metadata limit
                "class_num": str(standard),
                "subject": subject,
                "chapter": chapter,
                "source_file": source_file,
                "page": page,
                "chunk_index": i
            }
        })
    
    # Upsert in batches to the subject namespace
    total_added = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        _pinecone_index.upsert(vectors=batch, namespace=namespace)
        total_added += len(batch)
        logger.info(f"Added batch {i // batch_size + 1}: {len(batch)} vectors to namespace '{namespace}'")
    
    return total_added


async def delete_by_source(source_file: str, subject: Optional[str] = None) -> bool:
    """Delete all vectors for a specific source file from its namespace"""
    if _pinecone_index is None:
        return False
    
    try:
        namespace = get_namespace(subject) if subject else None
        _pinecone_index.delete(
            filter={"source_file": {"$eq": source_file}},
            namespace=namespace
        )
        logger.info(f"Deleted vectors for source: {source_file} from namespace: {namespace or 'default'}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete vectors: {e}")
        return False


async def get_stats() -> Dict:
    """Get Pinecone index statistics including namespace info"""
    if _pinecone_index is None:
        return {"status": "disconnected"}
    
    try:
        stats = _pinecone_index.describe_index_stats()
        
        # Get namespace-specific stats
        namespaces = {}
        if hasattr(stats, 'namespaces') and stats.namespaces:
            for ns_name, ns_stats in stats.namespaces.items():
                namespaces[ns_name or "default"] = ns_stats.vector_count
        
        return {
            "status": "connected",
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness,
            "namespaces": namespaces
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
