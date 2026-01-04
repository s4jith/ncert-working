"""
PDF Processor for NCERT Mathematics Books

Extracts text, formulas, and images from PDFs with high precision.
Handles both digital and scanned PDFs.

Features:
- Clean text extraction using PyMuPDF
- Image detection and cropping
- Page layout analysis
- Metadata preservation
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from PIL import Image
import io
import re

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Processes NCERT Math PDFs to extract text, images, and structure.
    
    Usage:
        processor = PDFProcessor()
        data = processor.process_pdf("class5_chapter1.pdf", class_num=5, chapter_num=1)
    """
    
    def __init__(self, output_dir: str = "./extracted_images"):
        """
        Initialize PDF processor.
        
        Args:
            output_dir: Directory to save extracted images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 PDF Processor initialized. Images will be saved to: {self.output_dir}")
    
    def process_pdf(
        self,
        pdf_path: str,
        class_num: int,
        chapter_num: int
    ) -> Dict:
        """
        Process a PDF and extract all content.
        
        Args:
            pdf_path: Path to PDF file
            class_num: Class number (5-12)
            chapter_num: Chapter number (1-N)
        
        Returns:
            Dict with:
                - text_blocks: List of text blocks with metadata
                - images: List of extracted images with metadata
                - metadata: PDF-level metadata
        """
        logger.info(f"📖 Processing PDF: {pdf_path}")
        logger.info(f"   Class: {class_num}, Chapter: {chapter_num}")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            text_blocks = []
            images = []
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                logger.info(f"   Processing page {page_num + 1}/{total_pages}")
                
                # Extract text blocks
                page_text_blocks = self._extract_text_blocks(page, page_num, class_num, chapter_num)
                text_blocks.extend(page_text_blocks)
                
                # Extract images
                page_images = self._extract_images(page, page_num, class_num, chapter_num)
                images.extend(page_images)
            
            doc.close()
            
            logger.info(f"✅ Extracted {len(text_blocks)} text blocks and {len(images)} images")
            
            return {
                "text_blocks": text_blocks,
                "images": images,
                "metadata": {
                    "class": class_num,
                    "chapter": chapter_num,
                    "total_pages": total_pages,
                    "source_file": str(pdf_path)
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to process PDF: {e}")
            raise
    
    def _extract_text_blocks(
        self,
        page: fitz.Page,
        page_num: int,
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """
        Extract text blocks from a page with position metadata.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-indexed)
            class_num: Class number
            chapter_num: Chapter number
        
        Returns:
            List of text block dictionaries
        """
        blocks = []
        
        # Get text blocks with positions
        text_dict = page.get_text("dict")
        
        for block_idx, block in enumerate(text_dict.get("blocks", [])):
            # Skip image blocks (type 1)
            if block.get("type") != 0:
                continue
            
            # Extract text from lines
            text_lines = []
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                text_lines.append(line_text.strip())
            
            full_text = " ".join(text_lines).strip()
            
            # Skip empty blocks
            if not full_text or len(full_text) < 3:
                continue
            
            # Skip page numbers and headers
            if self._is_noise(full_text):
                continue
            
            blocks.append({
                "text": full_text,
                "page_number": page_num + 1,  # 1-indexed for user
                "block_index": block_idx,
                "bbox": block.get("bbox"),  # Bounding box [x0, y0, x1, y1]
                "metadata": {
                    "class": str(class_num),
                    "chapter": str(chapter_num),
                    "page": page_num + 1
                }
            })
        
        return blocks
    
    def _extract_images(
        self,
        page: fitz.Page,
        page_num: int,
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """
        Extract and save images from a page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-indexed)
            class_num: Class number
            chapter_num: Chapter number
        
        Returns:
            List of image metadata dictionaries
        """
        images = []
        image_list = page.get_images(full=True)
        
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Create unique filename
                image_filename = f"class{class_num}_ch{chapter_num}_page{page_num+1}_img{img_idx+1}.{image_ext}"
                image_path = self.output_dir / image_filename
                
                # Save image
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Get image dimensions
                pil_image = Image.open(io.BytesIO(image_bytes))
                width, height = pil_image.size
                
                # Skip very small images (likely decorative)
                if width < 50 or height < 50:
                    image_path.unlink()  # Delete small image
                    continue
                
                images.append({
                    "image_path": str(image_path),
                    "page_number": page_num + 1,
                    "image_index": img_idx,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "metadata": {
                        "class": str(class_num),
                        "chapter": str(chapter_num),
                        "page": page_num + 1,
                        "type": "diagram"
                    }
                })
                
                logger.debug(f"      Saved image: {image_filename} ({width}x{height})")
            
            except Exception as e:
                logger.warning(f"      Failed to extract image {img_idx}: {e}")
                continue
        
        return images
    
    @staticmethod
    def _is_noise(text: str) -> bool:
        """
        Detect if text block is noise (headers, footers, page numbers).
        
        Args:
            text: Text to check
        
        Returns:
            True if text is noise
        """
        noise_patterns = [
            r"^\d+$",  # Just page numbers
            r"^Page \d+",
            r"^Chapter \d+$",
            r"^NCERT",
            r"^www\.",
            r"^https?://",
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
        
        return False
    
    def extract_with_ocr(
        self,
        pdf_path: str,
        class_num: int,
        chapter_num: int
    ) -> Dict:
        """
        Process scanned PDF using OCR (for low-quality scans).
        Falls back to Tesseract OCR when text extraction fails.
        
        Args:
            pdf_path: Path to scanned PDF
            class_num: Class number
            chapter_num: Chapter number
        
        Returns:
            Extracted data with OCR text
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError:
            logger.error("❌ OCR dependencies not installed. Install: pytesseract, pdf2image")
            raise
        
        logger.info(f"🔍 Using OCR for scanned PDF: {pdf_path}")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        text_blocks = []
        
        for page_num, img in enumerate(images):
            logger.info(f"   OCR page {page_num + 1}/{len(images)}")
            
            # Apply OCR
            text = pytesseract.image_to_string(img, lang='eng')
            
            if text.strip():
                text_blocks.append({
                    "text": text.strip(),
                    "page_number": page_num + 1,
                    "block_index": 0,
                    "ocr": True,
                    "metadata": {
                        "class": str(class_num),
                        "chapter": str(chapter_num),
                        "page": page_num + 1
                    }
                })
        
        logger.info(f"✅ OCR extracted {len(text_blocks)} text blocks")
        
        return {
            "text_blocks": text_blocks,
            "images": [],  # Images already present in PDF
            "metadata": {
                "class": class_num,
                "chapter": chapter_num,
                "total_pages": len(images),
                "ocr_used": True
            }
        }


if __name__ == "__main__":
    # Test the processor
    logging.basicConfig(level=logging.INFO)
    
    processor = PDFProcessor(output_dir="./test_extracted_images")
    
    # Example usage (replace with actual PDF path)
    # data = processor.process_pdf("sample_math.pdf", class_num=5, chapter_num=1)
    # print(f"Extracted {len(data['text_blocks'])} text blocks")
    # print(f"Extracted {len(data['images'])} images")
