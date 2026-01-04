"""
OPEA-style Ingestion Service

Intel-optimized: Uses OpenVINO for OCR on Intel CPU/iGPU.

This service wraps the PDF processing pipeline following OPEA architecture:
- PDF → OCR (OpenVINO) → Chunk → Embedding → Pinecone Upsert

Maps to OPEA's "Ingestion Microservice" in the Enterprise RAG reference.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from app.utils.performance_logger import measure_latency, IntelOptimizedConfig
from app.services.pdf_processor import AdvancedPDFProcessor, PineconeEmbeddingUploader, ProcessingResult

logger = logging.getLogger(__name__)

# Lazy import for OCR service to avoid circular imports
def _get_ocr_service():
    try:
        from app.services.openvino_ocr_service import get_openvino_ocr_service
        return get_openvino_ocr_service()
    except Exception as e:
        logger.warning(f"OpenVINO OCR not available: {e}")
        return None


@dataclass
class IngestionConfig(IntelOptimizedConfig):
    """Configuration for Ingestion Service."""
    intel_optimized: bool = True
    component_name: str = "IngestionService"
    description: str = "OPEA-style ingestion: PDF → OCR (OpenVINO) → Chunk → Embed → Upsert"
    
    # Processing settings
    chunk_size: int = 800
    chunk_overlap: int = 150
    dpi: int = 300
    use_gemini_vision: bool = True


class IngestionService:
    """
    OPEA-style Ingestion Service for document processing pipeline.
    
    Intel-optimized: Uses OpenVinoOCRService for text extraction on Intel CPU/iGPU.
    
    Pipeline:
        1. PDF loading and page extraction
        2. OCR text extraction (OpenVINO-accelerated)
        3. Content chunking with metadata
        4. Embedding generation (Gemini text-embedding-004)
        5. Vector upsert to Pinecone
    
    This component maps to OPEA's "Ingestion Microservice" pattern.
    """
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        
        # Initialize processor with OpenVINO OCR
        self.pdf_processor = AdvancedPDFProcessor(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            dpi=self.config.dpi,
            use_gemini_vision=self.config.use_gemini_vision
        )
        
        # Embedding uploader for Pinecone
        self.embedding_uploader = PineconeEmbeddingUploader()
        
        # OpenVINO OCR service (Intel-optimized) - lazy loaded
        self._ocr_service = None
        
        logger.info(f"✅ {self.config.component_name} initialized (Intel-optimized: {self.config.intel_optimized})")
    
    @property
    def ocr_service(self):
        """Lazy load OCR service."""
        if self._ocr_service is None:
            self._ocr_service = _get_ocr_service()
        return self._ocr_service
    
    @measure_latency("ingestion_full_pipeline")
    def ingest_pdf(
        self,
        pdf_path: str,
        book_metadata: Dict,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> ProcessingResult:
        """
        Ingest a PDF document into the vector database.
        
        Intel-optimized: Uses OpenVINO OCR for text extraction.
        
        Args:
            pdf_path: Path to the PDF file
            book_metadata: Metadata dict with title, subject, class_level, chapter
            progress_callback: Optional callback for progress updates
        
        Returns:
            ProcessingResult with success status and statistics
        """
        logger.info(f"📥 [IngestionService] Starting PDF ingestion: {pdf_path}")
        logger.info(f"   Metadata: {book_metadata}")
        
        # Step 1: Process PDF (extract text, OCR, images)
        result = self.pdf_processor.process_pdf(
            pdf_path=pdf_path,
            book_metadata=book_metadata,
            progress_callback=progress_callback
        )
        
        if not result.success:
            logger.error(f"❌ [IngestionService] PDF processing failed: {result.errors}")
            return result
        
        # Step 2: Create chunks
        chunks = self.pdf_processor.create_chunks(result.pages, book_metadata)
        result.total_chunks = len(chunks)
        
        logger.info(f"📦 [IngestionService] Created {len(chunks)} chunks from {result.processed_pages} pages")
        
        # Step 3: Generate embeddings and upload to Pinecone
        namespace = book_metadata.get("subject", "general").lower().replace(" ", "_")
        
        upload_result = self.embedding_uploader.upload_chunks(
            chunks=chunks,
            namespace=namespace
        )
        
        result.total_embeddings = upload_result.get("uploaded", 0)
        
        logger.info(f"✅ [IngestionService] Ingestion complete: {result.total_embeddings} embeddings uploaded")
        
        return result
    
    @measure_latency("ocr_openvino")
    def extract_text_from_image(self, image) -> str:
        """
        Extract text from an image using OpenVINO OCR.
        
        Intel-optimized: Runs on Intel CPU/iGPU via OpenVINO Runtime.
        
        Args:
            image: numpy array or PIL Image
        
        Returns:
            Extracted text string
        """
        if self.ocr_service is None:
            logger.warning("OCR service not available")
            return ""
        return self.ocr_service.read_text_from_image(image)
    
    @measure_latency("ocr_multilingual")
    def extract_text_multilingual(self, image, language_hint: Optional[str] = None) -> tuple:
        """
        Extract text from image using multilingual OCR.
        
        Intel-optimized: Uses EasyOCR for Urdu/Arabic/Indic, OpenVINO for English.
        
        Args:
            image: numpy array or PIL Image
            language_hint: Optional language code ("ur", "hi", "ar", "en", etc.)
        
        Returns:
            Tuple of (extracted_text, detected_language)
        """
        try:
            from app.services.multilingual_ocr_service import multilingual_ocr_service
            return multilingual_ocr_service.extract_text(image, language_hint)
        except Exception as e:
            logger.warning(f"Multilingual OCR failed: {e}")
            # Fallback to OpenVINO
            text = self.extract_text_from_image(image)
            return text, "en"
    
    def detect_book_language(self, sample_image) -> str:
        """
        Detect the language of a book from a sample page image.
        
        Args:
            sample_image: First page image of the book
        
        Returns:
            Language code: "en", "ur", "hi", "ta", etc.
        """
        try:
            from app.services.multilingual_ocr_service import multilingual_ocr_service
            text, lang = multilingual_ocr_service.extract_text(sample_image)
            logger.info(f"📚 Detected book language: {lang}")
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"
    
    def get_status(self) -> Dict:
        """Get service status for Intel endpoint."""
        multilingual_status = {}
        try:
            from app.services.multilingual_ocr_service import multilingual_ocr_service
            multilingual_status = multilingual_ocr_service.get_status()
        except:
            pass
        
        return {
            "service": self.config.component_name,
            "intel_optimized": self.config.intel_optimized,
            "ocr_backend": "OpenVINO + EasyOCR",
            "embedding_model": "Gemini text-embedding-004",
            "vector_db": "Pinecone",
            "multilingual_ocr": multilingual_status
        }


# Singleton instance
ingestion_service = IngestionService()

