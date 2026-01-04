"""
Setup script for OpenVINO Multilingual Model (LaBSE)

Downloads and converts LaBSE (Language-agnostic BERT Sentence Embedding)
to OpenVINO IR format for Intel-optimized multilingual embeddings.

Usage:
    python setup_multilingual_model.py
    
This will:
1. Download LaBSE from HuggingFace
2. Convert to OpenVINO IR format
3. Save to models/openvino_multilingual/
"""

import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "sentence-transformers/LaBSE"
OUTPUT_DIR = Path(__file__).parent / "models" / "openvino_multilingual"


def check_dependencies():
    """Check required dependencies."""
    missing = []
    
    try:
        import openvino
        logger.info(f"✓ OpenVINO version: {openvino.__version__}")
    except ImportError:
        missing.append("openvino>=2024.0.0")
    
    try:
        import transformers
        logger.info(f"✓ Transformers version: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
    
    try:
        from optimum.intel import OVModelForFeatureExtraction
        logger.info("✓ Optimum Intel available")
    except ImportError:
        missing.append("optimum[openvino]")
    
    try:
        import torch
        logger.info(f"✓ PyTorch version: {torch.__version__}")
    except ImportError:
        missing.append("torch")
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def download_and_convert():
    """Download LaBSE and convert to OpenVINO IR."""
    from transformers import AutoTokenizer, AutoModel
    
    logger.info(f"📥 Downloading {MODEL_NAME}...")
    
    # Download tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    logger.info("✓ Tokenizer downloaded")
    
    # Try optimum-intel conversion first
    try:
        from optimum.intel import OVModelForFeatureExtraction
        
        logger.info("🔄 Converting to OpenVINO using optimum-intel...")
        
        # Export directly to OpenVINO
        ov_model = OVModelForFeatureExtraction.from_pretrained(
            MODEL_NAME,
            export=True
        )
        
        # Save to output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ov_model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        logger.info(f"✓ Model saved to {OUTPUT_DIR}")
        return True
        
    except Exception as e:
        logger.warning(f"Optimum-intel conversion failed: {e}")
        logger.info("Trying manual conversion...")
    
    # Manual conversion fallback
    try:
        import openvino as ov
        from openvino.tools import mo
        import torch
        
        # Download PyTorch model
        model = AutoModel.from_pretrained(MODEL_NAME)
        model.eval()
        
        # Create dummy input
        dummy_input = tokenizer(
            "Test sentence for conversion",
            return_tensors="pt",
            max_length=128,
            truncation=True,
            padding=True
        )
        
        # Export to ONNX first
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        onnx_path = OUTPUT_DIR / "model.onnx"
        
        torch.onnx.export(
            model,
            (dummy_input['input_ids'], dummy_input['attention_mask']),
            str(onnx_path),
            input_names=['input_ids', 'attention_mask'],
            output_names=['last_hidden_state'],
            dynamic_axes={
                'input_ids': {0: 'batch', 1: 'sequence'},
                'attention_mask': {0: 'batch', 1: 'sequence'},
                'last_hidden_state': {0: 'batch', 1: 'sequence'}
            },
            opset_version=14
        )
        logger.info(f"✓ ONNX model exported to {onnx_path}")
        
        # Convert ONNX to OpenVINO IR
        ov_model = ov.convert_model(str(onnx_path))
        
        # Save OpenVINO model
        ir_path = OUTPUT_DIR / "model.xml"
        ov.save_model(ov_model, str(ir_path))
        
        # Save tokenizer
        tokenizer.save_pretrained(OUTPUT_DIR)
        
        # Clean up ONNX file
        onnx_path.unlink()
        
        logger.info(f"✓ OpenVINO IR model saved to {ir_path}")
        return True
        
    except Exception as e:
        logger.error(f"Manual conversion failed: {e}")
        return False


def verify_model():
    """Verify the converted model works."""
    logger.info("🔍 Verifying model...")
    
    try:
        import openvino as ov
        from transformers import AutoTokenizer
        
        # Load model
        core = ov.Core()
        model_xml = OUTPUT_DIR / "model.xml"
        if not model_xml.exists():
            model_xml = OUTPUT_DIR / "openvino_model.xml"
        
        model = core.compile_model(str(model_xml), "CPU")
        tokenizer = AutoTokenizer.from_pretrained(str(OUTPUT_DIR))
        
        # Test inference
        test_texts = [
            "Hello, how are you?",
            "नमस्ते, आप कैसे हैं?",
            "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
            "آپ کیسے ہیں؟"
        ]
        
        for text in test_texts:
            inputs = tokenizer(text, return_tensors="np", max_length=128, truncation=True, padding=True)
            output = model(inputs)
            
            # Get embedding shape
            if isinstance(output, dict):
                shape = output[list(output.keys())[0]].shape
            else:
                shape = output[0].shape
            
            logger.info(f"  '{text[:30]}...' → shape: {shape}")
        
        logger.info("✓ Model verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("OpenVINO Multilingual Model Setup (LaBSE)")
    logger.info("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if model already exists
    if (OUTPUT_DIR / "model.xml").exists() or (OUTPUT_DIR / "openvino_model.xml").exists():
        logger.info(f"Model already exists at {OUTPUT_DIR}")
        response = input("Re-download and convert? [y/N]: ")
        if response.lower() != 'y':
            logger.info("Using existing model.")
            verify_model()
            return
    
    # Download and convert
    if not download_and_convert():
        logger.error("❌ Model setup failed!")
        sys.exit(1)
    
    # Verify
    if not verify_model():
        logger.error("❌ Model verification failed!")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ Setup complete!")
    logger.info(f"Model location: {OUTPUT_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
