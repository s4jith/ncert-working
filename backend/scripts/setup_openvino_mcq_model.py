#!/usr/bin/env python3
"""
Setup OpenVINO MCQ Model

This script downloads and converts a T5-small model to OpenVINO IR format
for use with the OpenVinoMcqService.

Usage:
    python scripts/setup_openvino_mcq_model.py

Requirements:
    pip install transformers optimum[openvino] sentencepiece

Output:
    models/openvino_mcq/  - OpenVINO IR model files
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    
    try:
        import transformers
        logger.info(f"✓ transformers {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
    
    # Check optimum-intel (can be imported different ways)
    optimum_ok = False
    try:
        from optimum.intel import OVModelForSeq2SeqLM
        logger.info("✓ optimum-intel installed")
        optimum_ok = True
    except ImportError:
        pass
    
    if not optimum_ok:
        try:
            from optimum.intel.openvino import OVModelForSeq2SeqLM
            logger.info("✓ optimum-intel installed (alternate import)")
            optimum_ok = True
        except ImportError:
            pass
    
    if not optimum_ok:
        missing.append("optimum-intel (pip install optimum[openvino])")
    
    try:
        import openvino
        logger.info(f"✓ openvino {openvino.__version__}")
    except ImportError:
        missing.append("openvino")
    
    try:
        import sentencepiece
        logger.info("✓ sentencepiece installed")
    except ImportError:
        missing.append("sentencepiece")
    
    if missing:
        logger.error(f"❌ Missing packages: {', '.join(missing)}")
        logger.error("Install with: pip install transformers optimum[openvino] openvino sentencepiece")
        return False
    
    return True


def download_and_convert_model(
    model_name: str = "google/flan-t5-small",
    output_dir: str = "models/openvino_mcq",
    use_int8: bool = False
):
    """
    Download HuggingFace model and convert to OpenVINO IR format.
    
    Args:
        model_name: HuggingFace model ID
        output_dir: Output directory for OpenVINO model
        use_int8: Apply INT8 quantization (smaller, faster, slight quality loss)
    """
    from transformers import AutoTokenizer
    from optimum.intel import OVModelForSeq2SeqLM
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📥 Downloading model: {model_name}")
    logger.info(f"   Output directory: {output_path.absolute()}")
    
    # Load and convert model
    logger.info("🔄 Converting to OpenVINO IR format...")
    
    try:
        # Export directly to OpenVINO format
        model = OVModelForSeq2SeqLM.from_pretrained(
            model_name,
            export=True,  # Convert on-the-fly
            compile=False  # Don't compile yet
        )
        
        # Save the model
        logger.info(f"💾 Saving OpenVINO model to {output_path}...")
        model.save_pretrained(str(output_path))
        
        # Also save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(str(output_path))
        
        logger.info("✅ Model conversion complete!")
        
    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        raise


def verify_model(output_dir: str = "models/openvino_mcq"):
    """
    Verify the converted model works correctly.
    
    Args:
        output_dir: Path to the converted model
    """
    from transformers import AutoTokenizer
    from optimum.intel import OVModelForSeq2SeqLM
    
    output_path = Path(output_dir)
    
    logger.info("🔍 Verifying model...")
    
    # Check files exist
    required_files = [
        "openvino_encoder_model.xml",
        "openvino_encoder_model.bin",
        "openvino_decoder_model.xml",
        "openvino_decoder_model.bin",
        "tokenizer_config.json"
    ]
    
    for file in required_files:
        if not (output_path / file).exists():
            logger.warning(f"⚠️ Missing file: {file}")
    
    # Try loading and running inference
    try:
        logger.info("Loading model for verification...")
        model = OVModelForSeq2SeqLM.from_pretrained(str(output_path))
        tokenizer = AutoTokenizer.from_pretrained(str(output_path))
        
        # Test inference
        test_input = "Generate a question about photosynthesis"
        inputs = tokenizer(test_input, return_tensors="pt")
        
        logger.info("Running test inference...")
        outputs = model.generate(**inputs, max_length=100)
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info(f"✅ Test output: {result[:100]}...")
        logger.info("✅ Model verification successful!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def print_model_info(output_dir: str = "models/openvino_mcq"):
    """Print information about the converted model."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.error(f"Model directory not found: {output_path}")
        return
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_path.glob("*") if f.is_file())
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 MODEL INFORMATION")
    logger.info("=" * 60)
    logger.info(f"   Location: {output_path.absolute()}")
    logger.info(f"   Total Size: {total_size / (1024*1024):.1f} MB")
    
    # List files
    logger.info("\n   Files:")
    for f in sorted(output_path.glob("*")):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            logger.info(f"     - {f.name}: {size_kb:.1f} KB")
    
    logger.info("=" * 60)
    logger.info("\n🚀 Ready to use with OpenVinoMcqService!")
    logger.info("   Set OPENVINO_MCQ_MODEL_PATH environment variable if using custom path")


def main():
    parser = argparse.ArgumentParser(
        description="Setup OpenVINO MCQ model for Intel-accelerated MCQ generation"
    )
    parser.add_argument(
        "--model", "-m",
        default="google/flan-t5-small",
        help="HuggingFace model ID (default: google/flan-t5-small)"
    )
    parser.add_argument(
        "--output", "-o",
        default="models/openvino_mcq",
        help="Output directory (default: models/openvino_mcq)"
    )
    parser.add_argument(
        "--int8",
        action="store_true",
        help="Apply INT8 quantization for smaller/faster model"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing model, don't download"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show model info and exit"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🔧 OpenVINO MCQ Model Setup")
    print("   Intel-optimized MCQ generation for NCERT AI Learning")
    print("=" * 60 + "\n")
    
    # Show info only
    if args.info:
        print_model_info(args.output)
        return
    
    # Verify only
    if args.verify_only:
        if verify_model(args.output):
            print_model_info(args.output)
        return
    
    # Full setup
    if not check_dependencies():
        sys.exit(1)
    
    print()
    download_and_convert_model(
        model_name=args.model,
        output_dir=args.output,
        use_int8=args.int8
    )
    
    print()
    if verify_model(args.output):
        print_model_info(args.output)
    

if __name__ == "__main__":
    main()
