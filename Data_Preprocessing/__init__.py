"""
GenBFKit Data Preprocessing Module
===================================

A comprehensive, modular data preprocessing framework for time-series sensor data.
Provides advanced algorithms for missing value imputation, outlier detection, and data normalization.

Author: GenBFKit Team
Version: 1.0.0

使用说明:
1. 作为独立包使用: pip install -e .
2. 作为项目模块使用: from Data_Preprocessing import ...
3. 直接添加路径: sys.path.append('Data_Preprocessing')
"""

import sys
import os

# 获取当前模块的路径
_current_module_path = os.path.dirname(__file__)

# 将 Data_Preprocessing 目录添加到 sys.path（如果还未添加）
if _current_module_path not in sys.path:
    sys.path.insert(0, _current_module_path)

# 现在可以使用绝对导入了
from Data_Preprocessing.preprocessing_pipeline import PreprocessingPipeline
from Data_Preprocessing.missing_value import MissingValueHandler
from Data_Preprocessing.outlier_detection import OutlierDetector
from Data_Preprocessing.data_normalization import DataNormalizer
from Data_Preprocessing.database import DatabaseManager
from Data_Preprocessing.config import (
    PreprocessingConfig,
    MissingValueConfig,
    OutlierDetectionConfig,
    NormalizationConfig,
    DatabaseConfig
)

__version__ = "1.0.0"
__all__ = [
    "PreprocessingPipeline",
    "MissingValueHandler",
    "OutlierDetector",
    "DataNormalizer",
    "DatabaseManager",
    "PreprocessingConfig",
    "MissingValueConfig",
    "OutlierDetectionConfig",
    "NormalizationConfig",
    "DatabaseConfig",
]
