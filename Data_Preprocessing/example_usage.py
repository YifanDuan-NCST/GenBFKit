"""
GenBFKit Data Preprocessing Module - Example Usage
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig, DatabaseManager
from Data_Preprocessing import MissingValueHandler, MissingValueConfig
from Data_Preprocessing import OutlierDetector, OutlierDetectionConfig
from Data_Preprocessing import DataNormalizer, NormalizationConfig


def generate_sample_data(n_samples=1000):
    """Generate sample time-series sensor data"""
    # Generate time series
    start_time = datetime(2024, 1, 1)
    timestamps = [start_time + timedelta(minutes=i) for i in range(n_samples)]

    # Generate sensor data with some noise
    np.random.seed(42)
    temperature = 1500 + 50 * np.sin(np.linspace(0, 4*np.pi, n_samples)) + np.random.normal(0, 5, n_samples)
    pressure = 200 + 20 * np.cos(np.linspace(0, 2*np.pi, n_samples)) + np.random.normal(0, 2, n_samples)
    flow_rate = 100 + 10 * np.sin(np.linspace(0, 3*np.pi, n_samples)) + np.random.normal(0, 1, n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': temperature,
        'pressure': pressure,
        'flow_rate': flow_rate
    })

    return df


def inject_missing_values(df, missing_rate=0.1):
    """Inject missing values into DataFrame"""
    df_missing = df.copy()
    n_rows = len(df_missing)

    # Randomly set some values to NaN
    for col in ['temperature', 'pressure', 'flow_rate']:
        n_missing = int(n_rows * missing_rate)
        missing_indices = np.random.choice(n_rows, n_missing, replace=False)
        df_missing.loc[missing_indices, col] = np.nan

    # Add some consecutive missing values (more realistic)
    for col in ['temperature']:
        start_idx = np.random.randint(0, n_rows - 20)
        df_missing.loc[start_idx:start_idx+10, col] = np.nan

    return df_missing


def inject_outliers(df, outlier_rate=0.02):
    """Inject outliers into DataFrame"""
    df_outlier = df.copy()
    n_rows = len(df_outlier)

    # Add extreme values
    for col in ['temperature', 'pressure', 'flow_rate']:
        n_outliers = int(n_rows * outlier_rate)
        outlier_indices = np.random.choice(n_rows, n_outliers, replace=False)

        if col == 'temperature':
            # Add extreme temperatures
            df_outlier.loc[outlier_indices, col] *= 1.5
        elif col == 'pressure':
            # Add extreme pressures
            df_outlier.loc[outlier_indices, col] *= 2.0
        else:
            # Add extreme flow rates
            df_outlier.loc[outlier_indices, col] *= 1.8

    return df_outlier


def example_1_basic_preprocessing():
    """Example 1: Basic preprocessing with default configuration"""
    print("=" * 60)
    print("Example 1: Basic Preprocessing")
    print("=" * 60)

    # Generate sample data
    df = generate_sample_data(1000)
    df = inject_missing_values(df, 0.1)
    df = inject_outliers(df, 0.02)

    print(f"\nOriginal data shape: {df.shape}")
    print(f"Missing values per column:")
    print(df.isnull().sum())

    # Create pipeline
    config = PreprocessingConfig()
    pipeline = PreprocessingPipeline(config)

    # Analyze data quality
    print("\n" + "-" * 60)
    print("Data Quality Analysis")
    print("-" * 60)
    quality_report = pipeline.analyze_data_quality(df)
    print(f"Overall missing rate: {quality_report['overall_missing_rate']:.2%}")
    print(f"Duplicate rows: {quality_report['duplicate_rows']}")

    # Preprocess data
    print("\n" + "-" * 60)
    print("Preprocessing Data")
    print("-" * 60)
    steps = ["missing_values", "outlier_detection", "normalization"]

    df_processed, stats = pipeline.preprocess_dataframe(
        df=df,
        steps=steps
    )

    print(f"\nProcessed data shape: {df_processed.shape}")
    print(f"Remaining missing values: {df_processed.isnull().sum().sum()}")

    print("\nStep results:")
    for step, step_stats in stats.get('step_results', {}).items():
        print(f"\n{step}:")
        if 'final_missing_count' in step_stats:
            print(f"  Final missing count: {step_stats['final_missing_count']}")
        if 'total_outliers_detected' in step_stats:
            print(f"  Outliers detected: {step_stats['total_outliers_detected']}")
        if 'total_outliers_replaced' in step_stats:
            print(f"  Outliers replaced: {step_stats['total_outliers_replaced']}")
        if 'columns_normalized' in step_stats:
            print(f"  Columns normalized: {len(step_stats['columns_normalized'])}")

    print("\n" + "=" * 60 + "\n")


def example_2_custom_missing_value_handling():
    """Example 2: Custom missing value handling configuration"""
    print("=" * 60)
    print("Example 2: Custom Missing Value Handling")
    print("=" * 60)

    # Generate data with missing values
    df = generate_sample_data(500)
    df = inject_missing_values(df, 0.15)

    print(f"\nOriginal missing values:")
    print(df.isnull().sum())

    # Custom configuration
    mv_config = MissingValueConfig(
        use_mice=True,
        mice_max_iter=15,
        use_knn=True,
        knn_n_neighbors=7,
        knn_weights="distance",
        time_series_methods=[
            "linear_interpolation",
            "spline_interpolation",
            "kalman_filter"
        ]
    )

    handler = MissingValueHandler(mv_config)

    # Analyze missing patterns
    print("\n" + "-" * 60)
    print("Missing Value Analysis")
    print("-" * 60)
    analysis = handler.analyze_missing_values(df)
    print(f"Overall missing rate: {analysis['overall_missing_rate']:.2%}")
    print(f"Missing mechanism by column:")
    for col, mechanism in analysis.get('missing_mechanism', {}).items():
        print(f"  {col}: {mechanism}")

    # Handle missing values
    print("\n" + "-" * 60)
    print("Imputing Missing Values")
    print("-" * 60)
    df_imputed, imputation_stats = handler.handle_missing_values(df)

    print(f"\nImputation statistics:")
    for col_stat in imputation_stats.get('columns_processed', []):
        print(f"\n  Column: {col_stat['column']}")
        print(f"    Original missing: {col_stat['original_missing']}")
        print(f"    Filled: {col_stat['filled']}")
        print(f"    Remaining: {col_stat['remaining']}")
        print(f"    Fill rate: {col_stat['fill_rate']:.2%}")

    print(f"\nFinal missing count: {df_imputed.isnull().sum().sum()}")
    print("\n" + "=" * 60 + "\n")


def example_3_custom_outlier_detection():
    """Example 3: Custom outlier detection with ensemble methods"""
    print("=" * 60)
    print("Example 3: Custom Outlier Detection")
    print("=" * 60)

    # Generate data with outliers
    df = generate_sample_data(800)
    df = inject_outliers(df, 0.03)

    # Custom configuration
    od_config = OutlierDetectionConfig(
        methods=[
            "isolation_forest",
            "local_outlier_factor",
            "zscore",
            "iqr",
            "rolling_window"
        ],
        use_ensemble=True,
        ensemble_voting="soft",  # Use soft voting
        iso_forest_contamination=0.04,
        lof_n_neighbors=25,
        zscore_threshold=2.5,
        iqr_multiplier=2.0,
        time_series_window=15
    )

    detector = OutlierDetector(od_config)

    # Detect and handle outliers
    print("\nDetecting and handling outliers...")
    df_cleaned, detection_stats = detector.detect_and_handle_outliers(
        df,
        replace_method="median"
    )

    print(f"\nOutlier detection summary:")
    print(f"  Total columns processed: {detection_stats['total_columns_processed']}")
    print(f"  Total outliers detected: {detection_stats['total_outliers_detected']}")
    print(f"  Total outliers replaced: {detection_stats['total_outliers_replaced']}")

    print(f"\nPer-column statistics:")
    for col_stat in detection_stats.get('column_statistics', []):
        print(f"\n  Column: {col_stat['column']}")
        print(f"    Outlier count: {col_stat['outlier_count']}")
        print(f"    Outlier rate: {col_stat['outlier_rate']:.2%}")
        print(f"    Normal mean: {col_stat['normal_mean']:.2f}")
        print(f"    Normal std: {col_stat['normal_std']:.2f}")
        print(f"    Outlier mean: {col_stat['outlier_mean']:.2f}")

    print("\n" + "=" * 60 + "\n")


def example_4_data_normalization():
    """Example 4: Different normalization methods"""
    print("=" * 60)
    print("Example 4: Data Normalization Methods")
    print("=" * 60)

    # Generate clean data
    df = generate_sample_data(500)

    numeric_cols = ['temperature', 'pressure', 'flow_rate']

    # Test different normalization methods
    methods = ['zscore', 'minmax', 'robust', 'quantile', 'yeo-johnson']

    for method in methods:
        print(f"\n{'-' * 60}")
        print(f"Normalization Method: {method}")
        print("-" * 60)

        config = NormalizationConfig(method=method)
        normalizer = DataNormalizer(config)

        df_normalized, stats = normalizer.normalize(df, columns=numeric_cols)

        print(f"\nNormalized statistics:")
        for col in numeric_cols:
            if col in stats.get('normalized_stats', {}):
                norm_stats = stats['normalized_stats'][col]
                orig_stats = stats['original_stats'][col]
                print(f"\n  {col}:")
                print(f"    Original - Mean: {orig_stats['mean']:.2f}, Std: {orig_stats['std']:.2f}")
                print(f"    Normalized - Mean: {norm_stats['mean']:.2f}, Std: {norm_stats['std']:.2f}")
                print(f"    Range: [{norm_stats['min']:.2f}, {norm_stats['max']:.2f}]")

    # Save scalers
    print("\n" + "=" * 60)
    print("Saving and Loading Scalers")
    print("=" * 60)

    config = NormalizationConfig(method="zscore")
    normalizer = DataNormalizer(config)
    df_normalized, _ = normalizer.normalize(df, columns=numeric_cols)

    normalizer.save_scalers("example_scalers.pkl")
    print("Scalers saved to example_scalers.pkl")

    # Load and inverse transform
    normalizer2 = DataNormalizer(config)
    normalizer2.load_scalers("example_scalers.pkl")

    df_original = normalizer2.inverse_normalize(df_normalized, numeric_cols)
    print(f"Inverse transformation completed")

    # Verify reconstruction
    max_error = np.max(np.abs(df[numeric_cols].values - df_original[numeric_cols].values))
    print(f"Maximum reconstruction error: {max_error:.6f}")

    print("\n" + "=" * 60 + "\n")


def example_5_database_integration():
    """Example 5: Database integration (requires PostgreSQL)"""
    print("=" * 60)
    print("Example 5: Database Integration")
    print("=" * 60)

    # This example requires a running PostgreSQL database
    # Uncomment and configure to run

    """
    from Data_Preprocessing.config import DatabaseConfig

    # Database configuration
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="genbfkit",
        user="postgres",
        password="your_password"
    )

    # Create main configuration
    config = PreprocessingConfig(database=db_config)

    # Initialize database manager
    db_manager = DatabaseManager(db_config)

    # Create pipeline with database support
    pipeline = PreprocessingPipeline(config, db_manager)

    # Preprocess a table from database
    steps = ["missing_values", "outlier_detection", "normalization"]

    try:
        df_processed, stats = pipeline.preprocess_table(
            table_name="sensor_data",
            steps=steps,
            save_to_db=True
        )

        print(f"Preprocessing completed for table 'sensor_data'")
        print(f"Rows processed: {stats.get('rows_processed', 0)}")
        print(f"Rows modified: {stats.get('rows_modified', 0)}")

    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'genbfkit' exists")
        print("  3. Table 'sensor_data' exists in the database")
        print("  4. Database credentials are correct")

    finally:
        db_manager.close()
    """

    print("This example requires a PostgreSQL database.")
    print("Please configure your database connection and uncomment the code above to run.")
    print("\n" + "=" * 60 + "\n")


def example_6_batch_processing():
    """Example 6: Batch processing with pipeline"""
    print("=" * 60)
    print("Example 6: Batch Processing (Simulated)")
    print("=" * 60)

    # Simulate batch processing with multiple datasets
    datasets = {
        "sensor_1": generate_sample_data(300),
        "sensor_2": generate_sample_data(400),
        "sensor_3": generate_sample_data(350)
    }

    # Inject issues
    for name, df in datasets.items():
        datasets[name] = inject_missing_values(df, 0.1)
        datasets[name] = inject_outliers(df, 0.02)

    print(f"Processing {len(datasets)} datasets...")

    config = PreprocessingConfig()
    pipeline = PreprocessingPipeline(config)

    results = {}
    for name, df in datasets.items():
        print(f"\nProcessing {name}...")
        df_processed, stats = pipeline.preprocess_dataframe(
            df=df,
            steps=["missing_values", "outlier_detection", "normalization"]
        )

        results[name] = {
            "status": "success",
            "original_rows": len(df),
            "final_rows": len(df_processed),
            "stats": stats
        }

        print(f"  Original rows: {len(df)}")
        print(f"  Final rows: {len(df_processed)}")

    print("\n" + "=" * 60)
    print("Batch Processing Summary")
    print("=" * 60)

    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Status: {result['status']}")
        print(f"  Rows: {result['original_rows']} → {result['final_rows']}")

        mv_stats = result['stats'].get('step_results', {}).get('missing_values', {})
        if 'final_missing_count' in mv_stats:
            print(f"  Missing values handled: {mv_stats['final_missing_count'] == 0}")

        od_stats = result['stats'].get('step_results', {}).get('outlier_detection', {})
        if 'total_outliers_replaced' in od_stats:
            print(f"  Outliers replaced: {od_stats['total_outliers_replaced']}")

    print("\n" + "=" * 60 + "\n")


def main():
    """Run all examples"""
    print("\n")
    print("*" * 60)
    print("GenBFKit Data Preprocessing Module - Usage Examples")
    print("*" * 60)
    print("\n")

    # Run examples
    example_1_basic_preprocessing()
    example_2_custom_missing_value_handling()
    example_3_custom_outlier_detection()
    example_4_data_normalization()
    example_5_database_integration()
    example_6_batch_processing()

    print("*" * 60)
    print("All examples completed!")
    print("*" * 60)
    print("\n")


if __name__ == "__main__":
    main()
