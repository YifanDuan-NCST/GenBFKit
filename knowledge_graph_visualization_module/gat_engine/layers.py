"""
Graph Attention Network (GAT) layer implementation — Sparse version.

Uses edge-list-based attention computation instead of dense N×N matrix,
making it efficient for large sparse graphs (2000+ nodes).

Reference: "Graph Attention Networks" — Veličković et al., ICLR 2018
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


class SparseGATLayer(nn.Module):
    """
    Sparse Graph Attention Network layer.

    Instead of computing attention over all N×N pairs, only computes
    attention for edges that exist (given by edge_index).

    Complexity: O(|E|) instead of O(N²)
    """

    def __init__(self, in_features: int, out_features: int,
                 dropout: float = 0.2, alpha: float = 0.2, concat: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = dropout
        self.alpha = alpha
        self.concat = concat

        # Learnable parameters
        self.W = nn.Parameter(torch.empty(in_features, out_features))
        self.a_src = nn.Parameter(torch.empty(out_features, 1))
        self.a_dst = nn.Parameter(torch.empty(out_features, 1))

        self.leaky_relu = nn.LeakyReLU(alpha)
        self._init_params()

    def _init_params(self):
        nn.init.xavier_uniform_(self.W)
        nn.init.xavier_uniform_(self.a_src)
        nn.init.xavier_uniform_(self.a_dst)

    def forward(self, h: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h:           Node feature matrix, shape (N, in_features).
            edge_index:  Edge list, shape (2, E) where E is number of edges.
                         edge_index[0] = source, edge_index[1] = target.

        Returns:
            Updated node embeddings, shape (N, out_features).
        """
        N = h.size(0)

        # Linear transform
        Wh = torch.mm(h, self.W)  # (N, out_features)

        # Compute attention scores for edges only
        # e_ij = LeakyReLU(a_src^T * Wh_i + a_dst^T * Wh_j)
        src, dst = edge_index[0], edge_index[1]

        # Attention coefficients
        e_src = (Wh[src] @ self.a_src).squeeze(-1)  # (E,)
        e_dst = (Wh[dst] @ self.a_dst).squeeze(-1)  # (E,)
        e = self.leaky_relu(e_src + e_dst)  # (E,)

        # Softmax per target node (numerically stable)
        # Group by destination node
        e_max = torch.full((N,), -1e10, device=h.device)
        e_max.scatter_reduce_(0, dst, e, reduce="amax", include_self=True)
        e_exp = torch.exp(e - e_max[dst])

        # Sum of exp per destination
        e_sum = torch.zeros(N, device=h.device)
        e_sum.scatter_add_(0, dst, e_exp)

        # Normalized attention
        alpha = e_exp / (e_sum[dst] + 1e-16)  # (E,)
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)

        # Aggregate: weighted sum of neighbor features
        out = torch.zeros(N, self.out_features, device=h.device)
        weighted_features = alpha.unsqueeze(-1) * Wh[src]  # (E, out_features)
        out.scatter_add_(0, dst.unsqueeze(-1).expand_as(weighted_features), weighted_features)

        if self.concat:
            return F.elu(out)
        return out

    def __repr__(self):
        return f"{self.__class__.__name__}({self.in_features} -> {self.out_features})"


class MultiHeadSparseGATLayer(nn.Module):
    """
    Multi-head sparse GAT layer.
    """

    def __init__(self, in_features: int, out_features: int,
                 num_heads: int = 4, dropout: float = 0.2,
                 alpha: float = 0.2, concat: bool = True):
        super().__init__()
        self.num_heads = num_heads
        self.concat = concat
        self.out_features = out_features

        self.heads = nn.ModuleList([
            SparseGATLayer(in_features, out_features, dropout, alpha, concat=True)
            for _ in range(num_heads)
        ])

    def forward(self, h: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        head_outputs = [head(h, edge_index) for head in self.heads]
        if self.concat:
            return torch.cat(head_outputs, dim=1)
        else:
            return torch.mean(torch.stack(head_outputs), dim=0)


class SparseGATBody(nn.Module):
    """
    Two-layer sparse GAT model for knowledge graph embedding.
    """

    def __init__(self, in_features: int, hidden_features: int,
                 out_features: int, num_heads: int = 4,
                 dropout: float = 0.2, alpha: float = 0.2):
        super().__init__()
        self.dropout = dropout

        self.layer1 = MultiHeadSparseGATLayer(
            in_features, hidden_features,
            num_heads=num_heads, dropout=dropout, alpha=alpha, concat=True
        )

        self.layer2 = MultiHeadSparseGATLayer(
            hidden_features * num_heads, out_features,
            num_heads=1, dropout=dropout, alpha=alpha, concat=False
        )

    def forward(self, h: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.layer1(h, edge_index)
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.layer2(h, edge_index)
        return h
