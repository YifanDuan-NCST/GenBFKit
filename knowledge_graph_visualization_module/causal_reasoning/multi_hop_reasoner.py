"""
Multi-Hop Causal Reasoner for anomaly traceability.

When an anomaly is detected (e.g., abnormal hot metal temperature),
this module traverses the knowledge graph along process coupling
and hierarchical edges to identify root causes.

Algorithm:
    1. Start from anomalous node(s)
    2. BFS/DFS with priority queue (score-based)
    3. At each hop, follow:
       - Anomaly propagation edges (if previously computed)
       - Hierarchical parent edges (to find upstream process)
       - Process coupling edges (GAT-discovered cross-parameter links)
       - Cross-level edges (dataset ↔ pool relationships)
    4. Score each path by edge weights and node anomaly scores
    5. Return top-K root cause candidates with full reasoning paths
"""

import heapq
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, EdgeType, CausalPath, GraphNode
from ..config import (
    CAUSAL_MAX_HOPS, CAUSAL_TOP_K_PATHS,
    CAUSAL_MIN_PATH_SCORE,
)

logger = logging.getLogger(__name__)


class MultiHopCausalReasoner:
    """
    Performs multi-hop causal reasoning on the blast furnace knowledge graph
    to trace anomaly root causes.
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 max_hops: int = CAUSAL_MAX_HOPS,
                 top_k: int = CAUSAL_TOP_K_PATHS,
                 min_score: float = CAUSAL_MIN_PATH_SCORE):
        self.kg = kg
        self.max_hops = max_hops
        self.top_k = top_k
        self.min_score = min_score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def trace_anomaly(self, anomaly_node_id: str) -> List[CausalPath]:
        """
        Trace the root cause of an anomaly starting from the given node.

        Uses a priority-based BFS to explore paths upstream through
        the knowledge graph.

        Args:
            anomaly_node_id: ID of the node where anomaly was detected.

        Returns:
            List of CausalPath objects, sorted by confidence (descending).
        """
        node = self.kg.get_node(anomaly_node_id)
        if node is None:
            logger.warning("Node %s not found in KG.", anomaly_node_id)
            return []

        if not node.is_anomaly:
            logger.info("Node %s is not marked as anomalous.", anomaly_node_id)

        # Priority queue: (-score, hop_count, current_node_id, path, edge_types)
        # Using negative score because heapq is a min-heap
        initial_score = node.anomaly_score if node.anomaly_score > 0 else 1.0
        pq: List[Tuple[float, int, str, List[str], List[EdgeType]]] = [
            (-initial_score, 0, anomaly_node_id, [anomaly_node_id], [])
        ]

        results: List[CausalPath] = []
        visited_paths: Set[str] = set()

        while pq and len(results) < self.top_k * 3:
            neg_score, hops, current, path, edge_types = heapq.heappop(pq)
            score = -neg_score

            path_key = "→".join(path)
            if path_key in visited_paths:
                continue
            visited_paths.add(path_key)

            # If we've reached max hops or found a root-cause candidate
            if hops >= self.max_hops:
                if score >= self.min_score:
                    results.append(CausalPath(
                        path=list(path),
                        edge_types=list(edge_types),
                        confidence=score,
                        hop_count=hops,
                        description=self._describe_path(path),
                    ))
                continue

            # Check if current node is a root-cause candidate
            # Root causes are typically work_type or category level nodes
            current_node = self.kg.get_node(current)
            if current_node and hops > 0:
                if current_node.node_type in (NodeType.WORK_TYPE, NodeType.DATA_CATEGORY):
                    # Reached a high-level node — potential root cause
                    if score >= self.min_score:
                        results.append(CausalPath(
                            path=list(path),
                            edge_types=list(edge_types),
                            confidence=score,
                            hop_count=hops,
                            description=self._describe_path(path),
                        ))
                    continue

            # Expand: follow parent edges (upstream), coupling edges, etc.
            neighbors = self._get_upstream_neighbors(current)
            for neighbor_id, edge_type, edge_weight in neighbors:
                if neighbor_id in path:  # avoid cycles
                    continue

                neighbor_node = self.kg.get_node(neighbor_id)
                # Boost score if neighbor is also anomalous
                anomaly_boost = 0.0
                if neighbor_node and neighbor_node.is_anomaly:
                    anomaly_boost = 0.2

                # Decay score per hop and by edge weight
                new_score = (score + anomaly_boost) * edge_weight * 0.9

                if new_score >= self.min_score:
                    heapq.heappush(
                        pq,
                        (
                            -new_score,
                            hops + 1,
                            neighbor_id,
                            path + [neighbor_id],
                            edge_types + [edge_type],
                        ),
                    )

        # Deduplicate and sort
        results = self._deduplicate_paths(results)
        results.sort(key=lambda p: p.confidence, reverse=True)

        logger.info(
            "Traced anomaly from %s: found %d causal paths.",
            anomaly_node_id, len(results),
        )
        return results[:self.top_k]

    def trace_batch_anomalies(self, anomaly_node_ids: List[str]) -> Dict[str, List[CausalPath]]:
        """
        Trace anomalies for multiple nodes.

        Returns:
            Dict mapping anomaly_node_id → list of CausalPath.
        """
        results = {}
        for nid in anomaly_node_ids:
            paths = self.trace_anomaly(nid)
            if paths:
                results[nid] = paths
        return results

    def build_anomaly_propagation_graph(self, anomaly_node_ids: List[str]):
        """
        After tracing, add anomaly propagation edges to the KG
        for visualization purposes.
        """
        # Clear previous propagation edges
        G = self.kg.nx_graph
        edges_to_remove = [
            (u, v) for u, v, d in G.edges(data=True)
            if d.get("edge_type") == EdgeType.ANOMALY_PROPAGATION.value
        ]
        G.remove_edges_from(edges_to_remove)

        all_paths = self.trace_batch_anomalies(anomaly_node_ids)
        for nid, paths in all_paths.items():
            for path_obj in paths:
                for i in range(len(path_obj.path) - 1):
                    src = path_obj.path[i]
                    dst = path_obj.path[i + 1]
                    confidence = path_obj.confidence * (0.9 ** i)
                    self.kg.add_anomaly_propagation_edge(
                        src, dst, confidence, hop=i
                    )

        logger.info("Built anomaly propagation graph with %d traced paths.",
                     sum(len(p) for p in all_paths.values()))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _get_upstream_neighbors(self, node_id: str) -> List[Tuple[str, EdgeType, float]]:
        """
        Get upstream (incoming) neighbors with edge types and weights.
        Prioritizes anomaly propagation > process coupling > hierarchical > cross_level.
        """
        neighbors = []
        G = self.kg.nx_graph

        # Edge type priority mapping (higher = more important for causal reasoning)
        priority_map = {
            EdgeType.ANOMALY_PROPAGATION.value: 1.0,
            EdgeType.PROCESS_COUPLING.value: 0.8,
            EdgeType.HIERARCHICAL.value: 0.6,
            EdgeType.CROSS_LEVEL.value: 0.4,
        }

        for src, _, data in G.in_edges(node_id, data=True):
            et = data.get("edge_type", EdgeType.HIERARCHICAL.value)
            weight = data.get("weight", 1.0)
            priority = priority_map.get(et, 0.3)
            combined_weight = weight * priority
            try:
                edge_type = EdgeType(et)
            except ValueError:
                edge_type = EdgeType.HIERARCHICAL
            neighbors.append((src, edge_type, combined_weight))

        # Also follow outgoing coupling edges (bidirectional for coupling)
        for _, dst, data in G.out_edges(node_id, data=True):
            et = data.get("edge_type", "")
            if et == EdgeType.PROCESS_COUPLING.value:
                weight = data.get("weight", 1.0)
                neighbors.append((dst, EdgeType.PROCESS_COUPLING, weight * 0.8))

        return neighbors

    def _describe_path(self, path: List[str]) -> str:
        """Generate a human-readable description of a causal path."""
        descriptions = []
        for nid in path:
            node = self.kg.get_node(nid)
            if node:
                descriptions.append(f"{node.name_en}")
            else:
                descriptions.append(nid)
        return " → ".join(descriptions)

    def _deduplicate_paths(self, paths: List[CausalPath]) -> List[CausalPath]:
        """Remove duplicate paths (same endpoint, similar route)."""
        seen_endpoints: Dict[str, CausalPath] = {}
        for path in paths:
            endpoint = path.path[-1]
            if endpoint not in seen_endpoints or path.confidence > seen_endpoints[endpoint].confidence:
                seen_endpoints[endpoint] = path
        return list(seen_endpoints.values())
