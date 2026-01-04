"""
Multimodal Embedder for Mathematics Content

Generates unified 768-dimensional embeddings from text, formulas, and images.
Uses sentence-transformers for text/formulas and CLIP for images.

Priority:
1. Formula exists → embed formula (LaTeX)
2. No formula → embed text
3. Image only → embed image (projected to 768-dim)
4. Combined → weighted combination
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MultimodalEmbedder:
    """
    Generates 768-dimensional embeddings for multimodal math content.
    
    Usage:
        embedder = MultimodalEmbedder()
        embedding = embedder.embed_chunk(chunk_dict)
    """
    
    def __init__(
        self,
        text_model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: Optional[str] = None
    ):
        """
        Initialize multimodal embedder.
        
        Args:
            text_model_name: Sentence transformer model (must be 768-dim)
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        import torch
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"🔢 Initializing Multimodal Embedder on device: {self.device}")
        
        # Load text/formula embedder
        try:
            self.text_model = SentenceTransformer(text_model_name, device=self.device)
            
            # Verify output dimension
            test_emb = self.text_model.encode("test")
            if len(test_emb) != 768:
                raise ValueError(f"Text model must output 768-dim vectors, got {len(test_emb)}")
            
            logger.info(f"✅ Text model loaded: {text_model_name}")
            logger.info(f"   Output dimension: {len(test_emb)}")
        
        except Exception as e:
            logger.error(f"❌ Failed to load text model: {e}")
            raise
        
        # Image processor (lazy load when needed)
        self._image_processor = None
    
    @property
    def image_processor(self):
        """Lazy load image processor only when needed."""
        if self._image_processor is None:
            from .image_processor import ImageProcessor
            self._image_processor = ImageProcessor(device=self.device)
            logger.info("✅ Image processor loaded (lazy)")
        return self._image_processor
    
    def embed_chunk(self, chunk: Dict) -> np.ndarray:
        """
        Generate 768-dim embedding for a chunk based on priority rules.
        
        Priority:
        1. Formula exists → embed formula
        2. No formula → embed text
        3. Image only → embed image
        4. Text + Image → weighted combination
        
        Args:
            chunk: Chunk dictionary with raw_text, latex_formula, image_path
        
        Returns:
            768-dimensional numpy array
        """
        has_formula = chunk.get('has_formula', False) and chunk.get('latex_formula')
        has_image = chunk.get('has_image', False) and chunk.get('image_path')
        has_text = chunk.get('raw_text') and len(chunk.get('raw_text', '').strip()) > 0
        
        # Priority 1: Formula embedding
        if has_formula:
            latex = chunk['latex_formula']
            logger.debug(f"   Embedding formula: {latex[:50]}...")
            return self.embed_text(latex)
        
        # Priority 2: Text embedding
        elif has_text and not has_image:
            text = chunk['raw_text']
            logger.debug(f"   Embedding text: {text[:50]}...")
            return self.embed_text(text)
        
        # Priority 3: Image embedding
        elif has_image and not has_text:
            image_path = chunk['image_path']
            logger.debug(f"   Embedding image: {Path(image_path).name}")
            return self.image_processor.embed_image(image_path)
        
        # Priority 4: Combined text + image
        elif has_text and has_image:
            text = chunk['raw_text']
            image_path = chunk['image_path']
            logger.debug(f"   Embedding text+image: {text[:30]}... + {Path(image_path).name}")
            return self.embed_text_and_image(text, image_path, alpha=0.6)
        
        else:
            # Fallback: embed type/metadata
            fallback_text = f"{chunk.get('content_type', 'unknown')} content"
            logger.warning(f"   No content found, using fallback: {fallback_text}")
            return self.embed_text(fallback_text)
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate 768-dim embedding for text or formula.
        
        Args:
            text: Text or LaTeX formula string
        
        Returns:
            768-dimensional numpy array
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(768, dtype=np.float32)
        
        try:
            embedding = self.text_model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization
            )
            return embedding.astype(np.float32)
        
        except Exception as e:
            logger.error(f"❌ Failed to embed text: {e}")
            return np.zeros(768, dtype=np.float32)
    
    def embed_text_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
        
        Returns:
            numpy array of shape (len(texts), 768)
        """
        logger.info(f"Batch embedding {len(texts)} texts...")
        
        try:
            embeddings = self.text_model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            return embeddings.astype(np.float32)
        
        except Exception as e:
            logger.error(f"❌ Batch embedding failed: {e}")
            return np.zeros((len(texts), 768), dtype=np.float32)
    
    def embed_text_and_image(
        self,
        text: str,
        image_path: Union[str, Path],
        alpha: float = 0.6
    ) -> np.ndarray:
        """
        Generate combined text + image embedding.
        
        Args:
            text: Text content
            image_path: Path to image
            alpha: Weight for text (1-alpha for image)
        
        Returns:
            768-dimensional combined embedding
        """
        # Get text embedding
        text_emb = self.embed_text(text)
        
        # Get image embedding
        image_emb = self.image_processor.embed_image(image_path)
        
        # Weighted combination
        combined = alpha * text_emb + (1 - alpha) * image_emb
        
        # Normalize
        combined = combined / np.linalg.norm(combined)
        
        return combined.astype(np.float32)
    
    def embed_chunks_batch(
        self,
        chunks: List[Dict],
        show_progress: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple chunks efficiently.
        
        Args:
            chunks: List of chunk dictionaries
            show_progress: Whether to show progress
        
        Returns:
            List of 768-dimensional embeddings
        """
        logger.info(f"🔄 Batch processing {len(chunks)} chunks...")
        
        embeddings = []
        
        # Separate by content type for batch processing
        text_only_chunks = []
        formula_chunks = []
        image_chunks = []
        combined_chunks = []
        
        for i, chunk in enumerate(chunks):
            has_formula = chunk.get('has_formula', False) and chunk.get('latex_formula')
            has_image = chunk.get('has_image', False) and chunk.get('image_path')
            has_text = chunk.get('raw_text') and len(chunk.get('raw_text', '').strip()) > 0
            
            if has_formula:
                formula_chunks.append((i, chunk))
            elif has_image and not has_text:
                image_chunks.append((i, chunk))
            elif has_text and has_image:
                combined_chunks.append((i, chunk))
            else:
                text_only_chunks.append((i, chunk))
        
        # Initialize result array
        result_embeddings = [None] * len(chunks)
        
        # Batch process text/formulas
        if text_only_chunks or formula_chunks:
            all_text_chunks = text_only_chunks + formula_chunks
            texts = [
                chunk.get('latex_formula') if chunk.get('has_formula') else chunk.get('raw_text', '')
                for _, chunk in all_text_chunks
            ]
            
            logger.info(f"   Processing {len(texts)} text/formula chunks...")
            text_embeddings = self.embed_text_batch(texts)
            
            for (idx, _), emb in zip(all_text_chunks, text_embeddings):
                result_embeddings[idx] = emb
        
        # Process images
        if image_chunks:
            logger.info(f"   Processing {len(image_chunks)} image chunks...")
            for idx, chunk in image_chunks:
                emb = self.image_processor.embed_image(chunk['image_path'])
                result_embeddings[idx] = emb
        
        # Process combined (text + image)
        if combined_chunks:
            logger.info(f"   Processing {len(combined_chunks)} combined chunks...")
            for idx, chunk in combined_chunks:
                emb = self.embed_text_and_image(
                    chunk['raw_text'],
                    chunk['image_path'],
                    alpha=0.6
                )
                result_embeddings[idx] = emb
        
        logger.info(f"✅ Generated {len(result_embeddings)} embeddings")
        
        # Add embeddings back to chunks
        for i, chunk in enumerate(chunks):
            if result_embeddings[i] is not None:
                chunk['embedding'] = result_embeddings[i]
        
        return chunks
    
    def get_embedding_stats(self, embeddings: List[np.ndarray]) -> Dict:
        """
        Get statistics about embeddings.
        
        Args:
            embeddings: List of embedding vectors
        
        Returns:
            Dictionary with statistics
        """
        embeddings_array = np.array(embeddings)
        
        return {
            "count": len(embeddings),
            "dimension": embeddings_array.shape[1] if len(embeddings_array.shape) > 1 else 768,
            "mean_norm": float(np.mean([np.linalg.norm(e) for e in embeddings])),
            "std_norm": float(np.std([np.linalg.norm(e) for e in embeddings])),
            "mean_values": embeddings_array.mean(axis=0).tolist()[:10],  # First 10 dims
        }


if __name__ == "__main__":
    # Test the embedder
    logging.basicConfig(level=logging.INFO)
    
    embedder = MultimodalEmbedder()
    
    # Test chunks
    test_chunks = [
        {
            "raw_text": "Solve 2x + 3 = 7",
            "latex_formula": "$2x + 3 = 7$",
            "has_formula": True,
            "has_image": False
        },
        {
            "raw_text": "A triangle has three sides and three angles",
            "has_formula": False,
            "has_image": False
        }
    ]
    
    for chunk in test_chunks:
        emb = embedder.embed_chunk(chunk)
        print(f"\nChunk: {chunk['raw_text'][:40]}...")
        print(f"Embedding shape: {emb.shape}")
        print(f"Norm: {np.linalg.norm(emb):.4f}")
    
    print("\n✅ Embedder ready for production use")
