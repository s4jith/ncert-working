"""
Physics Multimodal Module

This module contains all components for processing NCERT Physics content:
- PDF extraction (text, formulas, diagrams, tables, experiments)
- Formula detection (physics-specific: F=ma, V=IR, KE, PE, etc.)
- Diagram processing (circuit diagrams, ray diagrams, force diagrams, graphs)
- Table extraction and parsing
- Semantic chunking (concept, law, derivation, numerical, solution steps, etc.)
- Embeddings generation (768-dim unified)
- Pinecone upload with physics namespace

All components are optimized for physics content with support for:
- Laws and principles
- Derivations (step-by-step)
- Numerical problems and solutions
- Experiments (aim, apparatus, theory, procedure)
- Diagrams (force, circuit, ray, velocity-time plots)
- Tables (experiment data)
"""

from .physics_pdf_processor import PhysicsPDFProcessor
from .physics_formula_extractor import PhysicsFormulaExtractor
from .physics_chunker import PhysicsChunker
from .physics_embedder import PhysicsEmbedder
from .physics_uploader import PhysicsUploader
from .physics_retrieval import PhysicsRetrieval

__all__ = [
    'PhysicsPDFProcessor',
    'PhysicsFormulaExtractor',
    'PhysicsChunker',
    'PhysicsEmbedder',
    'PhysicsUploader',
    'PhysicsRetrieval'
]
