"""
推理流水线

端到端的模型推理流水线，整合：
1. 数据接入与格式校验
2. 时序对齐（可选）
3. 特征组装
4. ONNX 模型推理
5. 结果后处理与反向映射
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..core.data_dictionary import DataDictionary
from .onnx_engine import ONNXEngine
from .feature_assembler import FeatureAssembler, FeatureSpec

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """推理结果封装。"""
    predictions: Dict[str, np.ndarray]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "metadata": self.metadata,
        }
        if self.success:
            result["predictions"] = {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in self.predictions.items()
            }
        else:
            result["error_message"] = self.error_message
        return result

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"InferenceResult({status} | "
            f"{self.processing_time_ms:.1f}ms | "
            f"outputs={list(self.predictions.keys()) if self.predictions else 'none'})"
        )


class InferencePipeline:
    """
    端到端推理流水线。

    整合数据接入、特征组装、模型推理与结果输出为一体，
    自动完成数据字典到模型输入的映射。

    Usage:
        pipeline = InferencePipeline(data_dict)
        pipeline.configure(
            engine=onnx_engine,
            features=[FeatureSpec(...), ...],
        )
        result = pipeline.run(raw_data_df)
    """

    def __init__(
        self,
        data_dictionary: Optional[DataDictionary] = None,
    ):
        self._dictionary = data_dictionary
        self._engine: Optional[ONNXEngine] = None
        self._assembler = FeatureAssembler(data_dictionary)
        self._column_mapping: Dict[str, str] = {}
        self._output_mapping: Dict[str, str] = {}  # ONNX输出 -> 业务含义
        self._pipeline_name: str = "default"

    def configure(
        self,
        engine: ONNXEngine,
        features: Optional[List[FeatureSpec]] = None,
        column_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        pipeline_name: str = "default",
    ) -> None:
        """
        配置推理流水线。

        Args:
            engine: 已加载的 ONNX 引擎
            features: 特征规格列表
            column_mapping: 输入列名映射 {特征名: 数据列名}
            output_mapping: 输出映射 {ONNX输出名: 业务名称}
            pipeline_name: 流水线名称
        """
        self._engine = engine
        self._pipeline_name = pipeline_name

        if features:
            self._assembler.declare_features(features)

        if column_mapping:
            self._column_mapping.update(column_mapping)

        if output_mapping:
            self._output_mapping.update(output_mapping)
        elif engine.model_info:
            # 自动从 ONNX 输出名生成映射
            self._output_mapping = {
                name: name for name in engine.model_info.output_names
            }

        if engine.model_info:
            logger.info(
                f"Pipeline '{pipeline_name}' configured: "
                f"{len(features) if features else 0} features -> "
                f"{len(engine.model_info.output_names)} outputs"
            )

    def run(
        self,
        data: pd.DataFrame,
        fit_normalizer: bool = False,
    ) -> InferenceResult:
        """
        执行推理流水线。

        Args:
            data: 输入数据 DataFrame
            fit_normalizer: 是否重新拟合归一化参数

        Returns:
            推理结果
        """
        start = time.perf_counter()

        if self._engine is None:
            return InferenceResult(
                predictions={},
                success=False,
                error_message="ONNX engine not configured. Call configure() first.",
                processing_time_ms=0.0,
            )

        try:
            # Step 1: 特征组装
            assembled = self._assembler.assemble(
                data, column_mapping=self._column_mapping, fit_normalizer=fit_normalizer
            )

            # Step 2: 模型推理
            raw_outputs = self._engine.infer(assembled)

            # Step 3: 输出映射
            predictions = {}
            for onnx_name, biz_name in self._output_mapping.items():
                if onnx_name in raw_outputs:
                    predictions[biz_name] = raw_outputs[onnx_name]

            elapsed = (time.perf_counter() - start) * 1000

            return InferenceResult(
                predictions=predictions,
                metadata={
                    "pipeline": self._pipeline_name,
                    "model": self._engine.model_info.model_name if self._engine.model_info else "unknown",
                    "input_rows": len(data),
                    "outputs": list(predictions.keys()),
                },
                processing_time_ms=elapsed,
                success=True,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"Pipeline inference failed: {e}", exc_info=True)
            return InferenceResult(
                predictions={},
                success=False,
                error_message=str(e),
                processing_time_ms=elapsed,
            )

    def run_batch(
        self,
        data: pd.DataFrame,
        batch_size: int = 256,
        fit_normalizer: bool = False,
    ) -> InferenceResult:
        """批量推理。"""
        start = time.perf_counter()

        if self._engine is None:
            return InferenceResult(
                predictions={},
                success=False,
                error_message="ONNX engine not configured.",
                processing_time_ms=0.0,
            )

        try:
            assembled = self._assembler.assemble(
                data, column_mapping=self._column_mapping, fit_normalizer=fit_normalizer
            )

            raw_outputs = self._engine.infer_batch(assembled, batch_size=batch_size)

            predictions = {}
            for onnx_name, biz_name in self._output_mapping.items():
                if onnx_name in raw_outputs:
                    predictions[biz_name] = raw_outputs[onnx_name]

            elapsed = (time.perf_counter() - start) * 1000

            return InferenceResult(
                predictions=predictions,
                metadata={
                    "pipeline": self._pipeline_name,
                    "model": self._engine.model_info.model_name if self._engine.model_info else "unknown",
                    "input_rows": len(data),
                    "batch_size": batch_size,
                    "outputs": list(predictions.keys()),
                },
                processing_time_ms=elapsed,
                success=True,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return InferenceResult(
                predictions={},
                success=False,
                error_message=str(e),
                processing_time_ms=elapsed,
            )