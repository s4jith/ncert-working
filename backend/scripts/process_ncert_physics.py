"""
NCERT Physics Processing Script

Process NCERT Physics PDFs through the full multimodal pipeline.
"""

import sys
import os
from pathlib import Path
import logging
import argparse
from tqdm import tqdm

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.multimodal.physics.physics_pdf_processor import PhysicsPDFProcessor
from app.services.multimodal.physics.physics_formula_extractor import PhysicsFormulaExtractor
from app.services.multimodal.physics.physics_chunker import PhysicsChunker
from app.services.multimodal.physics.physics_embedder import PhysicsEmbedder
from app.services.multimodal.physics.physics_uploader import PhysicsUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ncert_physics_processing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PhysicsProcessor:
    """Process NCERT Physics PDFs"""
    
    def __init__(self, output_dir: str = "extracted_images"):
        """Initialize processor"""
        logger.info("=" * 80)
        logger.info("🔬 NCERT PHYSICS PROCESSING PIPELINE")
        logger.info("=" * 80)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.pdf_processor = PhysicsPDFProcessor(output_dir=str(self.output_dir))
        self.formula_extractor = PhysicsFormulaExtractor()
        self.embedder = PhysicsEmbedder()
        self.uploader = PhysicsUploader()
        
        logger.info("✅ All components initialized")
    
    def process_pdf(
        self,
        pdf_path: Path,
        class_num: int,
        chapter_num: int
    ) -> dict:
        """Process single PDF"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📄 Processing: {pdf_path.name}")
        logger.info(f"   Class: {class_num}, Chapter: {chapter_num}")
        logger.info(f"{'='*80}")
        
        try:
            # Step 1: Extract content
            logger.info("\n[1/5] Extracting content from PDF...")
            extracted_data = self.pdf_processor.process_pdf(
                pdf_path=str(pdf_path),
                class_num=class_num,
                chapter_num=chapter_num
            )
            
            logger.info(f"   ✅ Extracted:")
            logger.info(f"      Text blocks: {len(extracted_data['text_blocks'])}")
            logger.info(f"      Diagrams: {len(extracted_data['diagrams'])}")
            logger.info(f"      Tables: {len(extracted_data['tables'])}")
            logger.info(f"      Experiments: {len(extracted_data['experiments'])}")
            logger.info(f"      Numericals: {len(extracted_data['numericals'])}")
            
            # Step 2: Extract formulas
            logger.info("\n[2/5] Extracting formulas...")
            all_text = " ".join([block['text'] for block in extracted_data['text_blocks']])
            formulas = self.formula_extractor.extract_formulas(all_text)
            logger.info(f"   ✅ Found {len(formulas)} formulas")
            
            # Step 3: Chunk content
            logger.info("\n[3/5] Chunking content...")
            chunks = PhysicsChunker.chunk_content(
                extracted_data,
                class_num,
                chapter_num
            )
            logger.info(f"   ✅ Created {len(chunks)} chunks")
            
            # Step 4: Generate embeddings
            logger.info("\n[4/5] Generating embeddings...")
            chunks_with_embeddings = self.embedder.embed_chunks_batch(chunks)
            logger.info(f"   ✅ Generated {len(chunks_with_embeddings)} embeddings")
            
            # Step 5: Upload to Pinecone
            logger.info("\n[5/5] Uploading to Pinecone...")
            upload_stats = self.uploader.upload_chunks(
                chunks_with_embeddings,
                namespace="physics"
            )
            
            logger.info(f"✅ PDF processing complete!")
            
            return {
                'pdf_name': pdf_path.name,
                'class': class_num,
                'chapter': chapter_num,
                'text_blocks': len(extracted_data['text_blocks']),
                'diagrams': len(extracted_data['diagrams']),
                'tables': len(extracted_data['tables']),
                'experiments': len(extracted_data['experiments']),
                'numericals': len(extracted_data['numericals']),
                'formulas': len(formulas),
                'chunks': len(chunks),
                'uploaded': upload_stats['uploaded'],
                'failed': upload_stats['failed']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_path.name}: {e}", exc_info=True)
            return {
                'pdf_name': pdf_path.name,
                'error': str(e)
            }
    
    def scan_physics_pdfs(self, dataset_dir: Path) -> list:
        """Scan for NCERT Physics PDFs"""
        logger.info("\n🔍 Scanning for Physics PDFs...")
        
        pdfs = []
        
        # Class 11 Physics: ieph1XX.pdf
        class11_dir = dataset_dir / "class-11"
        if class11_dir.exists():
            for pdf_path in sorted(class11_dir.glob("ieph1*.pdf")):
                # Extract chapter number from filename
                match = pdf_path.stem.replace("ieph1", "")
                if match.isdigit():
                    chapter_num = int(match)
                    pdfs.append({
                        'path': pdf_path,
                        'class': 11,
                        'chapter': chapter_num
                    })
        
        # Class 12 Physics: jeph1XX.pdf
        class12_dir = dataset_dir / "class-12"
        if class12_dir.exists():
            for pdf_path in sorted(class12_dir.glob("jeph1*.pdf")):
                # Extract chapter number from filename
                match = pdf_path.stem.replace("jeph1", "")
                if match.isdigit():
                    chapter_num = int(match)
                    pdfs.append({
                        'path': pdf_path,
                        'class': 12,
                        'chapter': chapter_num
                    })
        
        logger.info(f"   Found {len(pdfs)} Physics PDFs")
        logger.info(f"   Class 11: {sum(1 for p in pdfs if p['class'] == 11)}")
        logger.info(f"   Class 12: {sum(1 for p in pdfs if p['class'] == 12)}")
        
        return pdfs
    
    def process_all(self, dataset_dir: Path, class_filter: int = None):
        """Process all physics PDFs"""
        pdfs = self.scan_physics_pdfs(dataset_dir)
        
        # Apply class filter
        if class_filter:
            pdfs = [p for p in pdfs if p['class'] == class_filter]
            logger.info(f"   Filtering to Class {class_filter}: {len(pdfs)} PDFs")
        
        if not pdfs:
            logger.error("❌ No Physics PDFs found!")
            return
        
        # Process each PDF
        results = []
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Processing {len(pdfs)} Physics PDFs")
        logger.info(f"{'='*80}\n")
        
        for pdf_info in tqdm(pdfs, desc="Processing PDFs"):
            result = self.process_pdf(
                pdf_path=pdf_info['path'],
                class_num=pdf_info['class'],
                chapter_num=pdf_info['chapter']
            )
            results.append(result)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("📊 PROCESSING SUMMARY")
        logger.info("="*80)
        
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        logger.info(f"Total PDFs: {len(results)}")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        
        if successful:
            total_chunks = sum(r['chunks'] for r in successful)
            total_uploaded = sum(r['uploaded'] for r in successful)
            total_diagrams = sum(r['diagrams'] for r in successful)
            total_tables = sum(r['tables'] for r in successful)
            total_experiments = sum(r['experiments'] for r in successful)
            total_numericals = sum(r['numericals'] for r in successful)
            
            logger.info(f"\n📈 Content Statistics:")
            logger.info(f"   Total chunks: {total_chunks}")
            logger.info(f"   Uploaded: {total_uploaded}")
            logger.info(f"   Diagrams: {total_diagrams}")
            logger.info(f"   Tables: {total_tables}")
            logger.info(f"   Experiments: {total_experiments}")
            logger.info(f"   Numericals: {total_numericals}")
        
        if failed:
            logger.info(f"\n❌ Failed PDFs:")
            for r in failed:
                logger.info(f"   {r['pdf_name']}: {r['error']}")
        
        # Final Pinecone stats
        final_stats = self.uploader.get_namespace_stats("physics")
        logger.info(f"\n🌲 Final Pinecone Stats:")
        logger.info(f"   Physics namespace: {final_stats['vector_count']} vectors")
        logger.info(f"   Total index: {final_stats['total_vectors']} vectors")
        
        logger.info("\n" + "="*80)
        logger.info("✅ PHYSICS PROCESSING COMPLETE")
        logger.info("="*80)


def main():
    parser = argparse.ArgumentParser(description="Process NCERT Physics PDFs")
    parser.add_argument(
        '--dataset',
        type=str,
        default='ncert-working-dataset/Physics',
        help='Path to Physics dataset directory'
    )
    parser.add_argument(
        '--class',
        type=int,
        choices=[11, 12],
        dest='class_filter',
        help='Process only specific class (11 or 12)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='extracted_images',
        help='Output directory for extracted images'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = backend_dir / dataset_path
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset directory not found: {dataset_path}")
        return
    
    # Process
    processor = PhysicsProcessor(output_dir=args.output)
    processor.process_all(dataset_path, class_filter=args.class_filter)


if __name__ == "__main__":
    main()
