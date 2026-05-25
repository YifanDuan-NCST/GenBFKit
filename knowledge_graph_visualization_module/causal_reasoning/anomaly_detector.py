"""
Anomaly Detector: identifies anomalous nodes in the knowledge graph
based on statistical properties and graph topology.

For blast furnace scenarios, anomaly detection leverages:
  1. Statistical outliers (3σ rule on time-series data)
  2. Graph-structural anomalies (unexpected degree patterns)
  3. Cross-parameter correlation breaks
"""

import logging
from typing import Dict, List, Optional, Any

import numpy as np

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, GraphNode
from ..config import CAUSAL_ANOMALY_ZSCORE_THRESHOLD

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalous nodes in the knowledge graph.

    In production, this would ingest real-time sensor data.
    Here, we support:
      - Manual marking (via mark_anomaly)
      - Statistical detection from simulated/virtual data
      - Graph-structural anomaly scoring
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 z_threshold: float = CAUSAL_ANOMALY_ZSCORE_THRESHOLD):
        self.kg = kg
        self.z_threshold = z_threshold

    def detect_from_data(self, param_data: Dict[str, List[float]]) -> List[str]:
        """
        Detect anomalous parameters from time-series data using 3σ rule.

        Args:
            param_data: Mapping from dataset node_id → list of float values.

        Returns:
            List of node IDs flagged as anomalous.
        """
        anomalous = []
        for node_id, values in param_data.items():
            if not values:
                continue
            arr = np.array(values, dtype=np.float64)
            mean = np.nanmean(arr)
            std = np.nanstd(arr)
            if std < 1e-10:
                continue

            # Check the latest value
            latest = arr[-1]
            z_score = abs((latest - mean) / std)

            if z_score > self.z_threshold:
                score = min(z_score / 5.0, 1.0)  # normalize to [0, 1]
                self.kg.mark_anomaly(node_id, score)
                anomalous.append(node_id)

        logger.info("Detected %d anomalous nodes from data.", len(anomalous))
        return anomalous

    def detect_structural_anomalies(self) -> List[str]:
        """
        Detect graph-structural anomalies based on degree distribution.

        Nodes with unusually high or low degree (relative to their type)
        are flagged.
        """
        G = self.kg.nx_graph
        anomalous = []

        # Compute degree statistics per node type
        type_degrees: Dict[str, List[int]] = {}
        for nid in G.nodes():
            nt = G.nodes[nid].get("node_type", "unknown")
            type_degrees.setdefault(nt, []).append(G.degree(nid))

        type_stats = {}
        for nt, degrees in type_degrees.items():
            arr = np.array(degrees, dtype=np.float64)
            type_stats[nt] = {
                "mean": np.mean(arr),
                "std": np.std(arr),
            }

        for nid in G.nodes():
            nt = G.nodes[nid].get("node_type", "unknown")
            deg = G.degree(nid)
            stats = type_stats.get(nt)
            if stats and stats["std"] > 1e-10:
                z = abs((deg - stats["mean"]) / stats["std"])
                if z > self.z_threshold:
                    score = min(z / 5.0, 1.0)
                    self.kg.mark_anomaly(nid, score)
                    anomalous.append(nid)

        logger.info("Detected %d structural anomalies.", len(anomalous))
        return anomalous

    def manual_mark(self, node_ids: List[str], score: float = 1.0):
        """Manually mark nodes as anomalous."""
        for nid in node_ids:
            self.kg.mark_anomaly(nid, score)
        logger.info("Manually marked %d nodes as anomalous.", len(node_ids))
