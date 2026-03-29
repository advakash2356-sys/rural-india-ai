"""
Quantized Model Manager - Manages lifecycle of quantized Indic SLMs on edge nodes.
Handles model loading, unloading, and inference with memory constraints.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QuantizedModelManager:
    """
    Manages quantized Small Language Models for edge inference.
    
    Supports:
    - Loading GGUF format quantized models
    - Memory-efficient model swapping
    - Local inference without cloud
    - Model versioning and updates
    """
    
    def __init__(self, models_dir: Path, max_memory_mb: int = 2048):
        """
        Initialize model manager.
        
        Args:
            models_dir: Directory containing quantized model files
            max_memory_mb: Maximum memory for loaded models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_mb = max_memory_mb
        self.loaded_models = {}
        self.model_metadata = {}
        
        logger.info(f"QuantizedModelManager initialized, models_dir: {models_dir}, "
                   f"max_memory: {max_memory_mb}MB")
    
    async def load_default_models(self) -> List[str]:
        """
        Load default Indic SLMs for the edge node.
        
        Returns:
            List of loaded model IDs
        """
        default_models = [
            "sarvam-2b-indic-quantized-gguf",
            "llama-3-8b-indic-quantized-q4",
            "mobilebert-indic-lightweight"
        ]
        
        loaded = []
        for model_id in default_models:
            success = await self.load_model(model_id)
            if success:
                loaded.append(model_id)
                logger.info(f"Loaded default model: {model_id}")
        
        return loaded
    
    async def load_model(self, model_id: str) -> bool:
        """
        Load a quantized model from disk.
        
        Args:
            model_id: Identifier for the model
            
        Returns:
            True if successful
        """
        try:
            model_path = self.models_dir / f"{model_id}.gguf"
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            # Check memory constraints
            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            if sum(m.get('size_mb', 0) for m in self.loaded_models.values()) + file_size_mb > self.max_memory_mb:
                logger.warning(f"Insufficient memory to load {model_id} ({file_size_mb:.1f}MB)")
                return False
            
            # Simulate model loading (in production, use llama-cpp-python or similar)
            self.loaded_models[model_id] = {
                "path": str(model_path),
                "size_mb": file_size_mb,
                "loaded_at": datetime.utcnow().isoformat(),
                "inference_count": 0,
                "avg_latency_ms": 0
            }
            
            logger.info(f"Model loaded: {model_id} ({file_size_mb:.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model to free memory."""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            logger.info(f"Model unloaded: {model_id}")
            return True
        return False
    
    async def infer(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run inference on a quantized model.
        
        Args:
            query: Input query
            context: Optional context data
            
        Returns:
            Inference result
        """
        try:
            # Select best model (in production, route to specialized agents)
            model_id = "sarvam-2b-indic-quantized-gguf"
            
            if model_id not in self.loaded_models:
                return {"error": f"Model {model_id} not loaded"}
            
            # Simulate inference
            # In production: use llama-cpp-python or similar
            result = {
                "model_id": model_id,
                "query": query,
                "response": f"[Inference result for: {query}]",
                "tokens_used": len(query.split()),
                "inference_time_ms": 125,
                "confidence": 0.87,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update model statistics
            self.loaded_models[model_id]["inference_count"] += 1
            
            logger.info(f"Inference complete: {model_id}")
            return result
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {"error": str(e)}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        total_mb = sum(m.get('size_mb', 0) for m in self.loaded_models.values())
        return {
            "used_mb": total_mb,
            "max_mb": self.max_memory_mb,
            "percent_used": (total_mb / self.max_memory_mb * 100) if self.max_memory_mb > 0 else 0,
            "loaded_models": list(self.loaded_models.keys())
        }
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model."""
        return self.loaded_models.get(model_id)
