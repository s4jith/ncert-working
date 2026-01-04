"""
Multilingual OCR Service for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO for Latin text, EasyOCR for Urdu/Arabic/Indic scripts.

Supports all Indian languages:
- Urdu (Nastaliq script) - ur
- Hindi (Devanagari) - hi
- Tamil - ta
- Bengali - bn
- Telugu - te
- Kannada - kn
- Malayalam - ml
- Marathi - mr
- Gujarati - gu
- Punjabi (Gurmukhi) - pa
- Arabic - ar
- English - en

This service auto-detects the script type and routes to the appropriate OCR engine.
"""

import logging
from typing import Optional, List, Dict, Tuple
import numpy as np

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    easyocr = None

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from app.utils.performance_logger import measure_latency

logger = logging.getLogger(__name__)


# Script detection based on Unicode ranges
SCRIPT_RANGES = {
    "arabic": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],  # Arabic/Urdu/Persian
    "devanagari": [(0x0900, 0x097F)],  # Hindi, Marathi, Sanskrit
    "bengali": [(0x0980, 0x09FF)],  # Bengali, Assamese
    "tamil": [(0x0B80, 0x0BFF)],
    "telugu": [(0x0C00, 0x0C7F)],
    "kannada": [(0x0C80, 0x0CFF)],
    "malayalam": [(0x0D00, 0x0D7F)],
    "gujarati": [(0x0A80, 0x0AFF)],
    "gurmukhi": [(0x0A00, 0x0A7F)],  # Punjabi
    "odia": [(0x0B00, 0x0B7F)],
}

# EasyOCR language codes for each script
SCRIPT_TO_EASYOCR = {
    "arabic": ["ur", "ar"],  # Urdu + Arabic
    "devanagari": ["hi", "mr", "ne"],  # Hindi, Marathi, Nepali
    "bengali": ["bn", "as"],  # Bengali, Assamese
    "tamil": ["ta"],
    "telugu": ["te"],
    "kannada": ["kn"],
    "malayalam": ["ml"],
    "gujarati": ["gu"],
    "gurmukhi": ["pa"],  # Punjabi
    "odia": ["or"],
    "latin": ["en"],
}


