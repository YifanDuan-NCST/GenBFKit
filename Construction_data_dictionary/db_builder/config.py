# -*- coding: utf-8 -*-
"""数据库配置模块"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """数据库连接配置"""

    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口")
    database: str = Field(default="genbfkit", description="数据库名称")
    username: str = Field(default="postgres", description="用户名")
    password: str = Field(default="8848", description="密码")
    db_schema: str = Field(default="public", description="Database schema")

    @property
    def url(self) -> str:
        """生成数据库连接 URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """生成异步数据库连接 URL"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def display_url(self) -> str:
        """用于显示的连接信息（隐藏密码）"""
        return f"postgresql://{self.username}:***@{self.host}:{self.port}/{self.database}"


class AppSettings(BaseModel):
    """应用配置"""

    app_name: str = "GenBFKit Database Builder"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]
    static_files_path: Optional[Path] = None


class Settings(BaseSettings):
    """全局配置"""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    json_data_path: Optional[Path] = Field(default=None, description="JSON 数据文件路径")
    export_path: Path = Field(default=Path("./exports"), description="导出文件路径")

    model_config = SettingsConfigDict(
        env_prefix="GENBFKIT__",
        env_nested_delimiter="__",
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
