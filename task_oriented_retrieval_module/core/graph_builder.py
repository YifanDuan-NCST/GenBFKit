"""
Dictionary Graph Builder - Converts the five-level chain-like architecture
into a topological graph structure for GNN-based relevance ranking.

The graph captures:
  - Hierarchical edges: work_type → category → pool → dataset
  - Cross-level edges: dataset ↔ attribute (via pool)
  - Semantic proximity edges: datasets sharing the same category/pool

This graph serves as the structural foundation for the GNN ranker.
"""

import logging
from typing import Optional

import networkx as nx

from .dictionary_manager import DictionaryManager

logger = logging.getLogger(__name__)

# Node type constants
NODE_WORK_TYPE = "work_type"
NODE_CATEGORY = "category"
NODE_POOL = "pool"
NODE_DATASET = "dataset"
NODE_ATTRIBUTE = "attribute"

# Edge type constants
EDGE_HIERARCHICAL = "hierarchical"      # Parent-child in the chain
EDGE_CROSS_LEVEL = "cross_level"        # Dataset to attribute
EDGE_CO_CATEGORY = "co_category"        # Datasets sharing same category
EDGE_CO_POOL = "co_pool"                # Datasets sharing same pool


class DictionaryGraphBuilder:
    """
    Builds a NetworkX DiGraph from the data dictionary's five-level architecture.

    Graph structure:
      - Nodes: Each level entity (work_type, category, pool, dataset, attribute)
      - Edges:
          * Hierarchical: work_type→category, category→pool, pool→dataset
          * Cross-level: dataset→attribute (via pool association)
          * Co-occurrence: dataset↔dataset (shared category or pool)

    Node attributes:
      - node_type: one of the NODE_* constants
      - label: Human-readable name
      - label_zh: Chinese name (if available)
      - level: Hierarchy level (1-5)
    """

    def __init__(self, dict_manager: DictionaryManager):
        self._dm = dict_manager
        self._graph: Optional[nx.DiGraph] = None

    def build(self) -> nx.DiGraph:
        """Build the complete topology graph from the data dictionary."""
        G = nx.DiGraph()

        # ── Level 1: Work Type nodes ──
        for wt in self._dm.get_work_types():
            G.add_node(
                wt.work_type_en,
                node_type=NODE_WORK_TYPE,
                label=wt.work_type_en,
                label_zh=wt.work_type_zh,
                level=1,
            )

        # ── Level 2: Category nodes ──
        for cat in self._dm._snapshot.categories:
            G.add_node(
                cat.category_en,
                node_type=NODE_CATEGORY,
                label=cat.category_en,
                label_zh=cat.category_zh,
                level=2,
            )
            # Hierarchical edge: work_type → category
            G.add_edge(
                cat.work_type_en, cat.category_en,
                edge_type=EDGE_HIERARCHICAL,
            )

        # ── Level 3: Pool nodes ──
        for pool in self._dm.get_pools():
            G.add_node(
                pool.pool_en,
                node_type=NODE_POOL,
                label=pool.pool_en,
                label_zh=pool.pool_zh,
                level=3,
            )

        # ── Level 4: Dataset (param) nodes ──
        for ds in self._dm.get_all_datasets():
            G.add_node(
                ds.dataset_en,
                node_type=NODE_DATASET,
                label=ds.dataset_en,
                label_zh=ds.dataset_zh,
                pool=ds.pool_en,
                category=ds.category_en,
                work_type=ds.work_type_en,
                level=4,
            )
            # Hierarchical edge: category → dataset
            G.add_edge(
                ds.category_en, ds.dataset_en,
                edge_type=EDGE_HIERARCHICAL,
            )
            # Cross-level edge: pool → dataset
            G.add_edge(
                ds.pool_en, ds.dataset_en,
                edge_type=EDGE_CROSS_LEVEL,
            )

        # ── Level 5: Attribute nodes ──
        for pool_en, attr_template in self._dm._snapshot.attribute_templates.items():
            all_attrs = {**attr_template.base_attributes, **attr_template.unique_attributes}
            for attr_key, attr_name in all_attrs.items():
                attr_node_id = f"{pool_en}::{attr_name}"
                G.add_node(
                    attr_node_id,
                    node_type=NODE_ATTRIBUTE,
                    label=attr_name,
                    label_zh="",
                    pool=pool_en,
                    level=5,
                )
                # Cross-level edge: dataset ↔ attribute (through pool)
                G.add_edge(
                    pool_en, attr_node_id,
                    edge_type=EDGE_CROSS_LEVEL,
                )

        # ── Co-occurrence edges between datasets ──
        # Datasets sharing the same category get a co-category edge
        for cat_en, datasets in self._dm._ds_by_cat.items():
            ds_list = datasets[:50]  # Limit to avoid O(n^2) explosion
            for i in range(len(ds_list)):
                for j in range(i + 1, min(i + 10, len(ds_list))):
                    G.add_edge(
                        ds_list[i].dataset_en, ds_list[j].dataset_en,
                        edge_type=EDGE_CO_CATEGORY,
                    )

        # Datasets sharing the same pool get a co-pool edge
        for pool_en, datasets in self._dm._ds_by_pool.items():
            ds_list = datasets[:50]
            for i in range(len(ds_list)):
                for j in range(i + 1, min(i + 10, len(ds_list))):
                    G.add_edge(
                        ds_list[i].dataset_en, ds_list[j].dataset_en,
                        edge_type=EDGE_CO_POOL,
                    )

        self._graph = G
        logger.info(
            f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        )
        return G

    def get_graph(self) -> nx.DiGraph:
        """Return the built graph (builds if not yet built)."""
        if self._graph is None:
            self.build()
        return self._graph

    def get_subgraph_for_datasets(self, dataset_ids: list[str]) -> nx.DiGraph:
        """
        Extract a subgraph containing the specified datasets and their
        ancestor nodes (work_type, category, pool) for context.
        """
        G = self.get_graph()
        nodes_to_include = set(dataset_ids)

        # Walk up the hierarchy for each dataset
        for ds_id in dataset_ids:
            if ds_id not in G:
                continue
            node_data = G.nodes[ds_id]
            # Add parent category
            cat = node_data.get("category")
            if cat and cat in G:
                nodes_to_include.add(cat)
            # Add parent pool
            pool = node_data.get("pool")
            if pool and pool in G:
                nodes_to_include.add(pool)
            # Add parent work_type
            wt = node_data.get("work_type")
            if wt and wt in G:
                nodes_to_include.add(wt)

        return G.subgraph(nodes_to_include).copy()

    def get_statistics(self) -> dict:
        """Return graph statistics."""
        G = self.get_graph()
        node_types = {}
        for _, data in G.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_types[nt] = node_types.get(nt, 0) + 1

        edge_types = {}
        for _, _, data in G.edges(data=True):
            et = data.get("edge_type", "unknown")
            edge_types[et] = edge_types.get(et, 0) + 1

        return {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "node_type_distribution": node_types,
            "edge_type_distribution": edge_types,
            "is_directed": G.is_directed(),
        }
