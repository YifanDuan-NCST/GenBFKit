"""
Missing Value Detection and Imputation Module
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
import warnings

from Data_Preprocessing.config import MissingValueConfig
from Data_Preprocessing.utils import (
    DataTypeDetector, MissingValueAnalyzer, InterpolationHelper,
    MetricsCalculator, validate_dataframe
)

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class MissingValueHandler:
    """
    Advanced missing value detection and imputation handler
    Supports multiple state-of-the-art imputation algorithms
    """

    def __init__(self, config: MissingValueConfig):
        """
        Initialize missing value handler

        Args:
            config: MissingValueConfig instance
        """
        self.config = config
        self.column_types = {}
        self.time_col = None

    def analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing value patterns in the data

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with missing value analysis
        """
        validate_dataframe(df)

        # Detect column types and time column
        self.column_types = DataTypeDetector.detect_column_types(df)
        self.time_col = DataTypeDetector.detect_time_series_column(df)

        # Analyze missing patterns
        analysis = MissingValueAnalyzer.analyze_missing_pattern(df)
        analysis['column_types'] = self.column_types
        analysis['time_column'] = self.time_col

        # Detect missing mechanism for each column
        mechanism_analysis = {}
        for col in df.columns:
            if df[col].isnull().any():
                mechanism = MissingValueAnalyzer.detect_mcar_mnar_mar(df, col)
                mechanism_analysis[col] = mechanism

        analysis['missing_mechanism'] = mechanism_analysis

        logger.info(f"Missing value analysis completed. Overall missing rate: {analysis['overall_missing_rate']:.2%}")
        return analysis

    def impute_time_series(self, df: pd.DataFrame, column: str,
                          methods: Optional[List[str]] = None) -> pd.Series:
        """
        Impute missing values in time series using interpolation methods

        Args:
            df: Input DataFrame
            column: Column to impute
            methods: List of methods to try (in order)

        Returns:
            Imputed series
        """
        if methods is None:
            methods = self.config.time_series_methods

        series = df[column].copy()

        for method in methods:
            try:
                if method == "linear_interpolation":
                    if self.time_col and self.time_col in df.columns:
                        imputed = InterpolationHelper.time_based_interpolation(
                            series, df[self.time_col]
                        )
                    else:
                        imputed = InterpolationHelper.linear_interpolation(series)

                elif method == "spline_interpolation":
                    imputed = InterpolationHelper.spline_interpolation(series, order=3)

                elif method == "forward_fill":
                    imputed = InterpolationHelper.forward_fill(series)

                elif method == "backward_fill":
                    imputed = InterpolationHelper.backward_fill(series)

                elif method == "nearest_interpolation":
                    imputed = InterpolationHelper.nearest_interpolation(series)

                elif method == "kalman_filter":
                    # Use linear interpolation with smoothing as approximation
                    imputed = InterpolationHelper.linear_interpolation(series)
                    if not imputed.isnull().any():
                        # Apply simple moving average as smoothing
                        imputed = imputed.rolling(window=3, center=True, min_periods=1).mean()

                else:
                    continue

                # Check if imputation was successful
                missing_before = series.isnull().sum()
                missing_after = imputed.isnull().sum()

                if missing_after < missing_before:
                    logger.info(f"Method '{method}' reduced missing values from {missing_before} to {missing_after}")
                    return imputed

            except Exception as e:
                logger.warning(f"Method '{method}' failed: {e}")
                continue

        # Fallback: fill with mean/median
        if series.dtype in [np.float64, np.int64]:
            fill_value = series.median()
        else:
            fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]

        logger.warning(f"All interpolation methods failed. Fallback to fill with {fill_value}")
        return series.fillna(fill_value)

    def impute_with_knn(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Impute missing values using K-Nearest Neighbors

        Args:
            df: Input DataFrame
            columns: Columns to impute (None for all numeric)

        Returns:
            DataFrame with imputed values
        """
        df_numeric = df.select_dtypes(include=[np.number])
        if columns:
            df_numeric = df_numeric[[col for col in columns if col in df_numeric.columns]]

        if df_numeric.empty:
            return df

        imputer = KNNImputer(
            n_neighbors=self.config.knn_n_neighbors,
            weights=self.config.knn_weights
        )

        imputed_array = imputer.fit_transform(df_numeric)
        df_imputed = df.copy()
        df_imputed[df_numeric.columns] = imputed_array

        return df_imputed

    def impute_with_mice(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Impute missing values using MICE (Multivariate Imputation by Chained Equations)

        Args:
            df: Input DataFrame
            columns: Columns to impute (None for all numeric)

        Returns:
            DataFrame with imputed values
        """
        df_numeric = df.select_dtypes(include=[np.number])
        if columns:
            df_numeric = df_numeric[[col for col in columns if col in df_numeric.columns]]

        if df_numeric.empty:
            return df

        # Use RandomForest as the estimator for MICE
        estimator = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

        imputer = IterativeImputer(
            estimator=estimator,
            max_iter=self.config.mice_max_iter,
            random_state=self.config.mice_random_state
        )

        imputed_array = imputer.fit_transform(df_numeric)
        df_imputed = df.copy()
        df_imputed[df_numeric.columns] = imputed_array

        return df_imputed

    def impute_categorical(self, df: pd.DataFrame, column: str) -> pd.Series:
        """
        Impute missing values in categorical columns

        Args:
            df: Input DataFrame
            column: Categorical column to impute

        Returns:
            Imputed series
        """
        series = df[column].copy()

        for method in self.config.categorical_methods:
            try:
                if method == "most_frequent":
                    fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]
                    imputed = series.fillna(fill_value)

                elif method == "knn":
                    # One-hot encode and use KNN
                    df_encoded = pd.get_dummies(df.select_dtypes(include=[np.number]))
                    if column in df.columns and column in self.column_types:
                        # For categorical, we need special handling
                        # Use most frequent as fallback
                        fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]
                        imputed = series.fillna(fill_value)
                    else:
                        fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]
                        imputed = series.fillna(fill_value)

                elif method == "mice":
                    # Convert to numeric if possible
                    if series.dtype == 'object':
                        # Use most frequent for object type
                        fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]
                        imputed = series.fillna(fill_value)
                    else:
                        imputed = self.impute_with_mice(df[[column]])[column]

                else:
                    continue

                missing_before = series.isnull().sum()
                missing_after = imputed.isnull().sum()

                if missing_after < missing_before:
                    logger.info(f"Categorical method '{method}' reduced missing values from {missing_before} to {missing_after}")
                    return imputed

            except Exception as e:
                logger.warning(f"Categorical method '{method}' failed: {e}")
                continue

        # Fallback
        fill_value = series.mode()[0] if not series.mode().empty else series.dropna().iloc[0]
        logger.warning(f"All categorical methods failed. Fallback to most frequent: {fill_value}")
        return series.fillna(fill_value)

    def handle_missing_values(self, df: pd.DataFrame,
                            target_columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main method to handle missing values with appropriate methods

        Args:
            df: Input DataFrame
            target_columns: Columns to process (None for all)

        Returns:
            Tuple of (imputed DataFrame, statistics dictionary)
        """
        validate_dataframe(df)

        # Analyze missing values
        analysis = self.analyze_missing_values(df)

        if analysis['overall_missing_rate'] == 0:
            logger.info("No missing values found")
            return df.copy(), {"message": "No missing values"}

        df_imputed = df.copy()
        statistics = {
            "original_missing_count": analysis['columns_with_missing'],
            "imputation_methods_used": {},
            "columns_processed": []
        }

        # Determine columns to process
        if target_columns is None:
            columns_to_process = [col for col in df.columns if df[col].isnull().any()]
        else:
            columns_to_process = [col for col in target_columns if col in df.columns and df[col].isnull().any()]

        # Process each column
        for column in columns_to_process:
            logger.info(f"Processing column: {column}")

            col_type = self.column_types.get(column, 'unknown')
            missing_mask = df[column].isnull()
            missing_count = missing_mask.sum()

            if col_type == 'numeric' and column not in [self.time_col]:
                # Try time-series methods first if time column exists
                if self.time_col and df[self.time_col].isnull().sum() < len(df) * 0.1:
                    imputed_series = self.impute_time_series(df, column)
                else:
                    imputed_series = df[column].copy()

                # If still has missing values, try advanced methods
                if imputed_series.isnull().any():
                    if self.config.use_mice:
                        df_temp = self.impute_with_mice(df, [column])
                        imputed_series = df_temp[column]

                    if imputed_series.isnull().any() and self.config.use_knn:
                        df_temp = self.impute_with_knn(df, [column])
                        imputed_series = df_temp[column]

                df_imputed[column] = imputed_series
                statistics['imputation_methods_used'][column] = "time_series/mice/knn"

            elif col_type in ['categorical', 'text', 'categorical_numeric']:
                imputed_series = self.impute_categorical(df, column)
                df_imputed[column] = imputed_series
                statistics['imputation_methods_used'][column] = "categorical"

            elif col_type == 'datetime':
                # For datetime, use forward/backward fill with interpolation
                imputed_series = self.impute_time_series(df, column)
                df_imputed[column] = imputed_series
                statistics['imputation_methods_used'][column] = "datetime_interpolation"

            else:
                # Unknown type, use simple imputation
                if df[column].dtype in [np.float64, np.int64]:
                    fill_value = df[column].median()
                else:
                    fill_value = df[column].mode()[0] if not df[column].mode().empty else df[column].dropna().iloc[0]

                df_imputed[column] = df[column].fillna(fill_value)
                statistics['imputation_methods_used'][column] = "simple_fill"

            # Calculate statistics
            filled_count = missing_count - df_imputed[column].isnull().sum()
            statistics['columns_processed'].append({
                "column": column,
                "type": col_type,
                "original_missing": int(missing_count),
                "filled": int(filled_count),
                "remaining": int(df_imputed[column].isnull().sum()),
                "fill_rate": float(filled_count / missing_count) if missing_count > 0 else 1.0
            })

        # Verify
        final_missing = df_imputed.isnull().sum().sum()
        statistics['final_missing_count'] = int(final_missing)
        statistics['imputation_success_rate'] = 1.0 - (final_missing / analysis['columns_with_missing'].get(column, 0)) if analysis['columns_with_missing'] else 1.0

        logger.info(f"Missing value handling completed. Remaining missing: {final_missing}")
        return df_imputed, statistics
