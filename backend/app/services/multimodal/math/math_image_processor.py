"""
Image Processor with CLIP Embeddings

Generates 768-dimensional embeddings for mathematical diagrams, graphs, and figures.
Uses CLIP ViT-B/32 with projection layer to match text embedding dimensions.

Features:
- CLIP-based visual embeddings (512-dim → 768-dim projection)
- Image preprocessing and normalization
- Batch processing support
- Caption extraction from images
"""

import torch
import torch.nn as nn
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from typing import List, Dict, Optional, Union
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class CLIPProjector(nn.Module):
    """
    Projects CLIP 512-dim embeddings to 768-dim to match text embeddings.
    """
    
    def __init__(self, input_dim: int = 512, output_dim: int = 768):
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.LayerNorm(output_dim),
            nn.GELU(),
            nn.Linear(output_dim, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.projection(x)


class ImageProcessor:
    """
    Processes images and generates 768-dimensional embeddings using CLIP.
    
    Usage:
        processor = ImageProcessor()
        embedding = processor.embed_image("diagram.png")
    """
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: Optional[str] = None
    ):
        """
        Initialize image processor with CLIP model.
        
        Args:
            model_name: HuggingFace CLIP model name
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"🖼️  Initializing Image Processor on device: {self.device}")
        
        # Load CLIP model and processor
        try:
            self.model = CLIPModel.from_pretrained(model_name).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model.eval()
            
            # Initialize projection layer (512 → 768)
            self.projector = CLIPProjector(input_dim=512, output_dim=768).to(self.device)
            self.projector.eval()
            
            logger.info(f"✅ CLIP model loaded: {model_name}")
            logger.info(f"   Output dimension: 768 (projected from 512)")
        
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP model: {e}")
            raise
    
    def embed_image(
        self,
        image_path: Union[str, Path],
        caption: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate 768-dim embedding for a single image.
        
        Args:
            image_path: Path to image file
            caption: Optional image caption/description
        
        Returns:
            768-dimensional numpy array
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            # Generate CLIP embedding (512-dim)
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # Project to 768-dim
                projected_features = self.projector(image_features)
                
                # Normalize again
                projected_features = projected_features / projected_features.norm(dim=-1, keepdim=True)
            
            embedding = projected_features.cpu().numpy().flatten()
            
            logger.debug(f"   Generated embedding for: {Path(image_path).name} (shape: {embedding.shape})")
            
            return embedding
        
        except Exception as e:
            logger.error(f"❌ Failed to embed image {image_path}: {e}")
            raise
    
    def embed_images_batch(
        self,
        image_paths: List[Union[str, Path]],
        captions: Optional[List[str]] = None
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            captions: Optional list of captions
        
        Returns:
            List of 768-dimensional numpy arrays
        """
        logger.info(f"Processing batch of {len(image_paths)} images...")
        
        embeddings = []
        
        # Process in batches for efficiency
        batch_size = 8
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_captions = captions[i:i + batch_size] if captions else None
            
            # Load images
            images = []
            for path in batch_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to load image {path}: {e}")
                    images.append(None)
            
            # Process valid images
            valid_images = [img for img in images if img is not None]
            if not valid_images:
                continue
            
            inputs = self.processor(images=valid_images, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                # Generate CLIP embeddings
                image_features = self.model.get_image_features(**inputs)
                
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # Project to 768-dim
                projected_features = self.projector(image_features)
                
                # Normalize
                projected_features = projected_features / projected_features.norm(dim=-1, keepdim=True)
            
            batch_embeddings = projected_features.cpu().numpy()
            embeddings.extend(batch_embeddings)
        
        logger.info(f"✅ Generated {len(embeddings)} image embeddings")
        
        return embeddings
    
    def embed_with_text_context(
        self,
        image_path: Union[str, Path],
        text: str,
        alpha: float = 0.7
    ) -> np.ndarray:
        """
        Generate multimodal embedding combining image and text context.
        
        Args:
            image_path: Path to image file
            text: Related text (caption, description, surrounding context)
            alpha: Weight for image embedding (1-alpha for text)
        
        Returns:
            768-dimensional combined embedding
        """
        # Get image embedding
        image_emb = self.embed_image(image_path)
        
        # Get text embedding from CLIP text encoder
        inputs = self.processor(text=[text], return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Project text to 768-dim
            projected_text = self.projector(text_features)
            projected_text = projected_text / projected_text.norm(dim=-1, keepdim=True)
        
        text_emb = projected_text.cpu().numpy().flatten()
        
        # Weighted combination
        combined_emb = alpha * image_emb + (1 - alpha) * text_emb
        
        # Normalize
        combined_emb = combined_emb / np.linalg.norm(combined_emb)
        
        logger.debug(f"   Combined image+text embedding (alpha={alpha})")
        
        return combined_emb
    
    def preprocess_image(
        self,
        image_path: Union[str, Path],
        enhance: bool = True
    ) -> Image.Image:
        """
        Preprocess image for better embedding quality.
        
        Args:
            image_path: Path to image
            enhance: Whether to apply enhancement
        
        Returns:
            Preprocessed PIL Image
        """
        image = Image.open(image_path).convert("RGB")
        
        if enhance:
            from PIL import ImageEnhance
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
        
        return image
    
    def extract_caption(
        self,
        image_path: Union[str, Path],
        surrounding_text: Optional[str] = None
    ) -> str:
        """
        Extract or generate caption for an image.
        
        Args:
            image_path: Path to image
            surrounding_text: Text surrounding the image in the document
        
        Returns:
            Caption string
        """
        # For now, use filename and surrounding text
        # In future, could add image captioning model
        
        filename = Path(image_path).stem
        
        if surrounding_text:
            # Look for common caption patterns
            caption_patterns = [
                r'Figure \d+:?\s*([^\n]+)',
                r'Diagram \d+:?\s*([^\n]+)',
                r'Graph \d+:?\s*([^\n]+)',
            ]
            
            import re
            for pattern in caption_patterns:
                match = re.search(pattern, surrounding_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return filename.replace('_', ' ')
    
    def save_projector(self, path: str):
        """Save projection layer weights."""
        torch.save(self.projector.state_dict(), path)
        logger.info(f"💾 Saved projector weights to: {path}")
    
    def load_projector(self, path: str):
        """Load projection layer weights."""
        self.projector.load_state_dict(torch.load(path, map_location=self.device))
        logger.info(f"📂 Loaded projector weights from: {path}")


if __name__ == "__main__":
    # Test the processor
    logging.basicConfig(level=logging.INFO)
    
    processor = ImageProcessor()
    
    # Example usage (replace with actual image path)
    # embedding = processor.embed_image("sample_diagram.png")
    # print(f"Embedding shape: {embedding.shape}")
    # print(f"Embedding norm: {np.linalg.norm(embedding)}")
    
    print("✅ Image processor ready for use")
    print(f"   Model device: {processor.device}")
    print(f"   Output dimension: 768")
