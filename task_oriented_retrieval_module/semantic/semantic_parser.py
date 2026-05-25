"""
Semantic Parsing Engine - Transforms natural language queries into structured
retrieval conditions using an LLM fine-tuned for blast furnace domain.

Core capability:
  - Parse user natural language queries (e.g., "影响热风炉换热效率的控制参数")
  - Map to structured conditions: work_type, category, pool, keyword constraints
  - Leverage data dictionary's full hierarchy as semantic mapping rules
  - Output machine-readable task_config for the Chain Retriever

This engine acts as the "brain" that bridges human intent and structured data retrieval.

Standalone Design:
  - Primary mode: Uses OpenAI-compatible API via ``requests`` (no vendor SDK needed)
  - Fallback mode: Keyword-based offline parser (zero external dependencies)
  - Users only need to provide: base_url, api_key, model_name
"""

import json
import logging
import re
from typing import Optional

from ..core.dictionary_manager import DictionaryManager

logger = logging.getLogger(__name__)


def _build_system_prompt(dict_manager: DictionaryManager) -> str:
    """Build the system prompt with full data dictionary context for semantic parsing."""
    stats = dict_manager.get_statistics()

    # Build work type catalog
    wt_catalog = []
    for wt in dict_manager.get_work_types():
        cats = dict_manager.get_categories_by_work_type(wt.work_type_en)
        cat_names = [f'"{c.category_en}"' for c in cats]
        wt_catalog.append(
            f'  - {wt.work_type_en} ({wt.work_type_zh}): [{", ".join(cat_names[:5])}{"..." if len(cat_names) > 5 else ""}]'
        )

    # Build pool catalog
    pool_catalog = []
    for p in dict_manager.get_pools():
        ds_count = len(dict_manager.get_datasets_by_pool(p.pool_en))
        pool_catalog.append(f'  - {p.pool_en} ({p.pool_zh}): {ds_count} params')

    return f"""You are an expert blast furnace (高炉) data retrieval assistant. Your task is to parse the user's natural language query and convert it into a structured retrieval configuration for GenBFKit's data dictionary.

# Data Dictionary Overview
The data dictionary has a five-level chain-like architecture:
  work_type ({stats["total_work_types"]}) → data_category ({stats["total_categories"]}) → data_pool ({stats["total_pools"]}) → dataset/params ({stats["total_datasets"]}) → data_attribute

# Available Work Types & Categories
{chr(10).join(wt_catalog)}

# Available Data Pools
{chr(10).join(pool_catalog)}

# Your Task
Parse the user's query and output a JSON object with the following structure:
```json
{{
  "work_types": ["work_type_en_1", "work_type_en_2"],
  "categories": ["category_en_1"],
  "pools": ["pool_en_1", "pool_en_2"],
  "keywords": ["keyword1", "keyword2"],
  "intent_summary": "Brief description of what the user is looking for"
}}
```

# Rules
1. work_types: Must be exact matches from the catalog above. Select ALL relevant work types.
2. categories: Must be exact matches. Use partial match if the user refers to a subsystem (e.g., "热风炉" matches categories containing "Hot blast stove").
3. pools: Select based on the user's data type interest. If they want "control parameters", include "Controllable data"; if they want "monitoring indicators", include "Continuous time-series data", "Discrete time-series data", "Binary status data"; if they want "constraints/limits", include "Constraint data".
4. keywords: Extract key technical terms from the query that could match parameter names. Include both English and Chinese keywords.
5. If the user's query is ambiguous, make reasonable inferences based on blast furnace domain knowledge.
6. Always include "intent_summary" explaining your interpretation.

# Examples
Query: "影响热风炉换热效率的控制参数"
Response:
```json
{{
  "work_types": ["Hot blast supplying"],
  "categories": ["Hot blast supply system - Hot blast stove - Operation monitoring", "Hot blast supply system - Hot blast stove - System configuration"],
  "pools": ["Controllable data", "Response data"],
  "keywords": ["heat exchange", "efficiency", "stove", "换热", "效率", "热风炉"],
  "intent_summary": "User seeks controllable parameters affecting hot blast stove heat exchange efficiency"
}}
```

Query: "炉缸安全管控相关的监测指标"
Response:
```json
{{
  "work_types": ["BF operating"],
  "categories": [],
  "pools": ["Continuous time-series data", "Discrete time-series data", "Binary status data"],
  "keywords": ["hearth", "safety", "monitoring", "炉缸", "安全", "监测"],
  "intent_summary": "User seeks monitoring indicators related to hearth safety management"
}}
```

Output ONLY the JSON object, no additional text."""


