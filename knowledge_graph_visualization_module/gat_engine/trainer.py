"""
GAT Trainer: trains the sparse GAT link prediction model on the knowledge graph,
then uses learned embeddings to discover hidden process coupling relationships.

Uses edge-list-based sparse GAT for efficiency on large graphs (2000+ nodes).
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, EdgeType, GATDiscoveryResult
from .model import SparseGATLinkPredictionModel
from ..config import (
    GAT_NUM_HEADS, GAT_HIDDEN_DIM, GAT_NUM_EPOCHS,
    GAT_LEARNING_RATE, GAT_NEG_SAMPLE_RATIO, GAT_DROPOUT,
    GAT_DISCOVERY_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Efficiency caps
_MAX_TRAIN_EDGES = 3000
_MAX_CANDIDATES = 2000
_MINI_BATCH_SIZE = 512


class GATTrainer:
    """
    Trains a sparse GAT model on the knowledge graph and discovers
    hidden process coupling relationships.
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 num_heads: int = GAT_NUM_HEADS,
                 hidden_dim: int = GAT_HIDDEN_DIM,
                 num_epochs: int = GAT_NUM_EPOCHS,
                 lr: float = GAT_LEARNING_RATE,
                 neg_ratio: float = GAT_NEG_SAMPLE_RATIO,
                 dropout: float = GAT_DROPOUT,
                 threshold: float = GAT_DISCOVERY_THRESHOLD,
                 device: Optional[str] = None):
        self.kg = kg
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim
        self.num_epochs = num_epochs
        self.lr = lr
        self.neg_ratio = neg_ratio
        self.dropout = dropout
        self.threshold = threshold

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self._node_id_to_idx: Dict[str, int] = {}
        self._idx_to_node_id: Dict[int, str] = {}
        self.model: Optional[SparseGATLinkPredictionModel] = None
        self.node_features: Optional[torch.Tensor] = None
        self.edge_index: Optional[torch.Tensor] = None  # Sparse edge list
        self._is_trained = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train(self) -> Dict[str, Any]:
        """Train the GAT model on the knowledge graph."""
        self._prepare_data()
        self._build_model()
        return self._train_loop()

    def discover_hidden_relations(self) -> List[GATDiscoveryResult]:
        """
        After training, predict potential edges between candidate
        node pairs and return those above the discovery threshold.
        """
        if not self._is_trained:
            logger.warning("Model not trained yet. Call train() first.")
            return []

        self.model.eval()

        # Get embeddings
        with torch.no_grad():
            embeddings = self.model.get_embeddings(
                self.node_features.to(self.device),
                self.edge_index.to(self.device),
            ).cpu()

        # Identify candidate pairs (dataset nodes not directly connected)
        dataset_nodes = self.kg.get_nodes_by_type(NodeType.DATASET)
        ds_indices = [
            self._node_id_to_idx[n.node_id]
            for n in dataset_nodes
            if n.node_id in self._node_id_to_idx
        ]

        existing_edges = set()
        G = self.kg.nx_graph
        for u, v in G.edges():
            existing_edges.add((u, v))
            existing_edges.add((v, u))

        # Sample candidate pairs
        candidates = []
        rng = np.random.RandomState(42)
        n_candidates = min(_MAX_CANDIDATES, len(ds_indices) * 5)
        attempts = 0

        while len(candidates) < n_candidates and attempts < n_candidates * 5:
            attempts += 1
            i, j = rng.randint(0, len(ds_indices), size=2)
            if i == j:
                continue
            src_id = self._idx_to_node_id[ds_indices[i]]
            dst_id = self._idx_to_node_id[ds_indices[j]]
            if (src_id, dst_id) not in existing_edges:
                candidates.append((ds_indices[i], ds_indices[j]))

        if not candidates:
            return []

        # Batch predict using embedding dot products (fast)
        src_embs = embeddings[torch.tensor([c[0] for c in candidates])]
        dst_embs = embeddings[torch.tensor([c[1] for c in candidates])]
        scores = torch.sigmoid(torch.sum(src_embs * dst_embs, dim=1)).numpy()

        results = []
        for idx, (si, di) in enumerate(candidates):
            if scores[idx] >= self.threshold:
                src_id = self._idx_to_node_id[si]
                dst_id = self._idx_to_node_id[di]
                src_node = self.kg.get_node(src_id)
                dst_node = self.kg.get_node(dst_id)
                desc = (
                    f"Potential process coupling: {src_node.name_en} ↔ {dst_node.name_en} "
                    f"(attention={scores[idx]:.3f})"
                )
                results.append(GATDiscoveryResult(
                    source_id=src_id,
                    target_id=dst_id,
                    attention_score=float(scores[idx]),
                    edge_type=EdgeType.PROCESS_COUPLING,
                    description=desc,
                ))

        results.sort(key=lambda r: r.attention_score, reverse=True)
        logger.info("GAT discovered %d hidden relations (threshold=%.2f)",
                     len(results), self.threshold)
        return results

    def inject_discoveries(self, discoveries: Optional[List[GATDiscoveryResult]] = None):
        """Add discovered edges into the knowledge graph."""
        if discoveries is None:
            discoveries = self.discover_hidden_relations()
        for disc in discoveries:
            self.kg.add_discovered_edge(
                disc.source_id, disc.target_id,
                disc.attention_score, disc.description,
            )
        logger.info("Injected %d discovered edges into the KG.", len(discoveries))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _prepare_data(self):
        """Build node features, edge index, and training samples."""
        G = self.kg.nx_graph
        nodes = sorted(G.nodes())
        N = len(nodes)

        self._node_id_to_idx = {nid: i for i, nid in enumerate(nodes)}
        self._idx_to_node_id = {i: nid for i, nid in enumerate(nodes)}

        # ---- Node features ----
        level_map = {nt.value: i for i, nt in enumerate(NodeType)}
        features = np.zeros((N, len(NodeType) + 3), dtype=np.float32)

        for nid in nodes:
            idx = self._node_id_to_idx[nid]
            ndata = G.nodes[nid]
            nt_str = ndata.get("node_type", "dataset")
            level = ndata.get("level", 3)

            if nt_str in level_map:
                features[idx, level_map[nt_str]] = 1.0
            features[idx, len(NodeType)] = min(G.in_degree(nid), 50) / 50.0
            features[idx, len(NodeType) + 1] = min(G.out_degree(nid), 50) / 50.0
            features[idx, len(NodeType) + 2] = level / 4.0

        self.node_features = torch.tensor(features, dtype=torch.float32)

        # ---- Edge index (sparse, for GAT attention) ----
        # Include all structural edges (hierarchical + cross-level)
        # Also add self-loops
        src_list = []
        dst_list = []
        for u, v, d in G.edges(data=True):
            et = d.get("edge_type", "")
            if et in (EdgeType.HIERARCHICAL.value, EdgeType.CROSS_LEVEL.value,
                      EdgeType.PROCESS_COUPLING.value):
                ui, vi = self._node_id_to_idx[u], self._node_id_to_idx[v]
                src_list.extend([ui, vi])  # Bidirectional for attention
                dst_list.extend([vi, ui])

        # Add self-loops
        for i in range(N):
            src_list.append(i)
            dst_list.append(i)

        self.edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)

        # ---- Positive / negative edge samples (for link prediction training) ----
        pos_edges = []
        for u, v, d in G.edges(data=True):
            et = d.get("edge_type", "")
            if et in (EdgeType.HIERARCHICAL.value, EdgeType.CROSS_LEVEL.value):
                ui, vi = self._node_id_to_idx[u], self._node_id_to_idx[v]
                pos_edges.append((ui, vi))

        # Cap positive edges
        if len(pos_edges) > _MAX_TRAIN_EDGES // 2:
            rng = np.random.RandomState(42)
            indices = rng.choice(len(pos_edges), size=_MAX_TRAIN_EDGES // 2, replace=False)
            pos_edges = [pos_edges[i] for i in indices]

        # Negative edges
        n_neg = min(int(len(pos_edges) * self.neg_ratio), _MAX_TRAIN_EDGES // 2)
        adj_set = set()
        for u, v in G.edges():
            adj_set.add((self._node_id_to_idx[u], self._node_id_to_idx[v]))

        neg_edges = []
        rng = np.random.RandomState(43)
        attempts = 0
        while len(neg_edges) < n_neg and attempts < n_neg * 10:
            attempts += 1
            i, j = rng.randint(0, N), rng.randint(0, N)
            if i != j and (int(i), int(j)) not in adj_set:
                neg_edges.append((int(i), int(j)))

        self._pos_edges = pos_edges
        self._neg_edges = neg_edges

        logger.info("Data prepared: %d nodes, %d graph edges, %d pos, %d neg train edges",
                     N, self.edge_index.size(1), len(pos_edges), len(neg_edges))

    def _build_model(self):
        in_features = self.node_features.size(1)
        self.model = SparseGATLinkPredictionModel(
            in_features=in_features,
            hidden_features=self.hidden_dim,
            out_features=16,
            num_heads=self.num_heads,
            dropout=self.dropout,
        ).to(self.device)

    def _train_loop(self) -> Dict[str, Any]:
        """Training loop with BCE loss and mini-batch processing."""
        pos = self._pos_edges
        neg = self._neg_edges

        all_edges = pos + neg
        labels = [1.0] * len(pos) + [0.0] * len(neg)

        edge_index = torch.tensor(all_edges, dtype=torch.long).T  # (2, E)
        labels_t = torch.tensor(labels, dtype=torch.float32)

        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.BCELoss()

        history = {"losses": []}
        self.model.train()

        n_samples = edge_index.size(1)
        batch_size = _MINI_BATCH_SIZE

        for epoch in range(self.num_epochs):
            perm = torch.randperm(n_samples)
            edge_shuffled = edge_index[:, perm]
            labels_shuffled = labels_t[perm]

            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_edges = edge_shuffled[:, start:end].to(self.device)
                batch_labels = labels_shuffled[start:end].to(self.device)

                optimizer.zero_grad()
                scores = self.model(
                    self.node_features.to(self.device),
                    self.edge_index.to(self.device),
                    batch_edges,
                )
                loss = criterion(scores, batch_labels)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / max(n_batches, 1)
            history["losses"].append(avg_loss)

            if (epoch + 1) % 50 == 0:
                logger.info("Epoch %d/%d  Loss: %.4f", epoch + 1, self.num_epochs, avg_loss)

        self._is_trained = True
        logger.info("Training complete. Final loss: %.4f", history["losses"][-1])
        return history
