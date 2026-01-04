"""
MCQ Router - MCQ generation endpoints.

Supports hybrid pipeline:
- Gemini (default): Cloud-based, high quality  
- OpenVINO (local): Intel-accelerated, fast, on-device
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import MCQGenerationRequest, MCQGenerationResponse
from app.services.mcq_service import mcq_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mcq",
    tags=["MCQ Generation"]
)


@router.post("/generate", response_model=MCQGenerationResponse)
async def generate_mcqs(request: MCQGenerationRequest):
    """
    Generate AI-powered MCQs based on chapter content.
    
    Uses RAG to retrieve chapter context from Pinecone,
    then generates concept-based MCQs using selected pipeline.
    
    **Pipeline Options:**
    - `use_local_model=false` (default): Uses Gemini for high-quality MCQs
    - `use_local_model=true`: Uses Intel OpenVINO for fast local generation
    
    **Returns:**
    - List of MCQs with questions, options, correct answer, and explanations
    - Metadata about class, subject, and chapter
    - Pipeline used and inference time
    """
    try:
        logger.info(f"MCQ generation request: Class {request.class_level}, {request.subject}, Ch. {request.chapter}, {request.num_questions} questions, local_model={request.use_local_model}")
        
        # Generate MCQs
        mcqs, used_pipeline, inference_time_ms = mcq_service.generate_mcqs(
            class_level=request.class_level,
            subject=request.subject,
            chapter=request.chapter,
            num_questions=request.num_questions,
            page_range=request.page_range,
            use_local_model=request.use_local_model
        )
        
        metadata = {
            "class_level": request.class_level,
            "subject": request.subject,
            "chapter": request.chapter,
            "num_questions": len(mcqs),
            "requested_questions": request.num_questions
        }
        
        return MCQGenerationResponse(
            mcqs=mcqs,
            metadata=metadata,
            used_pipeline=used_pipeline,
            inference_time_ms=inference_time_ms
        )
    
    except Exception as e:
        logger.error(f"❌ MCQ generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark")
async def benchmark_mcq_generation():
    """
    Benchmark MCQ generation comparing OpenVINO vs Gemini performance.
    
    Returns timing statistics for both pipelines to demonstrate
    Intel OpenVINO acceleration benefits.
    """
    try:
        logger.info("Running MCQ generation benchmark...")
        
        # Test context
        test_context = """
        Photosynthesis is the process by which plants convert sunlight into chemical energy.
        It occurs in the chloroplasts of plant cells, specifically in the chlorophyll.
        The process requires carbon dioxide and water, producing glucose and oxygen.
        The chemical equation is: 6CO2 + 6H2O + light → C6H12O6 + 6O2.
        Light-dependent reactions occur in the thylakoid membranes.
        The Calvin cycle occurs in the stroma of the chloroplast.
        """
        
        results = {
            "test_context_preview": test_context[:100] + "...",
            "num_questions_tested": 4,
            "pipelines": {}
        }
        
        # Benchmark Gemini
        try:
            _, _, gemini_time = mcq_service._generate_with_gemini(
                context=test_context,
                num_questions=4,
                class_level=10,
                subject="Science",
                chapter=1
            )
            results["pipelines"]["gemini"] = {
                "available": True,
                "inference_time_ms": gemini_time
            }
        except Exception as e:
            results["pipelines"]["gemini"] = {
                "available": False,
                "error": str(e)
            }
        
        # Get OpenVINO status
        ov_status = mcq_service.get_openvino_status()
        results["pipelines"]["openvino"] = ov_status
        
        # Calculate speedup if both available
        if results["pipelines"]["gemini"].get("available") and ov_status.get("available"):
            if "avg_time_ms" in ov_status:
                gemini_ms = results["pipelines"]["gemini"]["inference_time_ms"]
                openvino_ms = ov_status["avg_time_ms"]
                speedup = gemini_ms / openvino_ms if openvino_ms > 0 else 0
                results["speedup"] = f"{speedup:.2f}x faster with OpenVINO"
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openvino-status")
async def get_openvino_status():
    """
    Get Intel OpenVINO MCQ service status.
    
    Returns availability, device, model path, and any errors.
    """
    try:
        status = mcq_service.get_openvino_status()
        return status
    except Exception as e:
        return {"available": False, "error": str(e)}

