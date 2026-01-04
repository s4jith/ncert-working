"""
Math Content Chunker

Intelligently splits mathematical content into semantic chunks.
Respects boundaries of questions, solutions, formulas, and diagrams.

Chunking Rules (STRICT):
- One question = One chunk
- One solution step = One chunk  
- One formula = One chunk
- One diagram = One chunk
- Definitions/theorems = Separate chunks
- Never split mid-formula or mid-step
"""

import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MathChunker:
    """
    Semantic chunker for mathematical content.
    
    Usage:
        chunker = MathChunker()
        chunks = chunker.chunk_content(text_blocks, images, formulas)
    """
    
    # Patterns for detecting content types
    QUESTION_PATTERNS = [
        r'^\d+\.\s+',  # Numbered questions: "1. "
        r'^Q\s*\d+[:.)]',  # Q1:, Q1., Q1)
        r'^Question\s+\d+',
        r'Solve:',
        r'Find:',
        r'Calculate:',
        r'Prove:',
        r'Show that:',
        r'Verify:',
    ]
    
    SOLUTION_PATTERNS = [
        r'^Solution:?',
        r'^Answer:?',
        r'^Sol:?',
        r'^Step\s+\d+:',
        r'^\(\d+\)',  # Step markers: (1), (2)
        r'^[a-z]\)',  # Sub-steps: a), b)
    ]
    
    DEFINITION_PATTERNS = [
        r'^Definition:',
        r'^Theorem:',
        r'^Lemma:',
        r'^Corollary:',
        r'^Axiom:',
        r'^Postulate:',
        r'^Property:',
        r'^Note:',
        r'^Important:',
        r'^Remember:',
    ]
    
    EXAMPLE_PATTERNS = [
        r'^Example\s+\d+',
        r'^Ex\.',
        r'^E\.g\.',
        r'^For example,',
    ]
    
    def __init__(self):
        """Initialize chunker with compiled patterns."""
        self.question_re = [re.compile(p, re.IGNORECASE) for p in self.QUESTION_PATTERNS]
        self.solution_re = [re.compile(p, re.IGNORECASE) for p in self.SOLUTION_PATTERNS]
        self.definition_re = [re.compile(p, re.IGNORECASE) for p in self.DEFINITION_PATTERNS]
        self.example_re = [re.compile(p, re.IGNORECASE) for p in self.EXAMPLE_PATTERNS]
        logger.info("📦 Math Chunker initialized")
    
    def chunk_content(
        self,
        text_blocks: List[Dict],
        images: List[Dict],
        formulas: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """
        Create semantic chunks from extracted content.
        
        Args:
            text_blocks: List of text blocks from PDF
            images: List of extracted images
            formulas: List of extracted formulas
            class_num: Class number
            chapter_num: Chapter number
        
        Returns:
            List of chunk dictionaries with:
                - chunk_id: Unique identifier
                - raw_text: Text content
                - latex_formula: LaTeX formula (or None)
                - image_path: Image path (or None)
                - content_type: question|step|formula|diagram|definition|example|text
                - step_number: Step number for solutions (or None)
                - metadata: Class, chapter, page, etc.
        """
        logger.info(f"📦 Chunking content for Class {class_num}, Chapter {chapter_num}")
        logger.info(f"   Input: {len(text_blocks)} text blocks, {len(images)} images, {len(formulas)} formulas")
        
        chunks = []
        chunk_counter = 0
        
        # Process text blocks
        for block in text_blocks:
            text = block['text']
            page = block.get('page_number', 0)
            
            # Detect content type
            content_type = self._detect_content_type(text)
            
            # Handle multi-step solutions
            if content_type == "solution":
                solution_chunks = self._split_solution_steps(text, block, class_num, chapter_num, chunk_counter)
                chunks.extend(solution_chunks)
                chunk_counter += len(solution_chunks)
            else:
                # Single chunk
                chunk_id = f"class{class_num}_ch{chapter_num}_{chunk_counter:04d}"
                
                chunk = {
                    "chunk_id": chunk_id,
                    "ncert_id": chunk_id,
                    "raw_text": text,
                    "latex_formula": None,
                    "image_path": None,
                    "content_type": content_type,
                    "step_number": None,
                    "has_formula": False,
                    "has_image": False,
                    "metadata": {
                        "class": str(class_num),
                        "chapter": str(chapter_num),
                        "page": page,
                        "subject": "Mathematics",
                        "type": content_type,
                        "ncert_id": chunk_id
                    }
                }
                
                chunks.append(chunk)
                chunk_counter += 1
        
        # Process standalone formulas
        for formula in formulas:
            chunk_id = f"class{class_num}_ch{chapter_num}_{chunk_counter:04d}"
            
            chunk = {
                "chunk_id": chunk_id,
                "ncert_id": chunk_id,
                "raw_text": formula.get('raw_text', ''),
                "latex_formula": formula.get('latex', ''),
                "image_path": None,
                "content_type": "formula",
                "step_number": None,
                "has_formula": True,
                "has_image": False,
                "metadata": {
                    "class": str(class_num),
                    "chapter": str(chapter_num),
                    "page": 0,  # Formula position info if available
                    "subject": "Mathematics",
                    "type": "formula",
                    "ncert_id": chunk_id,
                    "formula_type": self._classify_formula(formula.get('latex', ''))
                }
            }
            
            chunks.append(chunk)
            chunk_counter += 1
        
        # Process images (diagrams)
        for image in images:
            chunk_id = f"class{class_num}_ch{chapter_num}_{chunk_counter:04d}"
            
            chunk = {
                "chunk_id": chunk_id,
                "ncert_id": chunk_id,
                "raw_text": f"Diagram from page {image.get('page_number', 0)}",
                "latex_formula": None,
                "image_path": image.get('image_path', ''),
                "content_type": "diagram",
                "step_number": None,
                "has_formula": False,
                "has_image": True,
                "metadata": {
                    "class": str(class_num),
                    "chapter": str(chapter_num),
                    "page": image.get('page_number', 0),
                    "subject": "Mathematics",
                    "type": "diagram",
                    "ncert_id": chunk_id,
                    "image_width": image.get('width', 0),
                    "image_height": image.get('height', 0)
                }
            }
            
            chunks.append(chunk)
            chunk_counter += 1
        
        logger.info(f"✅ Created {len(chunks)} semantic chunks")
        
        # Add topics to chunks
        chunks = self._add_topics(chunks)
        
        return chunks
    
    def _detect_content_type(self, text: str) -> str:
        """
        Detect the type of mathematical content.
        
        Args:
            text: Text content
        
        Returns:
            Content type string
        """
        text_start = text[:100]  # Check first 100 chars
        
        # Check patterns in priority order
        for pattern in self.question_re:
            if pattern.match(text_start):
                return "question"
        
        for pattern in self.solution_re:
            if pattern.match(text_start):
                return "solution"
        
        for pattern in self.definition_re:
            if pattern.match(text_start):
                return "definition"
        
        for pattern in self.example_re:
            if pattern.match(text_start):
                return "example"
        
        # Default to general text
        return "text"
    
    def _split_solution_steps(
        self,
        text: str,
        block: Dict,
        class_num: int,
        chapter_num: int,
        start_counter: int
    ) -> List[Dict]:
        """
        Split a solution into individual step chunks.
        
        Args:
            text: Solution text
            block: Original text block
            class_num: Class number
            chapter_num: Chapter number
            start_counter: Starting chunk counter
        
        Returns:
            List of step chunks
        """
        chunks = []
        
        # Split by step markers
        step_pattern = r'(?:Step\s+\d+:|^\(\d+\)|^[a-z]\))'
        steps = re.split(step_pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Clean and filter steps
        steps = [s.strip() for s in steps if s.strip() and len(s.strip()) > 10]
        
        if len(steps) <= 1:
            # No clear steps, return as single chunk
            chunk_id = f"class{class_num}_ch{chapter_num}_{start_counter:04d}"
            chunk = {
                "chunk_id": chunk_id,
                "ncert_id": chunk_id,
                "raw_text": text,
                "latex_formula": None,
                "image_path": None,
                "content_type": "solution",
                "step_number": None,
                "has_formula": False,
                "has_image": False,
                "metadata": {
                    "class": str(class_num),
                    "chapter": str(chapter_num),
                    "page": block.get('page_number', 0),
                    "subject": "Mathematics",
                    "type": "solution",
                    "ncert_id": chunk_id
                }
            }
            return [chunk]
        
        # Create chunk for each step
        for step_num, step_text in enumerate(steps, 1):
            chunk_id = f"class{class_num}_ch{chapter_num}_{start_counter + step_num - 1:04d}"
            
            chunk = {
                "chunk_id": chunk_id,
                "ncert_id": chunk_id,
                "raw_text": step_text,
                "latex_formula": None,
                "image_path": None,
                "content_type": "step",
                "step_number": step_num,
                "has_formula": False,
                "has_image": False,
                "metadata": {
                    "class": str(class_num),
                    "chapter": str(chapter_num),
                    "page": block.get('page_number', 0),
                    "subject": "Mathematics",
                    "type": "step",
                    "solution_step_number": step_num,
                    "ncert_id": chunk_id
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _classify_formula(self, latex: str) -> str:
        """
        Classify formula by mathematical topic.
        
        Args:
            latex: LaTeX formula
        
        Returns:
            Topic classification
        """
        if 'frac' in latex or '/' in latex:
            return "algebra"
        elif '^' in latex or 'sqrt' in latex:
            return "algebra"
        elif any(trig in latex for trig in ['sin', 'cos', 'tan', 'theta']):
            return "trigonometry"
        elif any(calc in latex for calc in ['int', 'frac{d', 'partial']):
            return "calculus"
        elif any(geom in latex for geom in ['angle', 'triangle', 'parallel']):
            return "geometry"
        else:
            return "arithmetic"
    
    def _add_topics(self, chunks: List[Dict]) -> List[Dict]:
        """
        Add topic tags to chunks based on content.
        
        Args:
            chunks: List of chunks
        
        Returns:
            Chunks with topic tags added
        """
        # Simple keyword-based topic detection
        topic_keywords = {
            "algebra": ["variable", "equation", "expression", "solve", "x", "y"],
            "geometry": ["triangle", "circle", "angle", "parallel", "perpendicular", "area", "perimeter"],
            "arithmetic": ["addition", "subtraction", "multiplication", "division", "fraction"],
            "trigonometry": ["sine", "cosine", "tangent", "angle", "theta"],
            "calculus": ["derivative", "integral", "limit", "differentiation"],
            "statistics": ["mean", "median", "mode", "probability", "data"],
            "number_theory": ["prime", "factor", "multiple", "divisor", "lcm", "hcf"],
        }
        
        for chunk in chunks:
            text = chunk.get('raw_text', '').lower()
            topics = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    topics.append(topic)
            
            if not topics:
                topics = ["general"]
            
            chunk['metadata']['topics'] = topics
        
        return chunks


if __name__ == "__main__":
    # Test the chunker
    logging.basicConfig(level=logging.INFO)
    
    chunker = MathChunker()
    
    # Test data
    test_blocks = [
        {"text": "1. Solve the equation: 2x + 3 = 7", "page_number": 5},
        {"text": "Solution: Step 1: Subtract 3 from both sides. Step 2: Divide by 2.", "page_number": 5},
        {"text": "Definition: A prime number is a natural number greater than 1.", "page_number": 6},
    ]
    
    chunks = chunker.chunk_content(test_blocks, [], [], class_num=5, chapter_num=1)
    
    for chunk in chunks:
        print(f"\nChunk ID: {chunk['chunk_id']}")
        print(f"Type: {chunk['content_type']}")
        print(f"Text: {chunk['raw_text'][:80]}...")
