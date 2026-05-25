"""
Interactive Renderer: generates pyvis-based HTML visualizations
with full zoom/pan/click/hover interactivity.

Design principles for large-graph performance:
  - Hierarchy-first: show top levels (WT→CAT→POOL) by default,
    with per-level drill-down pages for deeper exploration.
  - Physics off by default for graphs > 80 nodes (instant layout).
  - Forced pre-computed layout for medium graphs (80–300 nodes).
  - Strict node budget: each page renders at most ~300 nodes.
  - Lightweight tooltips and minimal edge styling.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Set

import networkx as nx
from pyvis.network import Network

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, EdgeType
from ..config import (
    NODE_COLORS, EDGE_COLORS, NODE_SIZES,
    INTERACTIVE_HEIGHT, INTERACTIVE_BG_COLOR, OUTPUT_DIR,
)

logger = logging.getLogger(__name__)

# ── Node-budget thresholds ──────────────────────────────────────────
_PHYSICS_ON_LIMIT = 80       # below this → enable physics simulation
_PRECOMPUTE_LIMIT = 300      # below this → pre-compute layout, no physics
_MAX_RENDER_NODES = 300      # hard cap: never render more than this


class InteractiveRenderer:
    """
    Renders interactive HTML knowledge graph visualizations using PyVis.

    Strategy for 2300+ node knowledge graphs:
      - render_overview():  WT → CAT → POOL only (~115 nodes)
      - render_work_type_subgraph(): single WT subtree (~30–300 nodes)
      - render_pool_subgraph(): single POOL subtree (~50–400 nodes)
      - render_anomaly_trace(): anomaly + 1-hop neighbors (controlled)
      - render_discovered_relations(): discovered endpoints + parents (small)
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 output_dir: Optional[str] = None,
                 height: str = INTERACTIVE_HEIGHT,
                 bg_color: str = INTERACTIVE_BG_COLOR):
        self.kg = kg
        self.output_dir = output_dir or OUTPUT_DIR
        self.height = height
        self.bg_color = bg_color
        os.makedirs(self.output_dir, exist_ok=True)

    # ==================================================================
    # Public API
    # ==================================================================

    def render_full_graph(self, filename: str = "kg_full_interactive.html",
                           title: str = "GenBFKit Knowledge Graph - Overview"):
        """
        Render an overview of the full knowledge graph.
        Only shows top 3 hierarchy levels (Work Type → Data Category → Data Pool)
        to keep the node count manageable for the browser.
        """
        G = self.kg.nx_graph
        display_nodes = set()

        for nid in G.nodes():
            nt = G.nodes[nid].get("node_type", "")
            if nt in (NodeType.WORK_TYPE.value,
                      NodeType.DATA_CATEGORY.value,
                      NodeType.DATA_POOL.value):
                display_nodes.add(nid)

        # Also include anomaly nodes & discovered-edge endpoints at dataset level
        for nid in G.nodes():
            if G.nodes[nid].get("is_anomaly", False):
                display_nodes.add(nid)
        for u, v, _ in self.kg.get_discovered_edges():
            display_nodes.add(u)
            display_nodes.add(v)

        display_G = G.subgraph(display_nodes).copy()
        logger.info("render_full_graph: %d nodes, %d edges",
                     display_G.number_of_nodes(), display_G.number_of_edges())
        return self._render_network(display_G, filename, title)

    def render_work_type_subgraph(self, work_type_id: str,
                                    filename: Optional[str] = None):
        """Render an interactive sub-graph for a specific work type."""
        sub_kg = self.kg.get_subgraph_by_work_type(work_type_id)
        node = self.kg.get_node(work_type_id)
        wt_name = node.name_en if node else work_type_id

        fname = filename or f"kg_{wt_name.replace(' ', '_').replace('&', 'and')}_interactive.html"
        title = f"Knowledge Graph - {wt_name}"

        # If subgraph too large, trim dataset-level to top-N per category
        G = self._trim_if_large(sub_kg.nx_graph, max_nodes=_MAX_RENDER_NODES)
        return self._render_network(G, fname, title)

    def render_pool_subgraph(self, pool_id: str,
                              filename: Optional[str] = None):
        """Render an interactive sub-graph for a specific data pool."""
        sub_kg = self.kg.get_subgraph_by_pool(pool_id)
        node = self.kg.get_node(pool_id)
        pool_name = node.name_en if node else pool_id

        fname = filename or f"kg_pool_{pool_name.replace(' ', '_')}_interactive.html"
        title = f"Knowledge Graph - Pool: {pool_name}"

        G = self._trim_if_large(sub_kg.nx_graph, max_nodes=_MAX_RENDER_NODES)
        return self._render_network(G, fname, title)

    def render_anomaly_trace(self, anomaly_node_ids: List[str],
                              filename: str = "kg_anomaly_trace_interactive.html"):
        """
        Render an interactive graph focused on anomaly traceability.
        Uses 1-hop (not 2-hop) expansion to control node count.
        """
        G = self.kg.nx_graph
        focus_nodes: Set[str] = set(anomaly_node_ids)

        for nid in anomaly_node_ids:
            if nid in G:
                # 1-hop neighborhood only
                focus_nodes.update(G.neighbors(nid))

        display_G = G.subgraph(focus_nodes).copy()
        logger.info("render_anomaly_trace: %d nodes", display_G.number_of_nodes())
        return self._render_network(
            display_G, filename,
            "Anomaly Traceability - Interactive Knowledge Graph",
            highlight_anomalies=True,
        )

    def render_discovered_relations(self, filename: str = "kg_discovered_interactive.html"):
        """Render an interactive graph highlighting GAT-discovered edges."""
        discovered = self.kg.get_discovered_edges()
        G = self.kg.nx_graph

        focus_nodes: Set[str] = set()
        for src, dst, _ in discovered:
            focus_nodes.add(src)
            focus_nodes.add(dst)
            for nid in [src, dst]:
                parents = self.kg.get_parents(nid)
                focus_nodes.update(parents)

        if not focus_nodes:
            logger.info("No discovered edges to render.")
            return None

        display_G = G.subgraph(focus_nodes).copy()
        return self._render_network(
            display_G, filename,
            "GAT-Discovered Hidden Relations - Interactive View",
            highlight_discoveries=True,
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _trim_if_large(self, G: nx.DiGraph, max_nodes: int) -> nx.DiGraph:
        """If G exceeds max_nodes, keep all non-dataset nodes + first-N
        dataset nodes per parent category, then return a subgraph copy."""
        if G.number_of_nodes() <= max_nodes:
            return G

        keep: Set[str] = set()
        dataset_by_parent: Dict[str, List[str]] = {}

        for nid in G.nodes():
            nt = G.nodes[nid].get("node_type", "")
            if nt != NodeType.DATASET.value:
                keep.add(nid)
            else:
                # find parent category
                for pred in G.predecessors(nid):
                    dataset_by_parent.setdefault(pred, []).append(nid)
                    break
                else:
                    keep.add(nid)  # orphan dataset

        # Budget for datasets
        non_ds = len(keep)
        ds_budget = max_nodes - non_ds
        per_parent = max(ds_budget // max(len(dataset_by_parent), 1), 1)

        for parent, children in dataset_by_parent.items():
            keep.update(children[:per_parent])

        trimmed = G.subgraph(keep).copy()
        logger.info("Trimmed %d → %d nodes", G.number_of_nodes(), trimmed.number_of_nodes())
        return trimmed

    def _render_network(self, G, filename: str, title: str,
                         highlight_anomalies: bool = False,
                         highlight_discoveries: bool = False) -> str:
        """Core rendering method using PyVis with adaptive physics."""

        n_nodes = G.number_of_nodes()
        logger.info("_render_network: %d nodes, %d edges", n_nodes, G.number_of_edges())

        net = Network(
            height=self.height,
            bgcolor=self.bg_color,
            font_color="white",
            directed=True,
            select_menu=True,
            filter_menu=True,
        )
        net.heading = title

        # ── Adaptive physics / layout ──────────────────────────────
        if n_nodes <= _PHYSICS_ON_LIMIT:
            # Small graph → enable physics for nice organic layout
            opts = self._physics_options(stabilization_iters=60)
        elif n_nodes <= _PRECOMPUTE_LIMIT:
            # Medium graph → pre-compute layout via graphviz/hierarchy,
            # physics OFF for instant render
            self._precompute_layout(G)
            opts = self._no_physics_options()
        else:
            # Large graph → pre-compute, physics OFF, simpler edges
            self._precompute_layout(G)
            opts = self._no_physics_options()

        net.set_options(opts)

        # ── Add nodes ──────────────────────────────────────────────
        discovered_endpoints: Set[str] = set()
        if highlight_discoveries:
            for src, dst, _ in self.kg.get_discovered_edges():
                discovered_endpoints.add(src)
                discovered_endpoints.add(dst)

        for nid in G.nodes():
            ndata = G.nodes[nid]
            nt = ndata.get("node_type", "dataset")
            name_en = ndata.get("name_en", nid)
            name_zh = ndata.get("name_zh", "")
            is_anomaly = ndata.get("is_anomaly", False)

            color = NODE_COLORS.get(nt, "#6C757D")
            size = self._scale_size(NODE_SIZES.get(nt, 200))
            border_width = 1
            border_color = "#555555"

            if highlight_anomalies and is_anomaly:
                color = "#FF0000"
                size = self._scale_size(800)
                border_width = 3
                border_color = "#FFD700"

            if nid in discovered_endpoints:
                border_width = 2
                border_color = "#FF6B35"

            # Lightweight tooltip (no HTML heavy-lifting)
            tooltip = f"{name_en}"
            if name_zh:
                tooltip += f" | {name_zh}"
            tooltip += f" [{nt}]"
            if is_anomaly:
                tooltip += f" ⚠ ANOMALY score={ndata.get('anomaly_score', 0):.2f}"

            label = self._truncate_label(name_en, 22)

            node_kwargs = dict(
                label=label,
                title=tooltip,
                color=color,
                size=size,
                borderWidth=border_width,
                borderColor=border_color,
            )

            # Pass pre-computed x, y positions to PyVis
            if "x" in ndata and "y" in ndata:
                node_kwargs["x"] = ndata["x"]
                node_kwargs["y"] = ndata["y"]

            net.add_node(nid, **node_kwargs)

        # ── Add edges ──────────────────────────────────────────────
        for u, v, d in G.edges(data=True):
            et = d.get("edge_type", "hierarchical")
            weight = d.get("weight", 1.0)

            color = EDGE_COLORS.get(et, "#6C757D")
            width = 0.5
            dashes = False

            if et == EdgeType.PROCESS_COUPLING.value:
                width = 2.0
                dashes = True
            elif et == EdgeType.ANOMALY_PROPAGATION.value:
                width = 2.5
                dashes = True
            elif et == EdgeType.CROSS_LEVEL.value:
                width = 0.6
            elif et == EdgeType.HIERARCHICAL.value:
                width = 0.3

            # Lightweight edge tooltip
            edge_title = et
            if et in (EdgeType.PROCESS_COUPLING.value,
                      EdgeType.ANOMALY_PROPAGATION.value):
                edge_title += f" w={weight:.3f}"

            net.add_edge(
                u, v,
                color=color,
                width=width,
                dashes=dashes,
                title=edge_title,
                arrows="to",
            )

        # ── Save ───────────────────────────────────────────────────
        filepath = os.path.join(self.output_dir, filename)
        net.save_graph(filepath)

        # ── Patch HTML: force stabilization off for medium/large ───
        if n_nodes > _PHYSICS_ON_LIMIT:
            self._patch_html_disable_stabilization(filepath)

        logger.info("Saved interactive graph to %s (%d nodes)", filepath, n_nodes)
        return filepath

    # ── Layout helpers ─────────────────────────────────────────────

    @staticmethod
    def _precompute_layout(G: nx.DiGraph):
        """Assign x, y positions to nodes using a hierarchical tree layout.
        This avoids the browser needing to run physics simulation."""
        # Group nodes by level for hierarchical placement
        levels: Dict[int, List[str]] = {}
        for nid in G.nodes():
            lvl = G.nodes[nid].get("level", 3)
            levels.setdefault(lvl, []).append(nid)

        if not levels:
            return

        sorted_levels = sorted(levels.keys())
        y_gap = 350  # vertical gap between levels

        for li, lvl in enumerate(sorted_levels):
            nodes_at_level = levels[lvl]
            n = len(nodes_at_level)
            x_gap = max(250, 8000 // max(n, 1))

            for ni, nid in enumerate(nodes_at_level):
                x = (ni - n / 2) * x_gap
                y = li * y_gap
                G.nodes[nid]["x"] = float(x)
                G.nodes[nid]["y"] = float(y)

    @staticmethod
    def _physics_options(stabilization_iters: int = 60) -> str:
        return """{
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -60,
                    "centralGravity": 0.01,
                    "springLength": 120,
                    "springConstant": 0.06
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {
                    "enabled": true,
                    "iterations": %d,
                    "updateInterval": 25
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "navigationButtons": true,
                "keyboard": true
            },
            "edges": {
                "smooth": false
            }
        }""" % stabilization_iters

    @staticmethod
    def _no_physics_options() -> str:
        """Options for pre-computed layouts — no physics, instant render."""
        return """{
            "physics": {
                "enabled": false
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "navigationButtons": true,
                "keyboard": true
            },
            "edges": {
                "smooth": false
            }
        }"""

    @staticmethod
    def _patch_html_disable_stabilization(filepath: str):
        """Post-process the generated HTML to ensure stabilization is
        truly disabled for medium/large graphs, preventing the 0% freeze."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                html = f.read()

            # Force physics off & skip stabilization
            patch_script = """
    <script>
    // === GenBFKit patch: disable physics & stabilization for instant render ===
    (function() {
        // Wait for the network to be created
        var origDraw = window.drawGraph;
        var checkInterval = setInterval(function() {
            // Try to find the vis network instance
            var container = document.getElementById('mynetwork');
            if (container && container.network) {
                var net = container.network;
                net.setOptions({ physics: { enabled: false } });
                net.stabilize(0);
                clearInterval(checkInterval);
            }
        }, 100);
    })();
    </script>
"""
            # Insert before </body>
            if "</body>" in html:
                html = html.replace("</body>", patch_script + "</body>")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info("Patched HTML to disable stabilization: %s", filepath)
        except Exception as e:
            logger.warning("Failed to patch HTML: %s", e)

    @staticmethod
    def _scale_size(base_size: int) -> int:
        """Scale node size for PyVis (which uses pixel radius)."""
        return max(base_size // 15, 5)

    @staticmethod
    def _truncate_label(label: str, max_len: int = 22) -> str:
        if len(label) <= max_len:
            return label
        return label[:max_len - 2] + ".."
