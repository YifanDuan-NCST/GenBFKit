# -*- coding: utf-8 -*-
"""ORM 基础类和混入"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """时间戳混入 - 自动管理创建和更新时间"""

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)


class UUIDMixin:
    """UUID 主键混入"""

    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
