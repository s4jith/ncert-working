"""
OpenVINO Vision Service for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO Runtime for image analysis on Intel CPU/iGPU.

Intel OpenVINO-based image analysis service for educational content.
Analyzes student-uploaded images (textbook pages, diagrams, handwritten questions)
and extracts text/visual information for RAG processing.

This module provides:
- Image type classification (textbook, diagram, handwritten, formula)
- Text extraction via OpenVinoOCRService
- Visual content description generation

Maps to OPEA IngestionService image analysis component.
"""

import logging
from typing import Optional, Dict
import numpy as np
import cv2

from app.services.openvino_ocr_service import get_openvino_ocr_service, OpenVinoOCRService

logger = logging.getLogger(__name__)


class OpenVinoVisionService:
    """
    Intel OpenVINO-based vision service for educational image analysis.
    
    Analyzes images uploaded by students and extracts:
    - Text content via OCR
    - Image type classification
    - Visual content description
    
    Example:
        vision_service = OpenVinoVisionService()
        result = vision_service.analyze_image(image_array)
        # Returns: {"text": "...", "image_type": "textbook", "confidence": 0.9, "description": "..."}
    """
    
    # Image type categories
    IMAGE_TYPES = ["textbook", "diagram", "handwritten", "formula", "mixed"]
    
    def __init__(self, device: str = "CPU"):
        """
        Initialize the OpenVINO Vision Service.
        
        Args:
            device: OpenVINO device to use (CPU, GPU, AUTO)
        """
        self.device = device
        self._ocr_service: Optional[OpenVinoOCRService] = None
        
        logger.info(f"✓ OpenVinoVisionService initialized (device: {device})")
    
    @property
    def ocr_service(self) -> OpenVinoOCRService:
        """Lazy-load OCR service to avoid initialization overhead."""
        if self._ocr_service is None:
            self._ocr_service = get_openvino_ocr_service(device=self.device)
        return self._ocr_service
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for analysis.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        if image is None or image.size == 0:
            raise ValueError("Empty or invalid image provided")
        
        # Ensure image is in BGR format (OpenCV default)
        if len(image.shape) == 2:
            # Grayscale - convert to BGR
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            # RGBA - convert to BGR
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        elif image.shape[2] == 3:
            # Could be RGB - convert to BGR for OpenCV
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        return image
    
    def _classify_image_type(self, image: np.ndarray, ocr_text: str) -> tuple:
        """
        Classify the type of educational image.
        
        Uses heuristics based on:
        - Text density (OCR results)
        - Edge detection (for diagrams)
        - Visual features
        
        Args:
            image: Input image
            ocr_text: Extracted OCR text
            
        Returns:
            Tuple of (image_type, confidence)
        """
        height, width = image.shape[:2]
        total_pixels = height * width
        
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate text density
        text_length = len(ocr_text.strip())
        text_density = text_length / (total_pixels / 10000)  # Words per 10k pixels
        
        # Edge detection for diagram detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / total_pixels
        
        # Analyze contours for shapes (diagrams typically have more geometric shapes)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        shape_count = len(contours)
        
        # Calculate variance in pixel intensity (handwritten tends to have more variation)
        intensity_variance = np.var(gray)
        
        # Heuristic classification
        confidence = 0.7  # Base confidence
        
        if text_density > 50 and edge_density < 0.1:
            # High text, low edges = textbook page
            image_type = "textbook"
            confidence = min(0.95, 0.7 + text_density / 200)
        
        elif edge_density > 0.15 and shape_count > 20:
            # High edges, many shapes = diagram
            image_type = "diagram"
            confidence = min(0.9, 0.6 + edge_density * 2)
        
        elif intensity_variance > 2000 and text_density < 30:
            # High variance, less structured text = handwritten
            image_type = "handwritten"
            confidence = min(0.85, 0.6 + (intensity_variance / 5000))
        
        elif self._detect_formula_patterns(ocr_text):
            # Contains mathematical patterns
            image_type = "formula"
            confidence = 0.8
        
        else:
            # Mixed or unclear
            image_type = "mixed"
            confidence = 0.6
        
        return image_type, confidence
    
    def _detect_formula_patterns(self, text: str) -> bool:
        """Detect if text contains mathematical formula patterns."""
        # Common formula indicators
        formula_indicators = [
            '=', '+', '-', '*', '/', '^',  # Operators
            'sin', 'cos', 'tan', 'log', 'ln',  # Functions
            'sqrt', '∫', '∑', 'π', 'θ',  # Math symbols
            'x', 'y', 'z',  # Variables (if surrounded by operators)
        ]
        
        # Count formula indicators
        indicator_count = sum(1 for ind in formula_indicators if ind in text.lower())
        
        # Check for equation patterns like "a = b" or "f(x)"
        has_equation = '=' in text
        has_function_notation = '(' in text and ')' in text
        
        return indicator_count >= 3 or (has_equation and indicator_count >= 2)
    
    def _generate_description(self, image: np.ndarray, ocr_text: str, image_type: str) -> str:
        """
        Generate a brief description of the image content.
        
        Args:
            image: Input image
            ocr_text: Extracted OCR text
            image_type: Classified image type
            
        Returns:
            Brief description string
        """
        height, width = image.shape[:2]
        text_preview = ocr_text[:100].strip() if ocr_text else "No text detected"
        
        descriptions = {
            "textbook": f"Textbook page ({width}x{height}px) with educational content. Preview: \"{text_preview}...\"",
            "diagram": f"Educational diagram ({width}x{height}px) with visual elements. Text found: \"{text_preview}...\"",
            "handwritten": f"Handwritten content ({width}x{height}px). Detected text: \"{text_preview}...\"",
            "formula": f"Mathematical content ({width}x{height}px) with formulas. Content: \"{text_preview}...\"",
            "mixed": f"Mixed content image ({width}x{height}px). Contains: \"{text_preview}...\""
        }
        
        return descriptions.get(image_type, f"Image ({width}x{height}px)")
    
    def analyze_image(self, image: np.ndarray) -> Dict:
        """
        Analyze a student-uploaded image.
        
        Main method for image analysis. Extracts text, classifies image type,
        and generates a description suitable for RAG processing.
        
        Args:
            image: Input image as numpy array (H, W, C) from file upload
            
        Returns:
            Dictionary with:
            - text: Extracted OCR text
            - image_type: Classification (textbook/diagram/handwritten/formula/mixed)
            - confidence: Classification confidence (0-1)
            - description: Brief description of visual content
        """
        try:
            logger.info("🖼️ Analyzing image...")
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text using OpenVINO OCR
            logger.info("📝 Extracting text with OpenVINO OCR...")
            ocr_text = self.ocr_service.read_text_from_image(processed_image)
            logger.info(f"   Extracted {len(ocr_text)} characters")
            
            # Classify image type
            logger.info("🏷️ Classifying image type...")
            image_type, confidence = self._classify_image_type(processed_image, ocr_text)
            logger.info(f"   Type: {image_type} (confidence: {confidence:.2f})")
            
            # Generate description
            description = self._generate_description(processed_image, ocr_text, image_type)
            
            result = {
                "text": ocr_text,
                "image_type": image_type,
                "confidence": round(confidence, 2),
                "description": description
            }
            
            logger.info(f"✅ Image analysis complete: {image_type}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {e}")
            return {
                "text": "",
                "image_type": "unknown",
                "confidence": 0.0,
                "description": f"Analysis failed: {str(e)}"
            }
    
    def is_available(self) -> bool:
        """Check if the vision service is ready to use."""
        try:
            return self.ocr_service.is_available()
        except Exception:
            return False


# Singleton instance for reuse
_vision_service_instance: Optional[OpenVinoVisionService] = None


def get_openvino_vision_service(device: str = "CPU") -> OpenVinoVisionService:
    """
    Get or create the OpenVINO Vision service singleton.
    
    Args:
        device: OpenVINO device (CPU, GPU, AUTO)
        
    Returns:
        OpenVinoVisionService instance
    """
    global _vision_service_instance
    
    if _vision_service_instance is None:
        _vision_service_instance = OpenVinoVisionService(device=device)
    
    return _vision_service_instance
