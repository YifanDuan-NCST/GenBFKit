"""
Virtual Data Generator for testing the Knowledge Graph Visualization Module.

Generates synthetic blast furnace time-series data that mimics
real production scenarios, including:
  - Normal operating conditions for 2128 parameters
  - Anomalous events with configurable severity
  - Cross-parameter correlations (process coupling)
  - Multi-source temporal patterns (different sampling frequencies)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from ..graph_builder.knowledge_graph import BlastFurnaceKnowledgeGraph
from ..graph_builder.models import NodeType, EdgeType
from ..config import (
    VIRTUAL_NUM_TIMESTEPS, VIRTUAL_ANOMALY_RATIO, VIRTUAL_RANDOM_SEED,
    DATA_DIR,
)

logger = logging.getLogger(__name__)


class VirtualDataGenerator:
    """
    Generates virtual blast furnace data for testing the KG module.

    The generator is aware of the data dictionary structure and produces
    data that respects the 5-level hierarchy and pool-specific characteristics.
    """

    def __init__(self, kg: BlastFurnaceKnowledgeGraph,
                 num_timesteps: int = VIRTUAL_NUM_TIMESTEPS,
                 anomaly_ratio: float = VIRTUAL_ANOMALY_RATIO,
                 seed: int = VIRTUAL_RANDOM_SEED):
        self.kg = kg
        self.num_timesteps = num_timesteps
        self.anomaly_ratio = anomaly_ratio
        self.rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_time_series(self) -> Dict[str, np.ndarray]:
        """
        Generate synthetic time-series data for all dataset (param) nodes.

        Returns:
            Dict mapping node_id → 1D numpy array of values.
        """
        dataset_nodes = self.kg.get_nodes_by_type(NodeType.DATASET)
        data = {}

        for node in dataset_nodes:
            pool_en = node.properties.get("pool_en", "Continuous time-series data")
            ts = self._generate_param_series(pool_en)
            data[node.node_id] = ts

        logger.info("Generated time-series data for %d parameters.", len(data))
        return data

    def inject_anomalies(self, data: Dict[str, np.ndarray],
                          anomaly_node_ids: Optional[List[str]] = None,
                          anomaly_ratio: Optional[float] = None) -> Tuple[
                              Dict[str, np.ndarray], List[str]]:
        """
        Inject anomalies into the generated data.

        Args:
            data: Time-series data from generate_time_series().
            anomaly_node_ids: Specific nodes to inject anomalies into.
                             If None, randomly selects nodes.
            anomaly_ratio: Fraction of nodes to make anomalous.

        Returns:
            (modified_data, list_of_anomaly_node_ids)
        """
        ratio = anomaly_ratio or self.anomaly_ratio
        node_ids = list(data.keys())

        if anomaly_node_ids is None:
            n_anomalies = max(1, int(len(node_ids) * ratio))
            anomaly_node_ids = list(self.rng.choice(node_ids, size=n_anomalies, replace=False))

        for nid in anomaly_node_ids:
            if nid in data:
                ts = data[nid].copy()
                # Inject a spike anomaly in the last 5% of data
                anomaly_start = int(len(ts) * 0.95)
                anomaly_magnitude = self.rng.uniform(3, 6)  # 3-6 sigma
                std = np.std(ts[:anomaly_start]) if anomaly_start > 0 else 1.0
                ts[anomaly_start:] = ts[anomaly_start] + anomaly_magnitude * std
                data[nid] = ts

        logger.info("Injected anomalies into %d parameters.", len(anomaly_node_ids))
        return data, anomaly_node_ids

    def generate_full_scenario(self) -> Dict[str, Any]:
        """
        Generate a complete test scenario with data, anomalies, and metadata.

        Returns:
            Dict with keys: 'data', 'anomaly_ids', 'statistics', 'metadata'
        """
        data = self.generate_time_series()
        data, anomaly_ids = self.inject_anomalies(data)

        # Compute statistics
        stats = {}
        for nid, ts in data.items():
            node = self.kg.get_node(nid)
            stats[nid] = {
                "name_en": node.name_en if node else nid,
                "mean": float(np.mean(ts)),
                "std": float(np.std(ts)),
                "min": float(np.min(ts)),
                "max": float(np.max(ts)),
                "is_anomaly": nid in anomaly_ids,
            }

        return {
            "data": data,
            "anomaly_ids": anomaly_ids,
            "statistics": stats,
            "metadata": {
                "num_params": len(data),
                "num_timesteps": self.num_timesteps,
                "num_anomalies": len(anomaly_ids),
                "anomaly_ratio": len(anomaly_ids) / max(len(data), 1),
            },
        }

    def save_scenario(self, scenario: Dict[str, Any],
                       output_dir: Optional[str] = None):
        """Save scenario data to files."""
        out_dir = output_dir or DATA_DIR
        os.makedirs(out_dir, exist_ok=True)

        # Save statistics as JSON
        stats_path = os.path.join(out_dir, "virtual_scenario_stats.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(scenario["statistics"], f, ensure_ascii=False, indent=2)

        # Save data as CSV (long format)
        rows = []
        for nid, ts in scenario["data"].items():
            node = self.kg.get_node(nid)
            name = node.name_en if node else nid
            for t, val in enumerate(ts):
                rows.append({
                    "node_id": nid,
                    "param_name": name,
                    "timestep": t,
                    "value": val,
                    "is_anomaly": nid in scenario["anomaly_ids"],
                })

        df = pd.DataFrame(rows)
        csv_path = os.path.join(out_dir, "virtual_scenario_data.csv")
        df.to_csv(csv_path, index=False)

        # Save metadata
        meta_path = os.path.join(out_dir, "virtual_scenario_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(scenario["metadata"], f, ensure_ascii=False, indent=2)

        logger.info("Scenario saved to %s", out_dir)
        return {"stats": stats_path, "data": csv_path, "metadata": meta_path}

    # ------------------------------------------------------------------
    # Internal: pool-specific generators
    # ------------------------------------------------------------------
    def _generate_param_series(self, pool_en: str) -> np.ndarray:
        """Generate a time series appropriate for the given data pool type."""
        t = np.arange(self.num_timesteps, dtype=np.float64)

        if pool_en == "Continuous time-series data":
            return self._continuous_ts(t)
        elif pool_en == "Discrete time-series data":
            return self._discrete_ts(t)
        elif pool_en == "Binary status data":
            return self._binary_ts(t)
        elif pool_en == "Batch time-series data":
            return self._batch_ts(t)
        elif pool_en == "Controllable data":
            return self._controllable_ts(t)
        elif pool_en == "Response data":
            return self._response_ts(t)
        elif pool_en == "Constraint data":
            return self._constraint_ts(t)
        elif pool_en == "Text data":
            return self._text_ts(t)
        elif pool_en == "Image data":
            return self._image_ts(t)
        else:
            return self._continuous_ts(t)

    def _continuous_ts(self, t: np.ndarray) -> np.ndarray:
        """Continuous sensor readings: temperature, pressure, flow, etc."""
        base = self.rng.uniform(100, 1500)
        amplitude = self.rng.uniform(1, 30)
        freq = self.rng.uniform(0.001, 0.01)
        noise_std = self.rng.uniform(0.5, 5.0)

        trend = base + amplitude * np.sin(2 * np.pi * freq * t)
        noise = self.rng.normal(0, noise_std, size=len(t))
        return trend + noise

    def _discrete_ts(self, t: np.ndarray) -> np.ndarray:
        """Discrete measurements: lab results, manual readings."""
        base = self.rng.uniform(10, 100)
        values = self.rng.choice([base - 2, base - 1, base, base + 1, base + 2],
                                  size=len(t))
        # Most values stay the same (step function)
        result = np.full(len(t), base)
        change_points = self.rng.choice(len(t), size=len(t) // 10, replace=False)
        for cp in change_points:
            result[cp:] = values[cp]
        return result.astype(np.float64)

    def _binary_ts(self, t: np.ndarray) -> np.ndarray:
        """Binary on/off status: pump running, valve open, etc."""
        result = np.zeros(len(t), dtype=np.float64)
        # Mostly ON with occasional OFF periods
        result[:] = 1.0
        n_off_periods = self.rng.randint(0, 5)
        max_start = max(len(t) - 50, 1)
        for _ in range(n_off_periods):
            start = self.rng.randint(0, max_start)
            duration = self.rng.randint(10, min(50, len(t) - start))
            result[start:start + duration] = 0.0
        return result

    def _batch_ts(self, t: np.ndarray) -> np.ndarray:
        """Batch process data: composition analysis results."""
        batch_size = self.rng.randint(20, 100)
        base = self.rng.uniform(50, 200)
        noise_std = self.rng.uniform(0.5, 3.0)

        result = np.zeros(len(t), dtype=np.float64)
        batch_val = base + self.rng.normal(0, noise_std)
        for i in range(len(t)):
            if i % batch_size == 0:
                batch_val = base + self.rng.normal(0, noise_std)
            result[i] = batch_val
        return result

    def _controllable_ts(self, t: np.ndarray) -> np.ndarray:
        """Setpoint values: control commands."""
        base = self.rng.uniform(0, 100)
        result = np.full(len(t), base, dtype=np.float64)
        # Step changes (setpoint adjustments)
        n_changes = self.rng.randint(1, 10)
        change_points = sorted(self.rng.choice(len(t), size=n_changes, replace=False))
        for cp in change_points:
            new_val = base + self.rng.uniform(-20, 20)
            result[cp:] = new_val
            base = new_val
        return result

    def _response_ts(self, t: np.ndarray) -> np.ndarray:
        """Response variables: K value, permeability, gas utilization, etc."""
        # More dynamic with trends
        base = self.rng.uniform(0, 2)
        freq1 = self.rng.uniform(0.002, 0.008)
        freq2 = self.rng.uniform(0.0005, 0.002)
        noise_std = self.rng.uniform(0.01, 0.1)

        result = (base
                  + 0.3 * np.sin(2 * np.pi * freq1 * t)
                  + 0.1 * np.sin(2 * np.pi * freq2 * t)
                  + self.rng.normal(0, noise_std, size=len(t)))
        return result

    def _constraint_ts(self, t: np.ndarray) -> np.ndarray:
        """Constraint values: upper/lower limits, thresholds."""
        # Relatively stable with rare adjustments
        base = self.rng.uniform(50, 500)
        result = np.full(len(t), base, dtype=np.float64)
        n_adjust = self.rng.randint(0, 3)
        for _ in range(n_adjust):
            idx = self.rng.randint(len(t) // 4, 3 * len(t) // 4)
            new_val = base + self.rng.uniform(-10, 10)
            result[idx:] = new_val
        return result

    def _text_ts(self, t: np.ndarray) -> np.ndarray:
        """Text data: encode as numeric hash for graph purposes."""
        # Represent as a numeric placeholder (text length or category code)
        return self.rng.choice([1, 2, 3, 4, 5], size=len(t)).astype(np.float64)

    def _image_ts(self, t: np.ndarray) -> np.ndarray:
        """Image data: encode as quality score for graph purposes."""
        # Represent as image quality score (0-100)
        base = self.rng.uniform(70, 95)
        noise = self.rng.normal(0, 3, size=len(t))
        return np.clip(base + noise, 0, 100)
