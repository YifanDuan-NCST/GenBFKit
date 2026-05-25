"""
Outlier Detection and Replacement Module
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
from joblib import Parallel, delayed

from Data_Preprocessing.config import OutlierDetectionConfig
from Data_Preprocessing.utils import (
    DataTypeDetector, StatisticalTests, RollingWindowHelper,
    MetricsCalculator, validate_dataframe
)

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class OutlierDetector:
    """
    Advanced outlier detection using multiple algorithms
    Supports ensemble detection and time-series specific methods
    """

    def __init__(self, config: OutlierDetectionConfig):
        """
        Initialize outlier detector

        Args:
            config: OutlierDetectionConfig instance
        """
        self.config = config
        self.column_types = {}
        self.time_col = None
        self.models = {}
        self.scalers = {}

    def detect_outliers_isolation_forest(self, data: np.ndarray,
                                        contamination: Optional[float] = None) -> np.ndarray:
        """
        Detect outliers using Isolation Forest

        Args:
            data: Input data array
            contamination: Expected outlier proportion

        Returns:
            Boolean array indicating outliers (-1 for outliers, 1 for inliers)
        """
        if contamination is None:
            contamination = self.config.iso_forest_contamination

        model = IsolationForest(
            n_estimators=self.config.iso_forest_n_estimators,
            contamination=contamination,
            random_state=self.config.iso_forest_random_state,
            n_jobs=-1
        )

        outliers = model.fit_predict(data)
        return outliers == -1

    def detect_outliers_lof(self, data: np.ndarray,
                           contamination: Optional[float] = None) -> np.ndarray:
        """
        Detect outliers using Local Outlier Factor

        Args:
            data: Input data array
            contamination: Expected outlier proportion

        Returns:
            Boolean array indicating outliers
        """
        if contamination is None:
            contamination = self.config.lof_contamination

        model = LocalOutlierFactor(
            n_neighbors=self.config.lof_n_neighbors,
            contamination=contamination,
            n_jobs=-1
        )

        outliers = model.fit_predict(data)
        return outliers == -1

    def detect_outliers_zscore(self, data: pd.Series,
                              threshold: Optional[float] = None) -> np.ndarray:
        """
        Detect outliers using Z-score method

        Args:
            data: Input series
            threshold: Z-score threshold

        Returns:
            Boolean array indicating outliers
        """
        if threshold is None:
            threshold = self.config.zscore_threshold

        z_scores = np.abs(stats.zscore(data.dropna()))
        outlier_mask = pd.Series(False, index=data.index)
        outlier_mask.loc[data.dropna().index] = z_scores > threshold

        return outlier_mask.values

    def detect_outliers_iqr(self, data: pd.Series,
                           multiplier: Optional[float] = None) -> np.ndarray:
        """
        Detect outliers using Interquartile Range (IQR) method

        Args:
            data: Input series
            multiplier: IQR multiplier

        Returns:
            Boolean array indicating outliers
        """
        if multiplier is None:
            multiplier = self.config.iqr_multiplier

        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        outliers = (data < lower_bound) | (data > upper_bound)
        return outliers.values

    def detect_outliers_autoencoder(self, data: np.ndarray) -> np.ndarray:
        """
        Detect outliers using Autoencoder reconstruction error

        Args:
            data: Input data array

        Returns:
            Boolean array indicating outliers
        """
        try:
            from sklearn.neural_network import MLPRegressor

            # Normalize data
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)

            # Build autoencoder
            hidden_layers = self.config.autoencoder_hidden_layers + [self.config.autoencoder_encoding_dim]
            hidden_layers_rev = hidden_layers[::-1][1:] + [data.shape[1]]

            # Use MLP as autoencoder
            model = MLPRegressor(
                hidden_layer_sizes=hidden_layers + hidden_layers_rev,
                activation='relu',
                solver='adam',
                max_iter=self.config.autoencoder_epochs,
                batch_size=self.config.autoencoder_batch_size,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )

            model.fit(data_scaled, data_scaled)
            reconstructed = model.predict(data_scaled)

            # Calculate reconstruction error
            reconstruction_error = np.mean(np.square(data_scaled - reconstructed), axis=1)

            # Use 95th percentile as threshold
            threshold = np.percentile(reconstruction_error, 95)
            outliers = reconstruction_error > threshold

            return outliers

        except ImportError:
            logger.warning("Autoencoder requires sklearn neural network, skipping")
            return np.zeros(len(data), dtype=bool)
        except Exception as e:
            logger.warning(f"Autoencoder detection failed: {e}")
            return np.zeros(len(data), dtype=bool)

    def detect_outliers_rolling_window(self, series: pd.Series,
                                      window: Optional[int] = None) -> np.ndarray:
        """
        Detect outliers using rolling window statistics for time series

        Args:
            series: Input time series
            window: Rolling window size

        Returns:
            Boolean array indicating outliers
        """
        if window is None:
            window = self.config.time_series_window

        outliers = pd.Series(False, index=series.index)

        # Use rolling median and MAD
        rolling_median = series.rolling(window=window, center=True, min_periods=1).median()
        rolling_mad = np.abs(series - rolling_median).rolling(window=window, center=True, min_periods=1).median()

        # Threshold: 3 * MAD (similar to 3 * std for normal distribution)
        threshold = 3 * rolling_mad
        outliers = np.abs(series - rolling_median) > threshold

        return outliers.values

    def detect_outliers_moving_average(self, series: pd.Series,
                                      window: Optional[int] = None) -> np.ndarray:
        """
        Detect outliers using moving average method

        Args:
            series: Input time series
            window: Moving average window

        Returns:
            Boolean array indicating outliers
        """
        if window is None:
            window = self.config.time_series_window

        ma = series.rolling(window=window, center=True, min_periods=1).mean()
        std = series.rolling(window=window, center=True, min_periods=1).std()

        threshold = 3  # 3 standard deviations
        outliers = np.abs(series - ma) > threshold * std

        return outliers.values

    def detect_outliers_exponential_smoothing(self, series: pd.Series,
                                             alpha: float = 0.3) -> np.ndarray:
        """
        Detect outliers using exponential smoothing

        Args:
            series: Input time series
            alpha: Smoothing factor

        Returns:
            Boolean array indicating outliers
        """
        smoothed = series.ewm(alpha=alpha).mean()
        residuals = series - smoothed

        # Use rolling std of residuals
        rolling_std = np.abs(residuals).rolling(window=10, center=True, min_periods=1).mean()
        outliers = np.abs(residuals) > 3 * rolling_std

        return outliers.values

    def detect_outliers_ensemble(self, df: pd.DataFrame, column: str,
                                 methods: Optional[List[str]] = None) -> np.ndarray:
        """
        Detect outliers using ensemble of multiple methods

        Args:
            df: Input DataFrame
            column: Column to analyze
            methods: List of methods to use

        Returns:
            Boolean array indicating outliers
        """
        if methods is None:
            methods = self.config.methods

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        series = df[column].dropna()
        outlier_votes = pd.DataFrame(index=series.index)

        for method in methods:
            try:
                if method == "isolation_forest":
                    # Use multiple features if available
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    data = df[numeric_cols].dropna()
                    if len(data) > 0:
                        outliers_mask = self.detect_outliers_isolation_forest(data.values)
                        outlier_votes[method] = False
                        outlier_votes.loc[data.index, method] = outliers_mask

                elif method == "local_outlier_factor":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    data = df[numeric_cols].dropna()
                    if len(data) > 0:
                        outliers_mask = self.detect_outliers_lof(data.values)
                        outlier_votes[method] = False
                        outlier_votes.loc[data.index, method] = outliers_mask

                elif method == "zscore":
                    outliers_mask = self.detect_outliers_zscore(series)
                    outlier_votes[method] = outliers_mask

                elif method == "iqr":
                    outliers_mask = self.detect_outliers_iqr(series)
                    outlier_votes[method] = outliers_mask

                elif method == "autoencoder":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    data = df[numeric_cols].dropna()
                    if len(data) > 0:
                        outliers_mask = self.detect_outliers_autoencoder(data.values)
                        outlier_votes[method] = False
                        outlier_votes.loc[data.index, method] = outliers_mask

                elif method == "rolling_window":
                    outliers_mask = self.detect_outliers_rolling_window(series)
                    outlier_votes[method] = outliers_mask

                elif method == "moving_average":
                    outliers_mask = self.detect_outliers_moving_average(series)
                    outlier_votes[method] = outliers_mask

                elif method == "exponential_smoothing":
                    outliers_mask = self.detect_outliers_exponential_smoothing(series)
                    outlier_votes[method] = outliers_mask

            except Exception as e:
                logger.warning(f"Method '{method}' failed: {e}")
                continue

        if outlier_votes.empty:
            return np.zeros(len(df), dtype=bool)

        # Voting
        if self.config.ensemble_voting == "hard":
            # Majority vote
            outliers = outlier_votes.sum(axis=1) > len(outlier_votes.columns) / 2
        else:
            # Soft voting (average probability)
            outlier_scores = outlier_votes.mean(axis=1)
            threshold = 0.5
            outliers = outlier_scores > threshold

        # Map back to original DataFrame
        final_outliers = pd.Series(False, index=df.index)
        final_outliers.loc[outliers.index] = outliers

        return final_outliers.values

    def replace_outliers(self, df: pd.DataFrame, column: str,
                        outliers: np.ndarray,
                        method: str = "median") -> pd.Series:
        """
        Replace outliers with imputed values

        Args:
            df: Input DataFrame
            column: Column to process
            outliers: Boolean array indicating outliers
            method: Replacement method ('median', 'mean', 'interpolation', 'rolling_median')

        Returns:
            Series with outliers replaced
        """
        series = df[column].copy()

        if method == "median":
            fill_value = series[~outliers].median()
            series[outliers] = fill_value

        elif method == "mean":
            fill_value = series[~outliers].mean()
            series[outliers] = fill_value

        elif method == "interpolation":
            # Mark outliers as NaN and interpolate
            series[outliers] = np.nan
            series = series.interpolate(method='linear', limit_direction='both')

        elif method == "rolling_median":
            # Use rolling median to fill outliers
            rolling_median = series.rolling(window=5, center=True, min_periods=1).median()
            series[outliers] = rolling_median[outliers]

        elif method == "clip":
            # Clip to IQR bounds
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            series = series.clip(lower_bound, upper_bound)

        return series

    def detect_and_handle_outliers(self, df: pd.DataFrame,
                                  target_columns: Optional[List[str]] = None,
                                  replace_method: str = "median") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main method to detect and handle outliers

        Args:
            df: Input DataFrame
            target_columns: Columns to process (None for all numeric)
            replace_method: Method to replace outliers

        Returns:
            Tuple of (processed DataFrame, statistics dictionary)
        """
        validate_dataframe(df)

        # Detect column types
        self.column_types = DataTypeDetector.detect_column_types(df)
        self.time_col = DataTypeDetector.detect_time_series_column(df)

        # Determine columns to process
        if target_columns is None:
            columns_to_process = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            columns_to_process = [col for col in target_columns
                                if col in df.columns and self.column_types.get(col) == 'numeric']

        df_processed = df.copy()
        statistics = {
            "total_columns_processed": 0,
            "total_outliers_detected": 0,
            "total_outliers_replaced": 0,
            "column_statistics": []
        }

        for column in columns_to_process:
            if column == self.time_col:
                continue  # Skip time column

            logger.info(f"Detecting outliers in column: {column}")

            # Detect outliers
            if self.time_col and self.config.use_ensemble:
                # For time series, use time-series specific methods
                outliers = self.detect_outliers_ensemble(df, column, methods=[
                    'zscore', 'iqr', 'rolling_window', 'moving_average'
                ])
            else:
                outliers = self.detect_outliers_ensemble(df, column)

            outlier_count = np.sum(outliers)
            statistics['total_outliers_detected'] += outlier_count

            # Replace outliers
            if replace_method != "none":
                df_processed[column] = self.replace_outliers(
                    df_processed, column, outliers, method=replace_method
                )
                statistics['total_outliers_replaced'] += outlier_count

            # Calculate statistics
            col_stats = MetricsCalculator.calculate_outlier_statistics(
                df[column], outliers
            )
            col_stats['column'] = column
            col_stats['replacement_method'] = replace_method
            statistics['column_statistics'].append(col_stats)

            logger.info(f"Column '{column}': {outlier_count} outliers detected")

        statistics['total_columns_processed'] = len(columns_to_process)

        logger.info(f"Outlier detection and handling completed. "
                   f"Total outliers: {statistics['total_outliers_detected']}, "
                   f"Replaced: {statistics['total_outliers_replaced']}")

        return df_processed, statistics