class SemanticParser:
    """
    Semantic Parsing Engine for GenBFKit's task-oriented retrieval.

    Uses an LLM (domain-knowledge augmented) to parse natural language
    queries into structured retrieval configurations that the Chain Retriever
    can process directly.

    The engine embeds the full data dictionary hierarchy as context,
    enabling precise mapping from user intent to dictionary levels.

    LLM Backend Selection (priority order):
      1. Custom OpenAI-compatible API (base_url + api_key + model)
      2. coze_coding_dev_sdk (if available in Coze runtime)
      3. Fallback keyword parser (offline, always available)
    """

    def __init__(
        self,
        dict_manager: DictionaryManager,
        model: str = "doubao-seed-1-8-251228",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Args:
            dict_manager: Loaded dictionary manager instance
            model: LLM model identifier
            base_url: OpenAI-compatible API base URL (optional)
            api_key: API key for authentication (optional)
        """
        self._dm = dict_manager
        self._model = model
        self._base_url = base_url
        self._api_key = api_key
        self._system_prompt = _build_system_prompt(dict_manager)

    def parse(self, query: str, ctx=None) -> dict:
        """
        Parse a natural language query into a structured retrieval configuration.

        Args:
            query: User's natural language query (e.g., "影响热风炉换热效率的控制参数")
            ctx: Runtime context for request tracing (optional, Coze runtime only)

        Returns:
            Structured task_config dict for ChainRetriever.retrieve_by_task()
        """
        # Strategy 1: Custom OpenAI-compatible API (standalone mode)
        if self._base_url and self._api_key:
            return self._parse_via_openai_api(query)

        # Strategy 2: Coze runtime SDK (if available AND configured)
        try:
            return self._parse_via_coze_sdk(query, ctx)
        except (ImportError, Exception) as e:
            logger.info(f"Coze SDK not available or not configured, skipping: {e}")

        # Strategy 3: Fallback keyword parser (always available)
        logger.info("Using fallback keyword parser (offline mode)")
        return self._fallback_parse(query)

    def _parse_via_openai_api(self, query: str) -> dict:
        """Parse via OpenAI-compatible API using requests (fully standalone)."""
        import requests  # stdlib-adjacent, always available

        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": query},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            task_config = self._extract_json(content)
            if task_config is not None:
                logger.info(f"OpenAI API parse success: work_types={task_config.get('work_types')}")
                return task_config
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")

        return self._fallback_parse(query)

    def _parse_via_coze_sdk(self, query: str, ctx=None) -> dict:
        """Parse via coze_coding_dev_sdk (Coze runtime environment)."""
        from coze_coding_dev_sdk import LLMClient
        from langchain_core.messages import SystemMessage, HumanMessage
        from coze_coding_utils.runtime_ctx.context import new_context

        ctx = ctx or new_context(method="semantic_parse")
        client = LLMClient(ctx=ctx)

        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=query),
        ]

        try:
            response = client.invoke(
                messages=messages,
                model=self._model,
                temperature=0.1,
                max_completion_tokens=2048,
            )
        except Exception as e:
            logger.error(f"Coze SDK LLM invocation failed: {e}")
            return self._fallback_parse(query)

        # Extract text content safely
        content = response.content
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            content = " ".join(text_parts)
        content = str(content).strip()

        # Parse JSON from response
        task_config = self._extract_json(content)
        if task_config is None:
            logger.warning(f"Failed to parse LLM response as JSON, using fallback: {content[:200]}")
            return self._fallback_parse(query)

        logger.info(
            f"Semantic parse result: work_types={task_config.get('work_types')}, "
            f"pools={task_config.get('pools')}, keywords={task_config.get('keywords')}"
        )
        return task_config

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON object from potentially markdown-wrapped text."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def _fallback_parse(self, query: str) -> dict:
        """
        Fallback parser when LLM is unavailable.
        Uses comprehensive keyword matching against the dictionary,
        including Chinese alias mappings for work types and pools.

        This parser is 100% offline and requires no external dependencies,
        ensuring the retrieval module works even without network access
        (e.g., in isolated blast furnace control rooms).
        """
        query_lower = query.lower()

        # ── Work type matching with Chinese aliases ──
        work_type_aliases = {
            "Slag treating": ["slag", "炉渣", "渣处理", "冲渣", "水渣"],
            "Hot blast supplying": ["hot blast", "热风", "热风炉", "送风", "助燃", "stove"],
            "Gas & Dust treating": ["gas", "dust", "煤气", "除尘", "洗涤", "净化", "布袋"],
            "Equipment maintaining": ["equipment", "维修", "设备", "维护", "检修"],
            "Cooling monitoring": ["cooling", "冷却", "冷却壁", "水冷", "热负荷"],
            "Burden feeding": ["burden", "装料", "布料", "无钟", "料罐", "料车", "charging"],
            "BF tapping": ["tapping", "出铁", "铁口", "铁水", "撇渣器", "trough"],
            "BF operating": ["operating", "高炉操作", "炉况", "炉缸", "炉身", "炉腹", "风口", "鼓风"],
        }

        matched_wts = []
        for wt in self._dm.get_work_types():
            aliases = work_type_aliases.get(wt.work_type_en, [])
            if (wt.work_type_en.lower() in query_lower
                    or wt.work_type_zh in query
                    or any(a in query_lower for a in aliases)):
                matched_wts.append(wt.work_type_en)

        # ── Category matching with Chinese keyword extraction ──
        matched_categories = []
        for cat in self._dm._snapshot.categories:
            cat_parts = cat.category_en.split(" - ")
            cat_zh_parts = cat.category_zh.split("-")
            # Match if any part of the category name appears in query
            if (any(part.lower() in query_lower for part in cat_parts)
                    or any(part in query for part in cat_zh_parts)):
                matched_categories.append(cat.category_en)

        # ── Pool matching with Chinese aliases ──
        pool_keywords = {
            "Continuous time-series data": ["监测", "monitoring", "continuous", "连续", "时序", "温度", "压力", "流量"],
            "Controllable data": ["控制", "control", "controllable", "调控", "操作", "设定"],
            "Binary status data": ["状态", "status", "binary", "开关", "启停", "运行状态"],
            "Constraint data": ["约束", "constraint", "限制", "limit", "阈值", "报警", "上限", "下限"],
            "Response data": ["响应", "response", "反馈", "效果"],
            "Discrete time-series data": ["离散", "discrete", "批次", "化验"],
            "Batch time-series data": ["批量", "batch", "批", "LIMS", "检化验"],
            "Text data": ["文本", "text", "记录", "日志", "报告"],
            "Image data": ["图像", "image", "视频", "监控画面", "camera"],
        }

        matched_pools = []
        for p in self._dm.get_pools():
            kw_list = pool_keywords.get(p.pool_en, [])
            if any(k in query_lower for k in kw_list):
                matched_pools.append(p.pool_en)

        # ── Extract technical keywords ──
        # Common blast furnace technical terms
        bf_keywords_map = {
            "换热": ["heat exchange", "换热"],
            "效率": ["efficiency", "效率"],
            "燃烧": ["combustion", "燃烧", "burner"],
            "拱顶": ["dome", "拱顶"],
            "烟气": ["flue gas", "烟气", "废气"],
            "风温": ["blast temperature", "风温", "hot blast temperature"],
            "风压": ["blast pressure", "风压"],
            "铁水温度": ["hot metal temperature", "铁水温度"],
            "炉缸侵蚀": ["hearth erosion", "炉缸侵蚀"],
            "冷却壁温度": ["stave temperature", "冷却壁温度"],
            "料线": ["stock line", "料线"],
        }
        keywords = []
        for zh_term, en_terms in bf_keywords_map.items():
            if zh_term in query:
                keywords.extend(en_terms)
        # Add individual Chinese characters/words from query
        keywords.extend([w for w in query if len(w) > 1 and "\u4e00" <= w <= "\u9fff"])
        # Add the full query for partial matching
        keywords.append(query)
        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)

        return {
            "work_types": matched_wts if matched_wts else None,
            "categories": matched_categories[:10] if matched_categories else [],
            "pools": matched_pools if matched_pools else None,
            "keywords": unique_keywords,
            "intent_summary": f"Fallback parse for: {query}",
        }
