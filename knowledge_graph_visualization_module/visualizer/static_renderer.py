"""
Static Renderer: generates matplotlib-based visualizations of the
knowledge graph.

Supports:
  - Full hierarchy overview
  - Per-work-type sub-graph
  - Per-data-pool sub-graph
  - Anomaly highlight visualization
  - Discovered edges highlight
  - Causal path visualization
"""

import os
import logging
from typing import Dict, List, Optional, Set, Any

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, EdgeType
from ..config import (
    NODE_COLORS, EDGE_COLORS, NODE_SIZES,
    STATIC_FIG_SIZE, STATIC_DPI, OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


class StaticRenderer:
    """
    Renders static knowledge graph visualizations using matplotlib.
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 output_dir: Optional[str] = None,
                 fig_size: tuple = STATIC_FIG_SIZE,
                 dpi: int = STATIC_DPI):
        self.kg = kg
        self.output_dir = output_dir or OUTPUT_DIR
        self.fig_size = fig_size
        self.dpi = dpi
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render_hierarchy_overview(self, filename: str = "hierarchy_overview.png",
                                   title: str = "GenBFKit Knowledge Graph - Hierarchy Overview"):
        """
        Render the full 5-level hierarchy overview.

        Strategy: For the full graph (2327+ nodes), we render work_type → category → pool
        as the primary view, with dataset counts as labels.
        """
        G = self.kg.nx_graph

        # Build a simplified graph for the overview
        # Only show: work_type, category, pool nodes
        simple_nodes = set()
        for nid in G.nodes():
            nt = G.nodes[nid].get("node_type", "")
            if nt in (NodeType.WORK_TYPE.value, NodeType.DATA_CATEGORY.value, NodeType.DATA_POOL.value):
                simple_nodes.add(nid)

        sub_G = G.subgraph(simple_nodes).copy()

        fig, ax = plt.subplots(1, 1, figsize=self.fig_size, dpi=self.dpi)
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")

        # Layout
        pos = self._hierarchical_layout(sub_G)

        # Draw nodes by type
        for nt, color in NODE_COLORS.items():
            if nt == NodeType.DATASET.value or nt == NodeType.DATA_ATTRIBUTE.value:
                continue
            nodelist = [
                n for n in sub_G.nodes()
                if sub_G.nodes[n].get("node_type") == nt
            ]
            if not nodelist:
                continue

            node_size = NODE_SIZES.get(nt, 300)
            labels = {
                n: self._truncate_label(sub_G.nodes[n].get("name_en", n), max_len=25)
                for n in nodelist
            }

            nx.draw_networkx_nodes(
                sub_G, pos, nodelist=nodelist,
                node_color=color, node_size=node_size,
                alpha=0.9, ax=ax, edgecolors="white", linewidths=0.5,
            )
            nx.draw_networkx_labels(
                sub_G, pos, labels=labels,
                font_size=6, font_color="white", ax=ax,
            )

        # Draw edges
        nx.draw_networkx_edges(
            sub_G, pos, alpha=0.3, edge_color="#6C757D",
            arrows=True, arrowsize=8, ax=ax, width=0.5,
        )

        # Add dataset count annotations
        for nid in simple_nodes:
            nt = G.nodes[nid].get("node_type", "")
            if nt == NodeType.DATA_CATEGORY.value:
                ds_count = len(self.kg.get_children(nid, EdgeType.HIERARCHICAL))
                if ds_count > 0 and nid in pos:
                    ax.annotate(
                        f"({ds_count} params)",
                        xy=pos[nid],
                        xytext=(0, -12),
                        textcoords="offset points",
                        fontsize=5, color="#ADB5BD",
                        ha="center",
                    )

        # Legend
        legend_patches = [
            mpatches.Patch(color=NODE_COLORS[NodeType.WORK_TYPE.value], label="Work Type (8)"),
            mpatches.Patch(color=NODE_COLORS[NodeType.DATA_CATEGORY.value], label="Data Category (98)"),
            mpatches.Patch(color=NODE_COLORS[NodeType.DATA_POOL.value], label="Data Pool (9)"),
        ]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=8,
                  facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

        ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=20)
        ax.axis("off")

        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info("Saved hierarchy overview to %s", filepath)
        return filepath

    def render_work_type_subgraph(self, work_type_id: str,
                                   filename: Optional[str] = None):
        """
        Render a sub-graph for a specific work type, showing
        categories → datasets → pools.
        """
        sub_kg = self.kg.get_subgraph_by_work_type(work_type_id)
        node = self.kg.get_node(work_type_id)
        wt_name = node.name_en if node else work_type_id

        fname = filename or f"subgraph_{wt_name.replace(' ', '_').replace('&', 'and')}.png"
        title = f"Knowledge Graph - {wt_name}"

        return self._render_subgraph(sub_kg, fname, title)

    def render_pool_subgraph(self, pool_id: str,
                              filename: Optional[str] = None):
        """Render a sub-graph for datasets in a specific data pool."""
        sub_kg = self.kg.get_subgraph_by_pool(pool_id)
        node = self.kg.get_node(pool_id)
        pool_name = node.name_en if node else pool_id

        fname = filename or f"pool_{pool_name.replace(' ', '_')}.png"
        title = f"Knowledge Graph - Pool: {pool_name}"

        return self._render_subgraph(sub_kg, fname, title)

    def render_anomaly_highlight(self, anomaly_node_ids: List[str],
                                  filename: str = "anomaly_highlight.png"):
        """
        Render the graph with anomalous nodes highlighted in red,
        showing their neighborhood context.
        """
        # Collect anomaly nodes + their 2-hop neighborhood
        focus_nodes = set(anomaly_node_ids)
        G = self.kg.nx_graph
        for nid in anomaly_node_ids:
            focus_nodes.update(nx.single_source_shortest_path_length(G, nid, cutoff=2).keys())

        sub_G = G.subgraph(focus_nodes).copy()

        fig, ax = plt.subplots(1, 1, figsize=self.fig_size, dpi=self.dpi)
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")

        pos = nx.spring_layout(sub_G, k=2.0, iterations=50, seed=42)

        # Normal nodes
        normal_nodes = [n for n in sub_G.nodes() if n not in anomaly_node_ids]
        nx.draw_networkx_nodes(
            sub_G, pos, nodelist=normal_nodes,
            node_color="#457B9D", node_size=200,
            alpha=0.6, ax=ax,
        )

        # Anomaly nodes (highlighted)
        anomaly_colors = []
        for nid in anomaly_node_ids:
            ndata = G.nodes.get(nid, {})
            score = ndata.get("anomaly_score", 1.0)
            anomaly_colors.append(plt.cm.Reds(0.4 + 0.6 * min(score, 1.0)))

        nx.draw_networkx_nodes(
            sub_G, pos, nodelist=anomaly_node_ids,
            node_color=anomaly_colors, node_size=600,
            alpha=1.0, ax=ax, edgecolors="#FF0000", linewidths=2,
        )

        # Labels for anomaly nodes
        labels = {}
        for nid in anomaly_node_ids:
            node = self.kg.get_node(nid)
            if node:
                labels[nid] = self._truncate_label(node.name_en, 20)
        nx.draw_networkx_labels(sub_G, pos, labels=labels, font_size=7,
                                font_color="yellow", ax=ax)

        # Edges
        nx.draw_networkx_edges(sub_G, pos, alpha=0.3, edge_color="#6C757D",
                                arrows=True, ax=ax, width=0.5)

        # Anomaly propagation edges in red
        prop_edges = [
            (u, v) for u, v, d in sub_G.edges(data=True)
            if d.get("edge_type") == EdgeType.ANOMALY_PROPAGATION.value
        ]
        if prop_edges:
            nx.draw_networkx_edges(
                sub_G, pos, edgelist=prop_edges,
                edge_color="#D00000", width=2.0, arrows=True,
                arrowsize=15, ax=ax, style="dashed",
            )

        ax.set_title("Anomaly Traceability - Knowledge Graph", color="white",
                      fontsize=14, fontweight="bold")
        ax.axis("off")

        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info("Saved anomaly highlight to %s", filepath)
        return filepath

    def render_discovered_edges(self, filename: str = "discovered_edges.png"):
        """
        Render the graph with GAT-discovered edges highlighted.
        Shows a focused view around discovered process couplings.
        """
        discovered = self.kg.get_discovered_edges()
        if not discovered:
            logger.info("No discovered edges to render.")
            return None

        # Collect nodes involved in discoveries + their neighbors
        focus_nodes = set()
        G = self.kg.nx_graph
        for src, dst, _ in discovered:
            focus_nodes.add(src)
            focus_nodes.add(dst)
            # Add their categories and work types for context
            for nid in [src, dst]:
                focus_nodes.update(nx.single_source_shortest_path_length(G, nid, cutoff=1).keys())

        # Limit to manageable size
        if len(focus_nodes) > 200:
            # Keep only discovery endpoints + their direct parents
            core_nodes = set()
            for src, dst, _ in discovered:
                core_nodes.add(src)
                core_nodes.add(dst)
                for nid in [src, dst]:
                    parents = self.kg.get_parents(nid, EdgeType.HIERARCHICAL)
                    core_nodes.update(parents[:2])
            focus_nodes = core_nodes

        sub_G = G.subgraph(focus_nodes).copy()

        fig, ax = plt.subplots(1, 1, figsize=self.fig_size, dpi=self.dpi)
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")

        pos = nx.spring_layout(sub_G, k=1.5, iterations=50, seed=42)

        # Draw all nodes
        nx.draw_networkx_nodes(sub_G, pos, node_color="#457B9D",
                                node_size=150, alpha=0.6, ax=ax)

        # Draw normal edges
        normal_edges = [
            (u, v) for u, v, d in sub_G.edges(data=True)
            if d.get("edge_type") != EdgeType.PROCESS_COUPLING.value
        ]
        nx.draw_networkx_edges(sub_G, pos, edgelist=normal_edges,
                                alpha=0.2, edge_color="#6C757D",
                                arrows=True, ax=ax, width=0.3)

        # Draw discovered edges (highlighted)
        disc_edges_in_subgraph = [
            (u, v) for u, v, _ in discovered if u in focus_nodes and v in focus_nodes
        ]
        if disc_edges_in_subgraph:
            nx.draw_networkx_edges(
                sub_G, pos, edgelist=disc_edges_in_subgraph,
                edge_color="#FF6B35", width=2.0, arrows=False,
                style="dashed", alpha=0.9, ax=ax,
            )

        # Labels for discovery endpoints
        labels = {}
        for src, dst, _ in discovered:
            for nid in [src, dst]:
                node = self.kg.get_node(nid)
                if node and nid in pos:
                    labels[nid] = self._truncate_label(node.name_en, 18)
        nx.draw_networkx_labels(sub_G, pos, labels=labels, font_size=6,
                                font_color="#FF6B35", ax=ax)

        legend_patches = [
            mpatches.Patch(color="#457B9D", label="Existing nodes"),
            mpatches.Patch(color="#FF6B35", label="GAT-discovered coupling"),
        ]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=8,
                  facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

        ax.set_title("GAT-Discovered Hidden Process Couplings", color="white",
                      fontsize=14, fontweight="bold")
        ax.axis("off")

        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info("Saved discovered edges to %s", filepath)
        return filepath

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _render_subgraph(self, sub_kg: BlastFurnaceKnowledgeGraph,
                          filename: str, title: str):
        """Generic sub-graph renderer."""
        G = sub_kg.nx_graph

        fig, ax = plt.subplots(1, 1, figsize=self.fig_size, dpi=self.dpi)
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")

        # For large sub-graphs, use spring layout; otherwise hierarchical
        if G.number_of_nodes() < 50:
            pos = self._hierarchical_layout(G)
        else:
            pos = nx.spring_layout(G, k=1.5, iterations=80, seed=42)

        # Draw nodes by type
        for nt, color in NODE_COLORS.items():
            nodelist = [
                n for n in G.nodes()
                if G.nodes[n].get("node_type") == nt
            ]
            if not nodelist:
                continue

            node_size = NODE_SIZES.get(nt, 200)
            # Scale down for large sub-graphs
            if G.number_of_nodes() > 100:
                node_size = max(node_size // 3, 30)

            labels = {}
            for n in nodelist:
                name = G.nodes[n].get("name_en", n)
                labels[n] = self._truncate_label(name, 20)

            nx.draw_networkx_nodes(
                G, pos, nodelist=nodelist,
                node_color=color, node_size=node_size,
                alpha=0.85, ax=ax, edgecolors="white", linewidths=0.3,
            )

            # Only show labels for fewer nodes
            if len(nodelist) < 30:
                nx.draw_networkx_labels(
                    G, pos, labels=labels,
                    font_size=5, font_color="white", ax=ax,
                )

        # Draw edges by type
        for et, color in EDGE_COLORS.items():
            edgelist = [
                (u, v) for u, v, d in G.edges(data=True)
                if d.get("edge_type") == et
            ]
            if edgelist:
                width = 1.5 if et == EdgeType.PROCESS_COUPLING.value else 0.5
                style = "dashed" if et == EdgeType.PROCESS_COUPLING.value else "solid"
                nx.draw_networkx_edges(
                    G, pos, edgelist=edgelist,
                    edge_color=color, width=width,
                    style=style, alpha=0.5,
                    arrows=True, arrowsize=8, ax=ax,
                )

        ax.set_title(title, color="white", fontsize=14, fontweight="bold")
        ax.axis("off")

        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info("Saved sub-graph to %s", filepath)
        return filepath

    def _hierarchical_layout(self, G: nx.DiGraph) -> Dict[str, np.ndarray]:
        """
        Create a hierarchical layout where nodes are positioned by level
        (top = work_type, bottom = attribute).
        """
        level_groups: Dict[int, List[str]] = {}
        for nid in G.nodes():
            level = G.nodes[nid].get("level", 0)
            level_groups.setdefault(level, []).append(nid)

        max_level = max(level_groups.keys()) if level_groups else 0
        pos = {}

        for level, nodes in level_groups.items():
            y = 1.0 - (level / max(max_level, 1))
            n = len(nodes)
            for i, nid in enumerate(nodes):
                x = (i + 0.5) / max(n, 1)
                pos[nid] = np.array([x, y])

        return pos

    @staticmethod
    def _truncate_label(label: str, max_len: int = 20) -> str:
        if len(label) <= max_len:
            return label
        return label[:max_len - 2] + ".."
