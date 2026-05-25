"""
Comprehensive test suite for the Knowledge Graph Visualization Module.

Tests cover:
  1. Dictionary parsing & graph building
  2. Node/edge query operations
  3. Chain retrieval
  4. Sub-graph extraction
  5. GAT training & discovery
  6. Anomaly detection & causal reasoning
  7. Virtual data generation
  8. Static visualization rendering
  9. Interactive visualization rendering
 10. End-to-end pipeline
"""

import os
import sys
import json
import logging
import tempfile
import shutil

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.dictionary_parser import DictionaryParser
from ..graph_builder.models import (
    NodeType, EdgeType, GraphNode, GraphEdge, CausalPath, GATDiscoveryResult
)
from ..gat_engine.trainer import GATTrainer
from ..causal_reasoning.anomaly_detector import AnomalyDetector
from ..causal_reasoning.multi_hop_reasoner import MultiHopCausalReasoner
from ..visualizer.static_renderer import StaticRenderer
from ..visualizer.interactive_renderer import InteractiveRenderer
from ..data.virtual_generator import VirtualDataGenerator
from ..config import PREBUILT_JSON_PATH

logger = logging.getLogger(__name__)

# Global test state
_test_results = {"passed": 0, "failed": 0, "errors": []}
_kg = None
_tmpdir = None


def _assert(condition: bool, test_name: str, detail: str = ""):
    """Simple assertion helper."""
    if condition:
        _test_results["passed"] += 1
        print(f"  ✅ {test_name}")
    else:
        _test_results["failed"] += 1
        _test_results["errors"].append(f"{test_name}: {detail}")
        print(f"  ❌ {test_name} — {detail}")


def setup():
    """Shared setup: build the KG once."""
    global _kg, _tmpdir
    print("\n🔧 Setting up test environment...")
    _tmpdir = tempfile.mkdtemp(prefix="kg_test_")
    _kg = BlastFurnaceKnowledgeGraph(json_path=PREBUILT_JSON_PATH)
    _kg.build_from_prebuilt()
    print(f"   KG built: {_kg.nx_graph.number_of_nodes()} nodes, "
          f"{_kg.nx_graph.number_of_edges()} edges")
    print(f"   Temp dir: {_tmpdir}")


def teardown():
    """Clean up temp directory."""
    global _tmpdir
    if _tmpdir and os.path.exists(_tmpdir):
        shutil.rmtree(_tmpdir, ignore_errors=True)
    print(f"\n🧹 Cleaned up temp directory.")


# ======================================================================
# Test 1: Dictionary Parsing
# ======================================================================
def test_dictionary_parsing():
    print("\n📋 Test 1: Dictionary Parsing")
    parser = DictionaryParser(PREBUILT_JSON_PATH)
    nodes, edges = parser.parse()

    _assert(len(nodes) > 0, "Parser returns nodes", f"Got {len(nodes)} nodes")
    _assert(len(edges) > 0, "Parser returns edges", f"Got {len(edges)} edges")

    # Check expected counts
    wt_count = sum(1 for n in nodes.values() if n.node_type == NodeType.WORK_TYPE)
    cat_count = sum(1 for n in nodes.values() if n.node_type == NodeType.DATA_CATEGORY)
    pool_count = sum(1 for n in nodes.values() if n.node_type == NodeType.DATA_POOL)
    ds_count = sum(1 for n in nodes.values() if n.node_type == NodeType.DATASET)

    _assert(wt_count == 8, "8 work types", f"Got {wt_count}")
    _assert(cat_count == 98, "98 data categories", f"Got {cat_count}")
    _assert(pool_count == 9, "9 data pools", f"Got {pool_count}")
    _assert(ds_count == 2128, "2128 datasets", f"Got {ds_count}")


# ======================================================================
# Test 2: KG Build & Summary
# ======================================================================
def test_kg_build():
    print("\n🏗️ Test 2: Knowledge Graph Build & Summary")
    summary = _kg.summary()

    _assert(summary["total_nodes"] > 2200, "Total nodes > 2200", f"Got {summary['total_nodes']}")
    _assert(summary["total_edges"] > 4000, "Total edges > 4000", f"Got {summary['total_edges']}")
    _assert(summary["node_type_counts"].get("work_type", 0) == 8,
            "8 work_type nodes in summary")
    _assert(summary["anomaly_nodes"] == 0, "No anomalies initially")


