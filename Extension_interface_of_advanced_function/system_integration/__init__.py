"""Upper-level System Integration Module - 上层系统对接模块。

实现与外部系统的双向数据交互：
- 数字孪生平台数据推送
- 领域大模型集成
- 全链路闭环保活
"""

from .data_bus import DataBus, DataMessage, MessageType
from .digital_twin_adapter import DigitalTwinAdapter, TwinDataFrame
from .llm_adapter import LLMAdapter, LLMContext, LLMResponse
from .closed_loop import ClosedLoopEngine, LoopPhase

__all__ = [
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
]