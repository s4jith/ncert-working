"""
Process NCERT Math PDFs with custom naming convention.
Handles: eemm101, fegp101, etc. naming patterns.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.multimodal.math.math_pdf_processor import PDFProcessor
from app.services.multimodal.math.math_formula_extractor import FormulaExtractor
from app.services.multimodal.math.math_chunker import MathChunker
from app.services.multimodal.math.math_embedder import MultimodalEmbedder
from app.services.multimodal.math.math_uploader import PineconeUploader
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ncert_math_processing.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Force stdout to use UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)


class NCERTMathProcessor:
    """Process NCERT Math PDFs with custom naming convention."""
    
    # Mapping of filename prefixes to class numbers
    CLASS_MAPPING = {
        'eemm': 5,
        'fegp': 6,
        'gegp': 7,
        'hegp': 8,
        'iemh': 9,
        'jemh': 10,
        'kemh': 11,
        'lemh': 12,
    }
    
    def __init__(self, base_path: str = None):
        """Initialize processor."""
        if base_path is None:
            base_path = Path(__file__).parent.parent / "ncert-working-dataset" / "Maths"
        
        self.base_path = Path(base_path)
        self.pdf_processor = PDFProcessor()
        self.formula_extractor = FormulaExtractor()
        self.chunker = MathChunker()
        self.embedder = MultimodalEmbedder()
        self.uploader = PineconeUploader(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_MASTER_INDEX
        )
        
        logger.info("[INIT] NCERTMathProcessor initialized")
    
    def parse_filename(self, filename: str) -> Tuple[int, int]:
        """
        Parse NCERT filename to extract class and chapter.
        
        Examples:
            eemm101.pdf -> (5, 1)
            fegp102.pdf -> (6, 2)
            lemh201.pdf -> (12, 1) [volume 2]
        
        Returns:
            (class_number, chapter_number)
        """
        # Remove .pdf extension
        name = filename.replace('.pdf', '').lower()
        
        # Extract prefix (4 letters) and numbers
        match = re.match(r'([a-z]{4})([12])(\d{2})', name)
        if not match:
            raise ValueError(f"Cannot parse filename: {filename}")
        
        prefix, volume, chapter = match.groups()
        
        # Get class number from prefix
        class_num = self.CLASS_MAPPING.get(prefix)
        if class_num is None:
            raise ValueError(f"Unknown prefix: {prefix}")
        
        chapter_num = int(chapter)
        
        return class_num, chapter_num
    
    def process_class(self, class_num: int) -> Dict:
        """
        Process all PDFs for a specific class.
        
        Args:
            class_num: Class number (5-12)
        
        Returns:
            Statistics dictionary
        """
        class_dir = self.base_path / f"class-{class_num}"
        
        if not class_dir.exists():
            logger.error(f"[ERROR] Directory not found: {class_dir}")
            return {"error": "Directory not found"}
        
        # Get all PDFs
        pdf_files = sorted(list(class_dir.glob("*.pdf")))
        
        if not pdf_files:
            logger.warning(f"[WARN] No PDFs found in {class_dir}")
            return {"error": "No PDFs found"}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"[*] Processing Class {class_num} ({len(pdf_files)} PDFs)")
        logger.info(f"{'='*60}\n")
        
        stats = {
            "class": class_num,
            "total_pdfs": len(pdf_files),
            "processed": 0,
            "failed": 0,
            "total_chunks": 0,
            "total_time": 0
        }
        
        for pdf_file in pdf_files:
            try:
                result = self.process_pdf(pdf_file)
                stats["processed"] += 1
                stats["total_chunks"] += result.get("total_chunks", 0)
                stats["total_time"] += result.get("time", 0)
            except Exception as e:
                logger.error(f"[ERROR] Failed to process {pdf_file.name}: {e}")
                stats["failed"] += 1
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"[OK] Class {class_num} Complete!")
        logger.info(f"   Processed: {stats['processed']}/{stats['total_pdfs']}")
        logger.info(f"   Total chunks: {stats['total_chunks']}")
        logger.info(f"   Total time: {stats['total_time']:.2f}s")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def process_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a single PDF through the complete pipeline.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Statistics dictionary
        """
        start_time = time.time()
        
        # Parse filename
        class_num, chapter_num = self.parse_filename(pdf_path.name)
        
        logger.info(f"\n[*] Processing: {pdf_path.name}")
        logger.info(f"   Class: {class_num}, Chapter: {chapter_num}")
        
        # Step 1: Extract content from PDF
        logger.info("   [1/5] Extracting content...")
        extracted = self.pdf_processor.process_pdf(str(pdf_path), class_num, chapter_num)
        logger.info(f"      [+] Extracted {len(extracted['text_blocks'])} text blocks")
        logger.info(f"      [+] Extracted {len(extracted['images'])} images")
        
        # Step 2: Extract formulas
        logger.info("   [2/5] Extracting formulas...")
        all_formulas = []
        for block in extracted['text_blocks']:
            formulas = self.formula_extractor.extract_formulas(block['text'])
            all_formulas.extend(formulas)
        logger.info(f"      [+] Extracted {len(all_formulas)} formulas")
        
        # Step 3: Create semantic chunks
        logger.info("   [3/5] Creating chunks...")
        chunks = self.chunker.chunk_content(
            text_blocks=extracted['text_blocks'],
            formulas=all_formulas,
            images=extracted['images'],
            class_num=class_num,
            chapter_num=chapter_num
        )
        logger.info(f"      [+] Created {len(chunks)} chunks")
        
        # Count chunk types
        chunk_types = {}
        for chunk in chunks:
            ctype = chunk.get('content_type', 'unknown')
            chunk_types[ctype] = chunk_types.get(ctype, 0) + 1
        
        logger.info("      Chunk types:")
        for ctype, count in sorted(chunk_types.items()):
            logger.info(f"         - {ctype}: {count}")
        
        # Step 4: Generate embeddings
        logger.info("   [4/5] Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks_batch(chunks)
        
        # Verify embeddings
        valid_chunks = [c for c in chunks_with_embeddings if c.get('embedding') is not None]
        logger.info(f"      [+] Generated {len(valid_chunks)}/{len(chunks)} embeddings")
        
        if valid_chunks:
            import numpy as np
            norms = [np.linalg.norm(c['embedding']) for c in valid_chunks]
            logger.info(f"      Mean embedding norm: {np.mean(norms):.4f}")
        
        # Step 5: Upload to Pinecone
        logger.info("   [5/5] Uploading to Pinecone...")
        upload_result = self.uploader.upload_chunks(
            chunks=valid_chunks,
            namespace="mathematics"
        )
        logger.info(f"      [+] Uploaded {upload_result['uploaded']}/{upload_result['total']}")
        
        elapsed = time.time() - start_time
        logger.info(f"   [OK] Complete in {elapsed:.2f}s")
        
        return {
            "filename": pdf_path.name,
            "class": class_num,
            "chapter": chapter_num,
            "total_chunks": len(valid_chunks),
            "chunk_types": chunk_types,
            "time": elapsed,
            "upload_result": upload_result
        }
    
    def process_all_classes(self, start_class: int = 5, end_class: int = 12):
        """
        Process all classes from start to end.
        
        Args:
            start_class: Starting class number (default: 5)
            end_class: Ending class number (default: 12)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[*] Processing NCERT Math Classes {start_class}-{end_class}")
        logger.info(f"{'='*60}\n")
        
        overall_start = time.time()
        overall_stats = {
            "classes_processed": 0,
            "total_pdfs": 0,
            "total_chunks": 0,
            "failed_pdfs": 0
        }
        
        for class_num in range(start_class, end_class + 1):
            try:
                stats = self.process_class(class_num)
                overall_stats["classes_processed"] += 1
                overall_stats["total_pdfs"] += stats.get("processed", 0)
                overall_stats["total_chunks"] += stats.get("total_chunks", 0)
                overall_stats["failed_pdfs"] += stats.get("failed", 0)
            except Exception as e:
                logger.error(f"[ERROR] Failed to process Class {class_num}: {e}")
        
        overall_time = time.time() - overall_start
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"[SUCCESS] ALL CLASSES COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Classes processed: {overall_stats['classes_processed']}")
        logger.info(f"Total PDFs: {overall_stats['total_pdfs']}")
        logger.info(f"Failed PDFs: {overall_stats['failed_pdfs']}")
        logger.info(f"Total chunks uploaded: {overall_stats['total_chunks']}")
        logger.info(f"Total time: {overall_time/60:.2f} minutes")
        logger.info(f"{'='*60}\n")
        
        # Check Pinecone stats
        try:
            namespace_stats = self.uploader.get_namespace_stats("mathematics")
            logger.info(f"[STATS] Pinecone Mathematics Namespace:")
            logger.info(f"   Total vectors: {namespace_stats.get('vector_count', 'N/A')}")
        except Exception as e:
            logger.warning(f"Could not get Pinecone stats: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process NCERT Math PDFs with custom naming'
    )
    parser.add_argument(
        '--class',
        type=int,
        dest='class_num',
        help='Process specific class (5-12)'
    )
    parser.add_argument(
        '--pdf',
        type=str,
        help='Process specific PDF file'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all classes (5-12)'
    )
    parser.add_argument(
        '--start',
        type=int,
        default=5,
        help='Start class number (default: 5)'
    )
    parser.add_argument(
        '--end',
        type=int,
        default=12,
        help='End class number (default: 12)'
    )
    
    args = parser.parse_args()
    
    processor = NCERTMathProcessor()
    
    if args.pdf:
        # Process single PDF
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            sys.exit(1)
        processor.process_pdf(pdf_path)
    
    elif args.class_num:
        # Process single class
        processor.process_class(args.class_num)
    
    elif args.all:
        # Process all classes
        processor.process_all_classes(args.start, args.end)
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Process all classes")
        print("  python process_ncert_maths.py --all")
        print("\n  # Process specific class")
        print("  python process_ncert_maths.py --class 5")
        print("\n  # Process classes 5-8")
        print("  python process_ncert_maths.py --all --start 5 --end 8")
        print("\n  # Process single PDF")
        print("  python process_ncert_maths.py --pdf path/to/eemm101.pdf")


if __name__ == "__main__":
    main()
