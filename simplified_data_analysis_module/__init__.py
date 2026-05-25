"""
GenBFKit 简易数据分析模块 🚀
Simplified Data Analysis Module for GenBFKit Framework

提供三大核心分析功能：
1. 📊 统计指标分析 - 5大指标秒懂数据特征
2. 🔗 相关性分析 - 看透参数间的"爱恨情仇"
3. 🎯 SHAP可解释性分析 - 让XGBoost模型"开口说话"

Author: GenBFKit Team
Date: 2026-04-22
Version: 1.0.0
"""

from .statistical_analysis import StatisticalAnalyzer
from .correlation_analysis import CorrelationAnalyzer
from .shap_analysis import SHAPAnalyzer
from .data_generator import MockDataGenerator

__version__ = "1.0.0"
__all__ = [
    'StatisticalAnalyzer',
    'CorrelationAnalyzer',
    'SHAPAnalyzer',
    'MockDataGenerator'
]
