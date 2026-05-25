"""
GenBFKit - Knowledge Graph Visualization Module
================================================
A "Static Knowledge Display - Dynamic Association Mining - Anomaly Traceability Reasoning"
three-in-one graph application system for blast furnace process knowledge.
"""

__version__ = "1.0.0"
__author__ = "GenBFKit Team"

from .graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from .gat_engine.trainer import GATTrainer  # noqa: F401 — re-exported
from .causal_reasoning.multi_hop_reasoner import MultiHopCausalReasoner
from .visualizer.static_renderer import StaticRenderer
from .visualizer.interactive_renderer import InteractiveRenderer
from .data.virtual_generator import VirtualDataGenerator

__all__ = [
    "BlastFurnaceKnowledgeGraph",
    "GATTrainer",
    "MultiHopCausalReasoner",
    "StaticRenderer",
    "InteractiveRenderer",
    "VirtualDataGenerator",
]
