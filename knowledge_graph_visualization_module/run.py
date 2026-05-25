"""
GenBFKit Knowledge Graph Visualization Module — Main Entry Point
================================================================

Usage:
    python -m knowledge_graph_visualization_module.run [--mode MODE] [--output-dir DIR]

Modes:
    full            Build KG, train GAT, discover edges, trace anomalies, render all (default)
    build           Build the knowledge graph only
    gat             Build KG + train GAT + discover hidden relations
    anomaly         Build KG + detect anomalies + trace root causes
    visualize       Build KG + render all visualizations
    demo            Quick demo with virtual data (fast, for testing)
    test            Run comprehensive tests
"""

import os
import sys
import logging
import argparse
import time
from typing import Optional

from .graph_builder.models import NodeType as NT
from .graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from .gat_engine.trainer import GATTrainer
from .causal_reasoning.anomaly_detector import AnomalyDetector
from .causal_reasoning.multi_hop_reasoner import MultiHopCausalReasoner
from .visualizer.static_renderer import StaticRenderer
from .visualizer.interactive_renderer import InteractiveRenderer
from .data.virtual_generator import VirtualDataGenerator
from .config import OUTPUT_DIR, PREBUILT_JSON_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_knowledge_graph(json_path: Optional[str] = None) -> BlastFurnaceKnowledgeGraph:
    """Step 1: Build the knowledge graph from the prebuilt data architecture."""
    logger.info("=" * 60)
    logger.info("Step 1: Building Knowledge Graph from prebuilt data architecture...")
    logger.info("=" * 60)

    kg = BlastFurnaceKnowledgeGraph(json_path=json_path or PREBUILT_JSON_PATH)
    kg.build_from_prebuilt()

    summary = kg.summary()
    logger.info("KG Summary: %s", summary)
    return kg


def run_gat_discovery(kg: BlastFurnaceKnowledgeGraph,
                       num_epochs: int = 100,
                       threshold: float = 0.7) -> list:
    """Step 2: Train GAT and discover hidden process couplings."""
    logger.info("=" * 60)
    logger.info("Step 2: Training GAT model & discovering hidden relations...")
    logger.info("=" * 60)

    trainer = GATTrainer(kg, num_epochs=num_epochs, threshold=threshold)
    history = trainer.train()
    logger.info("GAT training complete. Final loss: %.4f", history["losses"][-1])

    discoveries = trainer.discover_hidden_relations()
    logger.info("Discovered %d hidden process couplings.", len(discoveries))

    # Inject top discoveries into the KG
    top_discoveries = discoveries[:50]  # Limit to top 50 for performance
    trainer.inject_discoveries(top_discoveries)

    return discoveries


def run_anomaly_trace(kg: BlastFurnaceKnowledgeGraph,
                       anomaly_ids: Optional[list] = None) -> dict:
    """Step 3: Detect anomalies and trace root causes."""
    logger.info("=" * 60)
    logger.info("Step 3: Anomaly detection & causal reasoning...")
    logger.info("=" * 60)

    detector = AnomalyDetector(kg)
    reasoner = MultiHopCausalReasoner(kg)

    if anomaly_ids is None:
        # Use virtual data to detect anomalies
        vgen = VirtualDataGenerator(kg, num_timesteps=500)
        scenario = vgen.generate_full_scenario()
        anomaly_ids = scenario["anomaly_ids"]

        # Also detect from virtual data
        data = scenario["data"]
        # Convert to format expected by detector
        param_data = {nid: ts.tolist() for nid, ts in data.items()}
        detected = detector.detect_from_data(param_data)
        anomaly_ids = list(set(anomaly_ids + detected))

    logger.info("Tracing anomalies for %d nodes...", len(anomaly_ids))

    # Trace each anomaly
    all_paths = reasoner.trace_batch_anomalies(anomaly_ids)
    for nid, paths in all_paths.items():
        node = kg.get_node(nid)
        logger.info("  Anomaly: %s → %d causal paths found",
                     node.name_en if node else nid, len(paths))
        for p in paths[:3]:  # Show top 3
            logger.info("    Path (confidence=%.3f): %s", p.confidence, p.description)

    # Build propagation graph
    reasoner.build_anomaly_propagation_graph(anomaly_ids)

    return all_paths


def run_visualization(kg: BlastFurnaceKnowledgeGraph,
                       output_dir: Optional[str] = None,
                       anomaly_ids: Optional[list] = None):
    """Step 4: Generate all visualizations."""
    logger.info("=" * 60)
    logger.info("Step 4: Generating visualizations...")
    logger.info("=" * 60)

    out = output_dir or OUTPUT_DIR
    os.makedirs(out, exist_ok=True)

    static = StaticRenderer(kg, output_dir=out)
    interactive = InteractiveRenderer(kg, output_dir=out)

    # 4a. Static hierarchy overview
    logger.info("  Rendering static hierarchy overview...")
    f1 = static.render_hierarchy_overview()
    logger.info("  → %s", f1)

    # 4b. Static work type subgraph (first work type)
    wt_nodes = kg.get_nodes_by_type(NT.WORK_TYPE)
    if wt_nodes:
        logger.info("  Rendering work type subgraph for %s...", wt_nodes[0].name_en)
        f2 = static.render_work_type_subgraph(wt_nodes[0].node_id)
        logger.info("  → %s", f2)

    # 4c. Interactive full graph
    logger.info("  Rendering interactive full graph...")
    f3 = interactive.render_full_graph()
    logger.info("  → %s", f3)

    # 4d. Anomaly visualization (if anomalies detected)
    if anomaly_ids:
        logger.info("  Rendering anomaly trace visualization...")
        f4 = static.render_anomaly_highlight(anomaly_ids)
        logger.info("  → %s", f4)
        f5 = interactive.render_anomaly_trace(anomaly_ids)
        logger.info("  → %s", f5)

    # 4e. Discovered edges visualization
    discovered = kg.get_discovered_edges()
    if discovered:
        logger.info("  Rendering discovered edges visualization...")
        f6 = static.render_discovered_edges()
        logger.info("  → %s", f6)
        f7 = interactive.render_discovered_relations()
        logger.info("  → %s", f7)

    logger.info("All visualizations saved to %s", out)


