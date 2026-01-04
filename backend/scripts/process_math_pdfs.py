"""
Main Pipeline Script for Processing NCERT Math PDFs

Orchestrates the complete multimodal embedding pipeline:
PDF → Extract → Chunk → Embed → Upload to Pinecone

Usage:
    python scripts/process_math_pdfs.py --pdf path/to/class5_chapter1.pdf --class 5 --chapter 1
    python scripts/process_math_pdfs.py --batch path/to/pdfs_folder/
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import argparse
import logging
from typing import Optional
from app.services.multimodal.pdf_processor import PDFProcessor
from app.services.multimodal.formula_extractor import FormulaExtractor
from app.services.multimodal.chunker import MathChunker
from app.services.multimodal.embedder import MultimodalEmbedder
from app.services.multimodal.uploader import PineconeUploader
from app.core.config import settings
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multimodal_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MathPDFPipeline:
    """
    Complete pipeline for processing NCERT Math PDFs.
    
    Pipeline:
        1. Extract text + images from PDF
        2. Extract formulas from text
        3. Chunk content semantically
        4. Generate 768-dim embeddings
        5. Upload to Pinecone mathematics namespace
    """
    
    def __init__(
        self,
        pinecone_api_key: str,
        pinecone_index: str,
        pinecone_host: Optional[str] = None,
        output_dir: str = "./extracted_data"
    ):
        """
        Initialize pipeline with all components.
        
        Args:
            pinecone_api_key: Pinecone API key
            pinecone_index: Pinecone index name
            pinecone_host: Pinecone index host URL
            output_dir: Directory for extracted images
        """
        logger.info("="*80)
        logger.info("🚀 Initializing NCERT Math Multimodal Pipeline")
        logger.info("="*80)
        
        # Initialize components
        self.pdf_processor = PDFProcessor(output_dir=output_dir)
        self.formula_extractor = FormulaExtractor()
        self.chunker = MathChunker()
        self.embedder = MultimodalEmbedder()
        self.uploader = PineconeUploader(
            api_key=pinecone_api_key,
            index_name=pinecone_index,
            index_host=pinecone_host
        )
        
        logger.info("✅ All components initialized successfully")
        logger.info("")
    
    def process_pdf(
        self,
        pdf_path: str,
        class_num: int,
        chapter_num: int,
        use_ocr: bool = False
    ) -> dict:
        """
        Process a single PDF through the complete pipeline.
        
        Args:
            pdf_path: Path to PDF file
            class_num: Class number (5-12)
            chapter_num: Chapter number (1-N)
            use_ocr: Whether to use OCR for scanned PDFs
        
        Returns:
            Processing results
        """
        start_time = time.time()
        
        logger.info("="*80)
        logger.info(f"📚 Processing: {Path(pdf_path).name}")
        logger.info(f"   Class: {class_num}, Chapter: {chapter_num}")
        logger.info("="*80)
        
        try:
            # Step 1: Extract from PDF
            logger.info("\n[1/5] 📄 Extracting content from PDF...")
            if use_ocr:
                pdf_data = self.pdf_processor.extract_with_ocr(pdf_path, class_num, chapter_num)
            else:
                pdf_data = self.pdf_processor.process_pdf(pdf_path, class_num, chapter_num)
            
            text_blocks = pdf_data['text_blocks']
            images = pdf_data['images']
            
            logger.info(f"   ✓ Extracted {len(text_blocks)} text blocks")
            logger.info(f"   ✓ Extracted {len(images)} images")
            
            # Step 2: Extract formulas
            logger.info("\n[2/5] 🔢 Extracting formulas from text...")
            all_formulas = []
            for block in text_blocks:
                formulas = self.formula_extractor.extract_formulas(block['text'])
                all_formulas.extend(formulas)
            
            logger.info(f"   ✓ Extracted {len(all_formulas)} formulas")
            
            # Step 3: Chunk content
            logger.info("\n[3/5] 📦 Creating semantic chunks...")
            chunks = self.chunker.chunk_content(
                text_blocks=text_blocks,
                images=images,
                formulas=all_formulas,
                class_num=class_num,
                chapter_num=chapter_num
            )
            
            logger.info(f"   ✓ Created {len(chunks)} chunks")
            
            # Log chunk type distribution
            type_counts = {}
            for chunk in chunks:
                ctype = chunk['content_type']
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
            
            logger.info("   Chunk types:")
            for ctype, count in sorted(type_counts.items()):
                logger.info(f"      - {ctype}: {count}")
            
            # Step 4: Generate embeddings
            logger.info("\n[4/5] 🔢 Generating 768-dim embeddings...")
            embeddings = self.embedder.embed_chunks_batch(chunks, show_progress=True)
            
            logger.info(f"   ✓ Generated {len(embeddings)} embeddings")
            
            # Get embedding stats
            stats = self.embedder.get_embedding_stats(embeddings)
            logger.info(f"   Mean norm: {stats['mean_norm']:.4f}")
            logger.info(f"   Std norm: {stats['std_norm']:.4f}")
            
            # Step 5: Upload to Pinecone
            logger.info("\n[5/5] 📤 Uploading to Pinecone (mathematics namespace)...")
            upload_results = self.uploader.upload_chunks(
                chunks=chunks,
                embeddings=embeddings,
                namespace="mathematics",
                batch_size=100,
                show_progress=True
            )
            
            logger.info(f"   ✓ Uploaded {upload_results['uploaded']}/{upload_results['total']} chunks")
            
            if upload_results['failed'] > 0:
                logger.warning(f"   ⚠️ Failed to upload {upload_results['failed']} chunks")
            
            # Calculate timing
            elapsed = time.time() - start_time
            
            logger.info("\n" + "="*80)
            logger.info("✅ Pipeline Complete!")
            logger.info("="*80)
            logger.info(f"Total time: {elapsed:.2f} seconds")
            logger.info(f"Chunks processed: {len(chunks)}")
            logger.info(f"Successfully uploaded: {upload_results['uploaded']}")
            logger.info("="*80)
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "class": class_num,
                "chapter": chapter_num,
                "chunks_created": len(chunks),
                "chunks_uploaded": upload_results['uploaded'],
                "chunks_failed": upload_results['failed'],
                "time_elapsed": elapsed,
                "chunk_types": type_counts
            }
        
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "pdf_path": pdf_path
            }
    
    def process_batch(
        self,
        pdf_directory: str,
        pattern: str = "*.pdf"
    ):
        """
        Process multiple PDFs in a directory.
        
        Args:
            pdf_directory: Directory containing PDFs
            pattern: File pattern to match (default: *.pdf)
        
        Expected filename format: classX_chapterY.pdf or classX_chY.pdf
        """
        pdf_dir = Path(pdf_directory)
        pdf_files = list(pdf_dir.glob(pattern))
        
        logger.info(f"📚 Found {len(pdf_files)} PDF files in {pdf_directory}")
        logger.info("")
        
        results = []
        
        for pdf_path in pdf_files:
            # Try to extract class and chapter from filename
            filename = pdf_path.stem  # Without extension
            
            # Pattern: class5_chapter1 or class5_ch1
            import re
            match = re.search(r'class(\d+).*?ch(?:apter)?(\d+)', filename, re.IGNORECASE)
            
            if match:
                class_num = int(match.group(1))
                chapter_num = int(match.group(2))
                
                logger.info(f"\n📖 Processing: {pdf_path.name}")
                logger.info(f"   Detected: Class {class_num}, Chapter {chapter_num}")
                
                result = self.process_pdf(str(pdf_path), class_num, chapter_num)
                results.append(result)
            else:
                logger.warning(f"⚠️ Skipping {pdf_path.name}: Cannot parse class/chapter from filename")
                logger.warning(f"   Expected format: classX_chapterY.pdf or classX_chY.pdf")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📊 BATCH PROCESSING SUMMARY")
        logger.info("="*80)
        
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        total_chunks = sum(r.get('chunks_uploaded', 0) for r in results)
        
        logger.info(f"Total PDFs processed: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total chunks uploaded: {total_chunks}")
        logger.info("="*80)
        
        return results


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Process NCERT Math PDFs for multimodal embedding"
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to single PDF file"
    )
    
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to directory containing multiple PDFs"
    )
    
    parser.add_argument(
        "--class",
        type=int,
        dest="class_num",
        help="Class number (5-12)"
    )
    
    parser.add_argument(
        "--chapter",
        type=int,
        dest="chapter_num",
        help="Chapter number"
    )
    
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Use OCR for scanned PDFs"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./extracted_data",
        help="Directory to save extracted images"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.pdf and not args.batch:
        parser.error("Either --pdf or --batch must be specified")
    
    if args.pdf and (not args.class_num or not args.chapter_num):
        parser.error("--class and --chapter are required when using --pdf")
    
    # Initialize pipeline
    try:
        pipeline = MathPDFPipeline(
            pinecone_api_key=settings.PINECONE_API_KEY,
            pinecone_index=settings.PINECONE_MASTER_INDEX,
            pinecone_host=settings.PINECONE_MASTER_HOST,
            output_dir=args.output_dir
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Process
    if args.pdf:
        # Single PDF
        result = pipeline.process_pdf(
            pdf_path=args.pdf,
            class_num=args.class_num,
            chapter_num=args.chapter_num,
            use_ocr=args.ocr
        )
        
        if not result['success']:
            sys.exit(1)
    
    elif args.batch:
        # Batch processing
        results = pipeline.process_batch(pdf_directory=args.batch)
        
        if not any(r.get('success') for r in results):
            sys.exit(1)


if __name__ == "__main__":
    main()
