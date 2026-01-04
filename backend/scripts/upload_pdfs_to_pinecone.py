"""
PDF to Pinecone Upload Script with OCR Support
Extracts text from PDFs (including text in images) and uploads to Pinecone
"""

import os
import sys
import re
import io
from pathlib import Path
from typing import List, Dict, Tuple
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# PDF Processing
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Google Gemini
import google.generativeai as genai

# Pinecone
from pinecone import Pinecone

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class PDFProcessor:
    """Process PDFs with OCR support for images"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from PDF including text in images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        print(f"\n📄 Processing: {Path(pdf_path).name}")
        
        all_text = []
        
        try:
            # Step 1: Extract regular text using PyPDF2
            print("  ├─ Extracting regular text...")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"  ├─ Total pages: {num_pages}")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():
                        all_text.append(f"\n--- Page {page_num + 1} ---\n")
                        all_text.append(text)
            
            # Step 2: Extract text from images using OCR
            print("  ├─ Converting pages to images for OCR...")
            images = convert_from_path(
                pdf_path,
                dpi=300,  # High quality for better OCR
                fmt='png'
            )
            
            print(f"  ├─ Running OCR on {len(images)} pages...")
            for page_num, image in enumerate(images, start=1):
                # Convert PIL image to numpy array for OpenCV processing
                img_array = np.array(image)
                
                # Preprocess image for better OCR
                processed_img = self._preprocess_image(img_array)
                
                # Extract text using Tesseract OCR
                ocr_text = pytesseract.image_to_string(
                    processed_img,
                    lang='eng',  # English language
                    config='--psm 6'  # Assume uniform text block
                )
                
                if ocr_text.strip():
                    # Only add if not already captured by PyPDF2
                    if not self._is_duplicate_text(ocr_text, ''.join(all_text)):
                        all_text.append(f"\n--- OCR Page {page_num} ---\n")
                        all_text.append(ocr_text)
                
                print(f"    ├─ OCR Page {page_num}/{len(images)} ✓")
            
            full_text = ''.join(all_text)
            print(f"  └─ ✓ Extracted {len(full_text)} characters")
            
            return full_text
            
        except Exception as e:
            print(f"  └─ ✗ Error: {str(e)}")
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: Image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        return denoised
    
    def _is_duplicate_text(self, new_text: str, existing_text: str, threshold: float = 0.8) -> bool:
        """
        Check if new text is already in existing text (avoid duplicates)
        
        Args:
            new_text: New text to check
            existing_text: Existing text corpus
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if duplicate, False otherwise
        """
        # Clean and normalize
        new_clean = re.sub(r'\s+', ' ', new_text.lower().strip())
        existing_clean = re.sub(r'\s+', ' ', existing_text.lower().strip())
        
        # If new text is very short, don't count as duplicate
        if len(new_clean) < 50:
            return False
        
        # Check if majority of new text exists in existing text
        words = new_clean.split()
        if len(words) < 10:
            return False
        
        matching_words = sum(1 for word in words if word in existing_clean)
        similarity = matching_words / len(words)
        
        return similarity >= threshold
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            metadata: Metadata for each chunk
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Clean text
        text = re.sub(r'\n+', '\n', text)  # Remove multiple newlines
        text = re.sub(r' +', ' ', text)    # Remove multiple spaces
        
        # Split into sentences (approximate)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        chunk_id = 1
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'id': f"{metadata['lesson_id']}_chunk_{chunk_id}",
                    'text': chunk_text,
                    'metadata': {
                        **metadata,
                        'chunk_id': chunk_id,
                        'chunk_length': len(chunk_text)
                    }
                })
                
                # Start new chunk with overlap
                overlap_text = ' '.join(current_chunk[-3:])  # Last 3 sentences as overlap
                current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(overlap_text) + sentence_length
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'id': f"{metadata['lesson_id']}_chunk_{chunk_id}",
                'text': chunk_text,
                'metadata': {
                    **metadata,
                    'chunk_id': chunk_id,
                    'chunk_length': len(chunk_text)
                }
            })
        
        print(f"  └─ Created {len(chunks)} chunks")
        return chunks


class PineconeUploader:
    """Upload embeddings to Pinecone"""
    
    def __init__(self):
        """Initialize Pinecone uploader"""
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index = self.pc.Index(
            host=os.getenv('PINECONE_HOST')
        )
        
        print("✓ Connected to Pinecone")
        print(f"✓ Index stats: {self.index.describe_index_stats()}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Gemini
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"    ✗ Embedding error: {str(e)}")
            raise
    
    def upload_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """
        Upload chunks to Pinecone with embeddings
        
        Args:
            chunks: List of text chunks with metadata
            batch_size: Number of vectors per batch
        """
        print(f"\n🚀 Uploading {len(chunks)} chunks to Pinecone...")
        
        vectors = []
        
        for i, chunk in enumerate(chunks, start=1):
            try:
                # Generate embedding
                embedding = self.generate_embedding(chunk['text'])
                
                # Prepare vector
                vector = {
                    'id': chunk['id'],
                    'values': embedding,
                    'metadata': {
                        **chunk['metadata'],
                        'text': chunk['text'][:1000]  # Store first 1000 chars
                    }
                }
                
                vectors.append(vector)
                
                # Upload in batches
                if len(vectors) >= batch_size:
                    self.index.upsert(vectors=vectors)
                    print(f"  ├─ Uploaded batch: {i-batch_size+1}-{i} ✓")
                    vectors = []
                
            except Exception as e:
                print(f"  ├─ Error on chunk {i}: {str(e)}")
                continue
        
        # Upload remaining vectors
        if vectors:
            self.index.upsert(vectors=vectors)
            print(f"  └─ Uploaded final batch: {len(vectors)} vectors ✓")
        
        print(f"✓ Upload complete!")


def get_lesson_metadata(filename: str) -> Dict:
    """
    Extract metadata from filename
    
    Args:
        filename: PDF filename (e.g., 'fees101.pdf')
        
    Returns:
        Metadata dictionary
    """
    # Extract lesson number from filename (e.g., 'fees101' -> '01')
    match = re.search(r'fees1(\d+)', filename)
    if match:
        lesson_num = match.group(1).zfill(2)
    else:
        lesson_num = '00'
    
    # Lesson titles (from frontend lessons.js)
    lesson_titles = {
        '01': 'Locating Places on the Earth',
        '02': 'Oceans and Continents',
        '03': 'Landforms and Life',
        '04': 'Timeline and Sources of History',
        '05': 'The Beginning of Indian Civilization',
        '06': 'India, That Is Bharat',
        '07': "India's Cultural Roots",
        '08': 'Unity in Diversity',
        '09': 'Family and Community',
        '10': 'Grassroot Democracy (Governance)',
        '11': 'Grassroot Democracy – Local Government in Rural Areas',
        '12': 'Grassroot Democracy – Local Government in Urban Areas',
        '13': 'The Value of Work',
        '14': 'Economic Activities Around Us',
        'gl': 'Glossary',
        'ps': 'Practice Set'
    }
    
    return {
        'lesson_id': f'lesson_{lesson_num}',
        'lesson_number': lesson_num,
        'lesson_title': lesson_titles.get(lesson_num, f'Lesson {lesson_num}'),
        'class': '6',
        'subject': 'Social Science',
        'source': filename
    }


async def main():
    """Main function to process PDFs and upload to Pinecone"""
    
    print("=" * 70)
    print("  📚 NCERT PDF to Pinecone Upload with OCR")
    print("=" * 70)
    
    # Initialize processors
    pdf_processor = PDFProcessor()
    uploader = PineconeUploader()
    
    # PDF directory
    pdf_dir = Path(__file__).parent.parent.parent / 'client' / 'src' / 'assets'
    
    if not pdf_dir.exists():
        print(f"✗ PDF directory not found: {pdf_dir}")
        return
    
    # Get all PDF files
    pdf_files = list(pdf_dir.glob('fees1*.pdf'))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {pdf_dir}")
        return
    
    print(f"\n✓ Found {len(pdf_files)} PDF files")
    print(f"✓ PDF Directory: {pdf_dir}")
    
    # Process each PDF
    all_chunks = []
    
    for pdf_file in sorted(pdf_files):
        try:
            # Extract metadata
            metadata = get_lesson_metadata(pdf_file.name)
            
            # Extract text (including OCR)
            text = pdf_processor.extract_text_from_pdf(str(pdf_file))
            
            # Chunk text
            chunks = pdf_processor.chunk_text(text, metadata)
            all_chunks.extend(chunks)
            
            print(f"✓ Processed: {pdf_file.name} ({len(chunks)} chunks)")
            
        except Exception as e:
            print(f"✗ Failed to process {pdf_file.name}: {str(e)}")
            continue
    
    # Upload all chunks to Pinecone
    if all_chunks:
        uploader.upload_chunks(all_chunks)
        
        # Show final stats
        stats = uploader.index.describe_index_stats()
        print("\n" + "=" * 70)
        print(f"  ✅ SUCCESS! Uploaded {stats.total_vector_count} vectors to Pinecone")
        print("=" * 70)
    else:
        print("\n✗ No chunks to upload")


if __name__ == "__main__":
    asyncio.run(main())
