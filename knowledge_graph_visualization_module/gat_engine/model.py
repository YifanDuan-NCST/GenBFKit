"""
GAT Model for Knowledge Graph Completion & Link Prediction — Sparse version.

Uses edge-list-based sparse GAT for efficient computation on large graphs.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional

from .layers import SparseGATBody


class LinkPredictor(nn.Module):
    """
    Bilinear dot-product link predictor.

    Given node embeddings h_i and h_j, the score of edge (i,j) is:
        score(i,j) = sigmoid( h_i^T * h_j )
    """

    def __init__(self, embedding_dim: int):
        super().__init__()
        self.R = nn.Parameter(torch.eye(embedding_dim))

    def forward(self, h_i: torch.Tensor, h_j: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h_i: (batch, dim)
            h_j: (batch, dim)

        Returns:
            (batch,) — probability scores for each edge
        """
        scores = torch.sigmoid(
            torch.sum(h_i * (h_j @ self.R.T), dim=1)
        )
        return scores


class SparseGATLinkPredictionModel(nn.Module):
    """
    End-to-end sparse GAT-based link prediction model.
    Uses edge-list-based attention for efficiency on large sparse graphs.
    """

    def __init__(self, in_features: int, hidden_features: int,
                 out_features: int, num_heads: int = 4,
                 dropout: float = 0.2):
        super().__init__()
        self.gat = SparseGATBody(
            in_features=in_features,
            hidden_features=hidden_features,
            out_features=out_features,
            num_heads=num_heads,
            dropout=dropout,
        )
        self.predictor = LinkPredictor(out_features)

    def forward(self, h: torch.Tensor, edge_index: torch.Tensor,
                pred_edge_index: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h:               (N, in_features) — node features
            edge_index:      (2, E) — graph edges for GAT attention
            pred_edge_index: (2, batch) — pairs of node indices to score

        Returns:
            (batch,) — probability scores
        """
        embeddings = self.gat(h, edge_index)  # (N, out_features)
        src_emb = embeddings[pred_edge_index[0]]
        dst_emb = embeddings[pred_edge_index[1]]
        scores = self.predictor(src_emb, dst_emb)
        return scores

    def get_embeddings(self, h: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """Get node embeddings without link prediction."""
        return self.gat(h, edge_index)
