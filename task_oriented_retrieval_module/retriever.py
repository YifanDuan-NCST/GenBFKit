"""
Task-Oriented Retriever - The main orchestrator for GenBFKit's retrieval module.

Integrates all sub-components into a unified retrieval pipeline:
  1. SemanticParser: Natural language → structured task config
  2. PresetTemplateManager: Template-based one-click retrieval
  3. ChainRetriever: Structured task config → filtered results
  4. GNNRanker: Filtered results → relevance-ranked results

This is the "front door" of the task-oriented retrieval module.
Users interact with this class directly for all retrieval operations.

Standalone Usage:
  This module is fully self-contained. When downloaded independently, users only need:
  - The ``prebuilt_full.json`` data architecture file
  - Standard Python dependencies (networkx, numpy, scipy, pydantic)
  - Optional: An OpenAI-compatible LLM API for enhanced semantic parsing
"""

import json
import logging
import os
from typing import Optional

from .core.dictionary_manager import DictionaryManager
from .core.chain_retriever import ChainRetriever, RetrievalResult
from .core.graph_builder import DictionaryGraphBuilder
from .semantic.semantic_parser import SemanticParser
from .ranking.gnn_ranker import GNNRanker
from .templates.preset_templates import PresetTemplateManager
from .virtual_data.generator import VirtualDataGenerator

logger = logging.getLogger(__name__)

# Resolve default dictionary path (priority: module-bundled > Coze runtime > relative fallback)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BUNDLED_DICT = os.path.join(_THIS_DIR, "data", "prebuilt_full.json")
if os.path.isfile(_BUNDLED_DICT):
    DEFAULT_DICT_PATH = _BUNDLED_DICT
else:
    _COZE_WS = os.getenv("COZE_WORKSPACE_PATH", "")
    if _COZE_WS:
        DEFAULT_DICT_PATH = os.path.join(_COZE_WS, "assets", "prebuilt_full.json")
    else:
        DEFAULT_DICT_PATH = os.path.join(_THIS_DIR, "..", "..", "assets", "prebuilt_full.json")


