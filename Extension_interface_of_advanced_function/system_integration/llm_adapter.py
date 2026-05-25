"""
领域大模型适配器

实现与高炉领域大模型的双向集成：
- 接收大模型输出的工艺优化策略与诊断结论
- 将大模型结果写入 GenBFKit 体系
- 知识复盘与图谱更新触发
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMContext:
    """大模型调用上下文。"""
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    knowledge_base: List[str] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.1


@dataclass
class LLMResponse:
    """大模型响应。"""
    success: bool = True
    content: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    latency_ms: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content_snippet": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "structured_data": self.structured_data,
            "error_message": self.error_message,
            "latency_ms": round(self.latency_ms, 1),
            "tokens_used": self.tokens_used,
        }


class LLMAdapter:
    """
    领域大模型适配器。

    负责与领域 LLM 进行通信，处理：
    - 工艺优化策略接收
    - 异常诊断结论接收
    - 参数调控指令解析
    - 结果的结构化提取与持久化

    Usage:
        adapter = LLMAdapter(endpoint="http://llm-service:8000/v1", api_key="...")
        response = adapter.query_strategy("Current hearth temperature is low, suggest adjustments")
    """

    def __init__(
        self,
        endpoint: str = "",
        api_key: str = "",
        model_name: str = "blast-furnace-llm",
        timeout_sec: int = 60,
        use_mock: bool = True,
    ):
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout_sec
        self._use_mock = use_mock
        self._response_history: List[LLMResponse] = []

    def query_strategy(self, context: LLMContext) -> LLMResponse:
        """
        向领域大模型查询工艺优化策略。

        Args:
            context: 查询上下文（包含当前工况数据）

        Returns:
            大模型的策略响应
        """
        if self._use_mock:
            return self._mock_query(context)

        return self._real_query(context)

    def query_diagnosis(self, context: LLMContext) -> LLMResponse:
        """
        查询异常诊断结论。
        """
        return self.query_strategy(context)

    def parse_decision_command(self, response: LLMResponse) -> Dict[str, Any]:
        """
        从 LLM 响应中解析调控指令。

        Returns:
            结构化的调控指令
            {
                "commands": [{"parameter": "...", "value": ..., "action": "increase|decrease|set"}],
                "priority": "high|medium|low",
                "rationale": "..."
            }
        """
        if response.structured_data:
            return response.structured_data

        # 尝试从 content 中解析
        try:
            content = response.content.strip()
            if content.startswith("{"):
                return json.loads(content)
            if content.startswith("```json"):
                json_str = content.replace("```json", "").replace("```", "").strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse LLM response as structured data: {e}")

        return {
            "commands": [],
            "priority": "medium",
            "rationale": response.content[:500],
        }

    def write_to_dictionary(self, response: LLMResponse, target: str = "knowledge") -> bool:
        """
        将 LLM 输出写入 GenBFKit 体系。

        Args:
            response: LLM 响应
            target: 写入目标 (knowledge, decision_log, parameter_update)

        Returns:
            是否成功
        """
        self._response_history.append(response)
        logger.info(f"[LLM] Written to '{target}': {response.to_dict()}")
        return True

    def _real_query(self, context: LLMContext) -> LLMResponse:
        """真实的 LLM API 调用。"""
        import httpx
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._endpoint}/chat/completions",
                    json={
                        "model": self._model_name,
                        "messages": [
                            {"role": "system", "content": "You are a blast furnace domain expert assistant."},
                            {"role": "user", "content": context.query},
                        ],
                        "max_tokens": context.max_tokens,
                        "temperature": context.temperature,
                    },
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                latency = (time.perf_counter() - start) * 1000

                content = data["choices"][0]["message"]["content"]

                # 尝试提取结构化数据
                structured = {}
                try:
                    if content.startswith("{"):
                        structured = json.loads(content)
                except (json.JSONDecodeError, Exception):
                    pass

                response = LLMResponse(
                    success=True,
                    content=content,
                    structured_data=structured,
                    latency_ms=latency,
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                )
                self._response_history.append(response)
                return response

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return LLMResponse(
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )

    def _mock_query(self, context: LLMContext) -> LLMResponse:
        """模拟 LLM 查询（开发/测试用）。"""
        start = time.perf_counter()
        time.sleep(0.05)  # 模拟延迟
        latency = (time.perf_counter() - start) * 1000

        # 根据查询内容生成模拟响应
        query_lower = context.query.lower()

        if "temperature" in query_lower or "热风" in query_lower:
            response = LLMResponse(
                success=True,
                content=json.dumps({
                    "commands": [
                        {"parameter": "hot_blast_temperature", "value": 1200, "action": "increase"},
                        {"parameter": "oxygen_enrichment", "value": 0.25, "action": "set"},
                    ],
                    "priority": "high",
                    "rationale": "Hearth temperature below optimal range. Increase hot blast temperature by 50°C and adjust oxygen enrichment to 25%.",
                }),
                structured_data={
                    "commands": [
                        {"parameter": "hot_blast_temperature", "value": 1200, "action": "increase"},
                        {"parameter": "oxygen_enrichment", "value": 0.25, "action": "set"},
                    ],
                    "priority": "high",
                    "rationale": "Hearth temperature below optimal range.",
                },
                latency_ms=latency,
                tokens_used=156,
            )
        elif "anomaly" in query_lower or "异常" in query_lower:
            response = LLMResponse(
                success=True,
                content=json.dumps({
                    "diagnosis": "Cooling system pressure anomaly detected",
                    "root_cause": "Circulating water pump #2 efficiency degradation",
                    "severity": "high",
                    "recommendation": "Schedule pump maintenance within 4 hours, activate backup pump",
                }),
                structured_data={
                    "diagnosis": "Cooling system pressure anomaly",
                    "root_cause": "Pump #2 efficiency degradation",
                    "severity": "high",
                    "recommendation": "Activate backup pump immediately",
                },
                latency_ms=latency,
                tokens_used=203,
            )
        else:
            response = LLMResponse(
                success=True,
                content=json.dumps({
                    "analysis": "Current blast furnace operating condition is stable.",
                    "recommendations": [
                        "Maintain current parameters",
                        "Monitor hearth temperature trend",
                        "Check tuyere condition at next inspection",
                    ],
                }),
                structured_data={
                    "analysis": "Stable operating condition",
                    "recommendations": ["Maintain parameters", "Monitor hearth temperature"],
                },
                latency_ms=latency,
                tokens_used=98,
            )

        self._response_history.append(response)
        return response