"""
Physics Embedder

Generates 768-dim unified embeddings for all physics content types.
"""

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PhysicsEmbedder:
    """Generate 768-dim embeddings for physics content"""
    
    def __init__(self, device: str = None):
        """Initialize embedder with models"""
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"🔢 Initializing Physics Embedder on device: {self.device}")
        
        # Text model (768-dim native)
        logger.info("   Loading text model...")
        self.text_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.text_model.to(self.device)
        logger.info(f"   ✅ Text model loaded: all-mpnet-base-v2 (768-dim)")
        
        # CLIP for diagrams (lazy load)
        self.clip_model = None
        self.clip_processor = None
        self.clip_projection = None
        
        logger.info("✅ Physics Embedder initialized")
    
    def _init_clip(self):
        """Lazy initialization of CLIP model"""
        if self.clip_model is not None:
            return
        
        logger.info("   Loading CLIP model for diagrams...")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model.to(self.device)
        
        # Create projection layer: 512 (CLIP) -> 768 (target)
        self.clip_projection = torch.nn.Sequential(
            torch.nn.Linear(512, 768),
            torch.nn.LayerNorm(768),
            torch.nn.GELU(),
            torch.nn.Linear(768, 768)
        ).to(self.device)
        
        logger.info(f"   ✅ CLIP model loaded and projected to 768-dim")
    
    def embed_chunks_batch(
        self,
        chunks: List[Dict],
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Generate embeddings for all chunks in batch
        
        Args:
            chunks: List of chunk dictionaries
            batch_size: Batch size for processing
        
        Returns:
            Chunks with 'embedding' field added
        """
        logger.info(f"🔄 Batch processing {len(chunks)} physics chunks...")
        
        # Separate chunks by type
        text_chunks = []
        diagram_chunks = []
        table_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk['_index'] = i  # Track original position
            
            if chunk.get('has_image'):
                diagram_chunks.append(chunk)
            elif chunk.get('has_table'):
                table_chunks.append(chunk)
            else:
                text_chunks.append(chunk)
        
        logger.info(f"   Processing {len(text_chunks)} text/formula chunks...")
        logger.info(f"   Processing {len(table_chunks)} table chunks...")
        logger.info(f"   Processing {len(diagram_chunks)} diagram chunks...")
        
        # Process text/formula chunks
        for chunk in text_chunks:
            embedding = self._embed_text_or_formula(chunk)
            chunk['embedding'] = embedding
        
        # Process table chunks
        for chunk in table_chunks:
            embedding = self._embed_table(chunk)
            chunk['embedding'] = embedding
        
        # Process diagram chunks
        if diagram_chunks:
            self._init_clip()  # Lazy load CLIP
            for chunk in diagram_chunks:
                embedding = self._embed_diagram(chunk)
                chunk['embedding'] = embedding
        
        # Remove temporary index
        for chunk in chunks:
            chunk.pop('_index', None)
        
        logger.info(f"✅ Generated {len(chunks)} embeddings")
        return chunks
    
    def _embed_text_or_formula(self, chunk: Dict) -> np.ndarray:
        """Embed text or formula chunk"""
        # Priority: formula > text
        if chunk.get('has_formula') and chunk.get('latex_formula'):
            text = f"{chunk.get('raw_text', '')} {chunk['latex_formula']}"
        else:
            text = chunk.get('raw_text', '')
        
        if not text:
            text = "Empty physics content"
        
        # Generate embedding
        embedding = self.text_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embedding
    
    def _embed_table(self, chunk: Dict) -> np.ndarray:
        """Embed table chunk"""
        # Convert table to structured text
        table_data = chunk.get('table_data', '')
        text = chunk.get('raw_text', '')
        
        # Combine caption and table data
        combined_text = f"{text}\n{table_data}" if table_data else text
        
        if not combined_text:
            combined_text = "Physics data table"
        
        # Generate embedding
        embedding = self.text_model.encode(
            combined_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embedding
    
    def _embed_diagram(self, chunk: Dict) -> np.ndarray:
        """Embed diagram using CLIP"""
        diagram_path = chunk.get('diagram_path')
        
        if not diagram_path or not Path(diagram_path).exists():
            logger.warning(f"Diagram not found: {diagram_path}, using text fallback")
            return self._embed_text_or_formula(chunk)
        
        try:
            # Load image
            image = Image.open(diagram_path).convert('RGB')
            
            # Process with CLIP
            inputs = self.clip_processor(
                images=image,
                return_tensors="pt"
            ).to(self.device)
            
            # Get CLIP embedding
            with torch.no_grad():
                clip_embedding = self.clip_model.get_image_features(**inputs)
                clip_embedding = clip_embedding.squeeze(0)  # Remove batch dim
                
                # Project to 768-dim
                projected_embedding = self.clip_projection(clip_embedding)
                
                # Normalize
                projected_embedding = torch.nn.functional.normalize(
                    projected_embedding,
                    p=2,
                    dim=0
                )
            
            # Convert to numpy
            embedding = projected_embedding.cpu().numpy()
            
            return embedding
            
        except Exception as e:
            logger.warning(f"Failed to embed diagram {diagram_path}: {e}, using text fallback")
            return self._embed_text_or_formula(chunk)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a search query
        
        Args:
            query: Search query text
        
        Returns:
            768-dim embedding
        """
        embedding = self.text_model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embedding
