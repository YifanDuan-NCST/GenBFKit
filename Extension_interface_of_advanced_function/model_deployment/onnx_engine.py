"""
ONNX 推理引擎

基于 ONNX Runtime 实现高效的模型推理，支持：
- CPU/CUDA 执行提供程序
- 动态输入形状
- 批量推理
- 输入输出元数据解析
- 模型量化 (INT8/FP16) 支持
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ONNXModelInfo:
    """ONNX 模型的元数据信息。"""
    model_path: str
    model_name: str
    input_names: List[str]
    input_shapes: List[Tuple[Optional[int], ...]]
    input_types: List[str]
    output_names: List[str]
    output_shapes: List[Tuple[Optional[int], ...]]
    output_types: List[str]
    model_size_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "inputs": [
                {"name": n, "shape": list(s), "dtype": t}
                for n, s, t in zip(self.input_names, self.input_shapes, self.input_types)
            ],
            "outputs": [
                {"name": n, "shape": list(s), "dtype": t}
                for n, s, t in zip(self.output_names, self.output_shapes, self.output_types)
            ],
            "model_size_mb": round(self.model_size_mb, 2),
        }


class ONNXEngine:
    """
    ONNX 推理引擎封装。

    特性：
    - 惰性加载 (lazy loading)
    - 自动设备选择 (CPU/GPU)
    - 会话级配置
    - 推理性能统计

    Usage:
        engine = ONNXEngine("model.onnx")
        engine.load()
        result = engine.infer({"input": np.array(...)})
    """

    def __init__(
        self,
        model_path: str | Path,
        providers: Optional[List[str]] = None,
        intra_op_num_threads: int = 4,
        enable_profiling: bool = False,
    ):
        """
        Args:
            model_path: ONNX 模型文件路径
            providers: ONNX Runtime 执行提供程序列表
            intra_op_num_threads: 内部操作线程数
            enable_profiling: 是否启用性能分析
        """
        self.model_path = str(model_path)
        self._providers = providers or self._default_providers()
        self._options = {
            "intra_op_num_threads": intra_op_num_threads,
            "enable_profiling": enable_profiling,
        }
        self._session = None
        self._model_info: Optional[ONNXModelInfo] = None
        self._inference_times: List[float] = []

    @staticmethod
    def _default_providers() -> List[str]:
        """获取默认执行提供程序（按优先级）。"""
        try:
            import onnxruntime as ort
            available = ort.get_available_providers()
            # 优先 CUDA
            preferred = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            return [p for p in preferred if p in available] or available
        except ImportError:
            return ["CPUExecutionProvider"]

    def load(self) -> ONNXModelInfo:
        """加载 ONNX 模型并解析元数据。"""
        import onnxruntime as ort

        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"ONNX model not found: {self.model_path}")

        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = self._options["intra_op_num_threads"]
        session_options.enable_profiling = self._options["enable_profiling"]
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self._session = ort.InferenceSession(
            self.model_path,
            sess_options=session_options,
            providers=self._providers,
        )

        # 解析元数据
        inputs = self._session.get_inputs()
        outputs = self._session.get_outputs()

        self._model_info = ONNXModelInfo(
            model_path=self.model_path,
            model_name=Path(self.model_path).stem,
            input_names=[inp.name for inp in inputs],
            input_shapes=[list(inp.shape) if inp.shape else [] for inp in inputs],
            input_types=[inp.type for inp in inputs],
            output_names=[out.name for out in outputs],
            output_shapes=[list(out.shape) if out.shape else [] for out in outputs],
            output_types=[out.type for out in outputs],
            model_size_mb=Path(self.model_path).stat().st_size / (1024 * 1024),
        )

        logger.info(
            f"Loaded ONNX model: {self._model_info.model_name} "
            f"({self._model_info.model_size_mb:.1f} MB)"
        )

        return self._model_info

    @property
    def model_info(self) -> Optional[ONNXModelInfo]:
        return self._model_info

    @property
    def is_loaded(self) -> bool:
        return self._session is not None

    def infer(
        self,
        inputs: Dict[str, np.ndarray],
        output_names: Optional[List[str]] = None,
    ) -> Dict[str, np.ndarray]:
        """
        ONNX 模型推理。

        Args:
            inputs: {输入名: numpy 数组}
            output_names: 期望的输出名称列表，None 表示全部输出

        Returns:
            {输出名: numpy 数组}

        Raises:
            RuntimeError: 模型未加载
            ValueError: 输入不匹配
        """
        if self._session is None:
            raise RuntimeError("ONNX model not loaded. Call load() first.")

        # 输入验证
        for name, arr in inputs.items():
            if name not in self._model_info.input_names:
                raise ValueError(f"Unexpected input '{name}'. Expected: {self._model_info.input_names}")

        # 类型转换
        ort_inputs = {}
        for name, arr in inputs.items():
            if arr.dtype == np.float64:
                arr = arr.astype(np.float32)
            ort_inputs[name] = arr

        # 推理
        if output_names is None:
            output_names = self._model_info.output_names

        start = time.perf_counter()
        outputs = self._session.run(output_names, ort_inputs)
        elapsed = time.perf_counter() - start

        self._inference_times.append(elapsed)

        result = dict(zip(output_names, outputs))
        logger.debug(f"Inference completed in {elapsed * 1000:.1f} ms")

        return result

    def infer_batch(
        self,
        inputs: Dict[str, np.ndarray],
        batch_size: int = 32,
    ) -> Dict[str, np.ndarray]:
        """
        批量推理（自动分片）。

        Args:
            inputs: {输入名: numpy 数组}
            batch_size: 每批大小

        Returns:
            合并后的 {输出名: numpy 数组}
        """
        n_samples = list(inputs.values())[0].shape[0]
        all_outputs: Dict[str, List[np.ndarray]] = {}

        for start_idx in range(0, n_samples, batch_size):
            end_idx = min(start_idx + batch_size, n_samples)
            batch = {k: v[start_idx:end_idx] for k, v in inputs.items()}
            batch_result = self.infer(batch)

            for k, v in batch_result.items():
                if k not in all_outputs:
                    all_outputs[k] = []
                all_outputs[k].append(v)

        return {k: np.concatenate(v, axis=0) for k, v in all_outputs.items()}

    def get_avg_inference_time(self) -> float:
        """获取平均推理时间（毫秒）。"""
        if not self._inference_times:
            return 0.0
        return float(np.mean(self._inference_times) * 1000)

    def unload(self) -> None:
        """卸载模型，释放资源。"""
        self._session = None
        self._model_info = None
        self._inference_times.clear()
        logger.info(f"Unloaded model: {Path(self.model_path).name}")

    def __enter__(self):
        if not self.is_loaded:
            self.load()
        return self

    def __exit__(self, *args):
        self.unload()