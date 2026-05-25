"""
Preprocessing Pipeline - Main Orchestration Module
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import traceback

from Data_Preprocessing.config import PreprocessingConfig
from Data_Preprocessing.database import DatabaseManager
from Data_Preprocessing.missing_value import MissingValueHandler
from Data_Preprocessing.outlier_detection import OutlierDetector
from Data_Preprocessing.data_normalization import DataNormalizer
from Data_Preprocessing.utils import validate_dataframe

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """
    Comprehensive preprocessing pipeline for time-series sensor data
    Orchestrates missing value handling, outlier detection, and normalization
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None,
                 db_manager: Optional[DatabaseManager] = None):
        """
        Initialize preprocessing pipeline

        Args:
            config: PreprocessingConfig instance
            db_manager: DatabaseManager instance (optional)
        """
        if config is None:
            config = PreprocessingConfig()

        self.config = config
        self.db_manager = db_manager

        # Initialize handlers
        self.missing_handler = MissingValueHandler(config.missing_value)
        self.outlier_detector = OutlierDetector(config.outlier_detection)
        self.normalizer = DataNormalizer(config.normalization)

        # Setup logging
        self._setup_logging()

        # Initialize metadata table if database manager provided
        if self.db_manager:
            self.db_manager.create_preprocessing_metadata_table(self.config.metadata_table)

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler()
            ]
        )

    def preprocess_table(self, table_name: str,
                        steps: List[str],
                        target_columns: Optional[List[str]] = None,
                        save_to_db: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess a database table through specified steps

        Args:
            table_name: Name of the table to preprocess
            steps: List of preprocessing steps to apply
                   ['missing_values', 'outlier_detection', 'normalization']
            target_columns: Columns to process (None for all applicable)
            save_to_db: Whether to save results back to database

        Returns:
            Tuple of (preprocessed DataFrame, complete statistics)
        """
        start_time = datetime.now()
        metadata_id = None

        try:
            # Load data from database
            if not self.db_manager:
                raise ValueError("Database manager is required for table preprocessing")

            logger.info(f"Loading data from table: {table_name}")
            df = self.db_manager.get_table_data(table_name)
            validate_dataframe(df)

            # Create metadata record
            metadata_id = self.db_manager.save_preprocessing_metadata(
                table_name=table_name,
                preprocessing_type="full_pipeline",
                status="started",
                parameters={"steps": steps, "target_columns": target_columns},
                statistics={},
                rows_processed=len(df),
                rows_modified=0,
                start_time=start_time
            )

            # Apply preprocessing steps
            complete_stats = {
                "table_name": table_name,
                "steps_applied": steps,
                "original_shape": df.shape,
                "step_results": {}
            }

            df_processed = df.copy()

            for step in steps:
                logger.info(f"Applying step: {step}")
                step_start_time = datetime.now()

                try:
                    if step == "missing_values":
                        df_processed, stats = self.missing_handler.handle_missing_values(
                            df_processed, target_columns
                        )
                        complete_stats["step_results"]["missing_values"] = stats

                    elif step == "outlier_detection":
                        df_processed, stats = self.outlier_detector.detect_and_handle_outliers(
                            df_processed, target_columns,
                            replace_method="median"
                        )
                        complete_stats["step_results"]["outlier_detection"] = stats

                    elif step == "normalization":
                        df_processed, stats = self.normalizer.normalize(
                            df_processed, target_columns
                        )
                        complete_stats["step_results"]["normalization"] = stats

                    else:
                        logger.warning(f"Unknown step: {step}")
                        continue

                    step_duration = (datetime.now() - step_start_time).total_seconds()
                    complete_stats["step_results"][step]["execution_time"] = f"{step_duration:.2f}s"

                except Exception as e:
                    logger.error(f"Step '{step}' failed: {e}")
                    complete_stats["step_results"][step] = {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                    raise

            complete_stats["final_shape"] = df_processed.shape
            complete_stats["rows_modified"] = len(df_processed) - len(df_processed.isnull().dropna(how='all'))

            # Save to database
            if save_to_db:
                logger.info(f"Saving processed data to table: {table_name}")
                if self.config.create_backup:
                    backup_table = self.db_manager.backup_table(table_name)
                    complete_stats["backup_table"] = backup_table

                if self.config.validate_before_save:
                    validate_dataframe(df_processed)

                rows_inserted = self.db_manager.insert_dataframe(table_name, df_processed)
                complete_stats["rows_inserted"] = rows_inserted

            # Update metadata
            end_time = datetime.now()
            self.db_manager.save_preprocessing_metadata(
                table_name=table_name,
                preprocessing_type="full_pipeline",
                status="completed",
                parameters={"steps": steps, "target_columns": target_columns},
                statistics=complete_stats,
                rows_processed=len(df),
                rows_modified=complete_stats["rows_modified"],
                start_time=start_time,
                end_time=end_time
            )

            logger.info(f"Preprocessing completed for table: {table_name}")
            return df_processed, complete_stats

        except Exception as e:
            logger.error(f"Preprocessing failed for table {table_name}: {e}")
            # Update metadata with error
            if metadata_id and self.db_manager:
                self.db_manager.save_preprocessing_metadata(
                    table_name=table_name,
                    preprocessing_type="full_pipeline",
                    status="failed",
                    parameters={"steps": steps, "target_columns": target_columns},
                    statistics={},
                    rows_processed=0,
                    rows_modified=0,
                    error_message=str(e),
                    start_time=start_time,
                    end_time=datetime.now()
                )
            raise

    def preprocess_dataframe(self, df: pd.DataFrame,
                            steps: List[str],
                            target_columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess a pandas DataFrame

        Args:
            df: Input DataFrame
            steps: List of preprocessing steps
            target_columns: Columns to process

        Returns:
            Tuple of (preprocessed DataFrame, statistics)
        """
        validate_dataframe(df)

        logger.info(f"Starting DataFrame preprocessing with steps: {steps}")

        complete_stats = {
            "steps_applied": steps,
            "original_shape": df.shape,
            "step_results": {}
        }

        df_processed = df.copy()

        for step in steps:
            logger.info(f"Applying step: {step}")

            if step == "missing_values":
                df_processed, stats = self.missing_handler.handle_missing_values(
                    df_processed, target_columns
                )
                complete_stats["step_results"]["missing_values"] = stats

            elif step == "outlier_detection":
                df_processed, stats = self.outlier_detector.detect_and_handle_outliers(
                    df_processed, target_columns,
                    replace_method="median"
                )
                complete_stats["step_results"]["outlier_detection"] = stats

            elif step == "normalization":
                df_processed, stats = self.normalizer.normalize(
                    df_processed, target_columns
                )
                complete_stats["step_results"]["normalization"] = stats

            else:
                logger.warning(f"Unknown step: {step}")

        complete_stats["final_shape"] = df_processed.shape

        logger.info(f"DataFrame preprocessing completed")
        return df_processed, complete_stats

    def batch_preprocess_tables(self, table_pattern: str,
                               steps: List[str],
                               target_columns: Optional[List[str]] = None,
                               max_tables: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Preprocess multiple tables matching a pattern

        Args:
            table_pattern: Pattern to match table names
            steps: Preprocessing steps
            target_columns: Columns to process
            max_tables: Maximum number of tables to process

        Returns:
            Dictionary with results for each table
        """
        if not self.db_manager:
            raise ValueError("Database manager is required for batch preprocessing")

        # List matching tables
        tables = self.db_manager.list_tables(pattern=table_pattern)
        logger.info(f"Found {len(tables)} tables matching pattern: {table_pattern}")

        if max_tables:
            tables = tables[:max_tables]

        results = {}

        for table_name in tables:
            logger.info(f"Processing table: {table_name}")
            try:
                df_processed, stats = self.preprocess_table(
                    table_name, steps, target_columns, save_to_db=True
                )
                results[table_name] = {
                    "status": "success",
                    "statistics": stats
                }
            except Exception as e:
                logger.error(f"Failed to process table {table_name}: {e}")
                results[table_name] = {
                    "status": "failed",
                    "error": str(e)
                }

        return results

    def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data quality before preprocessing

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with data quality metrics
        """
        validate_dataframe(df)

        quality_report = {
            "shape": df.shape,
            "columns": len(df.columns),
            "rows": len(df),
            "memory_usage": float(df.memory_usage(deep=True).sum() / (1024 ** 2)),  # MB
            "missing_values": {},
            "data_types": {},
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_rate": float(df.duplicated().sum() / len(df)) if len(df) > 0 else 0
        }

        # Missing values analysis
        missing_by_column = df.isnull().sum()
        for col in df.columns:
            missing_count = missing_by_column[col]
            missing_rate = missing_count / len(df) if len(df) > 0 else 0
            if missing_count > 0:
                quality_report["missing_values"][col] = {
                    "count": int(missing_count),
                    "rate": float(missing_rate)
                }

        # Data types
        for col in df.columns:
            quality_report["data_types"][col] = str(df[col].dtype)

        # Statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            quality_report["numeric_statistics"] = {}
            for col in numeric_cols:
                quality_report["numeric_statistics"][col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "median": float(df[col].median())
                }

        quality_report["overall_missing_rate"] = df.isnull().sum().sum() / (len(df) * len(df.columns))

        return quality_report

    def get_preprocessing_summary(self, table_names: List[str]) -> pd.DataFrame:
        """
        Get summary of preprocessing operations from metadata

        Args:
            table_names: List of table names

        Returns:
            DataFrame with preprocessing summary
        """
        if not self.db_manager:
            raise ValueError("Database manager is required")

        query = f"""
            SELECT
                table_name,
                preprocessing_type,
                start_time,
                end_time,
                status,
                rows_processed,
                rows_modified,
                parameters,
                statistics
            FROM {self.config.database.schema}.{self.config.metadata_table}
            WHERE table_name = ANY(%s)
            ORDER BY start_time DESC
        """

        results = self.db_manager.execute_query(query, (table_names,))
        return pd.DataFrame(results)

    def close(self):
        """Close database connections and cleanup"""
        if self.db_manager:
            self.db_manager.close()
        logger.info("Preprocessing pipeline closed")
