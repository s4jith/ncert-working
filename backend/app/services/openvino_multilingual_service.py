"""
OpenVINO Multilingual NLP Service for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO Runtime for multilingual embeddings on Intel CPU/iGPU.

Supports Indian languages:
- Hindi (hi), Tamil (ta), Urdu (ur), Bengali (bn), Marathi (mr)
- Kannada (kn), Telugu (te), Malayalam (ml), Gujarati (gu), Punjabi (pa)
- Odia (or), Assamese (as), Sanskrit (sa), Nepali (ne)

Uses LaBSE (Language-agnostic BERT Sentence Embedding) converted to OpenVINO IR
for cross-lingual semantic similarity across all supported languages.

Maps to OPEA IngestionService and RetrievalService multilingual component.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import openvino as ov
    HAS_OPENVINO = True
except ImportError:
    HAS_OPENVINO = False

try:
    from langdetect import detect, detect_langs, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

from app.utils.performance_logger import measure_latency

logger = logging.getLogger(__name__)


# Supported Indian languages with their ISO 639-1 codes
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "ur": "Urdu",
    "bn": "Bengali",
    "mr": "Marathi",
    "kn": "Kannada",
    "te": "Telugu",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "sa": "Sanskrit",
    "ne": "Nepali"
}

# Unicode ranges for Indian scripts (for fallback detection)
SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi, Marathi, Sanskrit, Nepali)
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "ur": (0x0600, 0x06FF),  # Arabic (Urdu uses Arabic script)
    "bn": (0x0980, 0x09FF),  # Bengali/Assamese
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "te": (0x0C00, 0x0C7F),  # Telugu
    "ml": (0x0D00, 0x0D7F),  # Malayalam
    "gu": (0x0A80, 0x0AFF),  # Gujarati
    "pa": (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
    "or": (0x0B00, 0x0B7F),  # Odia
}


class OpenVinoMultilingualService:
    """
    Intel OpenVINO-based multilingual NLP service.
    
    Intel-optimized: Uses LaBSE model converted to OpenVINO IR for
    cross-lingual embeddings on Intel CPU/iGPU.
    
    Features:
    - Multilingual embedding generation (768-dim, same as Gemini)
    - Language detection for Indian languages
    - Cross-lingual semantic search (Hindi query finds English content)
    
    Example:
        service = OpenVinoMultilingualService()
        embedding = service.generate_embedding("फोटोसिंथेसिस क्या है?", "hi")
        lang = service.detect_language("ஆக்ஸிஜனேஷன் என்றால் என்ன?")  # Returns "ta"
    """
    
    DEFAULT_MODEL_PATH = "models/openvino_multilingual"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "CPU"
    ):
        """
        Initialize the OpenVINO Multilingual Service.
        
        Args:
            model_path: Path to OpenVINO IR model directory
            device: OpenVINO device (CPU, GPU, AUTO)
        """
        self.device = device
        self._model = None
        self._tokenizer = None
        self._is_loaded = False
        self._load_error = None
        
        # Set model path
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                self.DEFAULT_MODEL_PATH
            )
        self.model_path = Path(model_path)
        
        # Try to load model
        self._try_load_model()
        
        logger.info(f"✓ OpenVinoMultilingualService initialized (device: {device}, loaded: {self._is_loaded})")
    
    def _try_load_model(self) -> None:
        """Attempt to load the OpenVINO LaBSE model."""
        if not HAS_OPENVINO:
            self._load_error = "OpenVINO not installed. Run: pip install openvino>=2024.0.0"
            logger.warning(f"⚠️ {self._load_error}")
            return
        
        if not self.model_path.exists():
            self._load_error = f"Model not found at {self.model_path}. Run setup_multilingual_model.py first."
            logger.warning(f"⚠️ {self._load_error}")
            return
        
        try:
            logger.info(f"Loading OpenVINO multilingual model from {self.model_path}...")
            
            # Check for optimum-intel model structure
            model_xml = self.model_path / "openvino_model.xml"
            if not model_xml.exists():
                model_xml = self.model_path / "model.xml"
            
            if model_xml.exists():
                # Load using OpenVINO Core
                core = ov.Core()
                self._model = core.compile_model(str(model_xml), self.device)
                
                # Load tokenizer
                try:
                    from transformers import AutoTokenizer
                    self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
                except:
                    # Fallback: try loading from HuggingFace directly
                    self._tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/LaBSE")
                
                self._is_loaded = True
                logger.info("✓ OpenVINO multilingual model loaded successfully")
            else:
                self._load_error = f"OpenVINO model files not found in {self.model_path}"
                logger.warning(f"⚠️ {self._load_error}")
                
        except Exception as e:
            self._load_error = f"Failed to load model: {e}"
            logger.error(f"❌ {self._load_error}")
    
    def is_available(self) -> bool:
        """Check if the multilingual service is ready."""
        return self._is_loaded and self._model is not None
    
    def get_status(self) -> Dict:
        """Get service status information."""
        return {
            "available": self.is_available(),
            "device": self.device,
            "model_path": str(self.model_path),
            "error": self._load_error,
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "has_langdetect": HAS_LANGDETECT
        }
    
    @measure_latency("multilingual_embedding")
    def generate_embedding(self, text: str, language: str = "auto") -> List[float]:
        """
        Generate multilingual embedding using OpenVINO LaBSE.
        
        Intel-optimized: Runs on Intel CPU/iGPU via OpenVINO Runtime.
        
        Args:
            text: Input text (can be in any supported language)
            language: Language hint (optional, for optimization)
        
        Returns:
            768-dimensional embedding vector (cross-lingual)
        """
        if not self.is_available():
            # Fallback to Gemini embeddings
            logger.warning("OpenVINO multilingual model not available, falling back to Gemini")
            return self._fallback_embedding(text)
        
        try:
            # Tokenize
            inputs = self._tokenizer(
                text,
                return_tensors="np",
                max_length=512,
                truncation=True,
                padding=True
            )
            
            # Run inference
            output = self._model(inputs)
            
            # Get sentence embedding (mean pooling or [CLS] token)
            if hasattr(output, 'last_hidden_state'):
                # Mean pooling
                embeddings = output.last_hidden_state
                attention_mask = inputs['attention_mask']
                mask_expanded = np.expand_dims(attention_mask, -1)
                sum_embeddings = np.sum(embeddings * mask_expanded, axis=1)
                sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
                embedding = (sum_embeddings / sum_mask)[0]
            else:
                # Direct output (sentence embedding)
                embedding = output[0][0]
            
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback to Gemini embeddings when OpenVINO unavailable."""
        try:
            import google.generativeai as genai
            from app.services.gemini_key_manager import gemini_key_manager
            
            api_key = gemini_key_manager.get_available_key()
            genai.configure(api_key=api_key)
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Fallback embedding failed: {e}")
            return [0.0] * 768  # Return zero vector
    
    @measure_latency("language_detection")
    def detect_language(self, text: str) -> str:
        """
        Detect language of input text.
        
        Supports all major Indian languages plus English.
        Uses langdetect library with fallback to Unicode script detection.
        
        Args:
            text: Input text
        
        Returns:
            ISO 639-1 language code: "en", "hi", "ta", "ur", etc.
        """
        if not text or len(text.strip()) < 3:
            return "en"
        
        # Try langdetect first
        if HAS_LANGDETECT:
            try:
                detected = detect(text)
                if detected in SUPPORTED_LANGUAGES:
                    return detected
                # Map similar languages
                if detected in ["mr", "ne", "sa"]:
                    return "hi"  # Same script as Hindi
                if detected in ["as"]:
                    return "bn"  # Same script as Bengali
            except LangDetectException:
                pass
        
        # Fallback: Unicode script detection
        return self._detect_by_script(text)
    
    def _detect_by_script(self, text: str) -> str:
        """Detect language based on Unicode script ranges."""
        script_counts = {lang: 0 for lang in SCRIPT_RANGES}
        
        for char in text:
            code = ord(char)
            for lang, (start, end) in SCRIPT_RANGES.items():
                if start <= code <= end:
                    script_counts[lang] += 1
                    break
        
        # Find dominant script
        max_count = max(script_counts.values())
        if max_count > 0:
            for lang, count in script_counts.items():
                if count == max_count:
                    return lang
        
        # Default to English
        return "en"
    
    def detect_language_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Detect language with confidence score.
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not text or len(text.strip()) < 3:
            return "en", 1.0
        
        if HAS_LANGDETECT:
            try:
                langs = detect_langs(text)
                if langs:
                    top_lang = langs[0]
                    lang_code = top_lang.lang
                    confidence = top_lang.prob
                    
                    if lang_code in SUPPORTED_LANGUAGES:
                        return lang_code, confidence
                    
                    # Map similar languages
                    if lang_code in ["mr", "ne", "sa"]:
                        return "hi", confidence * 0.9
                    if lang_code in ["as"]:
                        return "bn", confidence * 0.9
            except LangDetectException:
                pass
        
        # Fallback with fixed confidence
        lang = self._detect_by_script(text)
        return lang, 0.7 if lang != "en" else 0.8
    
    def get_language_name(self, code: str) -> str:
        """Get full language name from code."""
        return SUPPORTED_LANGUAGES.get(code, "Unknown")
    
    def is_indic_language(self, code: str) -> bool:
        """Check if language code is an Indian language."""
        return code in SUPPORTED_LANGUAGES and code != "en"


# Singleton instance
_multilingual_service_instance: Optional[OpenVinoMultilingualService] = None


def get_multilingual_service(device: str = "CPU") -> OpenVinoMultilingualService:
    """
    Get or create the OpenVINO Multilingual service singleton.
    
    Args:
        device: OpenVINO device (CPU, GPU, AUTO)
    
    Returns:
        OpenVinoMultilingualService instance
    """
    global _multilingual_service_instance
    
    if _multilingual_service_instance is None:
        _multilingual_service_instance = OpenVinoMultilingualService(device=device)
    
    return _multilingual_service_instance


# Convenience instance
multilingual_service = get_multilingual_service()
