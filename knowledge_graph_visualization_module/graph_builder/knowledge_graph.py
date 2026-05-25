"""
Core Knowledge Graph class for GenBFKit.

Wraps a NetworkX DiGraph and provides high-level operations:
  - Build from the prebuilt data architecture JSON
  - Query by node type, hierarchy, attributes
  - Add GAT-discovered edges / anomaly paths
  - Export sub-graphs for specific scenarios
  - Serialize / deserialize
"""

import os
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any

import networkx as nx

from .models import GraphNode, GraphEdge, NodeType, EdgeType, CausalPath
from .dictionary_parser import DictionaryParser

logger = logging.getLogger(__name__)


class BlastFurnaceKnowledgeGraph:
    """
    The central knowledge graph for blast furnace data.

    Internally stores nodes and edges in a NetworkX DiGraph.
    Provides chain-like retrieval following the 5-level hierarchy:
        work_type → data_category → data_pool → dataset → data_attribute
    """

    def __init__(self, json_path: Optional[str] = None):
        self._graph = nx.DiGraph()
        self._node_objects: Dict[str, GraphNode] = {}
        self._json_path = json_path

        # Index maps for fast lookup
        self._type_index: Dict[NodeType, Set[str]] = {
            nt: set() for nt in NodeType
        }
        self._hierarchy_children: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build_from_prebuilt(self, json_path: Optional[str] = None):
        """
        Build the knowledge graph from the prebuilt_full.json.
        """
        path = json_path or self._json_path
        parser = DictionaryParser(json_path=path)
        nodes, edges = parser.parse()

        for nid, node in nodes.items():
            self._add_node_object(node)

        for edge in edges:
            self._add_edge_object(edge)

        logger.info(
            "Knowledge graph built: %d nodes, %d edges",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
        )
        return self

    # ------------------------------------------------------------------
    # Node / Edge operations
    # ------------------------------------------------------------------
    def _add_node_object(self, node: GraphNode):
        self._graph.add_node(
            node.node_id,
            node_type=node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type,
            name_en=node.name_en,
            name_zh=node.name_zh,
            level=node.level,
            properties=node.properties,
            is_anomaly=node.is_anomaly,
            anomaly_score=node.anomaly_score,
        )
        self._node_objects[node.node_id] = node
        nt = NodeType(node.node_type) if isinstance(node.node_type, str) else node.node_type
        self._type_index[nt].add(node.node_id)

    def _add_edge_object(self, edge: GraphEdge):
        et = edge.edge_type.value if isinstance(edge.edge_type, EdgeType) else edge.edge_type
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=et,
            weight=edge.weight,
            properties=edge.properties,
        )
        # Track hierarchy children
        if et == EdgeType.HIERARCHICAL.value:
            self._hierarchy_children.setdefault(edge.source_id, []).append(edge.target_id)

    def add_discovered_edge(self, source_id: str, target_id: str,
                            attention_score: float, description: str = ""):
        """Add a GAT-discovered process coupling edge."""
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=EdgeType.PROCESS_COUPLING,
            weight=attention_score,
            properties={
                "attention_score": attention_score,
                "description": description,
                "source": "GAT_discovery",
            },
        )
        self._add_edge_object(edge)

    def add_anomaly_propagation_edge(self, source_id: str, target_id: str,
                                     confidence: float, hop: int):
        """Add an anomaly propagation edge from causal reasoning."""
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=EdgeType.ANOMALY_PROPAGATION,
            weight=confidence,
            properties={
                "confidence": confidence,
                "hop": hop,
                "source": "causal_reasoning",
            },
        )
        self._add_edge_object(edge)

    def mark_anomaly(self, node_id: str, score: float):
        """Mark a node as anomalous with a given score."""
        if node_id in self._node_objects:
            node = self._node_objects[node_id]
            node.is_anomaly = True
            node.anomaly_score = score
            self._graph.nodes[node_id]["is_anomaly"] = True
            self._graph.nodes[node_id]["anomaly_score"] = score

    def clear_anomalies(self):
        """Clear all anomaly flags."""
        for nid, node in self._node_objects.items():
            node.is_anomaly = False
            node.anomaly_score = 0.0
            self._graph.nodes[nid]["is_anomaly"] = False
            self._graph.nodes[nid]["anomaly_score"] = 0.0
        # Remove anomaly propagation edges
        edges_to_remove = [
            (u, v) for u, v, d in self._graph.edges(data=True)
            if d.get("edge_type") == EdgeType.ANOMALY_PROPAGATION.value
        ]
        self._graph.remove_edges_from(edges_to_remove)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._node_objects.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        ids = self._type_index.get(node_type, set())
        return [self._node_objects[nid] for nid in ids if nid in self._node_objects]

    def get_children(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[str]:
        """Get child node IDs, optionally filtered by edge type."""
        children = []
        for _, target, data in self._graph.out_edges(node_id, data=True):
            if edge_type is None or data.get("edge_type") == edge_type.value:
                children.append(target)
        return children

    def get_parents(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[str]:
        """Get parent node IDs, optionally filtered by edge type."""
        parents = []
        for source, _, data in self._graph.in_edges(node_id, data=True):
            if edge_type is None or data.get("edge_type") == edge_type.value:
                parents.append(source)
        return parents

    def chain_retrieve(self, work_type_id: str) -> Dict[str, Any]:
        """
        Chain-like data retrieval: work_type → data_category → data_pool → dataset → data_attribute.

        Returns a nested dict representing the full sub-tree under the given work_type.
        """
        if work_type_id not in self._node_objects:
            return {}

        result = {"work_type": self._node_to_dict(work_type_id), "categories": []}

        cat_ids = self.get_children(work_type_id, EdgeType.HIERARCHICAL)
        for cat_id in cat_ids:
            cat_dict = {
                "data_category": self._node_to_dict(cat_id),
                "datasets": [],
            }
            ds_ids = self.get_children(cat_id, EdgeType.HIERARCHICAL)
            for ds_id in ds_ids:
                ds_node = self._node_objects[ds_id]
                pool_ids = self.get_children(ds_id, EdgeType.CROSS_LEVEL)
                pool_id = pool_ids[0] if pool_ids else None
                ds_dict = {
                    "dataset": self._node_to_dict(ds_id),
                    "data_pool": self._node_to_dict(pool_id) if pool_id else None,
                }
                cat_dict["datasets"].append(ds_dict)
            result["categories"].append(cat_dict)

        return result

    def get_subgraph_by_work_type(self, work_type_id: str) -> "BlastFurnaceKnowledgeGraph":
        """Extract a sub-graph for a specific work type."""
        return self._extract_subgraph(
            self._get_descendants(work_type_id) | {work_type_id}
        )

    def get_subgraph_by_pool(self, pool_id: str) -> "BlastFurnaceKnowledgeGraph":
        """Extract a sub-graph for datasets belonging to a specific pool."""
        ds_ids = set(self.get_parents(pool_id, EdgeType.CROSS_LEVEL))
        # Also include their categories and work types
        all_ids = set(ds_ids)
        for ds_id in ds_ids:
            all_ids.update(self.get_parents(ds_id, EdgeType.HIERARCHICAL))
        all_ids.add(pool_id)
        # Add attributes of the pool
        all_ids.update(self.get_children(pool_id, EdgeType.HIERARCHICAL))
        return self._extract_subgraph(all_ids)

    def search_nodes(self, keyword: str, node_type: Optional[NodeType] = None) -> List[GraphNode]:
        """Search nodes by keyword in English or Chinese name."""
        results = []
        candidates = (
            self._type_index.get(node_type, set())
            if node_type
            else set(self._node_objects.keys())
        )
        keyword_lower = keyword.lower()
        for nid in candidates:
            node = self._node_objects.get(nid)
            if node and (keyword_lower in node.name_en.lower()
                         or keyword_lower in node.name_zh.lower()):
                results.append(node)
        return results

    def get_anomaly_nodes(self) -> List[GraphNode]:
        """Return all nodes flagged as anomalous."""
        return [n for n in self._node_objects.values() if n.is_anomaly]

    def get_discovered_edges(self) -> List[Tuple[str, str, float]]:
        """Return all GAT-discovered process coupling edges."""
        results = []
        for u, v, d in self._graph.edges(data=True):
            if d.get("edge_type") == EdgeType.PROCESS_COUPLING.value:
                results.append((u, v, d.get("weight", 0.0)))
        return results

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """Return a summary of the graph statistics."""
        type_counts = {nt.value: len(ids) for nt, ids in self._type_index.items()}
        edge_type_counts = {}
        for _, _, d in self._graph.edges(data=True):
            et = d.get("edge_type", "unknown")
            edge_type_counts[et] = edge_type_counts.get(et, 0) + 1
        return {
            "total_nodes": self._graph.number_of_nodes(),
            "total_edges": self._graph.number_of_edges(),
            "node_type_counts": type_counts,
            "edge_type_counts": edge_type_counts,
            "anomaly_nodes": len(self.get_anomaly_nodes()),
            "discovered_edges": len(self.get_discovered_edges()),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_json(self) -> str:
        """Serialize the full graph to JSON."""
        data = {
            "nodes": [
                {
                    "node_id": nid,
                    **dict(self._graph.nodes[nid]),
                }
                for nid in self._graph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **dict(d),
                }
                for u, v, d in self._graph.edges(data=True)
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def save_json(self, filepath: str):
        """Save the graph to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        logger.info("Graph saved to %s", filepath)

    # ------------------------------------------------------------------
    # Access to underlying NetworkX graph
    # ------------------------------------------------------------------
    @property
    def nx_graph(self) -> nx.DiGraph:
        return self._graph

    @property
    def node_objects(self) -> Dict[str, GraphNode]:
        return self._node_objects

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _node_to_dict(self, node_id: str) -> Optional[Dict]:
        node = self._node_objects.get(node_id)
        if not node:
            return None
        return {
            "id": node.node_id,
            "type": node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type,
            "name_en": node.name_en,
            "name_zh": node.name_zh,
            "level": node.level,
        }

    def _get_descendants(self, node_id: str) -> Set[str]:
        """Get all descendant node IDs via BFS."""
        visited = set()
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for _, target in self._graph.out_edges(current):
                if target not in visited:
                    queue.append(target)
        return visited - {node_id}

    def _extract_subgraph(self, node_ids: Set[str]) -> "BlastFurnaceKnowledgeGraph":
        """Extract a sub-graph containing only the specified nodes and their internal edges."""
        sub = BlastFurnaceKnowledgeGraph()
        sub_nx = self._graph.subgraph(node_ids).copy()
        sub._graph = sub_nx
        for nid in sub_nx.nodes():
            node = self._node_objects.get(nid)
            if node:
                sub._node_objects[nid] = node
                nt = NodeType(node.node_type) if isinstance(node.node_type, str) else node.node_type
                sub._type_index[nt].add(nid)
        for u, v, d in sub_nx.edges(data=True):
            et = d.get("edge_type", "")
            if et == EdgeType.HIERARCHICAL.value:
                sub._hierarchy_children.setdefault(u, []).append(v)
        return sub