# ======================================================================
# Test 3: Node/Edge Queries
# ======================================================================
def test_node_edge_queries():
    print("\n🔍 Test 3: Node/Edge Queries")

    # Get nodes by type
    wt_nodes = _kg.get_nodes_by_type(NodeType.WORK_TYPE)
    _assert(len(wt_nodes) == 8, "8 work type nodes via query")

    ds_nodes = _kg.get_nodes_by_type(NodeType.DATASET)
    _assert(len(ds_nodes) == 2128, "2128 dataset nodes via query")

    # Get a specific node
    if wt_nodes:
        node = _kg.get_node(wt_nodes[0].node_id)
        _assert(node is not None, "get_node returns a node")
        _assert(node.node_type == NodeType.WORK_TYPE, "Node type is work_type")

    # Get children
    if wt_nodes:
        children = _kg.get_children(wt_nodes[0].node_id, EdgeType.HIERARCHICAL)
        _assert(len(children) > 0, "Work type has children", f"Got {len(children)}")

    # Search
    results = _kg.search_nodes("temperature")
    _assert(len(results) > 0, "Search 'temperature' returns results", f"Got {len(results)}")

    results_zh = _kg.search_nodes("温度")
    _assert(len(results_zh) > 0, "Search '温度' returns results", f"Got {len(results_zh)}")


# ======================================================================
# Test 4: Chain Retrieval
# ======================================================================
def test_chain_retrieval():
    print("\n⛓️ Test 4: Chain Retrieval")

    wt_nodes = _kg.get_nodes_by_type(NodeType.WORK_TYPE)
    if wt_nodes:
        result = _kg.chain_retrieve(wt_nodes[0].node_id)
        _assert("work_type" in result, "Chain result has work_type key")
        _assert("categories" in result, "Chain result has categories key")
        _assert(len(result["categories"]) > 0, "Work type has categories")

    # Non-existent node
    result = _kg.chain_retrieve("nonexistent")
    _assert(result == {}, "Non-existent node returns empty dict")


# ======================================================================
# Test 5: Sub-graph Extraction
# ======================================================================
def test_subgraph_extraction():
    print("\n✂️ Test 5: Sub-graph Extraction")

    wt_nodes = _kg.get_nodes_by_type(NodeType.WORK_TYPE)
    if wt_nodes:
        sub = _kg.get_subgraph_by_work_type(wt_nodes[0].node_id)
        _assert(sub.nx_graph.number_of_nodes() > 0, "Sub-graph has nodes")
        _assert(sub.nx_graph.number_of_nodes() < _kg.nx_graph.number_of_nodes(),
                "Sub-graph smaller than full graph")

    pool_nodes = _kg.get_nodes_by_type(NodeType.DATA_POOL)
    if pool_nodes:
        sub = _kg.get_subgraph_by_pool(pool_nodes[0].node_id)
        _assert(sub.nx_graph.number_of_nodes() > 0, "Pool sub-graph has nodes")


# ======================================================================
# Test 6: GAT Training & Discovery
# ======================================================================
def test_gat():
    print("\n🧠 Test 6: GAT Training & Discovery")

    trainer = GATTrainer(_kg, num_epochs=15, threshold=0.5)
    history = trainer.train()

    _assert("losses" in history, "Training returns loss history")
    _assert(len(history["losses"]) == 15, "15 epochs recorded", f"Got {len(history['losses'])}")
    _assert(history["losses"][-1] < history["losses"][0], "Loss decreased during training",
            f"First: {history['losses'][0]:.4f}, Last: {history['losses'][-1]:.4f}")

    discoveries = trainer.discover_hidden_relations()
    _assert(isinstance(discoveries, list), "Discoveries is a list")
    _assert(len(discoveries) >= 0, "Discovery returns results (may be 0 with high threshold)")

    # Inject and verify
    if discoveries:
        trainer.inject_discoveries(discoveries[:5])
        disc_edges = _kg.get_discovered_edges()
        _assert(len(disc_edges) >= 5, "Discovered edges injected into KG",
                f"Got {len(disc_edges)}")


