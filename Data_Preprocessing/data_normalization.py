"""
Data Normalization Module
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from sklearn.preprocessing import (
    MinMaxScaler, StandardScaler, RobustScaler,
    QuantileTransformer, PowerTransformer
)
import pickle
import os

from Data_Preprocessing.config import NormalizationConfig
from Data_Preprocessing.utils import DataTypeDetector, validate_dataframe

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Data normalization with multiple scaling methods
    Supports saving and loading scalers for consistent transformations
    """

    def __init__(self, config: NormalizationConfig):
        """
        Initialize data normalizer

        Args:
            config: NormalizationConfig instance
        """
        self.config = config
        self.scalers = {}
        self.scaler_dir = "saved_scalers"

        # Create scaler directory if not exists
        if not os.path.exists(self.scaler_dir):
            os.makedirs(self.scaler_dir)

    def normalize_zscore(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                        use_median: Optional[bool] = None) -> pd.DataFrame:
        """
        Z-score normalization (Standardization)

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            use_median: Use median instead of mean for robust normalization

        Returns:
            Normalized DataFrame
        """
        if use_median is None:
            use_median = self.config.zscore_with_median

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()

        for col in columns:
            if col not in data.columns:
                continue

            if use_median:
                # Robust z-score using median and MAD
                median = data[col].median()
                mad = np.median(np.abs(data[col] - median))
                if mad == 0:
                    mad = 1  # Avoid division by zero
                df_normalized[col] = (data[col] - median) / mad
            else:
                # Standard z-score
                mean = data[col].mean()
                std = data[col].std()
                if std == 0:
                    std = 1  # Avoid division by zero
                df_normalized[col] = (data[col] - mean) / std

            # Save scaler parameters
            self.scalers[f"{col}_zscore"] = {
                "mean": float(data[col].mean()) if not use_median else float(data[col].median()),
                "scale": float(data[col].std()) if not use_median else float(np.median(np.abs(data[col] - data[col].median()))),
                "method": "zscore",
                "use_median": use_median
            }

        return df_normalized

    def normalize_minmax(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                        feature_range: Optional[Tuple[float, float]] = None) -> pd.DataFrame:
        """
        Min-Max normalization

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            feature_range: Target range (min, max)

        Returns:
            Normalized DataFrame
        """
        if feature_range is None:
            feature_range = self.config.minmax_range

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()
        scaler = MinMaxScaler(feature_range=feature_range)

        df_normalized[columns] = scaler.fit_transform(data[columns].values)

        # Save scaler
        for i, col in enumerate(columns):
            self.scalers[f"{col}_minmax"] = {
                "scaler": scaler,
                "method": "minmax",
                "feature_range": feature_range
            }

        return df_normalized

    def normalize_robust(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                        center: Optional[bool] = None, with_scaling: Optional[bool] = None,
                        quantile_range: Optional[Tuple[float, float]] = None) -> pd.DataFrame:
        """
        Robust normalization using median and quantiles

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            center: Center the data
            with_scaling: Scale the data
            quantile_range: Quantile range for scaling

        Returns:
            Normalized DataFrame
        """
        if center is None:
            center = self.config.robust_center
        if with_scaling is None:
            with_scaling = self.config.robust_with_scaling
        if quantile_range is None:
            quantile_range = self.config.robust_quantile_range

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()
        scaler = RobustScaler(
            with_centering=center,
            with_scaling=with_scaling,
            quantile_range=quantile_range
        )

        df_normalized[columns] = scaler.fit_transform(data[columns].values)

        # Save scaler
        for col in columns:
            self.scalers[f"{col}_robust"] = {
                "scaler": scaler,
                "method": "robust",
                "quantile_range": quantile_range
            }

        return df_normalized

    def normalize_quantile(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                          output_distribution: Optional[str] = None,
                          n_quantiles: Optional[int] = None) -> pd.DataFrame:
        """
        Quantile transformer normalization

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            output_distribution: 'uniform' or 'normal'
            n_quantiles: Number of quantiles

        Returns:
            Normalized DataFrame
        """
        if output_distribution is None:
            output_distribution = self.config.quantile_output_distribution
        if n_quantiles is None:
            n_quantiles = self.config.quantile_n_quantiles

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()

        # Adjust n_quantiles if data is small
        n_samples = len(data)
        if n_quantiles > n_samples:
            n_quantiles = max(10, n_samples // 2)
            logger.warning(f"Adjusted n_quantiles to {n_quantiles} due to small sample size")

        for col in columns:
            if col not in data.columns:
                continue

            scaler = QuantileTransformer(
                output_distribution=output_distribution,
                n_quantiles=n_quantiles,
                random_state=42
            )

            df_normalized[col] = scaler.fit_transform(data[[col]].values).flatten()

            # Save scaler
            self.scalers[f"{col}_quantile"] = {
                "scaler": scaler,
                "method": "quantile",
                "output_distribution": output_distribution
            }

        return df_normalized

    def normalize_yeojohnson(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                            standardize: Optional[bool] = None) -> pd.DataFrame:
        """
        Yeo-Johnson power transformation

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            standardize: Whether to standardize after transformation

        Returns:
            Normalized DataFrame
        """
        if standardize is None:
            standardize = self.config.yeojohnson_standardize

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()

        for col in columns:
            if col not in data.columns:
                continue

            # Remove zeros and negative values for log transform
            scaler = PowerTransformer(
                method='yeo-johnson',
                standardize=standardize
            )

            df_normalized[col] = scaler.fit_transform(data[[col]].values).flatten()

            # Save scaler
            self.scalers[f"{col}_yeojohnson"] = {
                "scaler": scaler,
                "method": "yeojohnson",
                "standardize": standardize
            }

        return df_normalized

    def normalize_log(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                     offset: Optional[float] = None) -> pd.DataFrame:
        """
        Log transformation

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            offset: Offset to handle zero/negative values

        Returns:
            Normalized DataFrame
        """
        if offset is None:
            offset = self.config.log_offset

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        df_normalized = data.copy()

        for col in columns:
            if col not in data.columns:
                continue

            # Ensure all values are positive
            if (data[col] + offset <= 0).any():
                logger.warning(f"Column '{col}' has values <= -{offset}, log transform may fail")
                df_normalized[col] = np.log1p(data[col].clip(lower=-offset + 1e-10))
            else:
                df_normalized[col] = np.log(data[col] + offset)

            # Save transform parameters
            self.scalers[f"{col}_log"] = {
                "method": "log",
                "offset": offset
            }

        return df_normalized

    def normalize(self, data: pd.DataFrame,
                 columns: Optional[List[str]] = None,
                 method: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main normalization method

        Args:
            data: Input DataFrame
            columns: Columns to normalize
            method: Normalization method

        Returns:
            Tuple of (normalized DataFrame, statistics dictionary)
        """
        validate_dataframe(data)

        if method is None:
            method = self.config.method

        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        statistics = {
            "method": method,
            "columns_normalized": [],
            "original_stats": {},
            "normalized_stats": {}
        }

        # Store original statistics
        for col in columns:
            if col in data.columns and np.issubdtype(data[col].dtype, np.number):
                statistics['original_stats'][col] = {
                    "mean": float(data[col].mean()),
                    "std": float(data[col].std()),
                    "min": float(data[col].min()),
                    "max": float(data[col].max()),
                    "median": float(data[col].median())
                }

        # Apply normalization
        if method == "zscore":
            df_normalized = self.normalize_zscore(data, columns)

        elif method == "minmax":
            df_normalized = self.normalize_minmax(data, columns)

        elif method == "robust":
            df_normalized = self.normalize_robust(data, columns)

        elif method == "quantile":
            df_normalized = self.normalize_quantile(data, columns)

        elif method == "yeo-johnson":
            df_normalized = self.normalize_yeojohnson(data, columns)

        elif method == "log":
            df_normalized = self.normalize_log(data, columns)

        else:
            raise ValueError(f"Unknown normalization method: {method}")

        # Store normalized statistics
        for col in columns:
            if col in df_normalized.columns and np.issubdtype(df_normalized[col].dtype, np.number):
                statistics['normalized_stats'][col] = {
                    "mean": float(df_normalized[col].mean()),
                    "std": float(df_normalized[col].std()),
                    "min": float(df_normalized[col].min()),
                    "max": float(df_normalized[col].max()),
                    "median": float(df_normalized[col].median())
                }
                statistics['columns_normalized'].append(col)

        logger.info(f"Normalization completed using '{method}' method. "
                   f"Columns normalized: {len(statistics['columns_normalized'])}")

        return df_normalized, statistics

    def inverse_normalize(self, data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Inverse normalize data using saved scalers

        Args:
            data: Normalized DataFrame
            columns: Columns to inverse normalize

        Returns:
            Original scale DataFrame
        """
        df_original = data.copy()

        for col in columns:
            scaler_key = None

            # Find the scaler for this column
            for key in self.scalers.keys():
                if key.startswith(col):
                    scaler_key = key
                    break

            if scaler_key is None:
                logger.warning(f"No scaler found for column '{col}'")
                continue

            scaler_info = self.scalers[scaler_key]
            method = scaler_info['method']

            if method == "zscore":
                mean = scaler_info['mean']
                scale = scaler_info['scale']
                df_original[col] = data[col] * scale + mean

            elif method == "minmax" or method == "robust" or method == "quantile" or method == "yeojohnson":
                scaler = scaler_info['scaler']
                df_original[col] = scaler.inverse_transform(data[[col]].values).flatten()

            elif method == "log":
                offset = scaler_info['offset']
                df_original[col] = np.exp(data[col]) - offset

        return df_original

    def save_scalers(self, filename: str = "normalization_scalers.pkl") -> None:
        """
        Save all scalers to file

        Args:
            filename: Filename to save scalers
        """
        filepath = os.path.join(self.scaler_dir, filename)

        # Separate picklable objects from sklearn scalers
        picklable_scalers = {}
        for key, value in self.scalers.items():
            if 'scaler' in value:
                picklable_scalers[key] = value
            else:
                picklable_scalers[key] = value

        with open(filepath, 'wb') as f:
            pickle.dump(picklable_scalers, f)

        logger.info(f"Scalers saved to {filepath}")

    def load_scalers(self, filename: str = "normalization_scalers.pkl") -> None:
        """
        Load scalers from file

        Args:
            filename: Filename to load scalers from
        """
        filepath = os.path.join(self.scaler_dir, filename)

        if not os.path.exists(filepath):
            logger.warning(f"Scaler file not found: {filepath}")
            return

        with open(filepath, 'rb') as f:
            self.scalers = pickle.load(f)

        logger.info(f"Scalers loaded from {filepath}")
