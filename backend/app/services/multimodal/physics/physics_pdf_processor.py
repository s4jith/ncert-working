"""
Physics PDF Processor

Extracts content from NCERT Physics PDFs with support for:
- Text content (concepts, definitions, laws, derivations)
- Formulas (physics-specific equations)
- Diagrams (circuit, ray, force, graphs, experiment setups)
- Tables (experiment readings, data tables)
- Numerical problems and solutions
- Experiments (aim, apparatus, theory, procedure, observations)
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import re
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PhysicsPDFProcessor:
    """
    Process Physics PDFs to extract text, formulas, diagrams, tables, and experiments
    """
    
    def __init__(self, output_dir: str = "extracted_physics_content"):
        """
        Initialize the physics PDF processor
        
        Args:
            output_dir: Directory to save extracted images/diagrams
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Physics-specific patterns
        self.experiment_keywords = [
            "aim", "apparatus", "theory", "procedure", "observation",
            "result", "precaution", "conclusion", "materials required"
        ]
        
        self.numerical_keywords = [
            "numerical", "problem", "example", "exercise", "question",
            "given", "find", "calculate", "determine", "solution"
        ]
        
        self.law_keywords = [
            "law", "principle", "theorem", "rule", "postulate",
            "newton", "ohm", "hooke", "archimedes", "pascal",
            "coulomb", "faraday", "ampere"
        ]
        
        logger.info("Physics PDF Processor initialized")
    
    def process_pdf(
        self,
        pdf_path: str,
        class_num: int,
        chapter_num: int
    ) -> Dict:
        """
        Process a physics PDF and extract all content
        
        Args:
            pdf_path: Path to PDF file
            class_num: NCERT class number (11 or 12)
            chapter_num: Chapter number
        
        Returns:
            Dictionary containing extracted content
        """
        logger.info(f"Processing PDF: {pdf_path}")
        logger.info(f"   Class: {class_num}, Chapter: {chapter_num}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Storage for extracted content
        text_blocks = []
        images = []
        tables = []
        experiments = []
        numerical_problems = []
        
        # Process each page
        for page_num in range(total_pages):
            logger.info(f"   Processing page {page_num + 1}/{total_pages}")
            page = doc[page_num]
            
            # Extract text blocks with position
            page_text_blocks = self._extract_text_blocks(
                page, page_num + 1, class_num, chapter_num
            )
            text_blocks.extend(page_text_blocks)
            
            # Extract images (diagrams, graphs, circuits)
            page_images = self._extract_images(
                page, page_num + 1, class_num, chapter_num, pdf_path
            )
            images.extend(page_images)
            
            # Extract tables
            page_tables = self._extract_tables(
                page, page_num + 1, class_num, chapter_num
            )
            tables.extend(page_tables)
            
            # Detect experiments
            page_experiments = self._detect_experiments(
                page_text_blocks, page_num + 1
            )
            experiments.extend(page_experiments)
            
            # Detect numerical problems
            page_numericals = self._detect_numerical_problems(
                page_text_blocks, page_num + 1
            )
            numerical_problems.extend(page_numericals)
        
        doc.close()
        
        result = {
            "text_blocks": text_blocks,
            "images": images,
            "tables": tables,
            "experiments": experiments,
            "numerical_problems": numerical_problems,
            "metadata": {
                "class": class_num,
                "chapter": chapter_num,
                "total_pages": total_pages,
                "pdf_path": str(pdf_path)
            }
        }
        
        logger.info(f"Extracted {len(text_blocks)} text blocks")
        logger.info(f"   [+] Extracted {len(images)} images/diagrams")
        logger.info(f"   [+] Extracted {len(tables)} tables")
        logger.info(f"   [+] Detected {len(experiments)} experiments")
        logger.info(f"   [+] Detected {len(numerical_problems)} numerical problems")
        
        return result
    
    def _extract_text_blocks(
        self,
        page: fitz.Page,
        page_num: int,
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Extract text blocks with metadata"""
        blocks = []
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                text_lines = []
                
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    text_lines.append(line_text)
                
                full_text = "\n".join(text_lines).strip()
                if not full_text:
                    continue
                
                # Detect block type
                block_type = self._classify_text_block(full_text)
                
                blocks.append({
                    "text": full_text,
                    "page": page_num,
                    "block_type": block_type,
                    "bbox": block.get("bbox"),
                    "metadata": {
                        "class": class_num,
                        "chapter": chapter_num,
                        "page": page_num
                    }
                })
        
        return blocks
    
    def _classify_text_block(self, text: str) -> str:
        """Classify text block into physics-specific types"""
        text_lower = text.lower()
        
        # Check for laws/principles
        if any(keyword in text_lower for keyword in self.law_keywords):
            return "law"
        
        # Check for definitions
        if text_lower.startswith("definition") or "is defined as" in text_lower:
            return "definition"
        
        # Check for derivations
        if "deriv" in text_lower or "proof" in text_lower:
            return "derivation"
        
        # Check for numerical
        if any(keyword in text_lower for keyword in self.numerical_keywords):
            return "numerical"
        
        # Check for experiments
        if any(keyword in text_lower for keyword in self.experiment_keywords):
            return "experiment"
        
        # Default
        return "concept"
    
    def _extract_images(
        self,
        page: fitz.Page,
        page_num: int,
        class_num: int,
        chapter_num: int,
        pdf_path: str
    ) -> List[Dict]:
        """Extract images and classify diagram types"""
        images = []
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Get image position
                rects = page.get_image_rects(xref)
                bbox = rects[0] if rects else None
                
                # Save image
                filename = f"class{class_num}_ch{chapter_num}_page{page_num}_img{img_index + 1}.{image_ext}"
                image_path = self.output_dir / filename
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                # Classify diagram type based on context
                diagram_type = self._classify_diagram_type(bbox, page) if bbox else "unknown"
                
                images.append({
                    "path": str(image_path),
                    "page": page_num,
                    "diagram_type": diagram_type,
                    "bbox": list(bbox) if bbox else None,
                    "metadata": {
                        "class": class_num,
                        "chapter": chapter_num,
                        "page": page_num,
                        "index": img_index + 1
                    }
                })
                
            except Exception as e:
                logger.warning(f"Failed to extract image {img_index} on page {page_num}: {e}")
                continue
        
        return images
    
    def _classify_diagram_type(self, bbox: fitz.Rect, page: fitz.Page) -> str:
        """Classify diagram type based on surrounding text"""
        # Get text near the image
        expanded_rect = fitz.Rect(
            bbox.x0 - 50,
            bbox.y0 - 100,
            bbox.x1 + 50,
            bbox.y1 + 50
        )
        
        nearby_text = page.get_text("text", clip=expanded_rect).lower()
        
        # Classify based on keywords
        if any(word in nearby_text for word in ["circuit", "resistor", "capacitor", "battery", "ammeter"]):
            return "circuit"
        elif any(word in nearby_text for word in ["ray", "lens", "mirror", "refraction", "reflection"]):
            return "ray_diagram"
        elif any(word in nearby_text for word in ["force", "vector", "acceleration", "velocity", "friction"]):
            return "force_diagram"
        elif any(word in nearby_text for word in ["graph", "plot", "vs", "versus", "curve"]):
            return "graph"
        elif any(word in nearby_text for word in ["apparatus", "setup", "experiment", "arrangement"]):
            return "experiment_setup"
        else:
            return "diagram"
    
    def _extract_tables(
        self,
        page: fitz.Page,
        page_num: int,
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Extract tables from page"""
        tables = []
        
        # Try to find tables using text structure
        text_dict = page.get_text("dict")
        
        # Look for blocks with regular structure (potential tables)
        # This is a simplified approach - for better results, use specialized libraries
        blocks = text_dict.get("blocks", [])
        
        for block_idx, block in enumerate(blocks):
            if block.get("type") != 0:
                continue
            
            lines = block.get("lines", [])
            if len(lines) < 2:
                continue
            
            # Check if lines have similar structure (potential table rows)
            if self._looks_like_table(lines):
                table_text = self._extract_table_text(lines)
                
                tables.append({
                    "data": table_text,
                    "page": page_num,
                    "bbox": block.get("bbox"),
                    "metadata": {
                        "class": class_num,
                        "chapter": chapter_num,
                        "page": page_num,
                        "block_index": block_idx
                    }
                })
        
        return tables
    
    def _looks_like_table(self, lines: List[Dict]) -> bool:
        """Check if lines look like a table structure"""
        if len(lines) < 2:
            return False
        
        # Check for similar number of spans per line (columns)
        span_counts = [len(line.get("spans", [])) for line in lines]
        
        # If most lines have similar span counts, likely a table
        if len(set(span_counts)) <= 2 and min(span_counts) > 1:
            return True
        
        return False
    
    def _extract_table_text(self, lines: List[Dict]) -> str:
        """Extract table as structured text"""
        rows = []
        
        for line in lines:
            cells = []
            for span in line.get("spans", []):
                cells.append(span.get("text", "").strip())
            rows.append(" | ".join(cells))
        
        return "\n".join(rows)
    
    def _detect_experiments(
        self,
        text_blocks: List[Dict],
        page_num: int
    ) -> List[Dict]:
        """Detect experiment sections"""
        experiments = []
        
        # Look for experiment patterns
        for i, block in enumerate(text_blocks):
            text_lower = block["text"].lower()
            
            # Check for experiment headers
            if any(keyword in text_lower for keyword in ["aim:", "objective:", "experiment"]):
                # Collect subsequent blocks as part of experiment
                experiment_text = [block["text"]]
                
                # Look ahead for related blocks
                for j in range(i + 1, min(i + 10, len(text_blocks))):
                    next_text = text_blocks[j]["text"].lower()
                    if any(keyword in next_text for keyword in self.experiment_keywords):
                        experiment_text.append(text_blocks[j]["text"])
                    elif len(text_blocks[j]["text"]) < 50:
                        break
                
                experiments.append({
                    "text": "\n\n".join(experiment_text),
                    "page": page_num,
                    "metadata": block.get("metadata", {})
                })
        
        return experiments
    
    def _detect_numerical_problems(
        self,
        text_blocks: List[Dict],
        page_num: int
    ) -> List[Dict]:
        """Detect numerical problems and solutions"""
        numericals = []
        
        for i, block in enumerate(text_blocks):
            text = block["text"]
            text_lower = text.lower()
            
            # Check for numerical problem indicators
            has_numbers = bool(re.search(r'\d+\.?\d*\s*(m|kg|s|n|j|w|v|a|ω|hz)', text_lower))
            has_keywords = any(keyword in text_lower for keyword in self.numerical_keywords)
            
            if has_numbers and has_keywords:
                # Try to find solution
                solution_text = None
                for j in range(i + 1, min(i + 5, len(text_blocks))):
                    next_text = text_blocks[j]["text"].lower()
                    if "solution" in next_text or "answer" in next_text:
                        solution_text = text_blocks[j]["text"]
                        break
                
                numericals.append({
                    "question": text,
                    "solution": solution_text,
                    "page": page_num,
                    "metadata": block.get("metadata", {})
                })
        
        return numericals
