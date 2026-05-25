"""
Database Manager Module for PostgreSQL Operations
"""

import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values, RealDictCursor
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging
from datetime import datetime

from Data_Preprocessing.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """PostgreSQL database manager with connection pooling"""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database manager with configuration

        Args:
            config: DatabaseConfig instance
        """
        self.config = config
        self._pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size + self.config.max_overflow,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)

    def execute_query(self, query: str, params: Optional[Tuple] = None,
                     fetch: bool = True) -> Optional[List[Dict]]:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            List of result rows if fetch=True, else None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    return [dict(row) for row in result]
                else:
                    conn.commit()
                    return None

    def get_table_data(self, table_name: str, columns: Optional[List[str]] = None,
                      limit: Optional[int] = None, conditions: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve data from a table as DataFrame

        Args:
            table_name: Name of the table
            columns: List of columns to retrieve (None for all)
            limit: Maximum number of rows
            conditions: SQL WHERE clause conditions

        Returns:
            DataFrame with table data
        """
        col_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_str} FROM {self.config.schema}.{table_name}"

        if conditions:
            query += f" WHERE {conditions}"

        if limit:
            query += f" LIMIT {limit}"

        result = self.execute_query(query)
        df = pd.DataFrame(result)

        # Convert timestamp columns to datetime
        for col in df.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def insert_dataframe(self, table_name: str, df: pd.DataFrame,
                        if_exists: str = "append") -> int:
        """
        Insert DataFrame into table

        Args:
            table_name: Name of the table
            df: DataFrame to insert
            if_exists: What to do if table exists ('append', 'replace', 'fail')

        Returns:
            Number of rows inserted
        """
        if df.empty:
            logger.warning(f"Empty DataFrame provided for table {table_name}")
            return 0

        if if_exists == "replace":
            self.execute_query(f"TRUNCATE TABLE {self.config.schema}.{table_name}", fetch=False)

        columns = df.columns.tolist()
        values = [tuple(row) for row in df.values]

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                insert_query = f"""
                    INSERT INTO {self.config.schema}.{table_name}
                    ({', '.join(columns)})
                    VALUES %s
                """
                execute_values(cursor, insert_query, values)
                inserted_count = cursor.rowcount
                conn.commit()

        logger.info(f"Inserted {inserted_count} rows into {table_name}")
        return inserted_count

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table

        Args:
            table_name: Name of the table

        Returns:
            List of column dictionaries
        """
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, (self.config.schema, table_name))

    def list_tables(self, pattern: Optional[str] = None) -> List[str]:
        """
        List tables in the schema

        Args:
            pattern: Optional pattern to filter table names

        Returns:
            List of table names
        """
        query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{self.config.schema}'
        """
        if pattern:
            query += f" AND table_name LIKE '%{pattern}%'"

        result = self.execute_query(query)
        return [row['table_name'] for row in result]

    def create_preprocessing_metadata_table(self, table_name: str = "preprocessing_metadata") -> None:
        """
        Create table to store preprocessing metadata

        Args:
            table_name: Name of the metadata table
        """
        query = f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema}.{table_name} (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(255) NOT NULL,
                preprocessing_type VARCHAR(100) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status VARCHAR(50) NOT NULL,
                parameters JSONB,
                statistics JSONB,
                rows_processed INTEGER,
                rows_modified INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_metadata_table ON {self.config.schema}.{table_name}(table_name);
            CREATE INDEX IF NOT EXISTS idx_metadata_type ON {self.config.schema}.{table_name}(preprocessing_type);
            CREATE INDEX IF NOT EXISTS idx_metadata_time ON {self.config.schema}.{table_name}(start_time);
        """
        self.execute_query(query, fetch=False)
        logger.info(f"Metadata table {table_name} created or already exists")

    def save_preprocessing_metadata(self, table_name: str, preprocessing_type: str,
                                   status: str, parameters: Dict[str, Any],
                                   statistics: Dict[str, Any], rows_processed: int,
                                   rows_modified: int, error_message: Optional[str] = None,
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None) -> int:
        """
        Save preprocessing operation metadata

        Args:
            table_name: Name of the processed table
            preprocessing_type: Type of preprocessing (e.g., 'missing_value_imputation')
            status: Status of the operation ('started', 'completed', 'failed')
            parameters: Parameters used in preprocessing
            statistics: Statistics about the preprocessing
            rows_processed: Number of rows processed
            rows_modified: Number of rows modified
            error_message: Error message if failed
            start_time: Start time of operation
            end_time: End time of operation

        Returns:
            ID of the inserted metadata record
        """
        if not start_time:
            start_time = datetime.now()

        query = f"""
            INSERT INTO {self.config.schema}.preprocessing_metadata
            (table_name, preprocessing_type, start_time, end_time, status,
             parameters, statistics, rows_processed, rows_modified, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        result = self.execute_query(
            query,
            (
                table_name, preprocessing_type, start_time, end_time,
                status, json.dumps(parameters), json.dumps(statistics),
                rows_processed, rows_modified, error_message
            )
        )

        if result:
            return result[0]['id']
        return -1

    def backup_table(self, table_name: str, backup_suffix: str = "_backup") -> str:
        """
        Create a backup of a table

        Args:
            table_name: Name of the table to backup
            backup_suffix: Suffix for backup table name

        Returns:
            Name of the backup table
        """
        backup_table = f"{table_name}{backup_suffix}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_backup_name = f"{backup_table}_{timestamp}"

        query = f"CREATE TABLE {self.config.schema}.{final_backup_name} AS SELECT * FROM {self.config.schema}.{table_name}"
        self.execute_query(query, fetch=False)

        logger.info(f"Created backup: {final_backup_name}")
        return final_backup_name

    def get_data_statistics(self, table_name: str, column: Optional[str] = None) -> Dict[str, Any]:
        """
        Get basic statistics for table data

        Args:
            table_name: Name of the table
            column: Specific column to analyze (None for all numeric columns)

        Returns:
            Dictionary with statistics
        """
        df = self.get_table_data(table_name)

        if column:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in table")
            numeric_cols = [column]
        else:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return {"message": "No numeric columns found"}

        stats = {}
        for col in numeric_cols:
            col_stats = {
                "count": df[col].count(),
                "missing": df[col].isnull().sum(),
                "missing_rate": df[col].isnull().sum() / len(df) if len(df) > 0 else 0,
                "mean": float(df[col].mean()) if df[col].count() > 0 else None,
                "std": float(df[col].std()) if df[col].count() > 0 else None,
                "min": float(df[col].min()) if df[col].count() > 0 else None,
                "max": float(df[col].max()) if df[col].count() > 0 else None,
                "median": float(df[col].median()) if df[col].count() > 0 else None,
                "q25": float(df[col].quantile(0.25)) if df[col].count() > 0 else None,
                "q75": float(df[col].quantile(0.75)) if df[col].count() > 0 else None
            }
            stats[col] = col_stats

        return stats

    def close(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")
