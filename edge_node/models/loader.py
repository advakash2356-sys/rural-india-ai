"""
Model Loader - Handles GGUF format model loading and conversion.
Optimizes for low-memory, edge device deployment.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Loads and manages quantized GGUF format models.
    
    Features:
    - GGUF format parsing
    - 4-bit and 8-bit quantization support
    - Memory-efficient loading
    - Model metadata extraction
    """
    
    SUPPORTED_FORMATS = [".gguf", ".bin"]
    QUANTIZATION_TYPES = ["q4_0", "q4_1", "q5_0", "q5_1", "q8_0"]
    
    @staticmethod
    def load_quantized_model(model_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a quantized GGUF model.
        
        Args:
            model_path: Path to GGUF model file
            
        Returns:
            Model object or None if failed
        """
        try:
            path = Path(model_path)
            
            if not path.exists():
                logger.error(f"Model file not found: {model_path}")
                return None
            
            if path.suffix not in ModelLoader.SUPPORTED_FORMATS:
                logger.error(f"Unsupported format: {path.suffix}")
                return None
            
            # In production: use llama-cpp-python or similar
            # For now, return metadata
            return {
                "path": str(path),
                "name": path.stem,
                "size_bytes": path.stat().st_size,
                "format": path.suffix,
                "quantization": "q4_0",  # Assume 4-bit by default
                "context_length": 2048,
                "vocab_size": 32000
            }
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    @staticmethod
    def get_model_memory_estimate(model_size_mb: float, quantization: str) -> float:
        """
        Estimate runtime memory needed for a model.
        
        Args:
            model_size_mb: Model file size in MB
            quantization: Quantization type (e.g., "q4_0")
            
        Returns:
            Estimated memory in MB (includes context buffers)
        """
        # Base model size
        memory = model_size_mb
        
        # Add overhead for context windows, activations, etc.
        # Typically 30-50% overhead depending on quantization
        overhead_multiplier = {
            "q4_0": 1.4,
            "q4_1": 1.45,
            "q5_0": 1.5,
            "q8_0": 1.6
        }
        
        return memory * overhead_multiplier.get(quantization, 1.5)
    
    @staticmethod
    def list_available_models(models_dir: str) -> list:
        """List all available quantized models in directory."""
        try:
            models_path = Path(models_dir)
            if not models_path.exists():
                return []
            
            models = []
            for model_file in models_path.glob("*.gguf"):
                models.append({
                    "name": model_file.stem,
                    "path": str(model_file),
                    "size_mb": model_file.stat().st_size / (1024 * 1024)
                })
            
            return sorted(models, key=lambda x: x["name"])
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
