"""
Configuration Management Module for Data Preprocessing
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MissingValueConfig:
    """Configuration for missing value handling"""
    # Detection
    detection_method: str = "all"  # 'simple', 'pattern', 'all'
    threshold: float = 0.05  # Missing rate threshold for alert

    # Imputation methods (priority order)
    time_series_methods: List[str] = field(default_factory=lambda: [
        "linear_interpolation",
        "spline_interpolation",
        "kalman_filter",
        "forward_fill",
        "backward_fill"
    ])

    categorical_methods: List[str] = field(default_factory=lambda: [
        "most_frequent",
        "knn",
        "mice"
    ])

    # Advanced methods
    use_mice: bool = True
    mice_max_iter: int = 10
    mice_random_state: int = 42

    use_lightgbm: bool = True
    lightgbm_params: Dict[str, Any] = field(default_factory=lambda: {
        "num_leaves": 31,
        "learning_rate": 0.05,
        "n_estimators": 100,
        "min_child_samples": 20
    })

    # KNN imputation
    use_knn: bool = True
    knn_n_neighbors: int = 5
    knn_weights: str = "uniform"  # 'uniform' or 'distance'


@dataclass
class OutlierDetectionConfig:
    """Configuration for outlier detection"""
    # Detection methods (can combine multiple)
    methods: List[str] = field(default_factory=lambda: [
        "isolation_forest",
        "local_outlier_factor",
        "zscore",
        "iqr",
        "autoencoder"
    ])

    # Isolation Forest
    iso_forest_contamination: float = 0.05
    iso_forest_n_estimators: int = 100
    iso_forest_random_state: int = 42

    # Local Outlier Factor
    lof_n_neighbors: int = 20
    lof_contamination: float = 0.05

    # Statistical methods
    zscore_threshold: float = 3.0
    iqr_multiplier: float = 1.5

    # Autoencoder (neural network)
    autoencoder_epochs: int = 50
    autoencoder_batch_size: int = 32
    autoencoder_encoding_dim: int = 8
    autoencoder_hidden_layers: List[int] = field(default_factory=lambda: [64, 32])

    # Ensemble
    use_ensemble: bool = True
    ensemble_voting: str = "hard"  # 'hard' or 'soft'

    # Time-series specific
    time_series_window: int = 10
    use_moving_average: bool = True
    use_exponential_smoothing: bool = True


@dataclass
class NormalizationConfig:
    """Configuration for data normalization"""
    # Normalization method
    method: str = "zscore"  # 'zscore', 'minmax', 'robust', 'quantile', 'yeo-johnson', 'log'
    zscore_with_median: bool = False  # Use median instead of mean for robust normalization

    # Min-Max
    minmax_range: tuple = (0, 1)

    # Robust scaling
    robust_center: bool = True
    robust_with_scaling: bool = True
    robust_quantile_range: tuple = (25.0, 75.0)

    # Quantile transformer
    quantile_output_distribution: str = "uniform"  # 'uniform' or 'normal'
    quantile_n_quantiles: int = 1000

    # Yeo-Johnson
    yeojohnson_standardize: bool = True

    # Log transform
    log_offset: float = 1.0  # To handle zero/negative values

    # Group-based normalization
    normalize_by_group: bool = False
    group_columns: Optional[List[str]] = None


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database connection"""
    host: str = "localhost"
    port: int = 5432
    database: str = "genbfkit"
    user: str = "postgres"
    password: str = ""
    schema: str = "public"

    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class PreprocessingConfig:
    """Main configuration class for data preprocessing"""

    # Database configuration
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Sub-module configurations
    missing_value: MissingValueConfig = field(default_factory=MissingValueConfig)
    outlier_detection: OutlierDetectionConfig = field(default_factory=OutlierDetectionConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)

    # Logging
    log_level: str = "INFO"
    log_file: str = "preprocessing.log"

    # Processing
    parallel_jobs: int = -1  # -1 means use all available cores
    batch_size: int = 10000  # For large datasets
    chunk_size: int = 1000

    # Metadata
    save_metadata: bool = True
    metadata_table: str = "preprocessing_metadata"

    # Validation
    validate_before_save: bool = True
    create_backup: bool = True

    @classmethod
    def from_json(cls, config_path: str) -> "PreprocessingConfig":
        """Load configuration from JSON file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)

        return cls(
            database=DatabaseConfig(**config_dict.get("database", {})),
            missing_value=MissingValueConfig(**config_dict.get("missing_value", {})),
            outlier_detection=OutlierDetectionConfig(**config_dict.get("outlier_detection", {})),
            normalization=NormalizationConfig(**config_dict.get("normalization", {})),
            **{k: v for k, v in config_dict.items()
               if k not in ["database", "missing_value", "outlier_detection", "normalization"]}
        )

    def to_json(self, save_path: str) -> None:
        """Save configuration to JSON file"""
        config_dict = {
            "database": self.database.__dict__,
            "missing_value": self.missing_value.__dict__,
            "outlier_detection": self.outlier_detection.__dict__,
            "normalization": self.normalization.__dict__,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "parallel_jobs": self.parallel_jobs,
            "batch_size": self.batch_size,
            "chunk_size": self.chunk_size,
            "save_metadata": self.save_metadata,
            "metadata_table": self.metadata_table,
            "validate_before_save": self.validate_before_save,
            "create_backup": self.create_backup
        }

        # Remove None values
        config_dict = {k: v for k, v in config_dict.items() if v is not None}

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    def get_env_config(self) -> "PreprocessingConfig":
        """Load configuration from environment variables"""
        # Override database config from environment
        if "DB_HOST" in os.environ:
            self.database.host = os.environ["DB_HOST"]
        if "DB_PORT" in os.environ:
            self.database.port = int(os.environ["DB_PORT"])
        if "DB_NAME" in os.environ:
            self.database.database = os.environ["DB_NAME"]
        if "DB_USER" in os.environ:
            self.database.user = os.environ["DB_USER"]
        if "DB_PASSWORD" in os.environ:
            self.database.password = os.environ["DB_PASSWORD"]

        return self
