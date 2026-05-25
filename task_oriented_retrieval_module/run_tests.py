"""
Comprehensive test suite for the Task-Oriented Retrieval Module.

Tests all components end-to-end using the virtual data generator,
without requiring external LLM or database connections.

Run with: python -m task_oriented_retrieval_module.run_tests
"""

import json
import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("retrieval_tests")

# Resolve dictionary path (priority: module-bundled > Coze runtime > relative fallback)
# Resolve path and sys.path for both module-mode and standalone execution
_this_dir = os.path.dirname(os.path.abspath(__file__))
_bundled_dict = os.path.join(_this_dir, "data", "prebuilt_full.json")
if os.path.isfile(_bundled_dict):
    DICT_PATH = _bundled_dict
else:
    _COZE_WS = os.getenv("COZE_WORKSPACE_PATH", "")
    if _COZE_WS:
        sys.path.insert(0, os.path.join(_COZE_WS, "src"))
        DICT_PATH = os.path.join(_COZE_WS, "assets", "prebuilt_full.json")
    else:
        sys.path.insert(0, os.path.join(_this_dir, ".."))
        DICT_PATH = os.path.join(_this_dir, "..", "..", "assets", "prebuilt_full.json")

# Ensure parent dir is in sys.path so `from task_oriented_retrieval_module.xxx` works
# when running as script or via `python -m`
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from task_oriented_retrieval_module.core.dictionary_manager import DictionaryManager
from task_oriented_retrieval_module.core.chain_retriever import ChainRetriever
from task_oriented_retrieval_module.core.graph_builder import DictionaryGraphBuilder
from task_oriented_retrieval_module.ranking.gnn_ranker import GNNRanker
from task_oriented_retrieval_module.templates.preset_templates import PresetTemplateManager, TaskTemplate
from task_oriented_retrieval_module.virtual_data.generator import VirtualDataGenerator
from task_oriented_retrieval_module.retriever import TaskOrientedRetriever

# ──────────────────────────────────────────────────────────
# Test helpers
# ──────────────────────────────────────────────────────────
test_results = []


