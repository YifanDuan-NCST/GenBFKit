"""
Core data models for the Knowledge Graph nodes and edges.
Uses dataclasses for clean, typed representations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class NodeType(str, Enum):
    """Enumeration of all node types in the knowledge graph."""
    WORK_TYPE = "work_type"
    DATA_CATEGORY = "data_category"
    DATA_POOL = "data_pool"
    DATASET = "dataset"
    DATA_ATTRIBUTE = "data_attribute"


class EdgeType(str, Enum):
    """Enumeration of all edge types in the knowledge graph."""
    HIERARCHICAL = "hierarchical"
    CROSS_LEVEL = "cross_level"
    PROCESS_COUPLING = "process_coupling"
    ANOMALY_PROPAGATION = "anomaly_propagation"


@dataclass
class GraphNode:
    """
    A node in the blast furnace knowledge graph.

    Attributes:
        node_id:    Unique identifier (e.g. "wt_1", "cat_5", "ds_2128").
        node_type:  One of NodeType enum values.
        name_en:    English name.
        name_zh:    Chinese name.
        level:      Hierarchy level (0=work_type, 1=category, 2=pool, 3=dataset, 4=attribute).
        properties: Additional key-value metadata.
        is_anomaly: Flag set by anomaly detection.
        anomaly_score: Score from anomaly detection (0 = normal, higher = more anomalous).
    """
    node_id: str
    node_type: NodeType
    name_en: str
    name_zh: str = ""
    level: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)
    is_anomaly: bool = False
    anomaly_score: float = 0.0

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.node_id == other.node_id

    def __repr__(self):
        return f"GraphNode({self.node_id}, type={self.node_type}, name={self.name_en})"


@dataclass
class GraphEdge:
    """
    A directed edge in the blast furnace knowledge graph.

    Attributes:
        source_id:    Source node ID.
        target_id:    Target node ID.
        edge_type:    One of EdgeType enum values.
        weight:       Edge weight (default 1.0 for hierarchical).
        properties:   Additional metadata (e.g. GAT attention score, causal confidence).
    """
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source_id, self.target_id, self.edge_type))

    def __repr__(self):
        return (f"GraphEdge({self.source_id} → {self.target_id}, "
                f"type={self.edge_type}, weight={self.weight:.3f})")


@dataclass
class CausalPath:
    """
    A multi-hop causal reasoning path from anomaly source to root cause.

    Attributes:
        path:          Ordered list of node IDs from anomaly → root.
        edge_types:    Edge types along the path.
        confidence:    Overall confidence score of the path.
        hop_count:     Number of hops.
        description:   Human-readable description of the reasoning.
    """
    path: List[str]
    edge_types: List[EdgeType]
    confidence: float
    hop_count: int
    description: str = ""

    def __repr__(self):
        return (f"CausalPath(hops={self.hop_count}, confidence={self.confidence:.3f}, "
                f"path={' → '.join(self.path)})")


@dataclass
class GATDiscoveryResult:
    """
    Result from GAT-based knowledge graph completion.

    Attributes:
        source_id:      Source node ID of the discovered edge.
        target_id:      Target node ID of the discovered edge.
        attention_score: Attention weight from GAT.
        edge_type:      Suggested edge type for the new relation.
        description:    Interpretation of the discovered relationship.
    """
    source_id: str
    target_id: str
    attention_score: float
    edge_type: EdgeType = EdgeType.PROCESS_COUPLING
    description: str = ""

    def __repr__(self):
        return (f"GATDiscovery({self.source_id} ↔ {self.target_id}, "
                f"score={self.attention_score:.3f})")