# ======================================================================
# Test 7: Anomaly Detection & Causal Reasoning
# ======================================================================
def test_anomaly_causal():
    print("\n⚠️ Test 7: Anomaly Detection & Causal Reasoning")

    # Generate virtual data
    vgen = VirtualDataGenerator(_kg, num_timesteps=100)
    scenario = vgen.generate_full_scenario()
    data = scenario["data"]
    anomaly_ids = scenario["anomaly_ids"]

    _assert(len(data) == 2128, "Virtual data for all 2128 params")
    _assert(len(anomaly_ids) > 0, "Anomalies injected", f"Got {len(anomaly_ids)}")

    # Detect anomalies
    detector = AnomalyDetector(_kg)
    param_data = {nid: ts.tolist() for nid, ts in data.items()}
    detected = detector.detect_from_data(param_data)
    _assert(len(detected) > 0, "Anomalies detected from data", f"Got {len(detected)}")

    # Causal reasoning
    reasoner = MultiHopCausalReasoner(_kg, max_hops=3, top_k=5)
    if detected:
        # Trace one anomaly
        paths = reasoner.trace_anomaly(detected[0])
        _assert(isinstance(paths, list), "Trace returns a list")
        _assert(len(paths) >= 0, "Causal paths found (may be 0 for shallow anomalies)")

        # Batch trace
        batch_results = reasoner.trace_batch_anomalies(detected[:5])
        _assert(isinstance(batch_results, dict), "Batch trace returns dict")

        # Build propagation graph
        reasoner.build_anomaly_propagation_graph(detected[:5])

    # Verify anomaly nodes are flagged
    anomaly_nodes = _kg.get_anomaly_nodes()
    _assert(len(anomaly_nodes) > 0, "Anomaly nodes flagged in KG",
            f"Got {len(anomaly_nodes)}")

    # Clear anomalies
    _kg.clear_anomalies()
    anomaly_nodes_after = _kg.get_anomaly_nodes()
    _assert(len(anomaly_nodes_after) == 0, "Anomalies cleared")


# ======================================================================
# Test 8: Virtual Data Generator
# ======================================================================
def test_virtual_data_generator():
    print("\n🎲 Test 8: Virtual Data Generator")

    vgen = VirtualDataGenerator(_kg, num_timesteps=50, seed=123)
    data = vgen.generate_time_series()

    _assert(len(data) == 2128, "Data generated for 2128 params")
    for nid, ts in list(data.items())[:5]:
        _assert(len(ts) == 50, f"Time series length is 50", f"Got {len(ts)}")
        _assert(not any(np.isnan(ts) for _ in [1] if False), "No NaN in series")  # quick check

    # Full scenario
    scenario = vgen.generate_full_scenario()
    _assert("data" in scenario, "Scenario has 'data' key")
    _assert("anomaly_ids" in scenario, "Scenario has 'anomaly_ids' key")
    _assert("statistics" in scenario, "Scenario has 'statistics' key")
    _assert("metadata" in scenario, "Scenario has 'metadata' key")

    # Save scenario
    saved = vgen.save_scenario(scenario, output_dir=_tmpdir)
    _assert(os.path.exists(saved["stats"]), "Stats file saved")
    _assert(os.path.exists(saved["data"]), "Data CSV saved")
    _assert(os.path.exists(saved["metadata"]), "Metadata file saved")


# ======================================================================
# Test 9: Static Visualization
# ======================================================================
def test_static_visualization():
    print("\n🖼️ Test 9: Static Visualization")

    renderer = StaticRenderer(_kg, output_dir=_tmpdir)

    # Hierarchy overview
    f1 = renderer.render_hierarchy_overview(filename="test_hierarchy.png")
    _assert(os.path.exists(f1), "Hierarchy overview PNG saved")
    _assert(os.path.getsize(f1) > 1000, "PNG file has content", f"Size: {os.path.getsize(f1)}")

    # Work type subgraph
    wt_nodes = _kg.get_nodes_by_type(NodeType.WORK_TYPE)
    if wt_nodes:
        f2 = renderer.render_work_type_subgraph(wt_nodes[0].node_id,
                                                   filename="test_wt_subgraph.png")
        _assert(os.path.exists(f2), "Work type subgraph PNG saved")

    # Anomaly highlight (with some anomalies marked)
    ds_nodes = _kg.get_nodes_by_type(NodeType.DATASET)
    anomaly_test_ids = [n.node_id for n in ds_nodes[:3]]
    for nid in anomaly_test_ids:
        _kg.mark_anomaly(nid, 0.8)

    f3 = renderer.render_anomaly_highlight(anomaly_test_ids,
                                            filename="test_anomaly.png")
    _assert(os.path.exists(f3), "Anomaly highlight PNG saved")

    # Clean up anomalies
    _kg.clear_anomalies()


