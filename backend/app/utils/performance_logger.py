"""
Performance Logger for Intel Optimization Metrics

Intel-optimized: Provides latency tracking for OPEA-style RAG components.
Logs execution times to console and MongoDB for Intel evaluation metrics.
"""

import time
import logging
import functools
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class IntelOptimizedConfig:
    """Configuration for Intel-optimized components."""
    intel_optimized: bool = True
    component_name: str = ""
    description: str = ""


@dataclass
class LatencyMetrics:
    """Stores moving average latency metrics."""
    total_calls: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    
    @property
    def avg_time_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_time_ms / self.total_calls
    
    def record(self, time_ms: float):
        self.total_calls += 1
        self.total_time_ms += time_ms
        self.min_time_ms = min(self.min_time_ms, time_ms)
        self.max_time_ms = max(self.max_time_ms, time_ms)


class PerformanceLogger:
    """
    Performance logger for tracking Intel-optimized component latencies.
    
    Intel-optimized: Provides evidence of Intel acceleration and RAG latency
    for OPEA-style pipeline evaluation (target: ≤3-5s for full RAG query).
    """
    
    _instance = None
    _metrics: Dict[str, LatencyMetrics] = defaultdict(LatencyMetrics)
    _mongo_db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Dict[str, float]]:
        """Get all latency metrics as dictionary."""
        result = {}
        for name, metrics in cls._metrics.items():
            result[name] = {
                "avg_ms": round(metrics.avg_time_ms, 2),
                "min_ms": round(metrics.min_time_ms, 2) if metrics.min_time_ms != float('inf') else 0,
                "max_ms": round(metrics.max_time_ms, 2),
                "total_calls": metrics.total_calls
            }
        return result
    
    @classmethod
    def record_latency(cls, component_name: str, time_ms: float, metadata: Optional[Dict] = None):
        """Record a latency measurement."""
        cls._metrics[component_name].record(time_ms)
        
        # Log to console with Intel branding
        logger.info(f"[PERF] {component_name}: {time_ms:.2f}ms")
        
        # Optionally log to MongoDB
        cls._log_to_mongo(component_name, time_ms, metadata)
    
    @classmethod
    def _log_to_mongo(cls, component_name: str, time_ms: float, metadata: Optional[Dict] = None):
        """Log latency to MongoDB intel_perf_logs collection."""
        try:
            if cls._mongo_db is None:
                from app.db.mongo import get_database
                cls._mongo_db = get_database()
            
            if cls._mongo_db is not None:
                log_entry = {
                    "component": component_name,
                    "latency_ms": time_ms,
                    "timestamp": datetime.utcnow(),
                    "metadata": metadata or {}
                }
                cls._mongo_db.intel_perf_logs.insert_one(log_entry)
        except Exception as e:
            # Don't fail on logging errors
            logger.debug(f"MongoDB perf logging failed: {e}")
    
    @classmethod
    def get_avg_latencies(cls) -> Dict[str, float]:
        """Get average latencies for Intel status endpoint."""
        return {
            name: round(metrics.avg_time_ms, 2)
            for name, metrics in cls._metrics.items()
        }


def measure_latency(component_name: str):
    """
    Decorator to measure execution latency of Intel-optimized components.
    
    Intel-optimized: Tracks performance for OPEA-style pipeline evaluation.
    
    Usage:
        @measure_latency("ocr_openvino")
        def extract_text(image):
            ...
    
    Args:
        component_name: Name of the component (e.g., "ocr_openvino", "rag_query")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000
                PerformanceLogger.record_latency(
                    component_name, 
                    elapsed_ms,
                    {"function": func.__name__}
                )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000
                PerformanceLogger.record_latency(
                    component_name, 
                    elapsed_ms,
                    {"function": func.__name__}
                )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


class LatencyContext:
    """
    Context manager for measuring latency of code blocks.
    
    Usage:
        with LatencyContext("rag_retrieval"):
            chunks = retrieval_service.query(...)
    """
    
    def __init__(self, component_name: str, metadata: Optional[Dict] = None):
        self.component_name = component_name
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        elapsed_ms = (end_time - self.start_time) * 1000
        PerformanceLogger.record_latency(self.component_name, elapsed_ms, self.metadata)
        return False


# Singleton instance
performance_logger = PerformanceLogger()
