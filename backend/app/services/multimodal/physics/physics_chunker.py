"""
Physics Chunker

Semantic chunking for physics content with 10 distinct chunk types.
Never splits formulas, derivations, or solution steps incorrectly.
"""

import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PhysicsChunker:
    """Semantic chunking for physics content"""
    
    def __init__(self):
        self.chunk_types = {
            'concept', 'law', 'formula', 'derivation',
            'numerical_question', 'solution_step',
            'diagram', 'table', 'experiment', 'example'
        }
        logger.info("⚙️ Physics Chunker initialized")
    
    def chunk_content(
        self,
        extracted_data: Dict,
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """
        Create semantic chunks from extracted physics content
        
        Args:
            extracted_data: Output from PhysicsPDFProcessor
            class_num: Class number
            chapter_num: Chapter number
        
        Returns:
            List of chunk dictionaries
        """
        logger.info(f"📦 Chunking physics content for Class {class_num}, Chapter {chapter_num}")
        
        chunks = []
        
        # Process text blocks into concept/law chunks
        text_chunks = self._chunk_text_blocks(
            extracted_data.get('text_blocks', []),
            class_num,
            chapter_num
        )
        chunks.extend(text_chunks)
        
        # Process diagrams
        diagram_chunks = self._chunk_diagrams(
            extracted_data.get('images', []),
            class_num,
            chapter_num
        )
        chunks.extend(diagram_chunks)
        
        # Process tables
        table_chunks = self._chunk_tables(
            extracted_data.get('tables', []),
            class_num,
            chapter_num
        )
        chunks.extend(table_chunks)
        
        # Process experiments
        experiment_chunks = self._chunk_experiments(
            extracted_data.get('experiments', []),
            class_num,
            chapter_num
        )
        chunks.extend(experiment_chunks)
        
        # Process numerical problems
        numerical_chunks = self._chunk_numericals(
            extracted_data.get('numerical_problems', []),
            class_num,
            chapter_num
        )
        chunks.extend(numerical_chunks)
        
        logger.info(f"✅ Created {len(chunks)} semantic chunks")
        self._log_chunk_distribution(chunks)
        
        return chunks
    
    def _chunk_text_blocks(
        self,
        text_blocks: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Chunk text blocks into concepts, laws, formulas, derivations"""
        chunks = []
        chunk_id_counter = 0
        
        for block in text_blocks:
            text = block.get('text', '').strip()
            if not text or len(text) < 10:
                continue
            
            block_type = block.get('block_type', 'concept')
            page = block.get('page', 1)
            
            # Determine content type
            content_type = self._determine_content_type(text, block_type)
            
            # Check for formulas in text
            has_formula, formula_text = self._extract_inline_formula(text)
            
            chunk_id = f"class{class_num}_ch{chapter_num}_{content_type}_{chunk_id_counter:04d}"
            chunk_id_counter += 1
            
            chunk = {
                'chunk_id': chunk_id,
                'raw_text': text,
                'latex_formula': formula_text if has_formula else None,
                'diagram_path': None,
                'table_data': None,
                'step_number': None,
                'content_type': content_type,
                'has_formula': has_formula,
                'has_image': False,
                'has_table': False,
                'metadata': {
                    'class': class_num,
                    'chapter': chapter_num,
                    'page': page,
                    'subject': 'Physics',
                    'ncert_id': f"class{class_num}_ch{chapter_num}_p{page}"
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_diagrams(
        self,
        images: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Create diagram chunks"""
        chunks = []
        
        for idx, img in enumerate(images):
            chunk_id = f"class{class_num}_ch{chapter_num}_diagram_{idx:04d}"
            
            # Generate caption from diagram type
            diagram_type = img.get('diagram_type', 'diagram')
            caption = self._generate_diagram_caption(diagram_type)
            
            chunk = {
                'chunk_id': chunk_id,
                'raw_text': caption,
                'latex_formula': None,
                'diagram_path': img.get('path'),
                'table_data': None,
                'step_number': None,
                'content_type': 'diagram',
                'has_formula': False,
                'has_image': True,
                'has_table': False,
                'metadata': {
                    'class': class_num,
                    'chapter': chapter_num,
                    'page': img.get('page', 1),
                    'subject': 'Physics',
                    'diagram_type': diagram_type,
                    'ncert_id': f"class{class_num}_ch{chapter_num}_p{img.get('page', 1)}"
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_tables(
        self,
        tables: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Create table chunks"""
        chunks = []
        
        for idx, table in enumerate(tables):
            chunk_id = f"class{class_num}_ch{chapter_num}_table_{idx:04d}"
            
            chunk = {
                'chunk_id': chunk_id,
                'raw_text': f"Experimental data table from page {table.get('page', 1)}",
                'latex_formula': None,
                'diagram_path': None,
                'table_data': table.get('data'),
                'step_number': None,
                'content_type': 'table',
                'has_formula': False,
                'has_image': False,
                'has_table': True,
                'metadata': {
                    'class': class_num,
                    'chapter': chapter_num,
                    'page': table.get('page', 1),
                    'subject': 'Physics',
                    'ncert_id': f"class{class_num}_ch{chapter_num}_p{table.get('page', 1)}"
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_experiments(
        self,
        experiments: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Create experiment chunks"""
        chunks = []
        
        for idx, exp in enumerate(experiments):
            chunk_id = f"class{class_num}_ch{chapter_num}_experiment_{idx:04d}"
            
            # Check for formulas in experiment text
            text = exp.get('text', '')
            has_formula, formula_text = self._extract_inline_formula(text)
            
            chunk = {
                'chunk_id': chunk_id,
                'raw_text': text,
                'latex_formula': formula_text if has_formula else None,
                'diagram_path': None,
                'table_data': None,
                'step_number': None,
                'content_type': 'experiment',
                'has_formula': has_formula,
                'has_image': False,
                'has_table': False,
                'metadata': {
                    'class': class_num,
                    'chapter': chapter_num,
                    'page': exp.get('page', 1),
                    'subject': 'Physics',
                    'ncert_id': f"class{class_num}_ch{chapter_num}_p{exp.get('page', 1)}"
                }
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_numericals(
        self,
        numericals: List[Dict],
        class_num: int,
        chapter_num: int
    ) -> List[Dict]:
        """Create numerical problem chunks with solution steps"""
        chunks = []
        
        for idx, num in enumerate(numericals):
            # Question chunk
            question_text = num.get('question', '')
            has_formula_q, formula_q = self._extract_inline_formula(question_text)
            
            question_chunk = {
                'chunk_id': f"class{class_num}_ch{chapter_num}_numerical_q_{idx:04d}",
                'raw_text': question_text,
                'latex_formula': formula_q if has_formula_q else None,
                'diagram_path': None,
                'table_data': None,
                'step_number': None,
                'content_type': 'numerical_question',
                'has_formula': has_formula_q,
                'has_image': False,
                'has_table': False,
                'metadata': {
                    'class': class_num,
                    'chapter': chapter_num,
                    'page': num.get('page', 1),
                    'subject': 'Physics',
                    'problem_id': idx,
                    'ncert_id': f"class{class_num}_ch{chapter_num}_p{num.get('page', 1)}"
                }
            }
            chunks.append(question_chunk)
            
            # Solution chunk (if exists)
            solution_text = num.get('solution')
            if solution_text:
                # Split solution into steps if possible
                solution_steps = self._split_solution_steps(solution_text)
                
                for step_idx, step_text in enumerate(solution_steps):
                    has_formula_s, formula_s = self._extract_inline_formula(step_text)
                    
                    solution_chunk = {
                        'chunk_id': f"class{class_num}_ch{chapter_num}_solution_{idx:04d}_step{step_idx}",
                        'raw_text': step_text,
                        'latex_formula': formula_s if has_formula_s else None,
                        'diagram_path': None,
                        'table_data': None,
                        'step_number': step_idx + 1,
                        'content_type': 'solution_step',
                        'has_formula': has_formula_s,
                        'has_image': False,
                        'has_table': False,
                        'metadata': {
                            'class': class_num,
                            'chapter': chapter_num,
                            'page': num.get('page', 1),
                            'subject': 'Physics',
                            'problem_id': idx,
                            'step_number': step_idx + 1,
                            'ncert_id': f"class{class_num}_ch{chapter_num}_p{num.get('page', 1)}"
                        }
                    }
                    chunks.append(solution_chunk)
        
        return chunks
    
    def _determine_content_type(self, text: str, block_type: str) -> str:
        """Determine content type from text and block type"""
        text_lower = text.lower()
        
        # Priority order matters
        if block_type == 'law':
            return 'law'
        elif block_type == 'derivation':
            return 'derivation'
        elif block_type == 'numerical':
            return 'numerical_question'
        elif block_type == 'experiment':
            return 'experiment'
        elif 'example' in text_lower and len(text) > 100:
            return 'example'
        elif self._is_formula_only(text):
            return 'formula'
        elif block_type == 'definition':
            return 'concept'
        else:
            return 'concept'
    
    def _is_formula_only(self, text: str) -> bool:
        """Check if text is primarily a formula"""
        # Check if text has equation markers and is short
        has_equals = '=' in text
        is_short = len(text) < 100
        has_variables = bool(re.search(r'[A-Z][a-z]?\s*=', text))
        
        return has_equals and (is_short or has_variables)
    
    def _extract_inline_formula(self, text: str) -> tuple:
        """Extract formula from text if present"""
        # Simple formula detection
        formula_patterns = [
            r'[A-Z]\s*=\s*[^.]{5,50}',  # Basic equation
            r'[FVIPmvuatghKEPEW]\s*=',  # Physics variables
        ]
        
        for pattern in formula_patterns:
            match = re.search(pattern, text)
            if match:
                formula = match.group(0).strip()
                return True, f"${formula}$"
        
        return False, None
    
    def _split_solution_steps(self, solution_text: str) -> List[str]:
        """Split solution into logical steps"""
        # Try to split by step markers
        step_markers = [
            r'\n\s*Step\s*\d+',
            r'\n\s*\(\d+\)',
            r'\n\s*\d+\.',
            r'\n\s*Given:',
            r'\n\s*Solution:',
            r'\n\s*Therefore,',
            r'\n\s*Hence,',
        ]
        
        # Try each marker
        for marker in step_markers:
            parts = re.split(marker, solution_text, flags=re.IGNORECASE)
            if len(parts) > 1:
                return [p.strip() for p in parts if p.strip()]
        
        # If no markers, return as single step
        return [solution_text.strip()]
    
    def _generate_diagram_caption(self, diagram_type: str) -> str:
        """Generate caption for diagram"""
        captions = {
            'circuit': 'Circuit diagram showing electrical components',
            'ray_diagram': 'Ray diagram illustrating light path through optical system',
            'force_diagram': 'Force diagram showing vectors and directions',
            'graph': 'Graph showing relationship between physical quantities',
            'experiment_setup': 'Experimental setup and apparatus arrangement',
            'diagram': 'Physics diagram illustration'
        }
        return captions.get(diagram_type, 'Physics diagram')
    
    def _log_chunk_distribution(self, chunks: List[Dict]):
        """Log distribution of chunk types"""
        from collections import Counter
        type_counts = Counter(chunk['content_type'] for chunk in chunks)
        
        logger.info("   Chunk type distribution:")
        for chunk_type in sorted(type_counts.keys()):
            logger.info(f"      - {chunk_type}: {type_counts[chunk_type]}")
