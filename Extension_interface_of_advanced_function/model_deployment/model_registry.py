"""
模型注册表

管理已部署模型的全生命周期，包括：
- 注册/注销 ONNX 模型
- 模型版本管理
- 元数据管理
- 模型查询与发现
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .onnx_engine import ONNXEngine, ONNXModelInfo

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """模型部署元数据。"""
    model_id: str
    model_name: str
    version: str = "1.0.0"
    description: str = ""
    task_type: str = "regression"
    input_description: str = ""
    output_description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    onnx_info: Optional[ONNXModelInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "description": self.description,
            "task_type": self.task_type,
            "input_description": self.input_description,
            "output_description": self.output_description,
            "tags": self.tags,
            "created_at": self.created_at,
            "onnx_info": self.onnx_info.to_dict() if self.onnx_info else None,
        }


class ModelRegistry:
    """
    模型注册表。

    管理 ONNX 模型的注册、发现与生命周期。
    支持按任务类型、标签等维度查询模型。

    Usage:
        registry = ModelRegistry()
        registry.register("temperature_model", "models/temp_pred.onnx",
                          task_type="regression", tags={"domain": "blast_furnace"})
        engine = registry.get_engine("temperature_model")
        result = engine.infer({"input": data})
    """

    def __init__(self, models_dir: str | Path = "./models"):
        self._models_dir = Path(models_dir)
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._registry: Dict[str, ModelMetadata] = {}
        self._engines: Dict[str, ONNXEngine] = {}

    def register(
        self,
        model_id: str,
        model_path: str | Path,
        version: str = "1.0.0",
        description: str = "",
        task_type: str = "regression",
        input_description: str = "",
        output_description: str = "",
        tags: Optional[Dict[str, str]] = None,
        auto_load: bool = False,
    ) -> ModelMetadata:
        """
        注册一个 ONNX 模型。

        Args:
            model_id: 唯一模型 ID
            model_path: ONNX 文件路径
            version: 版本号
            description: 模型描述
            task_type: 任务类型 (regression, classification, forecasting 等)
            input_description: 输入描述
            output_description: 输出描述
            tags: 自定义标签
            auto_load: 是否立即加载模型

        Returns:
            注册的模型元数据
        """
        resolved_path = self._resolve_path(model_path)

        if not Path(resolved_path).exists():
            raise FileNotFoundError(f"Model file not found: {resolved_path}")

        if model_id in self._registry:
            logger.warning(f"Model '{model_id}' already registered, overwriting...")

        metadata = ModelMetadata(
            model_id=model_id,
            model_name=Path(resolved_path).stem,
            version=version,
            description=description,
            task_type=task_type,
            input_description=input_description,
            output_description=output_description,
            tags=tags or {},
        )

        self._registry[model_id] = metadata

        if auto_load:
            self.load(model_id, resolved_path)

        logger.info(f"Registered model '{model_id}' (v{version}) from {resolved_path}")
        return metadata

    def load(self, model_id: str, model_path: Optional[str | Path] = None) -> ONNXEngine:
        """
        加载已注册的模型为 ONNXEngine。

        Args:
            model_id: 已注册的模型 ID
            model_path: 可选，覆盖模型文件路径

        Returns:
            ONNXEngine 实例（已加载）
        """
        if model_id not in self._registry:
            raise KeyError(f"Model '{model_id}' not registered. Call register() first.")

        if model_path is None:
            # 尝试从元数据中获取路径
            metadata = self._registry[model_id]
            if metadata.onnx_info and metadata.onnx_info.model_path:
                model_path = metadata.onnx_info.model_path
            else:
                # 在 models_dir 中查找
                candidate = self._models_dir / f"{model_id}.onnx"
                if candidate.exists():
                    model_path = candidate
                else:
                    raise FileNotFoundError(
                        f"No model path found for '{model_id}' and no .onnx file in {self._models_dir}"
                    )

        engine = ONNXEngine(model_path)
        info = engine.load()

        # 更新元数据中的 ONNX 信息
        self._registry[model_id].onnx_info = info
        self._engines[model_id] = engine

        return engine

    def get_engine(self, model_id: str) -> ONNXEngine:
        """
        获取已加载的模型引擎。

        Args:
            model_id: 模型 ID

        Returns:
            ONNXEngine 实例

        Raises:
            KeyError: 模型未注册或未加载
        """
        if model_id not in self._engines:
            if model_id in self._registry:
                # 自动加载
                return self.load(model_id)
            raise KeyError(f"Model '{model_id}' not loaded. Call load() first.")
        return self._engines[model_id]

    def get_metadata(self, model_id: str) -> ModelMetadata:
        """获取模型元数据。"""
        if model_id not in self._registry:
            raise KeyError(f"Model '{model_id}' not registered.")
        return self._registry[model_id]

    def unregister(self, model_id: str) -> bool:
        """注销模型并释放资源。"""
        if model_id in self._engines:
            self._engines[model_id].unload()
            del self._engines[model_id]
        if model_id in self._registry:
            del self._registry[model_id]
            logger.info(f"Unregistered model '{model_id}'")
            return True
        return False

    def list_models(self, task_type: Optional[str] = None) -> List[ModelMetadata]:
        """
        列出所有注册的模型。

        Args:
            task_type: 按任务类型过滤

        Returns:
            模型元数据列表
        """
        models = list(self._registry.values())
        if task_type:
            models = [m for m in models if m.task_type == task_type]
        return sorted(models, key=lambda m: m.created_at)

    def find_by_tag(self, key: str, value: str) -> List[ModelMetadata]:
        """按标签查找模型。"""
        return [m for m in self._registry.values() if m.tags.get(key) == value]

    def export_registry(self, json_path: str | Path) -> None:
        """将注册表导出为 JSON。"""
        data = {
            "models": {mid: meta.to_dict() for mid, meta in self._registry.items()},
            "models_dir": str(self._models_dir),
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Registry exported to {json_path}")

    def _resolve_path(self, path: str | Path) -> str:
        """解析模型路径（支持相对路径）。"""
        p = Path(path)
        if p.exists():
            return str(p)
        # 尝试在 models_dir 下查找
        candidate = self._models_dir / p.name
        if candidate.exists():
            return str(candidate)
        return str(p)