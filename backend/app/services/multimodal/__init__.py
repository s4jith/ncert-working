"""
Multimodal Embedding & Retrieval System for NCERT Mathematics

A production-grade pipeline for processing mathematical content with:
- Text embeddings (theory, questions, solutions)
- Formula extraction & LaTeX embeddings
- Image embeddings (diagrams, graphs, figures)
- Intelligent semantic chunking
- Pinecone storage with rich metadata
- Multimodal query retrieval

Architecture:
    PDF → Processor → Chunker → Embedder → Pinecone
         ↓           ↓          ↓
    Text+Images  Formulas   768-dim vectors
"""

# Note: Import from math/ subdirectory directly if needed
# These base classes are placeholders, actual implementations in math/ and physics/

try:
    from .pdf_processor import PDFProcessor
except ImportError:
    PDFProcessor = None

try:
    from .formula_extractor import FormulaExtractor
except ImportError:
    FormulaExtractor = None

try:
    from .image_processor import ImageProcessor
except ImportError:
    ImageProcessor = None

try:
    from .chunker import MathChunker
except ImportError:
    MathChunker = None

try:
    from .embedder import MultimodalEmbedder
except ImportError:
    MultimodalEmbedder = None

try:
    from .uploader import PineconeUploader
except ImportError:
    PineconeUploader = None

__all__ = [
    'PDFProcessor',
    'FormulaExtractor',
    'ImageProcessor',
    'MathChunker',
    'MultimodalEmbedder',
    'PineconeUploader'
]

__version__ = '1.0.0'
