"""
Utility Functions for Data Preprocessing
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from datetime import datetime
from scipy import stats
from scipy.interpolate import interp1d
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler, QuantileTransformer, PowerTransformer

logger = logging.getLogger(__name__)


class DataTypeDetector:
    """Detect and classify data types for appropriate preprocessing"""

    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect data types for each column

        Args:
            df: Input DataFrame

        Returns:
            Dictionary mapping column names to detected types
        """
        column_types = {}

        for col in df.columns:
            if df[col].dtype in ['object', 'category']:
                # Check if it's actually categorical but numeric
                try:
                    pd.to_numeric(df[col], errors='raise')
                    # Convertible to numeric
                    if df[col].nunique() < 20:  # Few unique values
                        column_types[col] = 'categorical_numeric'
                    else:
                        column_types[col] = 'numeric'
                except:
                    if df[col].nunique() / len(df) < 0.05:  # Low cardinality
                        column_types[col] = 'categorical'
                    else:
                        column_types[col] = 'text'
            elif np.issubdtype(df[col].dtype, np.datetime64):
                column_types[col] = 'datetime'
            elif np.issubdtype(df[col].dtype, np.number):
                if df[col].nunique() < 20:  # Few unique values
                    column_types[col] = 'categorical_numeric'
                else:
                    column_types[col] = 'numeric'
            else:
                column_types[col] = 'unknown'

        return column_types

    @staticmethod
    def detect_time_series_column(df: pd.DataFrame) -> Optional[str]:
        """
        Detect the time series column in DataFrame

        Args:
            df: Input DataFrame

        Returns:
            Name of the time series column or None
        """
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower() or 'timestamp' in col.lower():
                try:
                    pd.to_datetime(df[col], errors='raise')
                    return col
                except:
                    continue

        # Try to find datetime type
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            return datetime_cols[0]

        return None


