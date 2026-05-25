"""
全链路闭环引擎

实现"数据治理→智能分析→模型推理→工艺决策→效果反馈"的全链路闭环。

核心流程:
1. Data Governance (数据接入与标准化)
2. Intelligent Analysis (简易分析/查询检索)
3. Model Inference (ONNX 模型推理)
4. Decision Command (LLM 工艺决策)
5. Feedback Loop (效果反馈与知识更新)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from .data_bus import DataBus, DataMessage, MessageType
from .digital_twin_adapter import DigitalTwinAdapter, TwinDataFrame
from .llm_adapter import LLMAdapter, LLMContext, LLMResponse

logger = logging.getLogger(__name__)


class LoopPhase(Enum):
    """闭环阶段枚举。"""
    DATA_INGESTION = "data_ingestion"           # 数据接入
    DATA_GOVERNANCE = "data_governance"         # 数据治理
    INTELLIGENT_ANALYSIS = "intelligent_analysis"  # 智能分析
    MODEL_INFERENCE = "model_inference"         # 模型推理
    DECISION_MAKING = "decision_making"         # 工艺决策
    FEEDBACK = "feedback"                       # 效果反馈
    COMPLETED = "completed"                     # 完成


@dataclass
class LoopContext:
    """闭环执行上下文。"""
    loop_id: str = ""
    current_phase: LoopPhase = LoopPhase.DATA_INGESTION
    input_data: Optional[pd.DataFrame] = None
    analysis_result: Dict[str, Any] = field(default_factory=dict)
    model_result: Dict[str, Any] = field(default_factory=dict)
    decision_result: Dict[str, Any] = field(default_factory=dict)
    feedback_result: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time


class ClosedLoopEngine:
    """
    全链路闭环引擎。

    编排"数据治理→智能分析→模型推理→工艺决策→效果反馈"
    的全链路闭环流程。

    Usage:
        engine = ClosedLoopEngine(data_bus, llm_adapter)
        context = engine.execute(df)
        print(context.decision_result)
    """

    def __init__(
        self,
        data_bus: Optional[DataBus] = None,
        llm_adapter: Optional[LLMAdapter] = None,
        twin_adapter: Optional[DigitalTwinAdapter] = None,
        auto_feedback: bool = True,
    ):
        self._data_bus = data_bus or DataBus()
        self._llm = llm_adapter or LLMAdapter(use_mock=True)
        self._twin = twin_adapter or DigitalTwinAdapter(use_mock=True)
        self._auto_feedback = auto_feedback

        # 阶段处理器注册表
        self._phase_handlers: Dict[LoopPhase, Callable] = {
            LoopPhase.DATA_INGESTION: self._handle_data_ingestion,
            LoopPhase.DATA_GOVERNANCE: self._handle_data_governance,
            LoopPhase.INTELLIGENT_ANALYSIS: self._handle_intelligent_analysis,
            LoopPhase.MODEL_INFERENCE: self._handle_model_inference,
            LoopPhase.DECISION_MAKING: self._handle_decision_making,
            LoopPhase.FEEDBACK: self._handle_feedback,
        }

        # 外部可定制的处理钩子
        self.custom_handlers: Dict[LoopPhase, Optional[Callable]] = {
            phase: None for phase in LoopPhase
        }

        self._loop_history: List[LoopContext] = []

    def register_handler(self, phase: LoopPhase, handler: Callable) -> None:
        """注册自定义阶段处理器。"""
        self.custom_handlers[phase] = handler

    def execute(
        self,
        input_data: pd.DataFrame,
        loop_id: str = "",
    ) -> LoopContext:
        """
        执行全链路闭环。

        Args:
            input_data: 输入数据
            loop_id: 闭环 ID

        Returns:
            执行上下文（包含各阶段结果）
        """
        import uuid
        loop_id = loop_id or str(uuid.uuid4())

        context = LoopContext(
            loop_id=loop_id,
            input_data=input_data,
        )

        logger.info(f"[CLOSED-LOOP] Starting loop {loop_id}")

        # 按顺序执行各阶段
        phases = [
            LoopPhase.DATA_INGESTION,
            LoopPhase.DATA_GOVERNANCE,
            LoopPhase.INTELLIGENT_ANALYSIS,
            LoopPhase.MODEL_INFERENCE,
            LoopPhase.DECISION_MAKING,
            LoopPhase.FEEDBACK,
        ]

        for phase in phases:
            context.current_phase = phase
            handler = self.custom_handlers.get(phase) or self._phase_handlers.get(phase)

            if handler is None:
                logger.warning(f"No handler for phase {phase}, skipping...")
                continue

            try:
                logger.info(f"[CLOSED-LOOP] Executing phase: {phase.value}")
                handler(context)
            except Exception as e:
                error_msg = f"Phase '{phase.value}' failed: {e}"
                logger.error(f"[CLOSED-LOOP] {error_msg}", exc_info=True)
                context.errors.append(error_msg)
                # 继续后续阶段（尽可能完成闭环）
                continue

        context.current_phase = LoopPhase.COMPLETED

        # 发布闭环完成事件
        self._data_bus.publish(
            DataMessage(
                message_type=MessageType.SYSTEM_EVENT,
                channel="closed_loop",
                payload={
                    "loop_id": loop_id,
                    "status": "completed" if not context.errors else "completed_with_errors",
                    "elapsed_seconds": round(context.elapsed_seconds, 2),
                    "phase_results": {
                        "analysis": bool(context.analysis_result),
                        "model": bool(context.model_result),
                        "decision": bool(context.decision_result),
                        "feedback": bool(context.feedback_result),
                    },
                },
            )
        )

        self._loop_history.append(context)
        logger.info(
            f"[CLOSED-LOOP] Loop {loop_id} completed in "
            f"{context.elapsed_seconds:.1f}s "
            f"({len(context.errors)} errors)"
        )

        return context

    def get_history(self, limit: int = 10) -> List[LoopContext]:
        """获取闭环历史。"""
        return self._loop_history[-limit:]

    # ────── 各阶段默认处理器 ──────

    def _handle_data_ingestion(self, ctx: LoopContext) -> None:
        """阶段1: 数据接入。"""
        df = ctx.input_data
        if df is None or df.empty:
            raise ValueError("No input data provided")

        # 发布数据接入事件
        self._data_bus.publish(
            DataMessage(
                message_type=MessageType.DATA_PUSH,
                channel="data_ingestion",
                payload={
                    "rows": len(df),
                    "columns": list(df.columns),
                    "dtypes": {c: str(df[c].dtype) for c in df.columns},
                },
            )
        )
        logger.info(f"[INGESTION] Received {len(df)} rows x {len(df.columns)} columns")

    def _handle_data_governance(self, ctx: LoopContext) -> None:
        """阶段2: 数据治理（预处理摘要）。"""
        df = ctx.input_data
        summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_rates": {c: float(df[c].isna().mean()) for c in df.columns},
            "numeric_columns": list(df.select_dtypes(include=["number"]).columns),
        }
        ctx.analysis_result["governance"] = summary
        logger.info(f"[GOVERNANCE] Missing rate max: {max(summary['missing_rates'].values()):.2%}")

    def _handle_intelligent_analysis(self, ctx: LoopContext) -> None:
        """阶段3: 智能分析。"""
        df = ctx.input_data
        numeric_df = df.select_dtypes(include=["number"])

        if not numeric_df.empty:
            stats = {
                "mean": numeric_df.mean().to_dict(),
                "std": numeric_df.std().to_dict(),
                "min": numeric_df.min().to_dict(),
                "max": numeric_df.max().to_dict(),
                "correlation": numeric_df.corr().to_dict() if numeric_df.shape[1] < 20 else {},
            }
            ctx.analysis_result["statistics"] = stats

        logger.info(f"[ANALYSIS] Analyzed {len(numeric_df.columns)} numeric columns")

    def _handle_model_inference(self, ctx: LoopContext) -> None:
        """阶段4: 模型推理。"""
        # 由外部注册的模型推理处理器完成
        # 此处仅记录占位
        logger.info("[MODEL] No ONNX model registered for this loop phase")

    def _handle_decision_making(self, ctx: LoopContext) -> None:
        """阶段5: 工艺决策。"""
        df = ctx.input_data
        # 构造查询上下文
        query = "Analyze current blast furnace operating condition and provide optimization strategy."

        llm_context = LLMContext(
            query=query,
            parameters={
                "data_shape": list(df.shape),
                "data_columns": list(df.columns),
            },
        )

        response = self._llm.query_strategy(llm_context)
        ctx.decision_result = response.to_dict()

        # 通过数据总线发布决策
        self._data_bus.publish(
            DataMessage(
                message_type=MessageType.DECISION_COMMAND,
                channel="decisions",
                payload=response.to_dict(),
            )
        )

        logger.info(f"[DECISION] LLM decision: {response.to_dict()}")

    def _handle_feedback(self, ctx: LoopContext) -> None:
        """阶段6: 效果反馈。"""
        # 推送至数字孪生平台（效果评估）
        if self._auto_feedback:
            twin_frame = TwinDataFrame(
                frame_id=f"loop_{ctx.loop_id}",
                data={
                    "loop_id": ctx.loop_id,
                    "analysis": ctx.analysis_result,
                    "decision": ctx.decision_result,
                    "elapsed_seconds": ctx.elapsed_seconds,
                },
            )
            result = self._twin.push_measurements(twin_frame)
            ctx.feedback_result = result
            logger.info(f"[FEEDBACK] Pushed to twin platform: {result}")

        # 发布反馈事件
        self._data_bus.publish(
            DataMessage(
                message_type=MessageType.STATUS_UPDATE,
                channel="feedback",
                payload={"loop_id": ctx.loop_id, "status": "feedback_completed"},
            )
        )