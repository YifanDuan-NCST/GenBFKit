"""Custom Algorithm Deployment Module - 自定义算法部署模块。

基于 ONNX Runtime 实现标准化模型部署，支持：
- ONNX 模型加载与推理
- 模型注册与生命周期管理
- 自动特征组装（数据字典映射）
- 端到端推理流水线
"""

from .onnx_engine import ONNXEngine
from .model_registry import ModelRegistry, ModelMetadata
from .feature_assembler import FeatureAssembler, FeatureSpec
from .inference_pipeline import InferencePipeline, InferenceResult

__all__ = [
    "ONNXEngine",
    "ModelRegistry",
    "ModelMetadata",
    "FeatureAssembler",
    "FeatureSpec",
    "InferencePipeline",
    "InferenceResult",
]