#!/usr/bin/env python3
"""
Unit tests for GenBFKit Extension Interface modules.
Run with: python -m pytest tests/ -v
"""

import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

# Add module to path
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_parent_dir = os.path.dirname(_script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Extension_interface_of_advanced_function import (
    DataDictionary,
    DataPoolType,
    STANDARD_DATA_POOLS,
    ONNXEngine,
    ModelRegistry,
    FeatureAssembler,
    FeatureSpec,
    InferencePipeline,
    DataBus,
    DataMessage,
    MessageType,
    DigitalTwinAdapter, TwinDataFrame,
    LLMAdapter,
    LLMContext,
    ClosedLoopEngine,
    LoopPhase,
    SchemaManager,
    DictionaryCRUD,
    DataMapper,
    MappingRule,
    ExtensionConfig,
)


# ======================================================================
# Tests: Core Data Dictionary
# ======================================================================

class TestDataDictionary:
    def test_create_prebuilt(self):
        dd = DataDictionary.create_prebuilt()
        assert len(dd.work_types) == 8
        assert len(dd.pools) == 9
        assert "Slag treating" in dd.work_types
        assert "Continuous time-series data" in dd.pools

    def test_summary(self):
        dd = DataDictionary.create_prebuilt()
        s = dd.summary()
        assert s["work_types"] == 8
        assert s["pools"] == 9
        assert s["attributes"] > 0

    def test_chain_query(self):
        dd = DataDictionary.create_prebuilt()
        result = dd.chain_query(work_type="Slag treating")
        assert result.work_type is not None
        assert result.work_type.name_en == "Slag treating"

    def test_search_datasets(self):
        dd = DataDictionary.create_prebuilt()
        results = dd.search_datasets("temperature")
        assert isinstance(results, list)

    def test_pool_base_attributes(self):
        from Extension_interface_of_advanced_function.core.data_dictionary import POOL_BASE_ATTRIBUTES
        assert "Continuous time-series data" in POOL_BASE_ATTRIBUTES
        assert "Timestamp" in POOL_BASE_ATTRIBUTES["Continuous time-series data"]


# ======================================================================
# Tests: Model Deployment
# ======================================================================

def create_test_onnx(tmp_path):
    """Create a minimal ONNX model for testing."""
    import onnx
    from onnx import helper, TensorProto

    X = helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 1])
    W_init = helper.make_tensor("W", TensorProto.FLOAT, [1, 1], [2.0])
    B_init = helper.make_tensor("B", TensorProto.FLOAT, [1], [1.0])
    Y = helper.make_tensor_value_info("output", TensorProto.FLOAT, [None, 1])

    matmul = helper.make_node("MatMul", ["input", "W"], ["matmul_out"])
    add = helper.make_node("Add", ["matmul_out", "B"], ["output"])

    graph = helper.make_graph(
        [matmul, add], "test", [X], [Y],
        initializer=[W_init, B_init],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8

    model_path = os.path.join(tmp_path, "test_model.onnx")
    onnx.save(model, model_path)
    return model_path


class TestONNXEngine:
    def test_load_and_infer(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        engine = ONNXEngine(model_path)
        info = engine.load()
        assert info.input_names == ["input"]
        assert info.output_names == ["output"]
        assert engine.is_loaded

        # Inference
        result = engine.infer({"input": np.random.randn(3, 1).astype(np.float32)})
        assert "output" in result
        assert result["output"].shape == (3, 1)

        engine.unload()
        assert not engine.is_loaded

    def test_batch_inference(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        engine = ONNXEngine(model_path)
        engine.load()

        result = engine.infer_batch(
            {"input": np.random.randn(50, 1).astype(np.float32)},
            batch_size=16,
        )
        assert result["output"].shape == (50, 1)

        engine.unload()

    def test_avg_inference_time(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        engine = ONNXEngine(model_path)
        engine.load()

        for _ in range(5):
            engine.infer({"input": np.random.randn(10, 1).astype(np.float32)})

        avg_time = engine.get_avg_inference_time()
        assert avg_time > 0

        engine.unload()

    def test_context_manager(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        with ONNXEngine(model_path) as engine:
            assert engine.is_loaded
            result = engine.infer({"input": np.random.randn(2, 1).astype(np.float32)})
            assert "output" in result
        assert not engine.is_loaded


class TestModelRegistry:
    def test_register_and_load(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        registry = ModelRegistry(models_dir=str(tmp_path))

        meta = registry.register(
            "test_model", model_path, version="1.0",
            task_type="regression", tags={"domain": "test"},
            auto_load=True,
        )
        assert meta.model_id == "test_model"
        assert meta.onnx_info is not None

        engine = registry.get_engine("test_model")
        assert engine.is_loaded

    def test_list_models(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        registry = ModelRegistry(models_dir=str(tmp_path))
        registry.register("m1", model_path, auto_load=False)
        registry.register("m2", model_path, task_type="classification", auto_load=False)

        models = registry.list_models()
        assert len(models) == 2

        models_cls = registry.list_models(task_type="classification")
        assert len(models_cls) == 1

    def test_find_by_tag(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        registry = ModelRegistry(models_dir=str(tmp_path))
        registry.register("m1", model_path, tags={"env": "prod"}, auto_load=False)
        registry.register("m2", model_path, tags={"env": "test"}, auto_load=False)

        results = registry.find_by_tag("env", "prod")
        assert len(results) == 1
        assert results[0].model_id == "m1"

    def test_unregister(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        registry = ModelRegistry(models_dir=str(tmp_path))
        registry.register("m1", model_path, auto_load=True)

        assert registry.unregister("m1") is True
        assert registry.unregister("nonexistent") is False


class TestFeatureAssembler:
    def test_declare_and_assemble(self):
        dd = DataDictionary.create_prebuilt()
        assembler = FeatureAssembler(dd)

        assembler.declare_features([
            FeatureSpec(name="feat_1", shape=(-1,), normalizer="none"),
            FeatureSpec(name="feat_2", shape=(-1,), normalizer="zscore"),
        ])

        df = pd.DataFrame({
            "feat_1": [1.0, 2.0, 3.0],
            "feat_2": [10.0, 20.0, 30.0],
        })

        result = assembler.assemble(df, fit_normalizer=True)
        assert "feat_1" in result
        assert "feat_2" in result
        assert result["feat_1"].shape == (3,)

    def test_normalizer_zscore(self):
        assembler = FeatureAssembler()
        assembler.declare_features([
            FeatureSpec(name="x", shape=(-1,), normalizer="zscore"),
        ])

        df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0]})
        result = assembler.assemble(df, fit_normalizer=True)

        # Z-score normalized: mean should be ~0, std ~1
        assert abs(result["x"].mean()) < 1e-6
        assert abs(result["x"].std() - 1.0) < 1e-6


class TestInferencePipeline:
    def test_configure_and_run(self, tmp_path):
        model_path = create_test_onnx(tmp_path)
        engine = ONNXEngine(model_path)
        engine.load()

        pipeline = InferencePipeline()
        pipeline.configure(
            engine=engine,
            features=[FeatureSpec(name="input", shape=(-1, 1), normalizer="none")],
            pipeline_name="test_pipeline",
        )

        df = pd.DataFrame({"input": np.random.randn(5).astype(np.float32)})

        result = pipeline.run(df, fit_normalizer=False)
        assert result.success
        assert len(result.predictions) > 0
        assert result.processing_time_ms > 0


# ======================================================================
# Tests: System Integration
# ======================================================================

class TestDataBus:
    def test_publish_subscribe(self):
        bus = DataBus()
        received = []

        def callback(msg):
            received.append(msg)

        bus.subscribe("test", callback)
        msg = DataMessage(channel="test", payload={"key": "value"})
        count = bus.publish(msg)

        assert count == 1
        assert len(received) == 1
        assert received[0].payload["key"] == "value"

    def test_message_filtering(self):
        bus = DataBus()
        received = []

        def callback(msg):
            received.append(msg)

        bus.subscribe("test", callback, message_type=MessageType.ANOMALY_ALERT)

        # Publish different type - should not be received
        bus.publish(DataMessage(channel="test", message_type=MessageType.DATA_PUSH))
        assert len(received) == 0

        # Publish matching type - should be received
        bus.publish(DataMessage(channel="test", message_type=MessageType.ANOMALY_ALERT))
        assert len(received) == 1

    def test_channel_stats(self):
        bus = DataBus()
        bus.subscribe("ch1", lambda m: None)
        bus.subscribe("ch2", lambda m: None)
        bus.subscribe("ch2", lambda m: None)

        stats = bus.channel_stats()
        assert stats["ch1"] == 1
        assert stats["ch2"] == 2

    def test_dataframe_conversion(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        msg = DataBus.dataframe_to_message(df, channel="test")
        assert msg.message_type == MessageType.DATA_PUSH
        assert len(msg.payload) == 2


class TestDigitalTwinAdapter:
    def test_mock_push(self):
        adapter = DigitalTwinAdapter(use_mock=True)
        frame = TwinDataFrame(
            frame_id="test_001",
            data={"temperature": 1500},
        )
        result = adapter.push_measurements(frame)
        assert result["success"] is True
        assert result["frame_id"] == "test_001"

    def test_mock_pull_strategy(self):
        adapter = DigitalTwinAdapter(use_mock=True)
        strategy = adapter.pull_strategy()
        assert strategy["success"] is True
        assert "parameters" in strategy


class TestLLMAdapter:
    def test_mock_query_strategy(self):
        adapter = LLMAdapter(use_mock=True)
        ctx = LLMContext(query="Temperature is low, suggest adjustments")
        response = adapter.query_strategy(ctx)
        assert response.success
        assert len(response.content) > 0

    def test_mock_query_diagnosis(self):
        adapter = LLMAdapter(use_mock=True)
        ctx = LLMContext(query="Anomaly detected in cooling system")
        response = adapter.query_diagnosis(ctx)
        assert response.success

    def test_parse_decision_command(self):
        adapter = LLMAdapter(use_mock=True)
        ctx = LLMContext(query="Temperature is low")
        response = adapter.query_strategy(ctx)
        commands = adapter.parse_decision_command(response)
        assert "commands" in commands


class TestClosedLoopEngine:
    def test_execute_full_loop(self):
        bus = DataBus()
        llm = LLMAdapter(use_mock=True)
        twin = DigitalTwinAdapter(use_mock=True)

        engine = ClosedLoopEngine(
            data_bus=bus,
            llm_adapter=llm,
            twin_adapter=twin,
            auto_feedback=True,
        )

        df = pd.DataFrame({
            "a": np.random.randn(50),
            "b": np.random.randn(50),
            "c": np.random.randn(50),
        })

        ctx = engine.execute(df, loop_id="test_loop")
        assert ctx.current_phase == LoopPhase.COMPLETED
        assert ctx.analysis_result != {}
        assert ctx.decision_result != {}
        assert ctx.feedback_result != {}

    def test_custom_handler(self):
        engine = ClosedLoopEngine(auto_feedback=False)

        def custom_analysis(ctx):
            ctx.analysis_result["custom"] = "done"

        engine.register_handler(LoopPhase.INTELLIGENT_ANALYSIS, custom_analysis)

        df = pd.DataFrame({"x": [1, 2, 3]})
        ctx = engine.execute(df)
        assert ctx.analysis_result.get("custom") == "done"


# ======================================================================
# Tests: Data Extension
# ======================================================================

class TestSchemaManager:
    def test_validate_work_type(self):
        schema = SchemaManager()
        assert not schema.validate_work_type("").is_valid
        assert schema.validate_work_type("Valid Name").is_valid

    def test_validate_category_naming(self):
        schema = SchemaManager()
        result = schema.validate_category("System - Equipment - Function", "test")
        assert result.is_valid

        result = schema.validate_category("simple_name", "test")
        # Should have warning about naming convention
        assert len(result.warnings) >= 1

    def test_validate_pool(self):
        schema = SchemaManager()
        result = schema.validate_pool("Continuous time-series data")
        assert result.is_valid

        result = schema.validate_pool("Custom pool")
        assert len(result.warnings) >= 1  # Not standard pool

    def test_validate_hierarchy(self):
        schema = SchemaManager()
        result = schema.validate_hierarchy_integrity(
            {"work_types": 8, "datasets": 2000},
            {"work_types": 1, "datasets": 100},
        )
        assert result.is_valid

        result = schema.validate_hierarchy_integrity(
            {"work_types": 19, "datasets": 1000},
            {"work_types": 5, "datasets": 100},
        )
        assert not result.is_valid  # exceeds max


class TestDictionaryCRUD:
    def test_add_work_type(self):
        dd = DataDictionary.create_prebuilt()
        crud = DictionaryCRUD(dd)

        ok, msg = crud.add_work_type("Test Work Type", "测试工种")
        assert ok
        assert "Test Work Type" in dd.work_types

        # Duplicate
        ok, msg = crud.add_work_type("Test Work Type")
        assert not ok

    def test_add_category(self):
        dd = DataDictionary.create_prebuilt()
        crud = DictionaryCRUD(dd)

        # Add work type first
        crud.add_work_type("WT1", "工种1")

        ok, msg = crud.add_category("WT1", "System - Equipment - Monitoring", "系统-设备-监测")
        assert ok

        # Duplicate
        ok, msg = crud.add_category("WT1", "System - Equipment - Monitoring")
        assert not ok

    def test_add_dataset(self):
        dd = DataDictionary.create_prebuilt()
        crud = DictionaryCRUD(dd)
        crud.add_work_type("WT1")
        crud.add_category("WT1", "Cat1")

        ok, msg = crud.add_dataset("WT1", "Cat1", "Continuous time-series data", "test_param")
        assert ok

        # Duplicate
        ok, msg = crud.add_dataset("WT1", "Cat1", "Continuous time-series data", "test_param")
        assert not ok

    def test_bulk_add(self):
        dd = DataDictionary.create_prebuilt()
        crud = DictionaryCRUD(dd)
        crud.add_work_type("WT1")
        crud.add_category("WT1", "Cat1")

        datasets = [
            {"work_type_en": "WT1", "category_en": "Cat1",
             "pool_en": "Continuous time-series data", "dataset_en": f"param_{i}"}
            for i in range(5)
        ]
        result = crud.bulk_add_datasets(datasets)
        assert result["success"] == 5

    def test_search(self):
        dd = DataDictionary.create_prebuilt()
        crud = DictionaryCRUD(dd)
        result = crud.search("slag")
        assert len(result["work_types"]) > 0 or len(result["datasets"]) > 0


class TestDataMapper:
    def test_auto_discover(self):
        dd = DataDictionary.create_prebuilt()
        # Add some test datasets
        dd.add_dataset_from_kwargs = lambda **kw: None  # mock
        mapper = DataMapper(dd)

        rules = mapper.auto_discover_rules(["temperature", "pressure", "unknown_sensor"])
        assert isinstance(rules, list)

    def test_detect_pool_type(self):
        mapper = DataMapper()

        # Time-series data with timestamp
        df_ts = pd.DataFrame({"timestamp": [1, 2, 3], "value": [10, 20, 30]})
        pool = mapper.detect_pool_type(df_ts)
        assert "time-series" in pool.lower() or "continuous" in pool.lower()

        # Image data
        df_img = pd.DataFrame({"image_id": ["a", "b"], "capture_time": [1, 2]})
        pool = mapper.detect_pool_type(df_img)
        assert "image" in pool.lower()

    def test_mapping_result(self):
        mapper = DataMapper()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = mapper.map_dataframe(df, rules=[
            MappingRule(source_column="a", target_dataset="param_a"),
        ])
        assert result.mapped_columns == 1
        assert "b" in result.unmapped_columns


class TestExtensionConfig:
    def test_from_env(self):
        os.environ["GENBFKIT_LOG_LEVEL"] = "DEBUG"
        config = ExtensionConfig.from_env()
        assert config.log_level == "DEBUG"

    def test_to_dict(self):
        config = ExtensionConfig(server_port=9090)
        d = config.to_dict()
        assert d["server_port"] == 9090


if __name__ == "__main__":
    pytest.main([__file__, "-v"])