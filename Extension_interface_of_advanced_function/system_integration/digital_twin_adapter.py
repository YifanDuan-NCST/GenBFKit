"""
数字孪生适配器

实现与数字孪生平台的双向数据交换：
- 将 GenBFKit 标准化的高炉数据推送至数字孪生平台
- 接收数字孪生平台的仿真结果与工艺策略
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class TwinDataFrame:
    """数字孪生数据帧。"""
    timestamp: float = field(default_factory=time.time)
    frame_id: str = ""
    source: str = "genbfkit"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DigitalTwinAdapter:
    """
    数字孪生适配器。

    提供与数字孪生平台的标准数据交换接口。
    支持 REST API / WebSocket / gRPC 等多种通信方式。

    Usage:
        adapter = DigitalTwinAdapter(endpoint="http://twin-platform:8080/api")
        adapter.push_measurements(twin_frame)
        strategy = adapter.pull_strategy()
    """

    def __init__(
        self,
        endpoint: str = "",
        api_key: str = "",
        timeout_sec: int = 30,
        use_mock: bool = True,
    ):
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_sec
        self._use_mock = use_mock
        self._session_id: str = ""
        self._data_buffer: List[TwinDataFrame] = []

    def push_measurements(
        self,
        data_frame: TwinDataFrame,
    ) -> Dict[str, Any]:
        """
        推送实测/标准化数据至数字孪生平台。

        Args:
            data_frame: 数字孪生数据帧

        Returns:
            平台响应
        """
        if self._use_mock:
            return self._mock_push(data_frame)

        # 真实 HTTP 推送
        import httpx
        payload = {
            "timestamp": data_frame.timestamp,
            "frame_id": data_frame.frame_id,
            "source": data_frame.source,
            "data": data_frame.data,
            "metadata": data_frame.metadata,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._endpoint}/api/v1/measurements",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                logger.info(f"Pushed data frame {data_frame.frame_id} to twin platform")
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to push to twin platform: {e}")
            return {"success": False, "error": str(e)}

    def pull_strategy(self) -> Dict[str, Any]:
        """
        从数字孪生平台拉取工艺优化策略。

        Returns:
            包含策略参数的字典
        """
        if self._use_mock:
            return self._mock_pull_strategy()

        try:
            import httpx
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"{self._endpoint}/api/v1/strategies/latest",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to pull strategy: {e}")
            return {"success": False, "error": str(e)}

    def push_simulation_results(
        self,
        scenario_id: str,
        params: Dict[str, Any],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """推送仿真结果至数字孪生平台。"""
        frame = TwinDataFrame(
            frame_id=f"sim_{scenario_id}_{int(time.time())}",
            source="genbfkit_simulation",
            data={"scenario_id": scenario_id, "params": params, "results": results},
            metadata={"type": "simulation_result"},
        )
        return self.push_measurements(frame)

    def _mock_push(self, frame: TwinDataFrame) -> Dict[str, Any]:
        """模拟推送（开发/测试用）。"""
        self._data_buffer.append(frame)
        logger.info(f"[MOCK] Pushed data frame: {frame.frame_id}")
        return {
            "success": True,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "frame_id": frame.frame_id,
            "data_size": len(json.dumps(frame.data)),
        }

    def _mock_pull_strategy(self) -> Dict[str, Any]:
        """模拟拉取策略。"""
        return {
            "success": True,
            "strategy_id": "strategy_001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "hot_blast_temperature_adjustment": 5.0,
                "oxygen_enrichment_rate": 0.03,
                "coal_injection_rate": 2.5,
                "burden_distribution": "center_weighted",
            },
            "rationale": "Current hearth thermal condition suggests moderate adjustments.",
        }

    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取数据缓冲区统计。"""
        return {
            "buffer_size": len(self._data_buffer),
            "last_push": self._data_buffer[-1].timestamp if self._data_buffer else None,
        }