"""
OpenVINO MCQ Service for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO Runtime and optimum-intel for local MCQ generation on Intel CPU.

Intel OpenVINO-accelerated MCQ generation using a local T5 model.
Provides fast, on-device MCQ drafting with optional Gemini refinement.

This module provides:
- Local text-to-MCQ generation using OpenVINO
- Performance benchmarking vs cloud models
- Fallback to Gemini when local model unavailable

Maps to OPEA GenerationService MCQ component.
"""

import os
import logging
import time
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import openvino as ov
    from openvino_genai import LLMPipeline
    HAS_OPENVINO_GENAI = True
except ImportError:
    HAS_OPENVINO_GENAI = False

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from optimum.intel import OVModelForSeq2SeqLM
    HAS_OPTIMUM = True
except ImportError:
    HAS_OPTIMUM = False

logger = logging.getLogger(__name__)


# MCQ prompt template for T5
MCQ_PROMPT_TEMPLATE = """Generate {num_questions} multiple choice questions from this text. 
For each question, provide:
- The question
- Four options (A, B, C, D)
- The correct answer letter
- A brief explanation

Text: {text}

Questions:"""


class OpenVinoMcqService:
    """
    Intel OpenVINO-accelerated MCQ generation service.
    
    Uses a local T5-small model converted to OpenVINO IR format
    for fast on-device MCQ generation.
    
    Example:
        mcq_service = OpenVinoMcqService()
        mcqs = mcq_service.generate_mcq_draft("Photosynthesis is...", num_questions=4)
    """
    
    DEFAULT_MODEL_PATH = "models/openvino_mcq"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "CPU",
        use_int8: bool = True
    ):
        """
        Initialize the OpenVINO MCQ service.
        
        Args:
            model_path: Path to OpenVINO IR model directory
            device: OpenVINO device (CPU, GPU, AUTO)
            use_int8: Use INT8 quantization for faster inference
        """
        self.device = device
        self.use_int8 = use_int8
        self._model = None
        self._tokenizer = None
        self._is_loaded = False
        self._load_error = None
        
        # Set model path
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                self.DEFAULT_MODEL_PATH
            )
        self.model_path = Path(model_path)
        
        # Try to load model
        self._try_load_model()
        
        logger.info(f"✓ OpenVinoMcqService initialized (device: {device}, loaded: {self._is_loaded})")
    
    def _try_load_model(self) -> None:
        """Attempt to load the OpenVINO model."""
        if not HAS_OPTIMUM:
            self._load_error = "optimum-intel not installed. Run: pip install optimum[openvino]"
            logger.warning(f"⚠️ {self._load_error}")
            return
        
        if not self.model_path.exists():
            self._load_error = f"Model not found at {self.model_path}. Run setup_openvino_mcq_model.py first."
            logger.warning(f"⚠️ {self._load_error}")
            return
        
        try:
            logger.info(f"Loading OpenVINO MCQ model from {self.model_path}...")
            
            # Check if it's an optimum-intel model
            if (self.model_path / "openvino_encoder_model.xml").exists():
                self._model = OVModelForSeq2SeqLM.from_pretrained(
                    str(self.model_path),
                    device=self.device
                )
                self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
                self._is_loaded = True
                logger.info("✓ OpenVINO MCQ model loaded successfully")
            else:
                self._load_error = "OpenVINO model files not found in model directory"
                logger.warning(f"⚠️ {self._load_error}")
                
        except Exception as e:
            self._load_error = f"Failed to load model: {e}"
            logger.error(f"❌ {self._load_error}")
    
    def is_available(self) -> bool:
        """Check if the MCQ service is ready to use."""
        return self._is_loaded and self._model is not None
    
    def get_status(self) -> Dict:
        """Get service status information."""
        return {
            "available": self.is_available(),
            "device": self.device,
            "model_path": str(self.model_path),
            "error": self._load_error,
            "has_optimum": HAS_OPTIMUM,
            "has_openvino_genai": HAS_OPENVINO_GENAI
        }
    
    def _parse_mcq_output(self, text: str, num_questions: int) -> List[Dict]:
        """
        Parse model output into structured MCQ format.
        
        Args:
            text: Raw model output text
            num_questions: Expected number of questions
            
        Returns:
            List of MCQ dictionaries
        """
        mcqs = []
        
        # Try to parse structured output
        # Pattern: Q1. Question text\nA) option\nB) option\nC) option\nD) option\nAnswer: X\nExplanation: ...
        question_pattern = r'(?:Q?\d+[\.\)]\s*)?(.+?)\n\s*[Aa][\.\)]\s*(.+?)\n\s*[Bb][\.\)]\s*(.+?)\n\s*[Cc][\.\)]\s*(.+?)\n\s*[Dd][\.\)]\s*(.+?)(?:\n\s*(?:Answer|Correct):\s*([A-Da-d]))?(?:\n\s*(?:Explanation):\s*(.+?))?(?=\n\s*(?:Q?\d+[\.\)]|$))'
        
        matches = re.findall(question_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:num_questions]:
            question = match[0].strip() if match[0] else ""
            options = [
                match[1].strip() if match[1] else "",
                match[2].strip() if match[2] else "",
                match[3].strip() if match[3] else "",
                match[4].strip() if match[4] else ""
            ]
            answer = match[5].upper() if len(match) > 5 and match[5] else "A"
            explanation = match[6].strip() if len(match) > 6 and match[6] else "See textbook for details."
            
            if question and all(options):
                # Convert answer letter to index
                answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                correct_index = answer_map.get(answer, 0)
                
                mcqs.append({
                    "question": question,
                    "options": options,
                    "correct_index": correct_index,
                    "explanation": explanation
                })
        
        # If parsing failed, try simpler approach
        if not mcqs:
            mcqs = self._fallback_parse(text, num_questions)
        
        return mcqs
    
    def _fallback_parse(self, text: str, num_questions: int) -> List[Dict]:
        """Fallback parsing when structured parsing fails."""
        mcqs = []
        
        # Split by question numbers
        parts = re.split(r'\n\s*\d+[\.\)]\s*', text)
        
        for i, part in enumerate(parts[1:num_questions+1], 1):
            lines = [l.strip() for l in part.split('\n') if l.strip()]
            
            if len(lines) >= 5:
                question = lines[0]
                options = lines[1:5]
                # Clean option prefixes
                options = [re.sub(r'^[A-Da-d][\.\)]\s*', '', opt) for opt in options]
                
                mcqs.append({
                    "question": question,
                    "options": options,
                    "correct_index": 0,  # Default to first option
                    "explanation": f"Generated from textbook content about {question[:50]}..."
                })
        
        return mcqs
    
    def generate_mcq_draft(
        self,
        text_chunk: str,
        num_questions: int = 4,
        max_length: int = 1024
    ) -> Tuple[List[Dict], float]:
        """
        Generate draft MCQs using Intel OpenVINO.
        
        Args:
            text_chunk: Source text to generate MCQs from
            num_questions: Number of MCQs to generate
            max_length: Maximum output length
            
        Returns:
            Tuple of (list of MCQ dicts, inference time in ms)
        """
        if not self.is_available():
            raise RuntimeError(f"OpenVINO MCQ model not available: {self._load_error}")
        
        # Prepare prompt
        prompt = MCQ_PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            text=text_chunk[:2000]  # Limit input length
        )
        
        # Tokenize
        start_time = time.perf_counter()
        
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        
        # Generate
        outputs = self._model.generate(
            **inputs,
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=2
        )
        
        # Decode
        generated_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Parse output
        mcqs = self._parse_mcq_output(generated_text, num_questions)
        
        logger.info(f"✓ Generated {len(mcqs)} MCQs in {inference_time_ms:.1f}ms (OpenVINO)")
        
        return mcqs, inference_time_ms
    
    def benchmark(
        self,
        text_chunk: str,
        num_questions: int = 4,
        num_runs: int = 3
    ) -> Dict:
        """
        Benchmark MCQ generation performance.
        
        Args:
            text_chunk: Text to generate MCQs from
            num_questions: Number of questions per run
            num_runs: Number of benchmark runs
            
        Returns:
            Performance metrics dictionary
        """
        if not self.is_available():
            return {
                "error": self._load_error,
                "available": False
            }
        
        times = []
        mcq_counts = []
        
        for i in range(num_runs):
            try:
                mcqs, time_ms = self.generate_mcq_draft(text_chunk, num_questions)
                times.append(time_ms)
                mcq_counts.append(len(mcqs))
            except Exception as e:
                logger.error(f"Benchmark run {i+1} failed: {e}")
        
        if not times:
            return {"error": "All benchmark runs failed", "available": True}
        
        return {
            "available": True,
            "device": self.device,
            "num_runs": len(times),
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "avg_mcqs_generated": sum(mcq_counts) / len(mcq_counts),
            "times_ms": times
        }


# Singleton instance
_mcq_service_instance: Optional[OpenVinoMcqService] = None


def get_openvino_mcq_service(
    device: str = "CPU",
    model_path: Optional[str] = None
) -> OpenVinoMcqService:
    """
    Get or create the OpenVINO MCQ service singleton.
    
    Args:
        device: OpenVINO device (CPU, GPU, AUTO)
        model_path: Optional custom model path
        
    Returns:
        OpenVinoMcqService instance
    """
    global _mcq_service_instance
    
    if _mcq_service_instance is None:
        _mcq_service_instance = OpenVinoMcqService(
            device=device,
            model_path=model_path
        )
    
    return _mcq_service_instance
