"""
Module-level configuration for the Knowledge Graph Visualization Module.
Centralizes all tunable parameters, path constants, and color schemes.
"""

import os

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_MODULE_DIR, "data")
PREBUILT_JSON_PATH = os.path.join(DATA_DIR, "prebuilt_full.json")
OUTPUT_DIR = os.path.join(_MODULE_DIR, "output")

# ---------------------------------------------------------------------------
# Data dictionary hierarchy levels (top → bottom)
# ---------------------------------------------------------------------------
HIERARCHY_LEVELS = [
    "work_type",       # Level 1 – 8 nodes
    "data_category",   # Level 2 – 98 nodes
    "data_pool",       # Level 3 – 9 nodes
    "dataset",         # Level 4 – 2128 nodes
    "data_attribute",  # Level 5 – 49 attributes (distributed across pools)
]

# ---------------------------------------------------------------------------
# Node type enumeration
# ---------------------------------------------------------------------------
NODE_TYPE_WORK_TYPE = "work_type"
NODE_TYPE_CATEGORY = "data_category"
NODE_TYPE_POOL = "data_pool"
NODE_TYPE_DATASET = "dataset"
NODE_TYPE_ATTRIBUTE = "data_attribute"

# ---------------------------------------------------------------------------
# Edge type enumeration
# ---------------------------------------------------------------------------
EDGE_TYPE_HIERARCHICAL = "hierarchical"        # parent → child in the 5-level chain
EDGE_TYPE_CROSS_LEVEL = "cross_level"          # e.g. dataset ↔ pool (many-to-many)
EDGE_TYPE_PROCESS_COUPLING = "process_coupling"  # GAT-discovered hidden relation
EDGE_TYPE_ANOMALY_PROPAGATION = "anomaly_propagation"  # causal reasoning path

# ---------------------------------------------------------------------------
# Color palette (visually distinct, colorblind-friendly)
# ---------------------------------------------------------------------------
NODE_COLORS = {
    NODE_TYPE_WORK_TYPE:  "#E63946",   # Red
    NODE_TYPE_CATEGORY:   "#457B9D",   # Steel Blue
    NODE_TYPE_POOL:       "#2A9D8F",   # Teal
    NODE_TYPE_DATASET:    "#E9C46A",   # Gold
    NODE_TYPE_ATTRIBUTE:  "#8338EC",   # Purple
}

EDGE_COLORS = {
    EDGE_TYPE_HIERARCHICAL:          "#ADB5BD",  # Gray
    EDGE_TYPE_CROSS_LEVEL:           "#6C757D",  # Dark Gray
    EDGE_TYPE_PROCESS_COUPLING:      "#FF6B35",  # Orange
    EDGE_TYPE_ANOMALY_PROPAGATION:   "#D00000",  # Deep Red
}

# ---------------------------------------------------------------------------
# Node sizes for visualization (relative)
# ---------------------------------------------------------------------------
NODE_SIZES = {
    NODE_TYPE_WORK_TYPE:  1200,
    NODE_TYPE_CATEGORY:   600,
    NODE_TYPE_POOL:       900,
    NODE_TYPE_DATASET:    300,
    NODE_TYPE_ATTRIBUTE:  150,
}

# ---------------------------------------------------------------------------
# GAT hyper-parameters
# ---------------------------------------------------------------------------
GAT_NUM_HEADS = 4
GAT_HIDDEN_DIM = 64
GAT_NUM_EPOCHS = 200
GAT_LEARNING_RATE = 0.005
GAT_NEG_SAMPLE_RATIO = 1.0    # ratio of negative to positive edges
GAT_DROPOUT = 0.2
GAT_DISCOVERY_THRESHOLD = 0.7  # attention score threshold for "discovered" edges

# ---------------------------------------------------------------------------
# Causal reasoning parameters
# ---------------------------------------------------------------------------
CAUSAL_MAX_HOPS = 5
CAUSAL_TOP_K_PATHS = 10
CAUSAL_MIN_PATH_SCORE = 0.3
CAUSAL_ANOMALY_ZSCORE_THRESHOLD = 2.5  # 3σ rule

# ---------------------------------------------------------------------------
# Virtual data generator parameters
# ---------------------------------------------------------------------------
VIRTUAL_NUM_TIMESTEPS = 1000
VIRTUAL_ANOMALY_RATIO = 0.05
VIRTUAL_RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Output / rendering defaults
# ---------------------------------------------------------------------------
STATIC_FIG_SIZE = (20, 16)
STATIC_DPI = 150
INTERACTIVE_HEIGHT = "900px"
INTERACTIVE_BG_COLOR = "#1a1a2e"