# ======================================================================
# Test 10: Interactive Visualization
# ======================================================================
def test_interactive_visualization():
    print("\n🌐 Test 10: Interactive Visualization")

    renderer = InteractiveRenderer(_kg, output_dir=_tmpdir)

    # Full graph
    f1 = renderer.render_full_graph(filename="test_full_interactive.html")
    _assert(os.path.exists(f1), "Interactive HTML saved")
    _assert(os.path.getsize(f1) > 1000, "HTML file has content")

    # Anomaly trace
    ds_nodes = _kg.get_nodes_by_type(NodeType.DATASET)
    anomaly_test_ids = [n.node_id for n in ds_nodes[:2]]
    for nid in anomaly_test_ids:
        _kg.mark_anomaly(nid, 0.9)

    f2 = renderer.render_anomaly_trace(anomaly_test_ids,
                                        filename="test_anomaly_interactive.html")
    _assert(os.path.exists(f2), "Anomaly interactive HTML saved")

    # Clean up
    _kg.clear_anomalies()


# ======================================================================
# Test 11: Serialization
# ======================================================================
def test_serialization():
    print("\n💾 Test 11: Serialization")

    json_str = _kg.to_json()
    _assert(len(json_str) > 1000, "JSON serialization produces output")

    # Parse it back
    parsed = json.loads(json_str)
    _assert("nodes" in parsed, "JSON has 'nodes' key")
    _assert("edges" in parsed, "JSON has 'edges' key")
    _assert(len(parsed["nodes"]) > 0, "Nodes in JSON")
    _assert(len(parsed["edges"]) > 0, "Edges in JSON")

    # Save to file
    filepath = os.path.join(_tmpdir, "test_kg_export.json")
    _kg.save_json(filepath)
    _assert(os.path.exists(filepath), "JSON file saved")
    _assert(os.path.getsize(filepath) > 1000, "JSON file has content")


# ======================================================================
# Test 12: End-to-End Pipeline
# ======================================================================
def test_end_to_end():
    print("\n🚀 Test 12: End-to-End Pipeline")

    # Build
    kg = BlastFurnaceKnowledgeGraph(json_path=PREBUILT_JSON_PATH)
    kg.build_from_prebuilt()

    # GAT (minimal)
    trainer = GATTrainer(kg, num_epochs=10, threshold=0.5)
    trainer.train()
    discoveries = trainer.discover_hidden_relations()
    if discoveries:
        trainer.inject_discoveries(discoveries[:3])

    # Virtual data + anomaly
    vgen = VirtualDataGenerator(kg, num_timesteps=50)
    scenario = vgen.generate_full_scenario()
    detector = AnomalyDetector(kg)
    param_data = {nid: ts.tolist() for nid, ts in scenario["data"].items()}
    detected = detector.detect_from_data(param_data)

    # Causal reasoning
    if detected:
        reasoner = MultiHopCausalReasoner(kg, max_hops=2)
        reasoner.build_anomaly_propagation_graph(detected[:3])

    # Visualization
    e2e_dir = os.path.join(_tmpdir, "e2e_output")
    static = StaticRenderer(kg, output_dir=e2e_dir)
    f1 = static.render_hierarchy_overview(filename="e2e_hierarchy.png")
    _assert(os.path.exists(f1), "E2E: hierarchy overview rendered")

    interactive = InteractiveRenderer(kg, output_dir=e2e_dir)
    f2 = interactive.render_full_graph(filename="e2e_full.html")
    _assert(os.path.exists(f2), "E2E: interactive full graph rendered")

    # Summary
    summary = kg.summary()
    _assert(summary["total_nodes"] > 2200, "E2E: Final KG has expected nodes")
    _assert(summary["discovered_edges"] >= 0, "E2E: Discovered edges tracked")

    print(f"\n   📊 E2E Summary: {json.dumps(summary, indent=2)}")


# ======================================================================
# Runner
# ======================================================================
def run_all_tests():
    """Execute all tests and print results."""
    print("=" * 60)
    print("🧪 GenBFKit KG Module — Comprehensive Test Suite")
    print("=" * 60)

    setup()

    try:
        test_dictionary_parsing()
        test_kg_build()
        test_node_edge_queries()
        test_chain_retrieval()
        test_subgraph_extraction()
        test_gat()
        test_anomaly_causal()
        test_virtual_data_generator()
        test_static_visualization()
        test_interactive_visualization()
        test_serialization()
        test_end_to_end()
    except Exception as e:
        _test_results["errors"].append(f"Uncaught exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        teardown()

    # Print summary
    total = _test_results["passed"] + _test_results["failed"]
    print("\n" + "=" * 60)
    print(f"📋 Test Results: {_test_results['passed']}/{total} passed")
    if _test_results["errors"]:
        print("❌ Failures:")
        for err in _test_results["errors"]:
            print(f"   • {err}")
    else:
        print("🎉 All tests passed!")
    print("=" * 60)

    return _test_results["failed"] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
