"""
Virtual Data Generator - Generates synthetic blast furnace data for testing.

Creates realistic virtual datasets that conform to the prebuilt data architecture,
enabling full-stack testing of the task-oriented retrieval module without
requiring real production data.

Generated data includes:
  - Parameter values with realistic distributions per pool type
  - Timestamps with configurable sampling frequencies
  - Attribute values matching each pool's template
  - Multiple scenario profiles (normal, abnormal, transition)

This generator is the "digital twin's data sparring partner" — it throws
punches that look and feel like real blast furnace data, but without any
risk to actual operations.
"""

import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from ..core.dictionary_manager import (
    DictionaryManager,
    Dataset,
    AttributeTemplate,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Scenario profiles for data generation
# ──────────────────────────────────────────────────────────
SCENARIO_NORMAL = "normal"
SCENARIO_ABNORMAL = "abnormal"
SCENARIO_TRANSITION = "transition"

SCENARIO_PROFILES = {
    SCENARIO_NORMAL: {
        "continuous": {"mean_offset": 0.0, "std_multiplier": 1.0, "anomaly_rate": 0.01},
        "discrete": {"mode_probability": 0.9, "anomaly_rate": 0.02},
        "binary": {"on_probability": 0.85, "anomaly_rate": 0.01},
        "controllable": {"command_variance": 0.05, "anomaly_rate": 0.01},
        "batch": {"batch_variance": 0.1, "anomaly_rate": 0.03},
        "response": {"lag_sigma": 0.1, "anomaly_rate": 0.02},
        "constraint": {"violation_rate": 0.02},
    },
    SCENARIO_ABNORMAL: {
        "continuous": {"mean_offset": 2.0, "std_multiplier": 3.0, "anomaly_rate": 0.2},
        "discrete": {"mode_probability": 0.5, "anomaly_rate": 0.15},
        "binary": {"on_probability": 0.4, "anomaly_rate": 0.2},
        "controllable": {"command_variance": 0.3, "anomaly_rate": 0.15},
        "batch": {"batch_variance": 0.4, "anomaly_rate": 0.2},
        "response": {"lag_sigma": 0.5, "anomaly_rate": 0.2},
        "constraint": {"violation_rate": 0.25},
    },
    SCENARIO_TRANSITION: {
        "continuous": {"mean_offset": 0.5, "std_multiplier": 1.5, "anomaly_rate": 0.08},
        "discrete": {"mode_probability": 0.7, "anomaly_rate": 0.08},
        "binary": {"on_probability": 0.6, "anomaly_rate": 0.08},
        "controllable": {"command_variance": 0.15, "anomaly_rate": 0.08},
        "batch": {"batch_variance": 0.2, "anomaly_rate": 0.1},
        "response": {"lag_sigma": 0.3, "anomaly_rate": 0.1},
        "constraint": {"violation_rate": 0.1},
    },
}


class VirtualDataGenerator:
    """
    Generates synthetic blast furnace data conforming to the prebuilt architecture.

    This generator creates realistic test data for each of the 2128 parameters,
    following the attribute templates defined per data pool. It supports three
    scenario profiles (normal, abnormal, transition) to test retrieval under
    different operational conditions.

    Usage:
        vdg = VirtualDataGenerator(dict_manager)
        data = vdg.generate(num_records=100, scenario="normal")
    """

    def __init__(self, dict_manager: DictionaryManager, seed: int = 42):
        self._dm = dict_manager
        self._rng = np.random.default_rng(seed)
        random.seed(seed)

    def generate(
        self,
        num_records: int = 100,
        scenario: str = SCENARIO_NORMAL,
        work_type_filter: Optional[str] = None,
        pool_filter: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> dict:
        """
        Generate virtual blast furnace data.

        Args:
            num_records: Number of time-series records per parameter
            scenario: One of "normal", "abnormal", "transition"
            work_type_filter: Only generate data for this work type (optional)
            pool_filter: Only generate data for this pool type (optional)
            start_time: Starting timestamp (default: now - num_records * interval)

        Returns:
            Dict with structure:
            {
                "metadata": {...},
                "parameters": {
                    "param_en": {
                        "work_type": "...",
                        "category": "...",
                        "pool": "...",
                        "attributes": {...},
                        "records": [
                            {"timestamp": "...", "value": ..., "status": "normal"},
                            ...
                        ]
                    }
                }
            }
        """
        if scenario not in SCENARIO_PROFILES:
            raise ValueError(f"Unknown scenario: {scenario}. Must be one of {list(SCENARIO_PROFILES.keys())}")

        profile = SCENARIO_PROFILES[scenario]

        # Get datasets to generate data for
        datasets = self._dm.get_all_datasets()
        if work_type_filter:
            datasets = [d for d in datasets if d.work_type_en == work_type_filter]
        if pool_filter:
            datasets = [d for d in datasets if d.pool_en == pool_filter]

        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(hours=num_records)

        parameters = {}
        for ds in datasets:
            param_data = self._generate_parameter_data(
                ds, num_records, profile, start_time
            )
            parameters[ds.dataset_en] = param_data

        result = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "scenario": scenario,
                "num_records_per_param": num_records,
                "num_parameters": len(parameters),
                "work_type_filter": work_type_filter,
                "pool_filter": pool_filter,
                "generator_version": "1.0.0",
            },
            "parameters": parameters,
        }

        logger.info(
            f"Generated virtual data: {len(parameters)} params × {num_records} records "
            f"({scenario} scenario)"
        )
        return result

    def _generate_parameter_data(
        self,
        dataset: Dataset,
        num_records: int,
        profile: dict,
        start_time: datetime,
    ) -> dict:
        """Generate data for a single parameter based on its pool type."""
        pool_en = dataset.pool_en
        attr_template = self._dm.get_attributes_by_pool(pool_en)

        # Generate attribute values
        attributes = self._generate_attributes(attr_template) if attr_template else {}

        # Generate time-series records based on pool type
        records = self._generate_timeseries(
            pool_en, num_records, profile, start_time
        )

        return {
            "work_type": dataset.work_type_en,
            "category": dataset.category_en,
            "pool": dataset.pool_en,
            "name_zh": dataset.dataset_zh,
            "attributes": attributes,
            "records": records,
        }

    def _generate_attributes(self, attr_template: AttributeTemplate) -> dict:
        """Generate attribute values based on the pool's template."""
        attrs = {}

        # Base attributes (common to all pools)
        base = attr_template.base_attributes
        attrs["English_name"] = f"param_{uuid.uuid4().hex[:8]}"
        attrs["Chinese_name"] = f"参数_{random.randint(1000, 9999)}"
        attrs["Data_storage_type"] = "float"
        attrs["Storage_location"] = f"schema.table_{random.randint(1, 100)}"
        attrs["Data_description"] = f"Auto-generated parameter for testing"
        attrs["Priority_level"] = random.choice(["Critical", "High", "Medium", "Low"])

        # Unique attributes per pool
        unique = attr_template.unique_attributes
        if "Sampling_frequency" in unique.values() or "attribute_8" in unique:
            if attr_template.pool_en in [
                "Continuous time-series data",
                "Discrete time-series data",
                "Binary status data",
                "Batch time-series data",
            ]:
                attrs["Sampling_frequency"] = random.choice(["1s", "5s", "10s", "30s", "1min"])

        if "Valid_range" in unique.values():
            lower = round(self._rng.uniform(0, 100), 2)
            upper = round(lower + self._rng.uniform(10, 500), 2)
            attrs["Valid_range"] = f"[{lower}, {upper}]"

        if "Mean_value" in unique.values():
            attrs["Mean_value"] = round(self._rng.uniform(0, 1000), 2)

        if "Std_deviation" in unique.values():
            attrs["Std_deviation"] = round(self._rng.uniform(0.1, 50), 2)

        if "Data_Unit" in unique.values():
            attrs["Data_Unit"] = random.choice(["°C", "MPa", "m³/h", "%", "kg", "mm", "rpm"])

        if "Control_command_type" in unique.values():
            attrs["Control_command_type"] = random.choice(["Setpoint", "ON/OFF", "Analog"])

        if "Constraint_type" in unique.values():
            attrs["Constraint_type"] = random.choice(["Upper bound", "Lower bound", "Range"])

        return attrs

    def _generate_timeseries(
        self,
        pool_en: str,
        num_records: int,
        profile: dict,
        start_time: datetime,
    ) -> list[dict]:
        """Generate time-series records based on pool type."""
        timestamps = [
            (start_time + timedelta(seconds=i * 60)).isoformat()
            for i in range(num_records)
        ]

        if pool_en == "Continuous time-series data":
            p = profile["continuous"]
            values = self._rng.normal(
                loc=100 + p["mean_offset"] * 50,
                scale=10 * p["std_multiplier"],
                size=num_records,
            ).tolist()
            return self._annotate_records(timestamps, values, p["anomaly_rate"])

        elif pool_en == "Discrete time-series data":
            p = profile["discrete"]
            options = list(range(1, 6))
            mode = random.choice(options)
            values = []
            for _ in range(num_records):
                if self._rng.random() < p["mode_probability"]:
                    values.append(float(mode))
                else:
                    values.append(float(random.choice(options)))
            return self._annotate_records(timestamps, values, p["anomaly_rate"])

        elif pool_en == "Binary status data":
            p = profile["binary"]
            values = [
                1.0 if self._rng.random() < p["on_probability"] else 0.0
                for _ in range(num_records)
            ]
            return self._annotate_records(timestamps, values, p["anomaly_rate"])

        elif pool_en == "Controllable data":
            p = profile["controllable"]
            base_setpoint = self._rng.uniform(50, 200)
            values = self._rng.normal(
                loc=base_setpoint,
                scale=base_setpoint * p["command_variance"],
                size=num_records,
            ).tolist()
            return self._annotate_records(timestamps, values, p["anomaly_rate"])

        elif pool_en == "Batch time-series data":
            p = profile["batch"]
            batch_size = max(1, num_records // 10)
            values = []
            for i in range(0, num_records, batch_size):
                batch_mean = self._rng.normal(200, 200 * p["batch_variance"])
                batch_values = self._rng.normal(
                    batch_mean, 5, size=min(batch_size, num_records - i)
                ).tolist()
                values.extend(batch_values)
            return self._annotate_records(timestamps[:len(values)], values, p["anomaly_rate"])

        elif pool_en == "Response data":
            p = profile["response"]
            base_response = self._rng.uniform(100, 500)
            values = self._rng.normal(
                loc=base_response,
                scale=base_response * p["lag_sigma"],
                size=num_records,
            ).tolist()
            return self._annotate_records(timestamps, values, p["anomaly_rate"])

        elif pool_en == "Constraint data":
            p = profile["constraint"]
            threshold = self._rng.uniform(50, 200)
            values = []
            for _ in range(num_records):
                if self._rng.random() < p["violation_rate"]:
                    values.append(threshold + self._rng.uniform(1, 20))
                else:
                    values.append(threshold - self._rng.uniform(0, 10))
            return self._annotate_records(timestamps, values, p["violation_rate"])

        elif pool_en == "Text data":
            text_templates = [
                "设备运行正常", "检查完毕，无异常", "维修工单已提交",
                "传感器故障，需更换", "阀门开度调整至{}%", "计划停机维护",
            ]
            records = []
            for i, ts in enumerate(timestamps):
                text = random.choice(text_templates)
                if "{}" in text:
                    text = text.format(random.randint(10, 100))
                records.append({
                    "timestamp": ts,
                    "value": text,
                    "status": "normal",
                })
            return records

        elif pool_en == "Image data":
            records = []
            for ts in timestamps:
                records.append({
                    "timestamp": ts,
                    "value": f"img_{uuid.uuid4().hex[:12]}.png",
                    "status": "normal",
                })
            return records

        else:
            # Default: random float values
            values = self._rng.uniform(0, 100, size=num_records).tolist()
            return self._annotate_records(timestamps, values, 0.02)

    def _annotate_records(
        self, timestamps: list[str], values: list[float], anomaly_rate: float
    ) -> list[dict]:
        """Add status annotations (normal/anomaly) to records."""
        records = []
        for ts, val in zip(timestamps, values):
            is_anomaly = self._rng.random() < anomaly_rate
            records.append({
                "timestamp": ts,
                "value": round(val, 4),
                "status": "anomaly" if is_anomaly else "normal",
            })
        return records

    def generate_to_file(
        self,
        output_path: str,
        num_records: int = 100,
        scenario: str = SCENARIO_NORMAL,
        **kwargs,
    ) -> str:
        """Generate virtual data and save to a JSON file."""
        data = self.generate(num_records=num_records, scenario=scenario, **kwargs)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Virtual data saved to: {output_path}")
        return output_path
