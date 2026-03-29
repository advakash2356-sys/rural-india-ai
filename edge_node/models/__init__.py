"""Quantized model management for edge inference."""

from edge_node.models.manager import QuantizedModelManager
from edge_node.models.loader import ModelLoader

__all__ = ["QuantizedModelManager", "ModelLoader"]