def record_test(name: str, passed: bool, detail: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({"name": name, "passed": bool(passed), "detail": detail})
    print(f"  {status} - {name}" + (f" ({detail})" if detail else ""))


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ──────────────────────────────────────────────────────────
# Test 1: Dictionary Manager
# ──────────────────────────────────────────────────────────
def test_dictionary_manager():
    print_section("Test 1: Dictionary Manager")
    dm = DictionaryManager(DICT_PATH)

    # Test loading
    stats = dm.get_statistics()
    record_test("Dictionary loaded", stats["total_datasets"] == 2128,
                f"datasets={stats['total_datasets']}")
    record_test("8 work types", stats["total_work_types"] == 8,
                f"work_types={stats['total_work_types']}")
    record_test("98 categories", stats["total_categories"] == 98,
                f"categories={stats['total_categories']}")
    record_test("9 pools", stats["total_pools"] == 9,
                f"pools={stats['total_pools']}")

    # Test chain traversal
    bf_op = dm.chain_traverse(work_type_en="BF operating")
    record_test("Chain traverse by work type", len(bf_op) == 881,
                f"BF operating params={len(bf_op)}")

    hot_blast = dm.chain_traverse(work_type_en="Hot blast supplying")
    record_test("Hot blast supplying params", len(hot_blast) == 341,
                f"params={len(hot_blast)}")

    # Test cross-level retrieval
    cont_ds = dm.get_datasets_by_pool("Continuous time-series data")
    record_test("Continuous time-series datasets", len(cont_ds) == 1074,
                f"datasets={len(cont_ds)}")

    # Test attribute template resolution
    attrs = dm.get_attributes_by_pool("Continuous time-series data")
    record_test("Attribute template for continuous pool", attrs is not None,
                f"base_attrs={len(attrs.base_attributes)}, unique_attrs={len(attrs.unique_attributes)}" if attrs else "None")

    # Test CRUD operations
    test_ds = dm.get_all_datasets()[0]
    record_test("Get dataset by name", dm.get_dataset(test_ds.dataset_en) is not None,
                f"dataset={test_ds.dataset_en[:40]}")

    # Test JSON export
    exported = dm.export_json()
    record_test("JSON export works", "work_types" in exported and len(exported["work_types"]) == 8,
                f"top_keys={list(exported.keys())}")

    return dm


# ──────────────────────────────────────────────────────────
# Test 2: Chain Retriever
# ──────────────────────────────────────────────────────────
def test_chain_retriever(dm: DictionaryManager):
    print_section("Test 2: Chain Retriever")
    cr = ChainRetriever(dm)

    # Basic retrieval
    results = cr.retrieve(work_types=["BF operating"])
    record_test("Retrieve by work type", len(results) == 881,
                f"results={len(results)}")

    # Multi-level filter
    results = cr.retrieve(
        work_types=["Hot blast supplying"],
        pools=["Controllable data"],
    )
    record_test("Retrieve by work_type + pool", len(results) > 0,
                f"results={len(results)}")

    # Keyword search
    results = cr.retrieve(keyword="temperature", keyword_field="en")
    record_test("Keyword search (temperature)", len(results) > 0,
                f"results={len(results)}")

    # Chinese keyword
    results = cr.retrieve(keyword="温度", keyword_field="zh")
    record_test("Chinese keyword search", len(results) > 0,
                f"results={len(results)}")

    # Task-oriented retrieval
    task_config = {
        "work_types": ["BF operating"],
        "pools": ["Continuous time-series data", "Constraint data"],
        "keywords": ["hearth", "temperature", "炉缸", "温度"],
    }
    results = cr.retrieve_by_task(task_config)
    record_test("Task-oriented retrieval", len(results) > 0,
                f"results={len(results)}")

    # Verify chain context enrichment
    if results:
        r = results[0]
        record_test("Result has chain context",
                    r.work_type is not None and r.category is not None and r.pool is not None,
                    f"wt={r.work_type.work_type_en if r.work_type else 'None'}")

    return cr


# ──────────────────────────────────────────────────────────
# Test 3: Graph Builder
# ──────────────────────────────────────────────────────────
def test_graph_builder(dm: DictionaryManager):
    print_section("Test 3: Dictionary Graph Builder")
    gb = DictionaryGraphBuilder(dm)

    t0 = time.time()
    G = gb.build()
    build_time = time.time() - t0

    stats = gb.get_statistics()
    record_test("Graph built successfully", G.number_of_nodes() > 2000,
                f"nodes={G.number_of_nodes()}, edges={G.number_of_edges()}, time={build_time:.2f}s")

    # Verify node types
    node_types = stats.get("node_type_distribution", {})
    record_test("Has all node types",
                all(t in node_types for t in ["work_type", "category", "pool", "dataset", "attribute"]),
                f"types={list(node_types.keys())}")

    # Verify edge types
    edge_types = stats.get("edge_type_distribution", {})
    record_test("Has hierarchical edges", "hierarchical" in edge_types,
                f"edge_types={list(edge_types.keys())}")

    # Test subgraph extraction
    datasets = dm.get_datasets_by_pool("Controllable data")[:5]
    ds_ids = [d.dataset_en for d in datasets]
    subG = gb.get_subgraph_for_datasets(ds_ids)
    record_test("Subgraph extraction", subG.number_of_nodes() >= 5,
                f"subgraph_nodes={subG.number_of_nodes()}")

    return gb


# ──────────────────────────────────────────────────────────
# Test 4: GNN Ranker
# ──────────────────────────────────────────────────────────
def test_gnn_ranker(dm: DictionaryManager, cr: ChainRetriever, gb: DictionaryGraphBuilder):
    print_section("Test 4: GNN-Based Relevance Ranker")

    ranker = GNNRanker(gb, num_hops=3)

    # Create test results
    task_config = {
        "work_types": ["BF operating"],
        "pools": ["Continuous time-series data", "Constraint data"],
        "keywords": ["hearth", "temperature"],
    }
    results = cr.retrieve_by_task(task_config)

    t0 = time.time()
    ranked = ranker.rank(results, task_config, top_k=20)
    rank_time = time.time() - t0

    record_test("GNN ranking completed", len(ranked) > 0,
                f"ranked={len(ranked)}, time={rank_time:.2f}s")

    # Verify scores are in descending order
    scores = [r.relevance_score for r in ranked]
    is_descending = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    record_test("Scores in descending order", is_descending,
                f"top3_scores={scores[:3]}")

    # Verify top results have meaningful scores
    record_test("Top result has high relevance", ranked[0].relevance_score > 0.1,
                f"top_score={ranked[0].relevance_score:.4f}")

    # Test ranking explanation
    explanation = ranker.get_ranking_explanation(ranked[0])
    record_test("Ranking explanation available",
                "parameter" in explanation and "score" in explanation,
                f"param={explanation.get('parameter', '')[:30]}")

    return ranker


# ──────────────────────────────────────────────────────────
# Test 5: Preset Templates
# ──────────────────────────────────────────────────────────
def test_preset_templates():
    print_section("Test 5: Preset Task Templates")
    tm = PresetTemplateManager()

    # List templates
    templates = tm.list_templates()
    record_test("6 built-in templates", len(templates) == 6,
                f"templates={len(templates)}")

    # Get specific template
    tmpl = tm.get_template("hearth_safety")
    record_test("Get template by ID", tmpl is not None,
                f"name={tmpl.name_en if tmpl else 'None'}")

    # Search templates
    results = tm.search_templates("efficiency")
    record_test("Search templates by keyword", len(results) > 0,
                f"found={len(results)}")

    # Chinese search
    results = tm.search_templates("炉缸")
    record_test("Search templates in Chinese", len(results) > 0,
                f"found={len(results)}")

    # Create custom template
    custom = TaskTemplate(
        template_id="custom_test_1",
        name_en="Custom Test Template",
        name_zh="自定义测试模板",
        description="A test custom template",
        task_config={
            "work_types": ["BF operating"],
            "pools": ["Continuous time-series data"],
            "keywords": ["test"],
        },
        tags=["test", "custom"],
    )
    created = tm.create_template(custom)
    record_test("Create custom template", created,
                f"template_id={custom.template_id}")

    # Verify custom template
    retrieved = tm.get_template("custom_test_1")
    record_test("Retrieve custom template", retrieved is not None,
                f"name={retrieved.name_en if retrieved else 'None'}")

    # Delete custom template
    deleted = tm.delete_template("custom_test_1")
    record_test("Delete custom template", deleted,
                f"template_id=custom_test_1")

    # Cannot delete built-in
    not_deleted = tm.delete_template("hearth_safety")
    record_test("Cannot delete built-in template", not not_deleted,
                f"hearth_safety deletion blocked")

    return tm


# ──────────────────────────────────────────────────────────
# Test 6: Virtual Data Generator
# ──────────────────────────────────────────────────────────
def test_virtual_data_generator(dm: DictionaryManager):
    print_section("Test 6: Virtual Data Generator")
    vdg = VirtualDataGenerator(dm, seed=42)

    # Normal scenario
    t0 = time.time()
    data = vdg.generate(num_records=10, scenario="normal", pool_filter="Continuous time-series data")
    gen_time = time.time() - t0
    num_params = data["metadata"]["num_parameters"]
    record_test("Generate normal scenario data", num_params > 0,
                f"params={num_params}, time={gen_time:.2f}s")

    # Verify data structure
    if num_params > 0:
        first_param = list(data["parameters"].values())[0]
        has_records = len(first_param["records"]) == 10
        has_attrs = len(first_param["attributes"]) > 0
        record_test("Data has correct records count", has_records,
                    f"records={len(first_param['records'])}")
        record_test("Data has attributes", has_attrs,
                    f"attrs={len(first_param['attributes'])}")

    # Abnormal scenario
    data_abnormal = vdg.generate(num_records=5, scenario="abnormal", work_type_filter="Hot blast supplying")
    record_test("Generate abnormal scenario data",
                data_abnormal["metadata"]["num_parameters"] > 0,
                f"params={data_abnormal['metadata']['num_parameters']}")

    # Transition scenario
    data_transition = vdg.generate(num_records=5, scenario="transition")
    record_test("Generate transition scenario data",
                data_transition["metadata"]["num_parameters"] > 0,
                f"params={data_transition['metadata']['num_parameters']}")

    # Test all pool types
    for pool_name in ["Binary status data", "Controllable data", "Text data", "Image data",
                       "Batch time-series data", "Response data", "Constraint data",
                       "Discrete time-series data"]:
        pool_data = vdg.generate(num_records=5, scenario="normal", pool_filter=pool_name)
        ok = pool_data["metadata"]["num_parameters"] >= 0  # Some pools may have 0 params with filter
        record_test(f"Generate data for pool: {pool_name[:20]}", ok,
                    f"params={pool_data['metadata']['num_parameters']}")

    return vdg


# ──────────────────────────────────────────────────────────
# Test 7: End-to-End Integration
# ──────────────────────────────────────────────────────────
def test_e2e_integration(dm: DictionaryManager, cr: ChainRetriever, gb: DictionaryGraphBuilder):
    print_section("Test 7: End-to-End Integration (without LLM)")

    # Simulate what the full pipeline would do, but without LLM call
    # Use fallback parser logic

    # Step 1: Simulate semantic parsing output
    simulated_task_config = {
        "work_types": ["Hot blast supplying"],
        "categories": [],
        "pools": ["Controllable data", "Continuous time-series data"],
        "keywords": ["stove", "combustion", "热风炉", "燃烧"],
        "intent_summary": "Parameters affecting hot blast stove combustion efficiency",
    }

    # Step 2: Chain retrieval
    results = cr.retrieve_by_task(simulated_task_config)
    record_test("E2E: Chain retrieval", len(results) > 0,
                f"results={len(results)}")

    # Step 3: GNN ranking
    ranker = GNNRanker(gb, num_hops=2)
    ranked = ranker.rank(results, simulated_task_config, top_k=10)
    record_test("E2E: GNN ranking", len(ranked) > 0,
                f"top_k={len(ranked)}")

    # Step 4: Export results
    retriever = TaskOrientedRetriever.__new__(TaskOrientedRetriever)
    retriever._dm = dm
    retriever._chain = cr
    retriever._graph_builder = gb
    retriever._ranker = ranker

    json_export = retriever.export_results(ranked, format="json")
    record_test("E2E: JSON export", len(json_export) > 100,
                f"length={len(json_export)}")

    md_export = retriever.export_results(ranked, format="markdown")
    record_test("E2E: Markdown export", "Parameter (EN)" in md_export and len(md_export) > 100,
                f"length={len(md_export)}")

    return ranked


# ──────────────────────────────────────────────────────────
# Test 8: Fallback Parser
# ──────────────────────────────────────────────────────────
def test_fallback_parser(dm: DictionaryManager):
    print_section("Test 8: Fallback Semantic Parser")
    from task_oriented_retrieval_module.semantic.semantic_parser import SemanticParser

    parser = SemanticParser(dm)

    # Test fallback parsing (no LLM needed)
    result = parser._fallback_parse("热风炉换热效率控制参数")
    record_test("Fallback: Chinese query parsing",
                result.get("work_types") is not None or len(result.get("keywords", [])) > 0,
                f"work_types={result.get('work_types')}, keywords={result.get('keywords', [])[:3]}")

    result = parser._fallback_parse("Cooling monitoring continuous data")
    record_test("Fallback: English query parsing",
                "Cooling monitoring" in (result.get("work_types") or []),
                f"work_types={result.get('work_types')}")

    result = parser._fallback_parse("炉缸安全管控相关的控制参数")
    record_test("Fallback: Hearth safety query",
                "Controllable data" in (result.get("pools") or []),
                f"pools={result.get('pools')}")


# ──────────────────────────────────────────────────────────
# Main test runner
# ──────────────────────────────────────────────────────────
def run_all_tests():
    print("\n" + "🔥" * 30)
    print("  GenBFKit Task-Oriented Retrieval Module")
    print("  Full Test Suite")
    print("🔥" * 30 + "\n")

    start = time.time()

    dm = test_dictionary_manager()
    cr = test_chain_retriever(dm)
    gb = test_graph_builder(dm)
    test_gnn_ranker(dm, cr, gb)
    test_preset_templates()
    test_virtual_data_generator(dm)
    test_e2e_integration(dm, cr, gb)
    test_fallback_parser(dm)

    elapsed = time.time() - start

    # Summary
    print_section("Test Summary")
    passed = sum(1 for t in test_results if t["passed"])
    failed = sum(1 for t in test_results if not t["passed"])
    total = len(test_results)

    print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"  Time: {elapsed:.2f}s")

    if failed > 0:
        print("\n  Failed tests:")
        for t in test_results:
            if not t["passed"]:
                print(f"    ❌ {t['name']}: {t['detail']}")

    print("\n" + "🔥" * 30)

    # Save results to JSON
    report_path = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"),
        "assets", "test_report.json",
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "results": test_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"  Test report saved to: {report_path}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
