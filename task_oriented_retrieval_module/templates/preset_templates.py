"""
Preset Task Template Manager - One-click retrieval for typical blast furnace scenarios.

Provides pre-configured retrieval templates that encapsulate domain knowledge
about which work types, categories, pools, and keywords are relevant for
common operational scenarios. Users can invoke a template by name and get
instant access to all core associated parameters.

Built-in templates:
  1. Hearth Safety Management (炉缸安全管控)
  2. Hot Blast Stove Efficiency Optimization (热风炉效率优化)
  3. Burden Distribution Regulation (布料制度调控)
  4. Hot Metal Quality Improvement (铁水质量提升)
  5. Cooling System Monitoring (冷却系统监测)
  6. Gas & Dust Treatment Optimization (煤气除尘优化)

Custom templates:
  Users can create, save, and manage their own templates based on
  the data dictionary's CRUD capabilities.
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskTemplate(BaseModel):
    """A single task-oriented retrieval template."""
    template_id: str = Field(description="Unique template identifier")
    name_en: str = Field(description="Template name (English)")
    name_zh: str = Field(description="Template name (Chinese)")
    description: str = Field(description="What this template retrieves")
    task_config: dict = Field(description="Structured retrieval configuration")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")


# ──────────────────────────────────────────────────────────
# Built-in preset templates
# ──────────────────────────────────────────────────────────
BUILTIN_TEMPLATES: list[TaskTemplate] = [
    TaskTemplate(
        template_id="hearth_safety",
        name_en="Hearth Safety Management",
        name_zh="炉缸安全管控",
        description="Retrieve all monitoring, constraint, and control parameters related to blast furnace hearth safety management, including temperature monitoring, cooling status, and erosion indicators.",
        task_config={
            "work_types": ["BF operating"],
            "categories": [
                "BF operating system - Hearth - Operation monitoring",
                "BF operating system - Hearth - Safety management",
                "BF operating system - Hearth - System configuration",
                "BF operating system - Lower zone - Operation monitoring",
            ],
            "pools": [
                "Continuous time-series data",
                "Discrete time-series data",
                "Binary status data",
                "Constraint data",
                "Controllable data",
            ],
            "keywords": ["hearth", "erosion", "temperature", "safety", "炉缸", "侵蚀", "温度", "安全"],
            "intent_summary": "Hearth safety management: monitoring + constraint + control parameters",
        },
        tags=["safety", "hearth", "monitoring", "critical"],
    ),
    TaskTemplate(
        template_id="hot_blast_efficiency",
        name_en="Hot Blast Stove Efficiency Optimization",
        name_zh="热风炉效率优化",
        description="Retrieve parameters affecting hot blast stove heat exchange efficiency, including combustion control, gas flow, dome temperature, and waste gas conditions.",
        task_config={
            "work_types": ["Hot blast supplying"],
            "categories": [
                "Hot blast supply system - Hot blast stove - Operation monitoring",
                "Hot blast supply system - Hot blast stove - System configuration",
                "Blast supply system - Valve group - Hot blast control",
                "Hot blast supply system - Combustion air fan - Operation monitoring",
            ],
            "pools": [
                "Continuous time-series data",
                "Controllable data",
                "Response data",
                "Constraint data",
            ],
            "keywords": ["stove", "combustion", "dome", "efficiency", "gas", "热风炉", "燃烧", "拱顶", "效率", "煤气"],
            "intent_summary": "Hot blast stove efficiency: combustion + heat exchange + control parameters",
        },
        tags=["efficiency", "hot blast stove", "optimization", "combustion"],
    ),
    TaskTemplate(
        template_id="burden_distribution",
        name_en="Burden Distribution Regulation",
        name_zh="布料制度调控",
        description="Retrieve parameters for burden distribution control, including charging system status, bell-less top operation, and material layer monitoring.",
        task_config={
            "work_types": ["Burden feeding"],
            "categories": [
                "Burden feeding system - Bell-less top - Operation monitoring",
                "Burden feeding system - Bell-less top - System configuration",
                "Burden feeding system - Weighing hopper - Operation monitoring",
                "Burden feeding system - Belt conveyor - Operation monitoring",
            ],
            "pools": [
                "Continuous time-series data",
                "Discrete time-series data",
                "Controllable data",
                "Binary status data",
            ],
            "keywords": ["burden", "distribution", "charging", "bell-less", "hopper", "布料", "装料", "无钟", "料罐"],
            "intent_summary": "Burden distribution: charging + distribution + monitoring parameters",
        },
        tags=["burden", "distribution", "charging", "regulation"],
    ),
    TaskTemplate(
        template_id="hot_metal_quality",
        name_en="Hot Metal Quality Improvement",
        name_zh="铁水质量提升",
        description="Retrieve parameters related to hot metal quality, including tapping temperature, composition analysis, and slag-metal interaction indicators.",
        task_config={
            "work_types": ["BF tapping", "BF operating"],
            "categories": [
                "BF tapping system - Cast house - Operation monitoring",
                "BF tapping system - Trough - Operation monitoring",
                "BF operating system - Lower zone - Operation monitoring",
            ],
            "pools": [
                "Continuous time-series data",
                "Batch time-series data",
                "Constraint data",
                "Response data",
            ],
            "keywords": ["tapping", "hot metal", "temperature", "composition", "slag", "铁水", "出铁", "温度", "成分", "炉渣"],
            "intent_summary": "Hot metal quality: tapping + composition + temperature parameters",
        },
        tags=["quality", "tapping", "hot metal", "composition"],
    ),
    TaskTemplate(
        template_id="cooling_monitoring",
        name_en="Cooling System Monitoring",
        name_zh="冷却系统监测",
        description="Retrieve all cooling system monitoring parameters, including stave temperatures, water flow rates, and thermal load indicators.",
        task_config={
            "work_types": ["Cooling monitoring"],
            "categories": [],  # All categories under Cooling monitoring
            "pools": [
                "Continuous time-series data",
                "Discrete time-series data",
                "Binary status data",
                "Constraint data",
            ],
            "keywords": ["cooling", "stave", "water flow", "thermal", "冷却", "冷却壁", "水流量", "热负荷"],
            "intent_summary": "Cooling system monitoring: temperature + flow + thermal load parameters",
        },
        tags=["cooling", "monitoring", "stave", "thermal"],
    ),
    TaskTemplate(
        template_id="gas_dust_treatment",
        name_en="Gas & Dust Treatment Optimization",
        name_zh="煤气除尘优化",
        description="Retrieve parameters for gas cleaning and dust treatment optimization, including gas temperature, pressure, dust content, and scrubber operation.",
        task_config={
            "work_types": ["Gas & Dust treating"],
            "categories": [],  # All categories under Gas & Dust treating
            "pools": [
                "Continuous time-series data",
                "Discrete time-series data",
                "Controllable data",
                "Constraint data",
            ],
            "keywords": ["gas", "dust", "scrubber", "cleaning", "煤气", "除尘", "洗涤", "净化"],
            "intent_summary": "Gas & dust treatment: cleaning + monitoring + control parameters",
        },
        tags=["gas", "dust", "treatment", "optimization"],
    ),
]


class PresetTemplateManager:
    """
    Manages preset and custom task-oriented retrieval templates.

    Features:
      - List all available templates (built-in + custom)
      - Get template by ID or name
      - Create custom templates with user-defined task configs
      - Delete custom templates (built-in templates are immutable)
      - Search templates by tags or keywords
    """

    def __init__(self, custom_templates_path: Optional[str] = None):
        self._templates: dict[str, TaskTemplate] = {}
        self._custom_path = custom_templates_path

        # Load built-in templates
        for tmpl in BUILTIN_TEMPLATES:
            self._templates[tmpl.template_id] = tmpl

        # Load custom templates if available
        if custom_templates_path:
            self._load_custom_templates(custom_templates_path)

        logger.info(f"Template manager initialized with {len(self._templates)} templates")

    def list_templates(self, tags: Optional[list[str]] = None) -> list[TaskTemplate]:
        """
        List all available templates, optionally filtered by tags.
        """
        templates = list(self._templates.values())
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        return templates

    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """Get a template by its ID."""
        return self._templates.get(template_id)

    def search_templates(self, query: str) -> list[TaskTemplate]:
        """
        Search templates by name, description, or tags.
        Supports both English and Chinese queries.
        """
        query_lower = query.lower()
        results = []
        for tmpl in self._templates.values():
            searchable = (
                tmpl.name_en.lower()
                + " " + tmpl.name_zh.lower()
                + " " + tmpl.description.lower()
                + " " + " ".join(tmpl.tags).lower()
            )
            if query_lower in searchable:
                results.append(tmpl)
        return results

    def create_template(self, template: TaskTemplate) -> bool:
        """
        Create a new custom template.
        Returns False if template_id already exists.
        """
        if template.template_id in self._templates:
            logger.error(f"Template '{template.template_id}' already exists")
            return False
        self._templates[template.template_id] = template
        self._save_custom_templates()
        logger.info(f"Created custom template: {template.template_id}")
        return True

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a custom template.
        Built-in templates cannot be deleted.
        """
        builtin_ids = {t.template_id for t in BUILTIN_TEMPLATES}
        if template_id in builtin_ids:
            logger.error(f"Cannot delete built-in template: {template_id}")
            return False
        if template_id not in self._templates:
            logger.error(f"Template not found: {template_id}")
            return False
        del self._templates[template_id]
        self._save_custom_templates()
        logger.info(f"Deleted custom template: {template_id}")
        return True

    def update_template(self, template_id: str, **kwargs) -> bool:
        """
        Update fields of a custom template.
        Built-in templates cannot be updated.
        """
        builtin_ids = {t.template_id for t in BUILTIN_TEMPLATES}
        if template_id in builtin_ids:
            logger.error(f"Cannot update built-in template: {template_id}")
            return False
        tmpl = self._templates.get(template_id)
        if tmpl is None:
            logger.error(f"Template not found: {template_id}")
            return False
        for k, v in kwargs.items():
            if hasattr(tmpl, k):
                setattr(tmpl, k, v)
        self._save_custom_templates()
        logger.info(f"Updated custom template: {template_id}")
        return True

    def _load_custom_templates(self, path: str) -> None:
        """Load custom templates from a JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                tmpl = TaskTemplate(**item)
                if tmpl.template_id not in self._templates:
                    self._templates[tmpl.template_id] = tmpl
            logger.info(f"Loaded custom templates from: {path}")
        except FileNotFoundError:
            logger.info(f"No custom templates file found at: {path}")
        except Exception as e:
            logger.warning(f"Failed to load custom templates: {e}")

    def _save_custom_templates(self) -> None:
        """Save custom templates (non-built-in) to JSON file."""
        if not self._custom_path:
            return
        builtin_ids = {t.template_id for t in BUILTIN_TEMPLATES}
        custom = [
            self._templates[tid].model_dump()
            for tid in self._templates
            if tid not in builtin_ids
        ]
        try:
            with open(self._custom_path, "w", encoding="utf-8") as f:
                json.dump(custom, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save custom templates: {e}")
