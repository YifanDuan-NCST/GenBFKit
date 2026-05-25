# -*- coding: utf-8 -*-
"""FastAPI 主应用"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import settings
from ..services.database_manager import get_manager
from .routes import router
from .mock_routes import router as mock_router


def create_app(
    static_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
) -> FastAPI:
    """
    创建 FastAPI 应用

    Args:
        static_path: 静态文件目录路径
        json_path: JSON数据文件路径

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title=settings.app.app_name,
        description="GenBFKit 数据库构建工具 - 提供数据库表构建、可视化和数据管理功能",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router, prefix="/api")
    app.include_router(mock_router, prefix="/api")

    # 挂载静态文件
    if static_path and static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # 初始化数据库管理器
    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化"""
        manager = get_manager(json_path=json_path)
        # 存储到 app state
        app.state.manager = manager
        app.state.json_path = json_path

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        try:
            manager = get_manager()
            health = manager.health_check()
            return {
                "status": "healthy" if health.status == "healthy" else "warning",
                "details": health.dict(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    # 前端页面路由
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """主页"""
        static_dir = static_path or Path(__file__).parent.parent / "web"
        index_file = static_dir / "index.html"

        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>GenBFKit Database Builder</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; }
                    .links { margin-top: 20px; }
                    .links a { display: inline-block; margin: 10px 10px 10px 0; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                    .links a:hover { background: #0056b3; }
                    .info { margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>GenBFKit 数据库构建工具</h1>
                    <p>欢迎使用 GenBFKit 数据库构建模块</p>
                    <div class="links">
                        <a href="/api/docs">API 文档</a>
                        <a href="/api/redoc">ReDoc 文档</a>
                    </div>
                    <div class="info">
                        <p><strong>状态:</strong> 服务运行中</p>
                        <p><strong>功能:</strong></p>
                        <ul>
                            <li>从 JSON 文件全量构建数据库表</li>
                            <li>管理元数据和物理数据表</li>
                            <li>导出建表 SQL 脚本</li>
                            <li>查看数据库统计信息</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """

    return app


# 默认应用实例
app = create_app()
