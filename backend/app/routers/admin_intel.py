"""
Intel Status Admin Router

Provides endpoint for Intel evaluation to verify OPEA-style architecture
and OpenVINO integration status.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.utils.performance_logger import PerformanceLogger
from app.services.orchestrator_service import orchestrator_service
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Intel Admin"])


@router.get("/intel-status")
async def get_intel_status() -> Dict[str, Any]:
    """
    Get Intel optimization and OPEA architecture status.
    
    Returns comprehensive status for Intel evaluation:
    - OpenVINO service enablement
    - OPEA-style service list
    - Average latency metrics
    
    Target latencies:
    - OCR: <500ms
    - MCQ: <1000ms
    - RAG Query: <3000-5000ms
    """
    try:
        # Check OpenVINO service availability
        openvino_status = _check_openvino_status()
        
        # Get OPEA service list
        opea_services = [
            "IngestionService",
            "RetrievalService", 
            "GenerationService",
            "OrchestratorService"
        ]
        
        # Get latency metrics
        latencies = PerformanceLogger.get_avg_latencies()
        
        # Get detailed service statuses
        service_details = orchestrator_service.get_all_service_statuses()
        service_details["ingestion"] = ingestion_service.get_status()
        
        return {
            "status": "operational",
            "intel_optimized": True,
            "openvino_ocr_enabled": openvino_status.get("ocr", False),
            "openvino_vision_enabled": openvino_status.get("vision", False),
            "openvino_mcq_enabled": openvino_status.get("mcq", False),
            "opea_style_services": opea_services,
            "avg_latencies_ms": {
                "ocr_openvino": latencies.get("ocr_openvino", 0),
                "mcq_openvino": latencies.get("mcq_openvino", 0),
                "rag_retrieval": latencies.get("rag_retrieval", 0),
                "rag_generation": latencies.get("rag_generation", 0),
                "rag_full_pipeline": latencies.get("rag_full_pipeline", 0),
                "embedding_generation": latencies.get("embedding_generation", 0)
            },
            "target_latencies_ms": {
                "ocr_openvino": 500,
                "mcq_openvino": 1000,
                "rag_full_pipeline": 5000
            },
            "service_details": service_details,
            "architecture": "OPEA-style RAG Pipeline",
            "documentation": "/docs/intel_integration.md"
        }
    except Exception as e:
        logger.error(f"Failed to get Intel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intel-latency-report")
async def get_latency_report() -> Dict[str, Any]:
    """
    Get detailed latency report for Intel performance evaluation.
    """
    metrics = PerformanceLogger.get_metrics()
    
    return {
        "report_type": "Intel Performance Metrics",
        "metrics": metrics,
        "summary": {
            "total_components_tracked": len(metrics),
            "components": list(metrics.keys())
        }
    }


def _check_openvino_status() -> Dict[str, bool]:
    """Check availability of OpenVINO services."""
    status = {
        "ocr": False,
        "vision": False,
        "mcq": False
    }
    
    try:
        from app.services.openvino_ocr_service import openvino_ocr_service
        status["ocr"] = openvino_ocr_service is not None
    except:
        pass
    
    try:
        from app.services.openvino_vision_service import openvino_vision_service
        status["vision"] = openvino_vision_service is not None
    except:
        pass
    
    try:
        from app.services.openvino_mcq_service import openvino_mcq_service
        status["mcq"] = openvino_mcq_service is not None
    except:
        pass
    
    return status
