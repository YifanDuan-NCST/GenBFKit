"""
GenBFKit - Extension Interface of Advanced Function
高阶功能扩展接口模块

基于松耦合模块化架构，为 GenBFKit 提供以下扩展能力：

1. 自定义算法部署 (model_deployment)
   - ONNX Runtime 推理引擎
   - 模型注册与生命周期管理
   - 特征组装与数据字典映射
   - 端到端推理流水线

2. 上层系统对接 (system_integration)
   - 数据总线（发布-订阅）
   - 数字孪生平台适配器
   - 领域大模型适配器
   - 全链路闭环引擎

3. 底层数据架构拓展 (data_extension)
   - Schema 验证与管理
   - 字典层级 CRUD
   - 外部数据自动映射

Usage:
    from extension_interface import (
        DataDictionary,
        ONNXEngine, ModelRegistry,
        DataBus, DigitalTwinAdapter, LLMAdapter, ClosedLoopEngine,
        DictionaryCRUD, SchemaManager, DataMapper
    )
"""

from .core import (
    DataDictionary,
    WorkType,
    DataCategory,
    DataPool,
    Dataset,
    DataAttribute,
    DataPoolType,
    ChainQueryResult,
    ExtensionConfig,
    STANDARD_DATA_POOLS,
    POOL_BASE_ATTRIBUTES,
    PREBUILT_SUMMARY,
)

from .model_deployment import (
    ONNXEngine,
    ModelRegistry,
    ModelMetadata,
    FeatureAssembler,
    FeatureSpec,
    InferencePipeline,
    InferenceResult,
)

from .system_integration import (
    DataBus,
    DataMessage,
    MessageType,
    DigitalTwinAdapter,
    TwinDataFrame,
    LLMAdapter,
    LLMContext,
    LLMResponse,
    ClosedLoopEngine,
    LoopPhase,
)

from .data_extension import (
    SchemaManager,
    SchemaValidationResult,
    DictionaryCRUD,
    DataMapper,
    MappingRule,
)

__version__ = "1.0.0"

__all__ = [
    # Core
    "DataDictionary",
    "WorkType",
    "DataCategory",
    "DataPool",
    "Dataset",
    "DataAttribute",
    "DataPoolType",
    "ChainQueryResult",
    "ExtensionConfig",
    "STANDARD_DATA_POOLS",
    "POOL_BASE_ATTRIBUTES",
    "PREBUILT_SUMMARY",
    # Model Deployment
    "ONNXEngine",
    "ModelRegistry",
    "ModelMetadata",
    "FeatureAssembler",
    "FeatureSpec",
    "InferencePipeline",
    "InferenceResult",
    # System Integration
    "DataBus",
    "DataMessage",
    "MessageType",
    "DigitalTwinAdapter",
    "TwinDataFrame",
    "LLMAdapter",
    "LLMContext",
    "LLMResponse",
    "ClosedLoopEngine",
    "LoopPhase",
    # Data Extension
    "SchemaManager",
    "SchemaValidationResult",
    "DictionaryCRUD",
    "DataMapper",
    "MappingRule",
]