class TaskOrientedRetriever:
    """
    Task-Oriented Retriever - The unified entry point for all retrieval operations.

    Usage Modes:
      1. Natural Language Query: retriever.query("影响热风炉换热效率的控制参数")
      2. Template-Based: retriever.query_by_template("hot_blast_efficiency")
      3. Structured Config: retriever.query_by_config(task_config)

    Each mode follows the same pipeline:
      Parse/Resolve → Chain Retrieve → GNN Rank → Return ranked results

    Standalone Initialization:
      retriever = TaskOrientedRetriever(
          dict_path="/path/to/prebuilt_full.json",
          llm_base_url="https://your-llm-api.com/v1",   # optional
          llm_api_key="sk-xxx",                           # optional
          llm_model="your-model-name",                    # optional
      )
    """

    def __init__(
        self,
        dict_path: str = DEFAULT_DICT_PATH,
        llm_model: str = "doubao-seed-1-8-251228",
        llm_base_url: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        custom_templates_path: Optional[str] = None,
        gnn_num_hops: int = 3,
    ):
        """
        Args:
            dict_path: Path to the prebuilt_full.json data architecture file
            llm_model: LLM model identifier for semantic parsing
            llm_base_url: OpenAI-compatible API base URL (optional, for standalone LLM)
            llm_api_key: API key for LLM authentication (optional)
            custom_templates_path: Path to custom templates JSON file (optional)
            gnn_num_hops: Number of message-passing hops in GNN ranker (default: 3)
        """
        # Core: Dictionary Manager
        self._dm = DictionaryManager(dict_path)
        logger.info("Dictionary Manager loaded from: %s", dict_path)

        # Core: Chain Retriever
        self._chain = ChainRetriever(self._dm)

        # Core: Graph Builder & GNN Ranker
        self._graph_builder = DictionaryGraphBuilder(self._dm)
        self._ranker = GNNRanker(
            self._graph_builder,
            num_hops=gnn_num_hops,
        )

        # Semantic Parser (LLM-powered with fallback)
        self._parser = SemanticParser(
            self._dm,
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )

        # Template Manager
        self._templates = PresetTemplateManager(custom_templates_path)

        # Virtual Data Generator
        self._vdg = VirtualDataGenerator(self._dm)

    # ──────────────────────────────────────────────────────
    # Primary retrieval methods
    # ──────────────────────────────────────────────────────
    def query(
        self,
        natural_language_query: str,
        top_k: Optional[int] = None,
        ctx=None,
    ) -> list[RetrievalResult]:
        """
        Natural language query mode.

        Parses the user's natural language query into a structured task config
        using the semantic parsing engine, then retrieves and ranks results.

        Args:
            natural_language_query: User's query in natural language
            top_k: Return only top K results (None = all)
            ctx: Runtime context for LLM call tracing (Coze runtime only)

        Returns:
            Relevance-ranked list of RetrievalResult objects
        """
        logger.info(f"NL Query: {natural_language_query}")

        # Step 1: Semantic parsing
        task_config = self._parser.parse(natural_language_query, ctx=ctx)
        logger.info(f"Parsed task config: {json.dumps(task_config, ensure_ascii=False)[:200]}")

        # Step 2: Chain retrieval
        results = self._chain.retrieve_by_task(task_config)
        logger.info(f"Chain retrieval: {len(results)} results")

        # Step 3: GNN ranking
        ranked = self._ranker.rank(results, task_config, top_k=top_k)
        logger.info(f"GNN ranking: top score = {ranked[0].relevance_score:.4f}" if ranked else "No results")

        return ranked

    def query_by_template(
        self,
        template_id: str,
        top_k: Optional[int] = None,
    ) -> list[RetrievalResult]:
        """
        Template-based query mode.

        Uses a preset or custom template to instantly retrieve parameters
        for a common blast furnace scenario.

        Args:
            template_id: ID of the preset or custom template
            top_k: Return only top K results (None = all)

        Returns:
            Relevance-ranked list of RetrievalResult objects
        """
        template = self._templates.get_template(template_id)
        if template is None:
            logger.error(f"Template not found: {template_id}")
            return []

        logger.info(f"Template query: {template_id} ({template.name_en})")

        results = self._chain.retrieve_by_task(template.task_config)
        ranked = self._ranker.rank(results, template.task_config, top_k=top_k)
        return ranked

    def query_by_config(
        self,
        task_config: dict,
        top_k: Optional[int] = None,
    ) -> list[RetrievalResult]:
        """
        Structured config query mode.

        Directly provide a structured task_config dict to retrieve and rank results.
        This is the most flexible mode, suitable for programmatic usage.

        Args:
            task_config: Dict with keys: work_types, categories, pools, keywords
            top_k: Return only top K results (None = all)

        Returns:
            Relevance-ranked list of RetrievalResult objects
        """
        results = self._chain.retrieve_by_task(task_config)
        ranked = self._ranker.rank(results, task_config, top_k=top_k)
        return ranked

    # ──────────────────────────────────────────────────────
    # Template management
    # ──────────────────────────────────────────────────────
    def list_templates(self) -> list[dict]:
        """Return all available templates (preset + custom) as dicts."""
        return self._templates.list_templates()

    def get_template(self, template_id: str):
        """Return a specific template by ID."""
        return self._templates.get_template(template_id)

    # ──────────────────────────────────────────────────────
    # Virtual data generation
    # ──────────────────────────────────────────────────────
    def generate_virtual_data(
        self,
        num_records: int = 100,
        scenario: str = "normal",
        pool_filter: Optional[str] = None,
    ) -> dict:
        """Generate virtual blast furnace data for testing."""
        return self._vdg.generate(num_records, scenario, pool_filter)

    # ──────────────────────────────────────────────────────
    # Export & utility
    # ──────────────────────────────────────────────────────
    def export_results(self, results: list[RetrievalResult], format: str = "json") -> str:
        """Export retrieval results in the specified format."""
        if format == "json":
            data = []
            for r in results:
                data.append({
                    "name_en": r.dataset.dataset_en,
                    "name_zh": r.dataset.dataset_zh,
                    "work_type": r.work_type.work_type_zh,
                    "category": r.category.category_zh,
                    "data_pool": r.pool.pool_zh,
                    "relevance_score": round(r.relevance_score, 4),
                })
            return json.dumps(data, ensure_ascii=False, indent=2)

        elif format == "markdown":
            lines = [
                "| # | Parameter (EN) | Parameter (ZH) | Work Type | Category | Pool | Score |",
                "|---|----------------|----------------|-----------|----------|------|-------|",
            ]
            for i, r in enumerate(results, 1):
                lines.append(
                    f"| {i} | {r.dataset.dataset_en} | {r.dataset.dataset_zh} "
                    f"| {r.work_type.work_type_zh} | {r.category.category_zh} "
                    f"| {r.pool.pool_zh} | {r.relevance_score:.4f} |"
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_statistics(self) -> dict:
        """Return data dictionary statistics."""
        return self._dm.get_statistics()