class MissingValueAnalyzer:
    """Analyze missing value patterns"""

    @staticmethod
    def analyze_missing_pattern(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing value patterns in DataFrame

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with missing value analysis results
        """
        missing_count = df.isnull().sum()
        missing_rate = missing_count / len(df)

        result = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns_with_missing": missing_count[missing_count > 0].to_dict(),
            "missing_rate_by_column": missing_rate[missing_rate > 0].to_dict(),
            "overall_missing_rate": df.isnull().sum().sum() / (len(df) * len(df.columns)),
            "complete_rows": len(df.dropna()),
            "complete_rows_rate": len(df.dropna()) / len(df)
        }

        # Missing pattern analysis
        missing_patterns = df.isnull().astype(int).value_counts().sort_index(ascending=False)
        result["missing_patterns"] = {
            "pattern_counts": missing_patterns.head(10).to_dict(),
            "unique_patterns": len(missing_patterns)
        }

        return result

    @staticmethod
    def detect_mcar_mnar_mar(df: pd.DataFrame, column: str) -> str:
        """
        Simple heuristic to detect missing data mechanism

        Args:
            df: Input DataFrame
            column: Column to analyze

        Returns:
            'MCAR', 'MNAR', or 'MAR' (simplified detection)
        """
        if column not in df.columns:
            return 'Unknown'

        col_missing = df[column].isnull()
        other_cols = [c for c in df.columns if c != column and c in df.select_dtypes(include=[np.number]).columns]

        if not other_cols:
            return 'Unknown'

        # Test correlation with other numeric columns
        correlations = []
        for other_col in other_cols:
            if df[other_col].notnull().any():
                corr = df[other_col].notnull().astype(int).corr(col_missing.astype(int))
                correlations.append(abs(corr))

        if not correlations:
            return 'MCAR'

        avg_corr = np.mean(correlations)

        if avg_corr < 0.1:
            return 'MCAR'
        elif avg_corr < 0.3:
            return 'MAR'
        else:
            return 'MNAR'


class StatisticalTests:
    """Statistical tests for data validation"""

    @staticmethod
    def test_normality(data: pd.Series) -> Dict[str, Any]:
        """
        Test if data follows normal distribution

        Args:
            data: Input series

        Returns:
            Dictionary with test results
        """
        data = data.dropna()
        if len(data) < 3:
            return {"error": "Insufficient data points"}

        # Shapiro-Wilk test (for n < 5000)
        if len(data) < 5000:
            statistic, p_value = stats.shapiro(data)
            test_name = "Shapiro-Wilk"
        else:
            # Kolmogorov-Smirnov test
            statistic, p_value = stats.kstest(data, 'norm')
            test_name = "Kolmogorov-Smirnov"

        return {
            "test": test_name,
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_normal": p_value > 0.05,
            "alpha": 0.05
        }

    @staticmethod
    def detect_outliers_statistical(data: pd.Series, method: str = "iqr",
                                    threshold: float = 3.0) -> np.ndarray:
        """
        Detect outliers using statistical methods

        Args:
            data: Input series
            method: 'iqr' or 'zscore'
            threshold: Threshold value

        Returns:
            Boolean array indicating outliers
        """
        data = data.dropna()
        if len(data) == 0:
            return np.array([])

        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outliers = (data < lower_bound) | (data > upper_bound)

        elif method == "zscore":
            z_scores = np.abs(stats.zscore(data))
            outliers = z_scores > threshold

        else:
            raise ValueError(f"Unknown method: {method}")

        return outliers


class InterpolationHelper:
    """Helper functions for interpolation methods"""

    @staticmethod
    def linear_interpolation(series: pd.Series, limit_direction: str = 'both',
                           limit_area: Optional[str] = None) -> pd.Series:
        """Linear interpolation for time series"""
        return series.interpolate(method='linear', limit_direction=limit_direction,
                                limit_area=limit_area)

    @staticmethod
    def spline_interpolation(series: pd.Series, order: int = 3,
                            limit_direction: str = 'both') -> pd.Series:
        """Cubic spline interpolation for time series"""
        return series.interpolate(method='spline', order=order,
                                limit_direction=limit_direction)

    @staticmethod
    def time_based_interpolation(series: pd.Series, time_col: pd.Series) -> pd.Series:
        """Time-based interpolation considering timestamp"""
        if len(series) != len(time_col):
            raise ValueError("Series and time_col must have same length")

        df = pd.DataFrame({'time': time_col, 'value': series})
        df = df.sort_values('time')
        df['interpolated'] = df['value'].interpolate(method='time')
        return df.set_index(df.index)['interpolated']

    @staticmethod
    def nearest_interpolation(series: pd.Series) -> pd.Series:
        """Nearest neighbor interpolation"""
        return series.interpolate(method='nearest')

    @staticmethod
    def forward_fill(series: pd.Series, limit: Optional[int] = None) -> pd.Series:
        """Forward fill missing values"""
        return series.ffill(limit=limit)

    @staticmethod
    def backward_fill(series: pd.Series, limit: Optional[int] = None) -> pd.Series:
        """Backward fill missing values"""
        return series.bfill(limit=limit)


class RollingWindowHelper:
    """Helper functions for rolling window operations"""

    @staticmethod
    def rolling_mean(series: pd.Series, window: int, center: bool = True) -> pd.Series:
        """Calculate rolling mean"""
        return series.rolling(window=window, center=center).mean()

    @staticmethod
    def rolling_std(series: pd.Series, window: int, center: bool = True) -> pd.Series:
        """Calculate rolling standard deviation"""
        return series.rolling(window=window, center=center).std()

    @staticmethod
    def rolling_median(series: pd.Series, window: int, center: bool = True) -> pd.Series:
        """Calculate rolling median"""
        return series.rolling(window=window, center=center).median()

    @staticmethod
    def exponential_smoothing(series: pd.Series, alpha: float = 0.3) -> pd.Series:
        """Exponential smoothing"""
        return series.ewm(alpha=alpha).mean()


class MetricsCalculator:
    """Calculate preprocessing metrics"""

    @staticmethod
    def calculate_imputation_quality(original: pd.Series, imputed: pd.Series,
                                    mask: pd.Series) -> Dict[str, float]:
        """
        Calculate imputation quality metrics

        Args:
            original: Original data (with NaN)
            imputed: Imputed data
            mask: Boolean mask indicating imputed positions

        Returns:
            Dictionary with quality metrics
        """
        # Get imputed values
        imputed_values = imputed[mask]
        # For validation, we'd need original non-missing values, but here we return basic stats
        return {
            "count_imputed": int(mask.sum()),
            "imputation_rate": float(mask.mean()),
            "mean_imputed": float(imputed_values.mean()) if len(imputed_values) > 0 else 0,
            "std_imputed": float(imputed_values.std()) if len(imputed_values) > 0 else 0,
            "min_imputed": float(imputed_values.min()) if len(imputed_values) > 0 else 0,
            "max_imputed": float(imputed_values.max()) if len(imputed_values) > 0 else 0
        }

    @staticmethod
    def calculate_outlier_statistics(series: pd.Series, outliers: np.ndarray) -> Dict[str, Any]:
        """
        Calculate statistics about detected outliers

        Args:
            series: Input series
            outliers: Boolean array indicating outliers

        Returns:
            Dictionary with outlier statistics
        """
        if not isinstance(outliers, pd.Series):
            outliers = pd.Series(outliers, index=series.index)

        outlier_values = series[outliers]
        normal_values = series[~outliers]

        return {
            "total_count": len(series),
            "outlier_count": int(outliers.sum()),
            "outlier_rate": float(outliers.mean()),
            "outlier_mean": float(outlier_values.mean()) if len(outlier_values) > 0 else None,
            "outlier_std": float(outlier_values.std()) if len(outlier_values) > 0 else None,
            "normal_mean": float(normal_values.mean()) if len(normal_values) > 0 else None,
            "normal_std": float(normal_values.std()) if len(normal_values) > 0 else None,
            "outlier_min": float(outlier_values.min()) if len(outlier_values) > 0 else None,
            "outlier_max": float(outlier_values.max()) if len(outlier_values) > 0 else None
        }


def log_execution_time(func):
    """Decorator to log execution time"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate DataFrame format

    Args:
        df: DataFrame to validate

    Raises:
        ValueError: If DataFrame is invalid
    """
    if df is None:
        raise ValueError("DataFrame is None")

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if df.empty:
        raise ValueError("DataFrame is empty")

    if len(df.columns) == 0:
        raise ValueError("DataFrame has no columns")
