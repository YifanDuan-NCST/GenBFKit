# -*- coding: utf-8 -*-
"""API 模块"""

from .main import app, create_app
from .routes import router
from .mock_routes import router as mock_router

__all__ = ["app", "create_app", "router", "mock_router"]
