"""
OCR Service
Text extraction from images using Tesseract
"""

import logging
from typing import Optional

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


async def extract_text_from_image(image_path: str, languages: str = "eng+hin") -> str:
    """
    Extract text from an image using Tesseract OCR
    
    Args:
        image_path: Path to the image file
        languages: Tesseract language codes (e.g., "eng+hin" for English and Hindi)
    
    Returns:
        Extracted text string
    """
    try:
        # Open image
        image = Image.open(image_path)
        
        # Preprocess image for better OCR
        image = preprocess_image(image)
        
        # Extract text
        text = pytesseract.image_to_string(image, lang=languages)
        
        # Clean up text
        text = clean_ocr_text(text)
        
        logger.info(f"OCR extracted {len(text)} characters from {image_path}")
        return text
        
    except Exception as e:
        logger.error(f"OCR failed for {image_path}: {e}")
        raise


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR accuracy
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast (simple thresholding)
    threshold = 150
    image = image.point(lambda x: 255 if x > threshold else 0)
    
    return image


def clean_ocr_text(text: str) -> str:
    """
    Clean OCR extracted text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


async def detect_language(text: str) -> str:
    """
    Simple language detection based on script
    """
    if not text:
        return "en"
    
    # Count characters from different scripts
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    arabic = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    latin = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    
    total = len(text)
    if total == 0:
        return "en"
    
    if devanagari / total > 0.3:
        return "hi"
    if arabic / total > 0.3:
        return "ur"
    
    return "en"