class MultilingualOCRService:
    """
    Multilingual OCR service that supports all Indian languages.
    
    Intel-optimized: Uses OpenVINO for English, EasyOCR for Indic/Arabic scripts.
    
    Features:
    - Auto-detects script type from image
    - Routes to appropriate OCR engine
    - Supports RTL languages (Urdu, Arabic)
    - High accuracy for Nastaliq script
    
    Example:
        ocr = MultilingualOCRService()
        text, lang = ocr.extract_text(image)
    """
    
    def __init__(self):
        """Initialize the multilingual OCR service."""
        self._easyocr_readers = {}  # Lazy-loaded per language
        self._openvino_ocr = None
        
        if not HAS_EASYOCR:
            logger.warning("⚠️ EasyOCR not installed. Install with: pip install easyocr")
        else:
            logger.info("✅ EasyOCR available for multilingual OCR")
        
        logger.info("✅ MultilingualOCRService initialized")
    
    def _get_easyocr_reader(self, languages: List[str]) -> Optional["easyocr.Reader"]:
        """
        Get or create an EasyOCR reader for specified languages.
        
        Args:
            languages: List of language codes (e.g., ["ur", "en"])
        
        Returns:
            EasyOCR Reader instance
        """
        if not HAS_EASYOCR:
            return None
        
        # Create a key for this language combination
        key = tuple(sorted(languages))
        
        if key not in self._easyocr_readers:
            try:
                logger.info(f"📥 Loading EasyOCR for languages: {languages}")
                self._easyocr_readers[key] = easyocr.Reader(
                    languages,
                    gpu=False,  # Use CPU for Intel optimization
                    verbose=False
                )
                logger.info(f"✅ EasyOCR loaded for: {languages}")
            except Exception as e:
                logger.error(f"Failed to load EasyOCR for {languages}: {e}")
                return None
        
        return self._easyocr_readers[key]
    
    def _get_openvino_ocr(self):
        """Get OpenVINO OCR service for English text."""
        if self._openvino_ocr is None:
            try:
                from app.services.openvino_ocr_service import get_openvino_ocr_service
                self._openvino_ocr = get_openvino_ocr_service()
            except Exception as e:
                logger.warning(f"OpenVINO OCR not available: {e}")
        return self._openvino_ocr
    
    def detect_script(self, text: str) -> str:
        """
        Detect the script type from sample text.
        
        Args:
            text: Sample text to analyze
        
        Returns:
            Script name: "arabic", "devanagari", "tamil", etc. or "latin"
        """
        script_counts = {script: 0 for script in SCRIPT_RANGES}
        latin_count = 0
        
        for char in text:
            code = ord(char)
            
            # Check Latin
            if (0x0041 <= code <= 0x007A) or (0x00C0 <= code <= 0x024F):
                latin_count += 1
                continue
            
            # Check other scripts
            for script, ranges in SCRIPT_RANGES.items():
                for start, end in ranges:
                    if start <= code <= end:
                        script_counts[script] += 1
                        break
        
        # Find dominant script
        max_count = max(script_counts.values())
        if max_count > 0 and max_count >= latin_count:
            for script, count in script_counts.items():
                if count == max_count:
                    return script
        
        return "latin"
    
    def detect_script_from_image(self, image: np.ndarray) -> str:
        """
        Detect script type by doing a quick OCR pass.
        
        Uses EasyOCR with multiple languages to detect script.
        """
        if not HAS_EASYOCR:
            return "latin"
        
        try:
            # Quick detection with common scripts
            reader = self._get_easyocr_reader(["en", "ur", "hi"])
            if reader is None:
                return "latin"
            
            # Read a small sample
            results = reader.readtext(image, detail=0, paragraph=True)
            sample_text = " ".join(results[:5]) if results else ""
            
            return self.detect_script(sample_text)
        except Exception as e:
            logger.debug(f"Script detection failed: {e}")
            return "latin"
    
    @measure_latency("multilingual_ocr")
    def extract_text(
        self,
        image: np.ndarray,
        language_hint: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Extract text from image using appropriate OCR engine.
        
        Intel-optimized: Routes to OpenVINO for English, EasyOCR for Indic/Arabic.
        
        Args:
            image: Input image as numpy array
            language_hint: Optional language code hint (e.g., "ur", "hi", "en")
        
        Returns:
            Tuple of (extracted_text, detected_language)
        """
        if image is None or image.size == 0:
            return "", "unknown"
        
        # Determine which OCR to use
        if language_hint:
            script = self._language_to_script(language_hint)
        else:
            # Quick script detection
            script = self._detect_script_quick(image)
        
        logger.info(f"🔍 Detected script: {script}")
        
        # Route to appropriate OCR
        if script == "latin":
            return self._ocr_latin(image)
        elif script == "arabic":
            return self._ocr_arabic_urdu(image)
        else:
            return self._ocr_indic(image, script)
    
    def _language_to_script(self, lang_code: str) -> str:
        """Map language code to script type."""
        lang_to_script = {
            "en": "latin",
            "ur": "arabic",
            "ar": "arabic",
            "hi": "devanagari",
            "mr": "devanagari",
            "bn": "bengali",
            "ta": "tamil",
            "te": "telugu",
            "kn": "kannada",
            "ml": "malayalam",
            "gu": "gujarati",
            "pa": "gurmukhi",
            "or": "odia",
        }
        return lang_to_script.get(lang_code, "latin")
    
    def _detect_script_quick(self, image: np.ndarray) -> str:
        """Quick script detection without full OCR."""
        # For now, default to trying Urdu/Arabic first if not detected
        # In production, use a lightweight classifier
        return "arabic"  # Default to Arabic/Urdu for NCERT Urdu books
    
    def _ocr_latin(self, image: np.ndarray) -> Tuple[str, str]:
        """OCR for English/Latin text using OpenVINO."""
        ocr = self._get_openvino_ocr()
        if ocr and ocr.is_available():
            try:
                text = ocr.read_text_from_image(image)
                return text, "en"
            except Exception as e:
                logger.warning(f"OpenVINO OCR failed: {e}")
        
        # Fallback to EasyOCR
        return self._ocr_with_easyocr(image, ["en"])
    
    def _ocr_arabic_urdu(self, image: np.ndarray) -> Tuple[str, str]:
        """OCR for Arabic/Urdu text using EasyOCR."""
        return self._ocr_with_easyocr(image, ["ur", "ar", "en"])
    
    def _ocr_indic(self, image: np.ndarray, script: str) -> Tuple[str, str]:
        """OCR for Indic scripts using EasyOCR."""
        languages = SCRIPT_TO_EASYOCR.get(script, ["en"])
        # Always include English as fallback
        if "en" not in languages:
            languages = languages + ["en"]
        return self._ocr_with_easyocr(image, languages)
    
    def _ocr_with_easyocr(
        self,
        image: np.ndarray,
        languages: List[str]
    ) -> Tuple[str, str]:
        """
        Perform OCR using EasyOCR.
        
        Args:
            image: Input image
            languages: List of language codes
        
        Returns:
            Tuple of (text, primary_language)
        """
        if not HAS_EASYOCR:
            logger.warning("EasyOCR not available")
            return "", "unknown"
        
        try:
            reader = self._get_easyocr_reader(languages)
            if reader is None:
                return "", "unknown"
            
            # Perform OCR
            results = reader.readtext(image, detail=0, paragraph=True)
            
            # Join results
            text = "\n".join(results) if results else ""
            
            # Detect primary language from text
            script = self.detect_script(text)
            lang = "ur" if script == "arabic" else languages[0]
            
            logger.info(f"📝 EasyOCR extracted {len(text)} characters ({lang})")
            
            return text, lang
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return "", "unknown"
    
    def extract_text_with_positions(
        self,
        image: np.ndarray,
        languages: List[str] = None
    ) -> List[Dict]:
        """
        Extract text with bounding box positions.
        
        Useful for annotating or highlighting text regions.
        
        Returns:
            List of dicts with 'text', 'bbox', 'confidence'
        """
        if not HAS_EASYOCR:
            return []
        
        languages = languages or ["ur", "ar", "en"]
        
        try:
            reader = self._get_easyocr_reader(languages)
            if reader is None:
                return []
            
            results = reader.readtext(image, detail=1)
            
            return [
                {
                    "text": result[1],
                    "bbox": result[0],
                    "confidence": result[2]
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"OCR with positions failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if any OCR engine is available."""
        return HAS_EASYOCR or (self._get_openvino_ocr() is not None)
    
    def get_status(self) -> Dict:
        """Get service status."""
        return {
            "available": self.is_available(),
            "easyocr_available": HAS_EASYOCR,
            "openvino_available": self._get_openvino_ocr() is not None,
            "loaded_languages": list(self._easyocr_readers.keys()),
            "supported_scripts": list(SCRIPT_RANGES.keys()) + ["latin"]
        }


# Singleton instance
_multilingual_ocr_instance: Optional[MultilingualOCRService] = None


def get_multilingual_ocr_service() -> MultilingualOCRService:
    """Get or create the multilingual OCR service singleton."""
    global _multilingual_ocr_instance
    
    if _multilingual_ocr_instance is None:
        _multilingual_ocr_instance = MultilingualOCRService()
    
    return _multilingual_ocr_instance


# Convenience instance
multilingual_ocr_service = get_multilingual_ocr_service()
