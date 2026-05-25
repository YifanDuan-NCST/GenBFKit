"""
GenBFKit - Task-Oriented Retrieval Module

A semantic-driven, chain-like retrieval system for blast furnace data dictionary.
Implements "Task Requirement → Hierarchical Retrieval → Parameter Location" mechanism.
"""

from .retriever import TaskOrientedRetriever
from .core.dictionary_manager import DictionaryManager
from .core.chain_retriever import ChainRetriever
from .semantic.semantic_parser import SemanticParser
from .ranking.gnn_ranker import GNNRanker
from .templates.preset_templates import PresetTemplateManager

__all__ = [
    "TaskOrientedRetriever",
    "DictionaryManager",
    "ChainRetriever",
    "SemanticParser",
    "GNNRanker",
    "PresetTemplateManager",
]

__version__ = "1.0.0"
