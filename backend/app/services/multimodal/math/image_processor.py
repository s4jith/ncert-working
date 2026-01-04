"""
Image Embedding Processor for Mathematical Diagrams

Uses CLIP model to generate 512-dim embeddings from diagram images,
then projects to 768-dim to match text embeddings.

Features:
- CLIP-based visual understanding
- Dimension projection (512 → 768)
- Batch processing support
- Caching for efficiency
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Union, List
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Process mathematical diagram images into 768-dim embeddings.
    
    Uses CLIP (ViT-B/32) for visual feature extraction:
    - CLIP output: 512 dimensions
    - Projected to: 768 dimensions (to match sentence-transformers)
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize image processor with CLIP model.
        
        Args:
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self._clip_model = None
        self._clip_processor = None
        self._projection = None
        logger.info(f"🖼️ Initializing Image Processor on device: {device}")
    
    def _load_clip(self):
        """Lazy load CLIP model and projection layer."""
        if self._clip_model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                
                logger.info("Loading CLIP model (openai/clip-vit-base-patch32)...")
                self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                self._clip_model.to(self.device)
                self._clip_model.eval()
                
                # Create projection layer: 512 → 768 dimensions
                self._projection = torch.nn.Linear(512, 768).to(self.device)
                # Initialize with Xavier uniform for stable gradients
                torch.nn.init.xavier_uniform_(self._projection.weight)
                self._projection.eval()
                
                logger.info("✅ CLIP model and projection loaded successfully")
            
            except ImportError as e:
                logger.error(f"❌ Failed to import CLIP: {e}")
                logger.error("Install with: pip install transformers torch pillow")
                raise
            except Exception as e:
                logger.error(f"❌ Failed to load CLIP model: {e}")
                raise
    
    def embed_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Generate 768-dim embedding from image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            768-dimensional numpy array (normalized)
        """
        # Lazy load CLIP
        if self._clip_model is None:
            self._load_clip()
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Process with CLIP
            inputs = self._clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate CLIP embedding (512-dim)
            with torch.no_grad():
                outputs = self._clip_model.get_image_features(**inputs)
                clip_embedding = outputs[0]  # Shape: (512,)
                
                # Project to 768 dimensions
                projected = self._projection(clip_embedding)  # Shape: (768,)
                
                # Normalize
                embedding = torch.nn.functional.normalize(projected, p=2, dim=0)
            
            # Convert to numpy
            return embedding.cpu().numpy()
        
        except FileNotFoundError:
            logger.error(f"❌ Image not found: {image_path}")
            # Return zero vector as fallback
            return np.zeros(768, dtype=np.float32)
        
        except Exception as e:
            logger.error(f"❌ Failed to embed image {image_path}: {e}")
            # Return zero vector as fallback
            return np.zeros(768, dtype=np.float32)
    
    def embed_images_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple images (batch processing).
        
        Args:
            image_paths: List of image file paths
            batch_size: Number of images to process at once
        
        Returns:
            List of 768-dim numpy arrays
        """
        # Lazy load CLIP
        if self._clip_model is None:
            self._load_clip()
        
        embeddings = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            
            try:
                # Load batch of images
                images = []
                valid_indices = []
                
                for idx, path in enumerate(batch_paths):
                    try:
                        img = Image.open(path).convert('RGB')
                        images.append(img)
                        valid_indices.append(idx)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load image {path}: {e}")
                        # Add zero vector for failed images
                        embeddings.append(np.zeros(768, dtype=np.float32))
                
                if not images:
                    continue
                
                # Process batch
                inputs = self._clip_processor(images=images, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Generate embeddings
                with torch.no_grad():
                    outputs = self._clip_model.get_image_features(**inputs)
                    
                    # Project to 768-dim
                    projected = self._projection(outputs)
                    
                    # Normalize
                    normalized = torch.nn.functional.normalize(projected, p=2, dim=1)
                
                # Convert to numpy and insert at correct positions
                batch_embeddings = normalized.cpu().numpy()
                
                for idx, embedding in zip(valid_indices, batch_embeddings):
                    embeddings.append(embedding)
            
            except Exception as e:
                logger.error(f"❌ Batch embedding failed: {e}")
                # Add zero vectors for entire batch
                for _ in batch_paths:
                    embeddings.append(np.zeros(768, dtype=np.float32))
        
        return embeddings
    
    def combine_text_image_embedding(
        self,
        text_embedding: np.ndarray,
        image_embedding: np.ndarray,
        text_weight: float = 0.7,
        image_weight: float = 0.3
    ) -> np.ndarray:
        """
        Combine text and image embeddings with weighted average.
        
        Args:
            text_embedding: 768-dim text embedding
            image_embedding: 768-dim image embedding
            text_weight: Weight for text component (default: 0.7)
            image_weight: Weight for image component (default: 0.3)
        
        Returns:
            Combined 768-dim embedding (normalized)
        """
        # Weighted combination
        combined = (text_weight * text_embedding + image_weight * image_embedding)
        
        # Re-normalize
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        
        return combined
    
    def get_embedding_stats(self, embeddings: List[np.ndarray]) -> dict:
        """
        Calculate statistics for a list of embeddings.
        
        Args:
            embeddings: List of numpy arrays
        
        Returns:
            Dictionary with mean_norm, std_norm, min_norm, max_norm
        """
        norms = [np.linalg.norm(emb) for emb in embeddings]
        
        return {
            'count': len(embeddings),
            'mean_norm': np.mean(norms),
            'std_norm': np.std(norms),
            'min_norm': np.min(norms),
            'max_norm': np.max(norms),
            'dimension': embeddings[0].shape[0] if embeddings else 0
        }


# Singleton instance for lazy loading
_image_processor_instance = None


def get_image_processor(device: str = "cpu") -> ImageProcessor:
    """
    Get singleton ImageProcessor instance (lazy initialization).
    
    Args:
        device: 'cpu' or 'cuda'
    
    Returns:
        ImageProcessor instance
    """
    global _image_processor_instance
    
    if _image_processor_instance is None:
        _image_processor_instance = ImageProcessor(device=device)
    
    return _image_processor_instance
