"""
数据总线

实现发布-订阅模式的数据交换总线，支持：
- 标准化数据推送至外部系统（数字孪生、大模型等）
- 多通道消息路由
- 数据格式自动转换
- 消息持久化（可选）
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举。"""
    DATA_PUSH = "data_push"               # 数据推送
    MODEL_INPUT = "model_input"           # 模型输入
    MODEL_OUTPUT = "model_output"         # 模型输出
    DECISION_COMMAND = "decision_command" # 决策指令
    ANOMALY_ALERT = "anomaly_alert"       # 异常告警
    STATUS_UPDATE = "status_update"       # 状态更新
    SYSTEM_EVENT = "system_event"         # 系统事件
    CUSTOM = "custom"                     # 自定义


@dataclass
class DataMessage:
    """数据消息。"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.DATA_PUSH
    channel: str = "default"
    source: str = "genbfkit"
    target: str = ""
    payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class DataBus:
    """
    数据总线。

    基于发布-订阅模式，管理 GenBFKit 与外部系统的数据交换。
    支持多通道、多订阅者、消息过滤与转换。

    Usage:
        bus = DataBus()

        # 订阅消息
        def on_data(msg):
            print(f"Received: {msg.payload}")

        bus.subscribe("twin_channel", on_data, MessageType.DATA_PUSH)

        # 发布消息
        bus.publish(DataMessage(channel="twin_channel", payload={"temp": 1500}))
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._history: List[DataMessage] = []
        self._max_history: int = 1000
        self._transformers: Dict[str, Callable] = {}

    def subscribe(
        self,
        channel: str,
        callback: Callable[[DataMessage], None],
        message_type: Optional[MessageType] = None,
        filter_func: Optional[Callable[[DataMessage], bool]] = None,
    ) -> str:
        """
        订阅消息通道。

        Args:
            channel: 通道名称
            callback: 回调函数
            message_type: 可选，仅订阅特定类型的消息
            filter_func: 可选，自定义过滤函数

        Returns:
            订阅 ID（可用于取消订阅）
        """
        sub_id = str(uuid.uuid4())
        if channel not in self._subscribers:
            self._subscribers[channel] = []

        self._subscribers[channel].append({
            "id": sub_id,
            "callback": callback,
            "message_type": message_type,
            "filter_func": filter_func,
        })

        logger.debug(f"Subscribed to '{channel}' (id={sub_id})")
        return sub_id

    def unsubscribe(self, channel: str, sub_id: str) -> bool:
        """取消订阅。"""
        if channel not in self._subscribers:
            return False
        before = len(self._subscribers[channel])
        self._subscribers[channel] = [
            s for s in self._subscribers[channel] if s["id"] != sub_id
        ]
        return len(self._subscribers[channel]) < before

    def publish(self, message: DataMessage) -> int:
        """
        发布消息到指定通道。

        Args:
            message: 消息对象

        Returns:
            接收消息的订阅者数量
        """
        channel = message.channel
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # 应用数据转换器
        if channel in self._transformers:
            try:
                message = self._transformers[channel](message)
            except Exception as e:
                logger.error(f"Transformer failed for channel '{channel}': {e}")

        subscribers = self._subscribers.get(channel, [])
        count = 0

        for sub in subscribers:
            try:
                # 消息类型过滤
                if sub["message_type"] and message.message_type != sub["message_type"]:
                    continue
                # 自定义过滤
                if sub["filter_func"] and not sub["filter_func"](message):
                    continue

                sub["callback"](message)
                count += 1
            except Exception as e:
                logger.error(f"Subscriber error on channel '{channel}': {e}")

        logger.debug(f"Published to '{channel}': {count}/{len(subscribers)} subscribers")
        return count

    def register_transformer(
        self, channel: str, transformer: Callable[[DataMessage], DataMessage]
    ) -> None:
        """注册数据转换器。"""
        self._transformers[channel] = transformer

    def get_history(
        self,
        channel: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[DataMessage]:
        """查询消息历史。"""
        messages = self._history
        if channel:
            messages = [m for m in messages if m.channel == channel]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages[-limit:]

    def channel_stats(self) -> Dict[str, int]:
        """获取各通道的统计信息。"""
        stats = {}
        for channel, subs in self._subscribers.items():
            stats[channel] = len(subs)
        return stats

    @staticmethod
    def dataframe_to_message(
        df: pd.DataFrame,
        channel: str = "data_push",
        source: str = "genbfkit",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataMessage:
        """将 DataFrame 转换为数据消息。"""
        return DataMessage(
            channel=channel,
            source=source,
            payload=json.loads(df.to_json(orient="records", force_ascii=False)),
            metadata=metadata or {"rows": len(df), "columns": list(df.columns)},
        )