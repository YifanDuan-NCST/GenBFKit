"""
特征组装器

基于数据字典自动完成模型输入特征组装：
1. 解析模型输入规格
2. 从数据字典匹配对应参数
3. 自动完成数据链路对接、格式校验与特征组装
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.data_dictionary import DataDictionary

logger = logging.getLogger(__name__)


@dataclass
class FeatureSpec:
    """
    特征规格定义。

    描述模型期望的输入特征及其与数据字典的映射关系。
    """
    name: str
    dtype: str = "float32"
    shape: Tuple[Optional[int], ...] = (-1,)
    dictionary_mapping: str = ""  # 数据字典中的参数名
    pool_type: str = ""           # 对应的数据池类型
    normalizer: str = ""          # 归一化方法 (zscore, minmax, robust, none)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "shape": list(self.shape),
            "dictionary_mapping": self.dictionary_mapping,
            "pool_type": self.pool_type,
            "normalizer": self.normalizer,
            "description": self.description,
        }


class FeatureAssembler:
    """
    特征组装器。

    根据数据字典和模型特征规格，自动完成从原始数据到模型输入特征的转换。

    Usage:
        assembler = FeatureAssembler(data_dict)
        assembler.declare_features([
            FeatureSpec(name="temperature", dictionary_mapping="Hot metal temperature",
                       pool_type="Continuous time-series data", normalizer="zscore"),
        ])
        features = assembler.assemble(raw_data_df)
    """

    def __init__(self, data_dictionary: Optional[DataDictionary] = None):
        self._dictionary = data_dictionary
        self._feature_specs: Dict[str, FeatureSpec] = {}
        self._normalizers: Dict[str, Dict[str, Any]] = {}

    def declare_features(self, specs: List[FeatureSpec]) -> None:
        """声明模型所需的特征规格。"""
        for spec in specs:
            self._feature_specs[spec.name] = spec

            # 如果指定了数据字典映射，验证参数是否存在
            if self._dictionary and spec.dictionary_mapping:
                results = self._dictionary.search_datasets(spec.dictionary_mapping)
                if not results:
                    logger.warning(
                        f"Feature '{spec.name}': no dictionary match for "
                        f"'{spec.dictionary_mapping}'"
                    )

    def add_feature(self, spec: FeatureSpec) -> None:
        """添加单个特征规格。"""
        self._feature_specs[spec.name] = spec

    @property
    def feature_names(self) -> List[str]:
        return list(self._feature_specs.keys())

    def assemble(
        self,
        data: pd.DataFrame,
        column_mapping: Optional[Dict[str, str]] = None,
        fit_normalizer: bool = False,
    ) -> Dict[str, np.ndarray]:
        """
        将原始 DataFrame 组装为模型输入。

        Args:
            data: 原始数据 DataFrame
            column_mapping: 列名映射 {特征名: DataFrame列名}
            fit_normalizer: 是否重新拟合归一化参数

        Returns:
            {输入名: numpy 数组}，适配 ONNX 模型
        """
        if not self._feature_specs:
            raise RuntimeError("No features declared. Call declare_features() first.")

        result = {}
        for name, spec in self._feature_specs.items():
            # 确定数据列
            col = name
            if column_mapping and name in column_mapping:
                col = column_mapping[name]
            elif spec.dictionary_mapping and spec.dictionary_mapping in data.columns:
                col = spec.dictionary_mapping

            if col not in data.columns:
                raise ValueError(
                    f"Column '{col}' (for feature '{name}') not found in data. "
                    f"Available columns: {list(data.columns)}"
                )

            # 提取并转换
            values = data[col].values.astype(np.float32)

            # 处理缺失值
            values = np.nan_to_num(values, nan=0.0)

            # 归一化
            if spec.normalizer and spec.normalizer != "none":
                values = self._normalize(
                    values, name, spec.normalizer, fit=fit_normalizer
                )

            # 形状调整
            if len(spec.shape) > 1:
                target_shape = tuple(
                    -1 if s is None or s == -1 else s
                    for s in spec.shape
                )
                # 自动 reshape
                expected_dims = len(spec.shape)
                if expected_dims == 2 and values.ndim == 1:
                    values = values.reshape(-1, 1)
                elif expected_dims == 3 and values.ndim == 1:
                    values = values.reshape(-1, 1, 1)

            result[name] = values

        return result

    def _normalize(
        self,
        values: np.ndarray,
        name: str,
        method: str,
        fit: bool = False,
    ) -> np.ndarray:
        """归一化处理。"""
        if fit or name not in self._normalizers:
            if method == "zscore":
                mean = float(np.mean(values))
                std = float(np.std(values)) or 1.0
                self._normalizers[name] = {"mean": mean, "std": std}
            elif method == "minmax":
                vmin = float(np.min(values))
                vmax = float(np.max(values))
                self._normalizers[name] = {"min": vmin, "max": vmax}
            elif method == "robust":
                q1 = float(np.percentile(values, 25))
                q3 = float(np.percentile(values, 75))
                self._normalizers[name] = {"q1": q1, "q3": q3}

        params = self._normalizers.get(name, {})
        if method == "zscore":
            return (values - params["mean"]) / params["std"]
        elif method == "minmax":
            range_val = params["max"] - params["min"] or 1.0
            return (values - params["min"]) / range_val
        elif method == "robust":
            iqr = params["q3"] - params["q1"] or 1.0
            return (values - params["q1"]) / iqr
        return values

    def get_input_spec(self) -> Dict[str, Dict[str, Any]]:
        """获取模型输入规格说明。"""
        return {
            name: spec.to_dict()
            for name, spec in self._feature_specs.items()
        }

    def summary(self) -> str:
        """返回特征规格摘要。"""
        lines = [f"FeatureAssembler ({len(self._feature_specs)} features):"]
        for name, spec in self._feature_specs.items():
            mapping = spec.dictionary_mapping or "(direct)"
            norm = spec.normalizer or "none"
            lines.append(f"  - {name} -> dict[{mapping}] | norm={norm}")
        return "\n".join(lines)