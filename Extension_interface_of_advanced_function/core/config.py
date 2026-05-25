"""
配置管理模块

提供全局配置管理，支持从 JSON/YAML 文件或环境变量加载配置。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ExtensionConfig:
    """
    GenBFKit Extension Interface 全局配置。

    Attributes:
        data_dictionary_path: 数据字典 JSON 文件路径
        onnx_models_dir: ONNX 模型存放目录
        model_cache_dir: 模型缓存目录
        log_level: 日志级别
        server_host: 系统集成服务监听地址
        server_port: 系统集成服务监听端口
        digital_twin_endpoint: 数字孪生平台 API 端点
        llm_endpoint: 领域大模型 API 端点
        llm_api_key: 领域大模型 API Key
        db_connection_string: 数据库连接字符串（如 PostgreSQL）
    """

    # 数据字典
    data_dictionary_path: str = ""
    onnx_models_dir: str = "./models"
    model_cache_dir: str = "./cache"

    # 日志
    log_level: str = "INFO"

    # 系统集成
    server_host: str = "0.0.0.0"
    server_port: int = 18080
    digital_twin_endpoint: str = ""
    llm_endpoint: str = ""
    llm_api_key: str = ""
    db_connection_string: str = ""

    # 扩展字段
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, path: str | Path) -> "ExtensionConfig":
        """从 JSON 配置文件加载。"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_env(cls) -> "ExtensionConfig":
        """从环境变量加载配置（优先级低于 from_json）。"""
        return cls(
            data_dictionary_path=os.getenv("GENBFKIT_DICT_PATH", ""),
            onnx_models_dir=os.getenv("GENBFKIT_MODELS_DIR", "./models"),
            model_cache_dir=os.getenv("GENBFKIT_CACHE_DIR", "./cache"),
            log_level=os.getenv("GENBFKIT_LOG_LEVEL", "INFO"),
            server_host=os.getenv("GENBFKIT_HOST", "0.0.0.0"),
            server_port=int(os.getenv("GENBFKIT_PORT", "18080")),
            digital_twin_endpoint=os.getenv("GENBFKIT_DT_ENDPOINT", ""),
            llm_endpoint=os.getenv("GENBFKIT_LLM_ENDPOINT", ""),
            llm_api_key=os.getenv("GENBFKIT_LLM_API_KEY", ""),
            db_connection_string=os.getenv("GENBFKIT_DB_CONNECTION", ""),
        )

    def resolve_path(self, relative_path: str) -> str:
        """将相对路径解析为模块根目录下的绝对路径。"""
        if os.path.isabs(relative_path):
            return relative_path
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, relative_path)

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典。"""
        return {
            "data_dictionary_path": self.data_dictionary_path,
            "onnx_models_dir": self.onnx_models_dir,
            "model_cache_dir": self.model_cache_dir,
            "log_level": self.log_level,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "digital_twin_endpoint": self.digital_twin_endpoint,
            "llm_endpoint": self.llm_endpoint,
            "llm_api_key": "***" if self.llm_api_key else "",
            "db_connection_string": "***" if self.db_connection_string else "",
            "extra": self.extra,
        }