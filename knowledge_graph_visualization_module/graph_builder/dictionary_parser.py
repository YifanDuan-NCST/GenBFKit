"""
Dictionary parser: reads the prebuilt_full.json and converts it into
structured GraphNode / GraphEdge objects following the 5-level chain
architecture:

    work_type (8) → data_category (98) → data_pool (9) → dataset (2128) → data_attribute (49)
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from .models import GraphNode, GraphEdge, NodeType, EdgeType


class DictionaryParser:
    """
    Parses the GenBFKit prebuilt data architecture JSON into graph primitives.

    The JSON structure has 5 top-level keys:
      - base_work_types: list of 8 work types
      - categories: list of 98 data categories
      - pools: list of 9 data pools
      - datasets: list of 2128 datasets (params)
      - attribute_templates: dict mapping pool_name → attribute dict
    """

    def __init__(self, json_path: Optional[str] = None):
        if json_path is None:
            json_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "data", "prebuilt_full.json"
            )
        self.json_path = os.path.normpath(json_path)
        self._raw: dict = {}
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._wt_to_cats: Dict[str, List[str]] = defaultdict(list)
        self._cat_to_pools: Dict[str, List[str]] = defaultdict(list)
        self._pool_to_datasets: Dict[str, List[str]] = defaultdict(list)
        self._ds_to_attrs: Dict[str, List[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self) -> Tuple[Dict[str, GraphNode], List[GraphEdge]]:
        """
        Parse the JSON file and return (nodes_dict, edges_list).
        """
        self._load_json()
        self._build_work_type_nodes()
        self._build_category_nodes()
        self._build_pool_nodes()
        self._build_dataset_nodes()
        self._build_attribute_nodes()
        self._build_cross_level_edges()
        return dict(self._nodes), list(self._edges)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_json(self):
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)

    def _add_node(self, node: GraphNode):
        self._nodes[node.node_id] = node

    def _add_edge(self, edge: GraphEdge):
        self._edges.append(edge)

    # ---- Level 1: Work Types (8) ------------------------------------
    def _build_work_type_nodes(self):
        for wt in self._raw["base_work_types"]:
            nid = f"wt_{wt['no']}"
            node = GraphNode(
                node_id=nid,
                node_type=NodeType.WORK_TYPE,
                name_en=wt["work_type_en"],
                name_zh=wt.get("work_type_zh", ""),
                level=0,
                properties={"no": wt["no"]},
            )
            self._add_node(node)

    # ---- Level 2: Data Categories (98) → linked to work types -------
    def _build_category_nodes(self):
        wt_name_to_id = {
            wt["work_type_en"]: f"wt_{wt['no']}"
            for wt in self._raw["base_work_types"]
        }
        for idx, cat in enumerate(self._raw["categories"], start=1):
            nid = f"cat_{idx}"
            node = GraphNode(
                node_id=nid,
                node_type=NodeType.DATA_CATEGORY,
                name_en=cat["category_en"],
                name_zh=cat.get("category_zh", ""),
                level=1,
                properties={
                    "work_type_en": cat["work_type_en"],
                },
            )
            self._add_node(node)

            # hierarchical edge: work_type → category
            wt_id = wt_name_to_id.get(cat["work_type_en"])
            if wt_id:
                self._add_edge(GraphEdge(
                    source_id=wt_id,
                    target_id=nid,
                    edge_type=EdgeType.HIERARCHICAL,
                    weight=1.0,
                    properties={"relation": "work_type_contains_category"},
                ))
                self._wt_to_cats[wt_id].append(nid)

    # ---- Level 3: Data Pools (9) ------------------------------------
    def _build_pool_nodes(self):
        for idx, pool in enumerate(self._raw["pools"], start=1):
            nid = f"pool_{idx}"
            node = GraphNode(
                node_id=nid,
                node_type=NodeType.DATA_POOL,
                name_en=pool["pool_en"],
                name_zh=pool.get("pool_zh", ""),
                level=2,
                properties={"index": idx},
            )
            self._add_node(node)

    # ---- Level 4: Datasets / Params (2128) → linked to category & pool
    def _build_dataset_nodes(self):
        cat_name_to_id = {
            cat["category_en"]: f"cat_{i}"
            for i, cat in enumerate(self._raw["categories"], start=1)
        }
        pool_name_to_id = {
            pool["pool_en"]: f"pool_{i}"
            for i, pool in enumerate(self._raw["pools"], start=1)
        }
        for idx, ds in enumerate(self._raw["datasets"], start=1):
            nid = f"ds_{idx}"
            node = GraphNode(
                node_id=nid,
                node_type=NodeType.DATASET,
                name_en=ds["dataset_en"],
                name_zh=ds.get("dataset_zh", ""),
                level=3,
                properties={
                    "work_type_en": ds["work_type_en"],
                    "category_en": ds["category_en"],
                    "pool_en": ds["pool_en"],
                },
            )
            self._add_node(node)

            # hierarchical edge: category → dataset
            cat_id = cat_name_to_id.get(ds["category_en"])
            if cat_id:
                self._add_edge(GraphEdge(
                    source_id=cat_id,
                    target_id=nid,
                    edge_type=EdgeType.HIERARCHICAL,
                    weight=1.0,
                    properties={"relation": "category_contains_dataset"},
                ))
                self._cat_to_pools[cat_id].append(nid)

            # cross-level edge: dataset → pool
            pool_id = pool_name_to_id.get(ds["pool_en"])
            if pool_id:
                self._add_edge(GraphEdge(
                    source_id=nid,
                    target_id=pool_id,
                    edge_type=EdgeType.CROSS_LEVEL,
                    weight=1.0,
                    properties={"relation": "dataset_belongs_to_pool"},
                ))
                self._pool_to_datasets[pool_id].append(nid)

    # ---- Level 5: Data Attributes (49 distributed across pools) -----
    def _build_attribute_nodes(self):
        pool_name_to_id = {
            pool["pool_en"]: f"pool_{i}"
            for i, pool in enumerate(self._raw["pools"], start=1)
        }
        attr_global_idx = 1
        for pool_name, attrs in self._raw["attribute_templates"].items():
            pool_id = pool_name_to_id.get(pool_name)
            for attr_key, attr_name in attrs.items():
                nid = f"attr_{attr_global_idx}"
                node = GraphNode(
                    node_id=nid,
                    node_type=NodeType.DATA_ATTRIBUTE,
                    name_en=attr_name,
                    name_zh="",
                    level=4,
                    properties={
                        "pool_en": pool_name,
                        "attr_key": attr_key,
                    },
                )
                self._add_node(node)

                # hierarchical edge: pool → attribute
                if pool_id:
                    self._add_edge(GraphEdge(
                        source_id=pool_id,
                        target_id=nid,
                        edge_type=EdgeType.HIERARCHICAL,
                        weight=1.0,
                        properties={"relation": "pool_defines_attribute"},
                    ))
                    self._ds_to_attrs[pool_id].append(nid)

                attr_global_idx += 1

    # ---- Cross-level edges for datasets sharing same category --------
    def _build_cross_level_edges(self):
        """
        Add cross-level edges between datasets that belong to the same
        data category (sibling coupling) — these form the basis for
        GAT-based hidden relation discovery.
        """
        cat_to_datasets: Dict[str, List[str]] = defaultdict(list)
        for edge in self._edges:
            if (edge.edge_type == EdgeType.HIERARCHICAL
                    and edge.properties.get("relation") == "category_contains_dataset"):
                cat_to_datasets[edge.source_id].append(edge.target_id)

        # For categories with >1 dataset, add intra-category coupling edges
        # (We only add a subset to keep the graph manageable — every pair
        #  would be O(n²), so we add edges between consecutive datasets.)
        for cat_id, ds_ids in cat_to_datasets.items():
            if len(ds_ids) > 1:
                for i in range(len(ds_ids) - 1):
                    self._add_edge(GraphEdge(
                        source_id=ds_ids[i],
                        target_id=ds_ids[i + 1],
                        edge_type=EdgeType.CROSS_LEVEL,
                        weight=0.5,
                        properties={"relation": "intra_category_coupling"},
                    ))