def run_full_pipeline(json_path: Optional[str] = None,
                       output_dir: Optional[str] = None):
    """Run the complete pipeline: Build → GAT → Anomaly → Visualize."""
    start_time = time.time()

    # Step 1: Build KG
    kg = build_knowledge_graph(json_path)

    # Step 2: GAT discovery
    discoveries = run_gat_discovery(kg, num_epochs=100)

    # Step 3: Anomaly trace
    anomaly_results = run_anomaly_trace(kg)
    anomaly_ids = list(anomaly_results.keys())

    # Step 4: Visualization
    run_visualization(kg, output_dir=output_dir, anomaly_ids=anomaly_ids)

    # Final summary
    elapsed = time.time() - start_time
    summary = kg.summary()
    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1f seconds!", elapsed)
    logger.info("Final KG summary: %s", summary)
    logger.info("=" * 60)


def run_demo():
    """Quick demo with virtual data — fast, for testing."""
    logger.info("=" * 60)
    logger.info("GenBFKit KG Module — Quick Demo")
    logger.info("=" * 60)

    # Build KG
    kg = build_knowledge_graph()
    summary = kg.summary()
    print(f"\n📊 Knowledge Graph Built!")
    print(f"   Nodes: {summary['total_nodes']}")
    print(f"   Edges: {summary['total_edges']}")
    print(f"   Node types: {summary['node_type_counts']}")

    # Quick GAT (few epochs)
    print(f"\n🧠 Training GAT (50 epochs)...")
    discoveries = run_gat_discovery(kg, num_epochs=50, threshold=0.65)
    print(f"   Discovered {len(discoveries)} hidden process couplings!")
    if discoveries:
        print(f"   Top discovery: {discoveries[0].description}")

    # Virtual data + anomaly
    print(f"\n🔬 Generating virtual data & detecting anomalies...")
    vgen = VirtualDataGenerator(kg, num_timesteps=200)
    scenario = vgen.generate_full_scenario()
    print(f"   Generated data for {scenario['metadata']['num_params']} params")
    print(f"   Injected {scenario['metadata']['num_anomalies']} anomalies")

    # Detect from data
    detector = AnomalyDetector(kg)
    param_data = {nid: ts.tolist() for nid, ts in scenario["data"].items()}
    detected = detector.detect_from_data(param_data)
    print(f"   Detected {len(detected)} anomalous parameters")

    # Trace
    if detected:
        reasoner = MultiHopCausalReasoner(kg)
        paths = reasoner.trace_batch_anomalies(detected)
        print(f"   Traced {len(paths)} anomalies")
        for nid, path_list in list(paths.items())[:3]:
            node = kg.get_node(nid)
            print(f"     • {node.name_en if node else nid}: {len(path_list)} causal paths")
        reasoner.build_anomaly_propagation_graph(detected)

    # Visualize
    print(f"\n🎨 Generating visualizations...")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    run_visualization(kg, output_dir=out, anomaly_ids=detected)

    print(f"\n✅ Demo complete! Check the 'output' directory for results.")


def run_tests():
    """Run comprehensive module tests."""
    logger.info("Running comprehensive tests...")
    from .tests.test_all import run_all_tests
    run_all_tests()


def main():
    parser = argparse.ArgumentParser(
        description="GenBFKit Knowledge Graph Visualization Module"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "build", "gat", "anomaly", "visualize", "demo", "test"],
        default="demo",
        help="Execution mode (default: demo)",
    )
    parser.add_argument(
        "--json-path",
        type=str,
        default=None,
        help="Path to prebuilt_full.json (default: bundled)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for visualizations",
    )

    args = parser.parse_args()

    if args.mode == "full":
        run_full_pipeline(args.json_path, args.output_dir)
    elif args.mode == "build":
        kg = build_knowledge_graph(args.json_path)
        print(json_summary(kg))
    elif args.mode == "gat":
        kg = build_knowledge_graph(args.json_path)
        discoveries = run_gat_discovery(kg)
        print(f"Discovered {len(discoveries)} hidden relations.")
    elif args.mode == "anomaly":
        kg = build_knowledge_graph(args.json_path)
        results = run_anomaly_trace(kg)
        print(f"Traced {len(results)} anomalies.")
    elif args.mode == "visualize":
        kg = build_knowledge_graph(args.json_path)
        run_visualization(kg, args.output_dir)
    elif args.mode == "demo":
        run_demo()
    elif args.mode == "test":
        run_tests()


def json_summary(kg):
    import json
    return json.dumps(kg.summary(), indent=2)


if __name__ == "__main__":
    main()
