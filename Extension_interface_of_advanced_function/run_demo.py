#!/usr/bin/env python3
"""
GenBFKit Extension Interface - 综合演示脚本

演示三大扩展接口模块的核心功能：
1. 自定义算法部署 (model_deployment)
2. 上层系统对接 (system_integration)
3. 底层数据架构拓展 (data_extension)

可作为独立脚本直接运行：
    python run_demo.py
"""

import json
import logging
import sys
import os
import tempfile
from pathlib import Path

# ── 确保模块可独立导入 ──
_script_dir = Path(__file__).resolve().parent
_parent_dir = _script_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

import numpy as np
import pandas as pd

from Extension_interface_of_advanced_function import (
    # Core
    DataDictionary,
    DataPoolType,
    STANDARD_DATA_POOLS,
    POOL_BASE_ATTRIBUTES,
    # Model Deployment
    ONNXEngine,
    ModelRegistry,
    ModelMetadata,
    FeatureAssembler,
    FeatureSpec,
    InferencePipeline,
    InferenceResult,
    # System Integration
    DataBus,
    DataMessage,
    MessageType,
    DigitalTwinAdapter,
    TwinDataFrame,
    LLMAdapter,
    LLMContext,
    LLMResponse,
    ClosedLoopEngine,
    LoopPhase,
    # Data Extension
    SchemaManager,
    SchemaValidationResult,
    DictionaryCRUD,
    DataMapper,
    MappingRule,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("GenBFKit-Demo")

SEPARATOR = "\n" + "=" * 70


def create_sample_onnx_model() -> str:
    """创建一个简单的 ONNX 测试模型（线性回归：标量输入输出）。"""
    import onnx
    from onnx import helper, TensorProto

    # 构建简单的线性模型: output = w * input + b
    # input: (N, 1), output: (N, 1)
    X = helper.make_tensor_value_info("input", TensorProto.FLOAT, [None, 1])
    W_init = helper.make_tensor("W", TensorProto.FLOAT, [1, 1],
                                [2.0])  # w = 2.0
    B_init = helper.make_tensor("B", TensorProto.FLOAT, [1],
                                [1.0])  # b = 1.0
    Y = helper.make_tensor_value_info("output", TensorProto.FLOAT, [None, 1])

    matmul = helper.make_node("MatMul", ["input", "W"], ["matmul_out"], name="matmul")
    add = helper.make_node("Add", ["matmul_out", "B"], ["output"], name="add")

    graph = helper.make_graph(
        [matmul, add],
        "linear_model",
        [X],
        [Y],
        initializer=[W_init, B_init],
    )

    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8

    # 保存
    model_path = os.path.join(tempfile.gettempdir(), "test_model.onnx")
    onnx.save(model, model_path)
    logger.info(f"Created sample ONNX model at: {model_path}")
    return model_path


def demo_model_deployment():
    """演示自定义算法部署模块。"""
    print(SEPARATOR)
    print("📦 MODULE 1: Custom Algorithm Deployment (自定义算法部署)")
    print(SEPARATOR)

    # 1.1 创建数据字典
    print("\n[1.1] Creating prebuilt data dictionary...")
    data_dict = DataDictionary.create_prebuilt()
    summary = data_dict.summary()
    print(f"    Data dictionary loaded: {summary}")

    # 1.2 创建 ONNX 模型并注册
    print("\n[1.2] Creating and registering ONNX model...")
    model_path = create_sample_onnx_model()

    registry = ModelRegistry(models_dir=tempfile.gettempdir())
    metadata = registry.register(
        model_id="blast_temp_predictor",
        model_path=model_path,
        version="1.0.0",
        description="Blast furnace temperature prediction model",
        task_type="regression",
        tags={"domain": "blast_furnace", "subsystem": "thermal"},
        auto_load=True,
    )
    print(f"    Model registered: {metadata.model_id} (v{metadata.version})")
    print(f"    ONNX info: {metadata.onnx_info.to_dict() if metadata.onnx_info else 'N/A'}")

    # 1.3 特征组装器
    print("\n[1.3] Configuring feature assembler...")
    assembler = FeatureAssembler(data_dict)
    assembler.declare_features([
        FeatureSpec(
            name="input",
            dtype="float32",
            shape=(-1, 4),
            description="Model input features (temperature, pressure, flow, level)",
        ),
    ])
    print(assembler.summary())

    # 1.4 推理流水线
    print("\n[1.4] Running inference pipeline...")
    engine = registry.get_engine("blast_temp_predictor")

    pipeline = InferencePipeline(data_dictionary=data_dict)
    pipeline.configure(
        engine=engine,
        features=[
            FeatureSpec(
                name="input",
                dtype="float32",
                shape=(-1, 1),
                normalizer="zscore",
            ),
        ],
        pipeline_name="temperature_prediction",
    )

    # 创建测试数据 - 单列匹配特征名
    test_data = pd.DataFrame({
        "input": np.random.randn(10).astype(np.float32),
    })

    result = pipeline.run(test_data, fit_normalizer=True)
    print(f"    Inference result: {result}")
    if result.success:
        for name, pred in result.predictions.items():
            print(f"    Prediction '{name}': shape={pred.shape}, values={pred[:3].tolist()}...")

    # 1.5 模型注册表查询
    print("\n[1.5] Model registry query...")
    all_models = registry.list_models()
    print(f"    Registered models: {len(all_models)}")
    for m in all_models:
        print(f"      - {m.model_id} (v{m.version}, {m.task_type})")

    registry_export_path = os.path.join(tempfile.gettempdir(), "model_registry.json")
    registry.export_registry(registry_export_path)
    print(f"    Registry exported to: {registry_export_path}")

    # 清理
    engine.unload()
    print("\n✅ Model deployment demo completed!")


def demo_system_integration():
    """演示上层系统对接模块。"""
    print(SEPARATOR)
    print("🔗 MODULE 2: Upper-level System Integration (上层系统对接)")
    print(SEPARATOR)

    # 2.1 数据总线
    print("\n[2.1] Data bus (publish-subscribe)...")
    bus = DataBus()
    received_messages = []

    def on_message(msg: DataMessage):
        received_messages.append(msg)
        payload_summary = str(msg.payload)[:80] if msg.payload else "N/A"
        print(f"      [Subscriber] Received: type={msg.message_type.value}, "
              f"channel={msg.channel}, payload={payload_summary}...")

    sub_id = bus.subscribe("blast_furnace_data", on_message, MessageType.DATA_PUSH)
    print(f"    Subscribed with id: {sub_id}")

    # 发布消息
    msg = DataMessage(
        message_type=MessageType.DATA_PUSH,
        channel="blast_furnace_data",
        source="genbfkit",
        payload={"temperature": 1520, "pressure": 0.45, "flow": 3200},
        metadata={"unit": "metric"},
    )
    delivered = bus.publish(msg)
    print(f"    Message published, delivered to {delivered} subscriber(s)")

    stats = bus.channel_stats()
    print(f"    Channel stats: {stats}")

    # 2.2 数字孪生适配器
    print("\n[2.2] Digital twin adapter...")
    twin = DigitalTwinAdapter(use_mock=True)

    frame = TwinDataFrame(
        frame_id="demo_frame_001",
        source="genbfkit_demo",
        data={
            "hot_metal_temp": 1500,
            "blast_pressure": 0.42,
            "oxygen_rate": 0.25,
            "coal_injection": 180,
        },
        metadata={"scenario": "normal_operation"},
    )
    push_result = twin.push_measurements(frame)
    print(f"    Push result: {push_result}")

    strategy = twin.pull_strategy()
    print(f"    Strategy pulled:")
    print(f"      Parameters: {strategy.get('parameters', {})}")
    print(f"      Rationale: {strategy.get('rationale', '')[:80]}...")

    # 2.3 领域大模型适配器
    print("\n[2.3] Domain LLM adapter...")
    llm = LLMAdapter(use_mock=True)

    # 查询工艺优化策略
    context = LLMContext(
        query="The current hearth temperature is decreasing. "
              "Please provide optimization strategies for hot blast temperature and oxygen enrichment.",
        parameters={"current_temp": 1480, "target_temp": 1520},
    )
    response = llm.query_strategy(context)
    print(f"    LLM response: {response.to_dict()}")

    # 解析决策指令
    commands = llm.parse_decision_command(response)
    print(f"    Parsed commands: {json.dumps(commands, indent=6, ensure_ascii=False)}")

    # 2.4 全链路闭环引擎
    print("\n[2.4] Closed-loop engine...")
    loop_engine = ClosedLoopEngine(
        data_bus=bus,
        llm_adapter=llm,
        twin_adapter=twin,
        auto_feedback=True,
    )

    # 模拟输入数据
    df = pd.DataFrame({
        "temperature": np.random.randn(100) * 50 + 1500,
        "pressure": np.random.randn(100) * 0.05 + 0.42,
        "flow_rate": np.random.randn(100) * 100 + 3200,
        "co2_level": np.random.randn(100) * 0.5 + 22.0,
    })

    loop_ctx = loop_engine.execute(df, loop_id="demo_loop_001")
    print(f"    Loop completed:")
    print(f"      ID: {loop_ctx.loop_id}")
    print(f"      Duration: {loop_ctx.elapsed_seconds:.2f}s")
    print(f"      Errors: {len(loop_ctx.errors)}")
    print(f"      Analysis: {'✓' if loop_ctx.analysis_result else '✗'}")
    print(f"      Decision: {'✓' if loop_ctx.decision_result else '✗'}")
    print(f"      Feedback: {'✓' if loop_ctx.feedback_result else '✗'}")

    print("\n✅ System integration demo completed!")


def demo_data_extension():
    """演示底层数据架构拓展模块。"""
    print(SEPARATOR)
    print("📐 MODULE 3: Data Architecture Extension (底层数据架构拓展)")
    print(SEPARATOR)

    # 3.1 创建数据字典
    print("\n[3.1] Creating data dictionary...")
    data_dict = DataDictionary.create_prebuilt()
    print(f"    Initial summary: {data_dict.summary()}")

    # 3.2 Schema 验证
    print("\n[3.2] Schema validation...")
    schema = SchemaManager()

    test_cases = [
        ("", ""),                    # 空名称
        ("New Process", "新工艺"),   # 有效
    ]
    for name_en, name_zh in test_cases:
        result = schema.validate_work_type(name_en, name_zh)
        print(f"    Work type '{name_en or '(empty)'}': {result.summary()}")

    # 验证数据类别命名规范
    cat_result = schema.validate_category("Cooling system - Water pump", "Cooling monitoring")
    print(f"    Category 'Cooling system - Water pump': {cat_result.summary()}")

    cat_result2 = schema.validate_category("simple_name", "Cooling monitoring")
    print(f"    Category 'simple_name': {cat_result2.summary()}")

    # 3.3 CRUD 操作
    print("\n[3.3] Dictionary CRUD operations...")
    crud = DictionaryCRUD(data_dict)

    # 添加工种
    ok, msg = crud.add_work_type("New process type", "新工艺类型")
    print(f"    Add work type: {msg}")

    # 添加数据类别
    ok, msg = crud.add_category(
        "New process type",
        "New system - New equipment - Temperature monitoring",
        "新系统-新设备-温度监测",
    )
    print(f"    Add category: {msg}")

    # 添加数据集
    ok, msg = crud.add_dataset(
        work_type_en="New process type",
        category_en="New system - New equipment - Temperature monitoring",
        pool_en="Continuous time-series data",
        dataset_en="cooling_water_inlet_temp",
        dataset_zh="冷却水入口温度",
    )
    print(f"    Add dataset: {msg}")

    # 添加属性
    ok, msg = crud.add_attribute(
        pool_en="Continuous time-series data",
        attribute_name="custom_sensor_id",
        data_type="string",
        description="Custom sensor identifier for new equipment",
    )
    print(f"    Add attribute: {msg}")

    # 关键词搜索
    search_result = crud.search("temperature")
    print(f"    Search 'temperature':")
    print(f"      Datasets: {search_result['datasets'][:5]}")
    print(f"      Attributes: {search_result['attributes'][:5]}")

    # 批量添加
    print("\n[3.4] Bulk dataset import...")
    new_datasets = [
        {
            "work_type_en": "New process type",
            "category_en": "New system - New equipment - Temperature monitoring",
            "pool_en": "Continuous time-series data",
            "dataset_en": "cooling_water_outlet_temp",
            "dataset_zh": "冷却水出口温度",
        },
        {
            "work_type_en": "New process type",
            "category_en": "New system - New equipment - Temperature monitoring",
            "pool_en": "Continuous time-series data",
            "dataset_en": "cooling_tower_temp_differential",
            "dataset_zh": "冷却塔温差",
        },
    ]
    bulk_result = crud.bulk_add_datasets(new_datasets)
    print(f"    Bulk add: {bulk_result['success']} success, {bulk_result['failed']} failed")

    # 最终统计
    print(f"\n    Final dictionary summary: {data_dict.summary()}")

    # 3.4 数据映射器
    print("\n[3.5] Data mapper (external data mapping)...")
    mapper = DataMapper(data_dict)

    # 外部数据
    external_df = pd.DataFrame({
        "hot_metal_temperature": [1500, 1510, 1490, 1520],
        "blast_pressure_MPa": [0.42, 0.43, 0.41, 0.44],
        "unknown_sensor_01": [100, 102, 98, 101],
    })
    print(f"    External data columns: {list(external_df.columns)}")

    # 自动发现映射
    auto_rules = mapper.auto_discover_rules(list(external_df.columns))
    print(f"    Auto-discovered rules: {len(auto_rules)}")
    for rule in auto_rules:
        print(f"      '{rule.source_column}' -> '{rule.target_dataset}' "
              f"(pool: {rule.target_pool})")

    # 执行映射
    result = mapper.map_dataframe(external_df)
    print(f"    Mapping result:")
    print(f"      Mapped: {result.mapped_columns} columns")
    print(f"      Unmapped: {result.unmapped_columns}")
    print(f"      Warnings: {len(result.warnings)}")

    # 自动检测数据池类型
    pool_type = mapper.detect_pool_type(external_df)
    print(f"    Detected pool type: {pool_type}")

    print("\n✅ Data extension demo completed!")


def main():
    """主函数：运行所有演示。"""
    print("=" * 70)
    print("🏭 GenBFKit - Extension Interface of Advanced Function")
    print("   High-level Function Extension Interface Module")
    print("=" * 70)
    print(f"\nSystem: Python {sys.version.split()[0]}")
    print(f"NumPy: {np.__version__}")
    print(f"Pandas: {pd.__version__}")

    demo_model_deployment()
    demo_system_integration()
    demo_data_extension()

    print(SEPARATOR)
    print("🎉 All demos completed successfully!")
    print(SEPARATOR)
    print("\nNext Steps:")
    print("  1. Deploy your ONNX models using ModelRegistry")
    print("  2. Configure DigitalTwinAdapter with real endpoints")
    print("  3. Extend the data dictionary with DictionaryCRUD")
    print("  4. Map external data sources with DataMapper")
    print("\n📖 See module docstrings for detailed API documentation.")


if __name__ == "__main__":
    main()