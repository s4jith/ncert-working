"""
OpenVINO OCR Service for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO Runtime for text detection and recognition on Intel CPU/iGPU.

Intel OpenVINO-based OCR service that replaces Tesseract for scanned PDF pages.
Uses Intel's horizontal-text-detection-0001 and text-recognition-0014 models.

This module provides:
- OpenVINO model loading and management
- Text detection and recognition pipeline
- Image preprocessing for optimal OCR results

Maps to OPEA IngestionService OCR component.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import openvino as ov
    HAS_OPENVINO = True
except ImportError:
    HAS_OPENVINO = False
    ov = None

logger = logging.getLogger(__name__)

if not HAS_OPENVINO:
    logger.warning("⚠️ OpenVINO not installed. OCR service will be disabled. Install with: pip install openvino>=2024.0.0")


# Character list for text-recognition-0014 model (alphanumeric + special)
CHARS = "0123456789abcdefghijklmnopqrstuvwxyz#"


class OpenVinoOCRService:
    """
    OpenVINO-based OCR service for extracting text from images.
    
    Uses Intel's Open Model Zoo models:
    - horizontal-text-detection-0001: Detects text regions in images
    - text-recognition-0014: Recognizes text from detected regions
    
    Example:
        ocr_service = OpenVinoOCRService(device="CPU")
        text = ocr_service.read_text_from_image(page_image)
    """
    
    # Model URLs from Intel Open Model Zoo
    DETECTION_MODEL_URL = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/horizontal-text-detection-0001/FP16/horizontal-text-detection-0001.xml"
    RECOGNITION_MODEL_URL = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1/text-recognition-0014/FP16/text-recognition-0014.xml"
    
    def __init__(
        self,
        device: str = "CPU", 
        model_dir: Optional[str] = None,
        detection_confidence: float = 0.5
    ):
        """
        Initialize the OpenVINO OCR service.
        
        Args:
            device: OpenVINO device to use (CPU, GPU, AUTO)
            model_dir: Directory to store/load models (default: models/openvino)
            detection_confidence: Minimum confidence for text detection (0-1)
        """
        self.device = device
        self.detection_confidence = detection_confidence
        self._is_available = False
        
        # Check OpenVINO availability
        if not HAS_OPENVINO:
            logger.warning("OpenVINO not available - OCR service disabled")
            self.core = None
            self._detection_model = None
            self._recognition_model = None
            return
        
        if not HAS_CV2:
            logger.warning("OpenCV not available - OCR service disabled")
            self.core = None
            self._detection_model = None
            self._recognition_model = None
            return
        
        # Set up model directory
        if model_dir is None: 
            model_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models", "openvino"
            )
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize OpenVINO Core
            self.core = ov.Core()
            
            # Load models
            self._detection_model = None
            self._recognition_model = None
            self._load_models()
            self._is_available = True
            
            logger.info(f"✓ OpenVinoOCRService initialized (device: {device})")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenVINO OCR: {e}")
            self.core = None
            self._detection_model = None
            self._recognition_model = None
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self._is_available and self._detection_model is not None
    
    def _download_model(self, url: str, model_name: str) -> Path:
        """Download model files if not already present."""
        import requests
        
        model_subdir = self.model_dir / model_name / "FP16"
        model_subdir.mkdir(parents=True, exist_ok=True)
        
        xml_path = model_subdir / f"{model_name}.xml"
        bin_path = model_subdir / f"{model_name}.bin"
        
        if not xml_path.exists():
            logger.info(f"Downloading {model_name}.xml...")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            xml_path.write_bytes(response.content)
        
        bin_url = url.replace(".xml", ".bin")
        if not bin_path.exists():
            logger.info(f"Downloading {model_name}.bin...")
            response = requests.get(bin_url, timeout=120)
            response.raise_for_status()
            bin_path.write_bytes(response.content)
        
        return xml_path
    
    def _load_models(self) -> None:
        """Load detection and recognition models."""
        try:
            # Download and load detection model
            det_path = self._download_model(
                self.DETECTION_MODEL_URL,
                "horizontal-text-detection-0001"
            )
            det_model = self.core.read_model(det_path)
            self._detection_model = self.core.compile_model(det_model, self.device)
            self._det_input_layer = self._detection_model.input(0)
            self._det_output_layer = self._detection_model.output(0)
            
            # Download and load recognition model
            rec_path = self._download_model(
                self.RECOGNITION_MODEL_URL,
                "text-recognition-0014"
            )
            rec_model = self.core.read_model(rec_path)
            self._recognition_model = self.core.compile_model(rec_model, self.device)
            self._rec_input_layer = self._recognition_model.input(0)
            self._rec_output_layer = self._recognition_model.output(0)
            
            logger.info("✓ OpenVINO OCR models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load OpenVINO models: {e}")
            raise
    
    def _preprocess_for_detection(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Preprocess image for text detection model.
        
        Args:
            image: Input image as numpy array (H, W, C) in RGB or BGR format
            
        Returns:
            Tuple of (preprocessed_image, original_size)
        """
        original_size = (image.shape[1], image.shape[0])  # (width, height)
        
        # Get expected input shape from model
        _, _, h, w = self._det_input_layer.shape
        
        # Resize image
        resized = cv2.resize(image, (w, h))
        
        # Convert to float and normalize
        input_image = resized.astype(np.float32)
        
        # Transpose from HWC to CHW format
        input_image = input_image.transpose((2, 0, 1))
        
        # Add batch dimension: (1, C, H, W)
        input_image = np.expand_dims(input_image, axis=0)
        
        return input_image, original_size
    
    def _detect_text_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Detect text regions in the image.
        
        horizontal-text-detection-0001 outputs:
        - boxes: [100, 5] with [x_min, y_min, x_max, y_max, confidence]
        - Coordinates are in input image scale (704x704), need to rescale to original
        
        Args:
            image: Input image (H, W, C)
            
        Returns:
            List of bounding boxes as numpy arrays [x1, y1, x2, y2]
        """
        input_image, original_size = self._preprocess_for_detection(image)
        
        # Run detection
        result = self._detection_model([input_image])[self._det_output_layer]
        
        # Parse detections - horizontal-text-detection-0001 outputs [N, 5] format
        # Each detection: [x_min, y_min, x_max, y_max, confidence]
        boxes = []
        _, _, model_h, model_w = self._det_input_layer.shape
        
        # Flatten if needed and ensure we have the right shape
        detections = result.reshape(-1, 5) if result.size >= 5 else np.array([]).reshape(0, 5)
        
        # Scale factors to convert from model input size to original image size
        scale_x = original_size[0] / model_w
        scale_y = original_size[1] / model_h
        
        for detection in detections:
            # Format: [x_min, y_min, x_max, y_max, confidence]
            confidence = float(detection[4])
            
            if confidence > self.detection_confidence:
                # Scale coordinates from model input size to original image size
                x1 = int(float(detection[0]) * scale_x)
                y1 = int(float(detection[1]) * scale_y)
                x2 = int(float(detection[2]) * scale_x)
                y2 = int(float(detection[3]) * scale_y)
                
                # Ensure valid coordinates
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(original_size[0], x2), min(original_size[1], y2)
                
                if x2 > x1 and y2 > y1:
                    boxes.append(np.array([x1, y1, x2, y2]))
        
        # Sort boxes by y then x (reading order)
        if boxes:
            boxes = sorted(boxes, key=lambda b: (b[1] // 30, b[0]))
        
        return boxes
    
    def _preprocess_for_recognition(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess a text region crop for recognition.
        
        Args:
            image: Cropped text region (H, W, C)
            
        Returns:
            Preprocessed image for recognition model
        """
        # Get expected input shape: (1, 1, 32, 120) for text-recognition-0014
        _, c, h, w = self._rec_input_layer.shape
        
        # Convert to grayscale if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Resize to model input size
        resized = cv2.resize(gray, (w, h))
        
        # Normalize
        input_image = resized.astype(np.float32) / 255.0
        
        # Add channel and batch dimensions: (1, 1, H, W)
        input_image = np.expand_dims(input_image, axis=(0, 1))
        
        return input_image
    
    def _decode_recognition_output(self, output: np.ndarray) -> str:
        """
        Decode the recognition model output to text.
        
        Uses CTC decoding with the character set.
        
        Args:
            output: Model output tensor
            
        Returns:
            Decoded text string
        """
        # Output shape: (1, W, num_classes) or similar
        # Get most likely character at each position
        output = np.squeeze(output)
        
        # Ensure output has at least 2 dimensions for argmax
        if output.ndim == 0:
            # Scalar - nothing to decode
            return ""
        elif output.ndim == 1:
            # Single timestep - reshape to (1, num_classes)
            output = output.reshape(1, -1)
        
        # Argmax to get character indices (along the last axis for classes)
        char_indices = np.argmax(output, axis=-1)
        
        # Ensure char_indices is iterable (convert scalar to array if needed)
        if char_indices.ndim == 0:
            char_indices = np.array([char_indices.item()])
        else:
            char_indices = char_indices.flatten()
        
        # CTC decoding: remove blanks and duplicates
        decoded = []
        prev_char = None
        blank_index = len(CHARS) - 1  # '#' is blank
        
        for idx in char_indices:
            idx_val = int(idx) if hasattr(idx, '__int__') else idx
            if idx_val != blank_index and idx_val != prev_char:
                if idx_val < len(CHARS) - 1:  # Exclude blank character
                    decoded.append(CHARS[idx_val])
            prev_char = idx_val
        
        return "".join(decoded)
    
    def _recognize_text(self, image: np.ndarray, box: np.ndarray) -> str:
        """
        Recognize text from a detected region.
        
        Args:
            image: Full input image
            box: Bounding box [x1, y1, x2, y2]
            
        Returns:
            Recognized text string
        """
        # Crop the text region
        x1, y1, x2, y2 = box
        crop = image[y1:y2, x1:x2]
        
        if crop.size == 0:
            return ""
        
        # Preprocess for recognition
        input_image = self._preprocess_for_recognition(crop)
        
        # Run recognition
        result = self._recognition_model([input_image])[self._rec_output_layer]
        
        # Decode output
        text = self._decode_recognition_output(result)
        
        return text
    
    def read_text_from_image(self, image: np.ndarray) -> str:
        """
        Extract text from an image using OpenVINO OCR.
        
        This is the main method to call for OCR. It:
        1. Detects text regions in the image
        2. Recognizes text from each region
        3. Combines results in reading order
        
        Args:
            image: Input image as numpy array (H, W, C) in RGB or BGR format
                   Typically from pdf2image or PIL Image converted to numpy
            
        Returns:
            Extracted text as a single string with newlines between detected regions
        """
        if image is None or image.size == 0:
            logger.warning("Empty image provided to OCR")
            return ""
        
        # Ensure image is in correct format
        if len(image.shape) == 2:
            # Grayscale - convert to BGR
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            # RGBA - convert to BGR
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        elif image.shape[2] == 3:
            # Could be RGB or BGR - model expects RGB values
            pass
        
        try:
            # Detect text regions
            boxes = self._detect_text_regions(image)
            
            if not boxes:
                logger.debug("No text regions detected in image")
                return ""
            
            # Recognize text from each region
            recognized_texts = []
            for box in boxes:
                text = self._recognize_text(image, box)
                if text.strip():
                    recognized_texts.append(text)
            
            # Combine results
            full_text = " ".join(recognized_texts)
            
            logger.debug(f"OCR extracted {len(recognized_texts)} text regions")
            return full_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return ""
    
    def is_available(self) -> bool:
        """Check if the OCR service is ready to use."""
        return (
            self._detection_model is not None and 
            self._recognition_model is not None
        )


# Singleton instance for reuse
_ocr_service_instance: Optional[OpenVinoOCRService] = None


def get_openvino_ocr_service(
    device: str = "CPU",
    model_dir: Optional[str] = None
) -> OpenVinoOCRService:
    """
    Get or create the OpenVINO OCR service singleton.
    
    Args:
        device: OpenVINO device (CPU, GPU, AUTO)
        model_dir: Optional model directory path
        
    Returns:
        OpenVinoOCRService instance
    """
    global _ocr_service_instance
    
    if _ocr_service_instance is None:
        _ocr_service_instance = OpenVinoOCRService(
            device=device,
            model_dir=model_dir
        )
    
    return _ocr_service_instance
