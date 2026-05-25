"""
GenBFKit 时间尺度对齐模板 - PostgreSQL 数据库集成模块
提供与 GenBFKit 数据库的交互功能，包括元数据更新、对齐日志记录等
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2 import sql, extras
from psycopg2.extras import execute_batch

# 导入核心模块
from time_scale_alignment_template import (
    TimeScaleAlignmentTemplate,
    AlignmentResult,
    TimeAlignmentConfig,
    InterpolationMethod,
    TimestampFormat
)

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库连接配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "genbfkit"
    user: str = "postgres"
    password: str = ""
    schema: str = "public"


class PostgreSQLAlignmentManager:
    """PostgreSQL 对齐管理器"""

    def __init__(self, db_config: DatabaseConfig, alignment_config: TimeAlignmentConfig):
        """
        初始化 PostgreSQL 对齐管理器

        Args:
            db_config: 数据库配置
            alignment_config: 对齐配置
        """
        self.db_config = db_config
        self.alignment_config = alignment_config
        self.tsat = TimeScaleAlignmentTemplate(alignment_config)
        self.connection = None

    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password
            )
            logger.info(f"成功连接到数据库: {self.db_config.database}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def setup_metadata_tables(self):
        """初始化元数据表结构（GenBFKit 扩展）"""
        with self.connection.cursor() as cur:
            try:
                # 1. 扩展 Data attribute dictionary 表
                alter_sql = """
                ALTER TABLE "Data attribute dictionary"
                ADD COLUMN IF NOT EXISTS time_alignment_strategy VARCHAR(50),
                ADD COLUMN IF NOT EXISTS default_timezone VARCHAR(50) DEFAULT 'UTC',
                ADD COLUMN IF NOT EXISTS timestamp_format VARCHAR(50) DEFAULT 'ISO8601',
                ADD COLUMN IF NOT EXISTS sampling_interval_seconds FLOAT,
                ADD COLUMN IF NOT EXISTS allow_interpolation BOOLEAN DEFAULT true,
                ADD COLUMN IF NOT EXISTS interpolation_method VARCHAR(50) DEFAULT 'LINEAR';
                """
                cur.execute(alter_sql)
                logger.info("Data attribute dictionary 表扩展完成")

                # 2. 创建时间对齐日志表
                create_log_table_sql = """
                CREATE TABLE IF NOT EXISTS time_alignment_log (
                    log_id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    batch_id VARCHAR(100) NOT NULL,
                    source_timestamp TIMESTAMP WITH TIME ZONE,
                    aligned_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    alignment_method VARCHAR(50),
                    interpolation_method VARCHAR(50),
                    is_interpolated BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_time_alignment_log_table
                ON time_alignment_log(table_name);
                CREATE INDEX IF NOT EXISTS idx_time_alignment_log_batch
                ON time_alignment_log(batch_id);
                CREATE INDEX IF NOT EXISTS idx_time_alignment_log_ts
                ON time_alignment_log(aligned_timestamp);
                """
                cur.execute(create_log_table_sql)
                logger.info("time_alignment_log 表创建完成")

                # 3. 创建对齐批次摘要表
                create_batch_summary_sql = """
                CREATE TABLE IF NOT EXISTS time_alignment_batch_summary (
                    batch_id VARCHAR(100) PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    original_record_count INTEGER NOT NULL,
                    aligned_record_count INTEGER NOT NULL,
                    interpolated_count INTEGER NOT NULL,
                    missing_count INTEGER NOT NULL,
                    alignment_config JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_alignment_batch_summary_table
                ON time_alignment_batch_summary(table_name);
                """
                cur.execute(create_batch_summary_sql)
                logger.info("time_alignment_batch_summary 表创建完成")

                self.connection.commit()

            except Exception as e:
                self.connection.rollback()
                logger.error(f"元数据表初始化失败: {e}")
                raise

    def get_table_alignment_config(self, table_name: str) -> Optional[Dict]:
        """
        从数据字典获取表的对齐配置

        Args:
            table_name: 表名

        Returns:
            Optional[Dict]: 对齐配置字典
        """
        with self.connection.cursor() as cur:
            query = """
            SELECT
                tad.time_alignment_strategy,
                tad.default_timezone,
                tad.timestamp_format,
                tad.sampling_interval_seconds,
                tad.allow_interpolation,
                tad.interpolation_method
            FROM "Data attribute dictionary" tad
            JOIN "Dataset dictionary" dd ON tad.dataset_id = dd.dataset_id
            WHERE dd.table_name = %s;
            """
            cur.execute(query, (table_name,))
            result = cur.fetchone()

            if result:
                return {
                    "time_alignment_strategy": result[0],
                    "default_timezone": result[1] or "UTC",
                    "timestamp_format": result[2] or "ISO8601",
                    "sampling_interval_seconds": result[3],
                    "allow_interpolation": result[4],
                    "interpolation_method": result[5]
                }
            return None

    def update_table_alignment_config(
        self,
        table_name: str,
        config_dict: Dict
    ):
        """
        更新表的对齐配置

        Args:
            table_name: 表名
            config_dict: 配置字典
        """
        with self.connection.cursor() as cur:
            update_sql = """
            UPDATE "Data attribute dictionary" tad
            SET
                time_alignment_strategy = %s,
                default_timezone = %s,
                timestamp_format = %s,
                sampling_interval_seconds = %s,
                allow_interpolation = %s,
                interpolation_method = %s
            FROM "Dataset dictionary" dd
            WHERE tad.dataset_id = dd.dataset_id AND dd.table_name = %s;
            """
            cur.execute(update_sql, (
                config_dict.get("time_alignment_strategy"),
                config_dict.get("default_timezone", "UTC"),
                config_dict.get("timestamp_format", "ISO8601"),
                config_dict.get("sampling_interval_seconds"),
                config_dict.get("allow_interpolation", True),
                config_dict.get("interpolation_method", "LINEAR"),
                table_name
            ))
            self.connection.commit()
            logger.info(f"表 {table_name} 的对齐配置已更新")

    def read_raw_data(
        self,
        table_name: str,
        timestamp_column: str = "timestamp",
        value_columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Tuple[List[datetime], Dict[str, List[float]]]:
        """
        从物理表中读取原始数据

        Args:
            table_name: 表名
            timestamp_column: 时间戳列名
            value_columns: 值列名列表
            limit: 限制读取行数

        Returns:
            Tuple[List[datetime], Dict[str, List[float]]]: (时间戳列表, 值字典)
        """
        with self.connection.cursor() as cur:
            # 如果没有指定列名，自动推断
            if value_columns is None:
                # 查询所有列名，排除时间戳列
                columns_query = sql.SQL("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name != %s
                    ORDER BY ordinal_position;
                """)
                cur.execute(columns_query, (table_name, timestamp_column))
                value_columns = [row[0] for row in cur.fetchall()]

            if not value_columns:
                raise ValueError(f"表 {table_name} 没有找到值列")

            # 构建查询
            select_columns = sql.SQL(", ").join([
                sql.Identifier(timestamp_column)
            ] + [sql.Identifier(col) for col in value_columns])

            query = sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
                select_columns,
                sql.Identifier(table_name),
                sql.Identifier(timestamp_column)
            )

            if limit:
                query = sql.SQL("{} LIMIT %s").format(query)
                cur.execute(query, (limit,))
            else:
                cur.execute(query)

            # 提取数据
            timestamps = []
            values_dict = {col: [] for col in value_columns}

            for row in cur.fetchall():
                timestamps.append(row[0])
                for i, col in enumerate(value_columns, start=1):
                    values_dict[col].append(row[i] if row[i] is not None else float('nan'))

            logger.info(f"从表 {table_name} 读取了 {len(timestamps)} 条记录")

            return timestamps, values_dict

    def write_aligned_data(
        self,
        table_name: str,
        timestamps: List[datetime],
        values_dict: Dict[str, List[float]],
        batch_id: str
    ):
        """
        写入对齐后的数据（创建新表或插入到表）

        Args:
            table_name: 表名
            timestamps: 对齐后的时间戳
            values_dict: 对齐后的值字典
            batch_id: 批次ID
        """
        with self.connection.cursor() as cur:
            # 创建对齐后的表（如果不存在）
            aligned_table_name = f"{table_name}_aligned"

            # 检查表是否存在
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            """, (aligned_table_name,))

            table_exists = cur.fetchone()[0]

            if not table_exists:
                # 创建表结构（复制原表结构）
                create_sql = sql.SQL("""
                    CREATE TABLE {} AS
                    SELECT * FROM {} WHERE 1=0;
                """).format(
                    sql.Identifier(aligned_table_name),
                    sql.Identifier(table_name)
                )
                cur.execute(create_sql)

                # 添加批次ID列
                alter_sql = sql.SQL("""
                    ALTER TABLE {} ADD COLUMN IF NOT EXISTS batch_id VARCHAR(100);
                    ALTER TABLE {} ADD COLUMN IF NOT EXISTS is_interpolated BOOLEAN DEFAULT false;
                """).format(
                    sql.Identifier(aligned_table_name),
                    sql.Identifier(aligned_table_name)
                )
                cur.execute(alter_sql)

                logger.info(f"创建对齐表: {aligned_table_name}")

            # 批量插入数据
            value_columns = list(values_dict.keys())
            insert_columns = ["timestamp"] + value_columns + ["batch_id", "is_interpolated"]

            for i, ts in enumerate(timestamps):
                values = [ts]
                for col in value_columns:
                    val = values_dict[col][i]
                    # 检查是否为 NaN（插值产生的缺失值）
                    if val is None or (isinstance(val, float) and val != val):  # NaN check
                        values.append(None)
                    else:
                        values.append(val)

                # 添加批次ID和插值标记（这里简化处理，实际应从 AlignmentResult 获取）
                values.append(batch_id)
                values.append(False)

                insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(aligned_table_name),
                    sql.SQL(", ").join([sql.Identifier(col) for col in insert_columns]),
                    sql.SQL(", ").join([sql.Placeholder()] * len(insert_columns))
                )
                cur.execute(insert_sql, values)

            self.connection.commit()
            logger.info(f"向表 {aligned_table_name} 写入 {len(timestamps)} 条对齐记录")

    def log_alignment_details(
        self,
        table_name: str,
        batch_id: str,
        result: AlignmentResult,
        source_timestamps: List[datetime]
    ):
        """
        记录详细的对齐日志

        Args:
            table_name: 表名
            batch_id: 批次ID
            result: 对齐结果
            source_timestamps: 原始时间戳
        """
        with self.connection.cursor() as cur:
            insert_sql = """
            INSERT INTO time_alignment_log
            (table_name, batch_id, source_timestamp, aligned_timestamp,
             alignment_method, is_interpolated)
            VALUES (%s, %s, %s, %s, %s, %s);
            """

            data = []
            for i, aligned_ts in enumerate(result.aligned_timestamps):
                val = result.aligned_values[i]
                is_interpolated = False

                # 简单判断：如果值在原始时间戳中不存在，则认为是插值的
                # 注意：这里简化处理，实际应该更精确
                if val is None:
                    is_interpolated = True

                data.append((
                    table_name,
                    batch_id,
                    source_timestamps[i] if i < len(source_timestamps) else None,
                    aligned_ts,
                    result.alignment_method,
                    is_interpolated
                ))

            execute_batch(cur, insert_sql, data, page_size=100)
            self.connection.commit()

            logger.info(f"记录了 {len(data)} 条对齐日志")

    def log_batch_summary(
        self,
        table_name: str,
        batch_id: str,
        start_time: datetime,
        end_time: datetime,
        original_count: int,
        aligned_count: int,
        result: AlignmentResult
    ):
        """
        记录批次摘要

        Args:
            table_name: 表名
            batch_id: 批次ID
            start_time: 开始时间
            end_time: 结束时间
            original_count: 原始记录数
            aligned_count: 对齐记录数
            result: 对齐结果
        """
        with self.connection.cursor() as cur:
            insert_sql = """
            INSERT INTO time_alignment_batch_summary
            (batch_id, table_name, start_time, end_time, original_record_count,
             aligned_record_count, interpolated_count, missing_count, alignment_config)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            config_json = {
                "target_frequency": self.alignment_config.target_frequency,
                "default_interpolation": self.alignment_config.default_interpolation.value,
                "max_gap_seconds": self.alignment_config.max_gap_seconds
            }

            cur.execute(insert_sql, (
                batch_id,
                table_name,
                start_time,
                end_time,
                original_count,
                aligned_count,
                result.interpolated_count,
                result.missing_count,
                config_json
            ))
            self.connection.commit()

            logger.info(f"记录批次摘要: {batch_id}")

    def align_table_data(
        self,
        table_name: str,
        timestamp_column: str = "timestamp",
        value_columns: Optional[List[str]] = None,
        batch_id: Optional[str] = None
    ) -> Dict[str, AlignmentResult]:
        """
        对齐表中的所有数据（支持多列）

        Args:
            table_name: 表名
            timestamp_column: 时间戳列名
            value_columns: 值列名列表
            batch_id: 批次ID

        Returns:
            Dict[str, AlignmentResult]: 每列的对齐结果
        """
        if batch_id is None:
            batch_id = f"{table_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"开始对齐表 {table_name}，批次ID: {batch_id}")

        # 读取原始数据
        timestamps, values_dict = self.read_raw_data(
            table_name,
            timestamp_column,
            value_columns
        )

        if not timestamps:
            logger.warning(f"表 {table_name} 没有数据")
            return {}

        # 获取表的对齐配置
        table_config = self.get_table_alignment_config(table_name)

        # 应用表特定的配置
        if table_config:
            logger.info(f"应用表 {table_name} 的特定配置")
            # 这里可以根据配置调整 alignment_config

        results = {}
        aligned_values_dict = {}

        # 对每列进行对齐
        for col_name, values in values_dict.items():
            logger.info(f"对齐列: {col_name}")

            # 过滤掉 NaN 值进行对齐
            valid_indices = [i for i, v in enumerate(values)
                           if v is not None and not (isinstance(v, float) and v != v)]
            valid_timestamps = [timestamps[i] for i in valid_indices]
            valid_values = [values[i] for i in valid_indices]

            if not valid_timestamps:
                logger.warning(f"列 {col_name} 没有有效数据")
                continue

            # 执行对齐
            result = self.tsat.align_time_series(
                valid_timestamps,
                valid_values,
                table_name=f"{table_name}.{col_name}"
            )

            results[col_name] = result
            aligned_values_dict[col_name] = result.aligned_values

            # 记录对齐日志
            # self.log_alignment_details(table_name, batch_id, result, valid_timestamps)

        # 写入对齐后的数据
        if aligned_values_dict:
            # 获取第一个结果的时间戳作为统一时间轴
            first_result = next(iter(results.values()))
            self.write_aligned_data(
                table_name,
                first_result.aligned_timestamps,
                aligned_values_dict,
                batch_id
            )

            # 记录批次摘要
            self.log_batch_summary(
                table_name,
                batch_id,
                min(timestamps),
                max(timestamps),
                len(timestamps),
                len(first_result.aligned_timestamps),
                first_result
            )

        logger.info(f"表 {table_name} 对齐完成")
        return results


def demo_database_integration():
    """演示数据库集成功能"""
    print("=" * 60)
    print("GenBFKit PostgreSQL 集成演示")
    print("=" * 60)

    # 配置
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="genbfkit",
        user="postgres",
        password="your_password"
    )

    alignment_config = TimeAlignmentConfig(
        target_frequency="5S",
        default_interpolation=InterpolationMethod.LINEAR
    )

    # 创建管理器
    with PostgreSQLAlignmentManager(db_config, alignment_config) as manager:
        # 初始化元数据表
        print("\n【步骤1: 初始化元数据表】")
        manager.setup_metadata_tables()
        print("✓ 元数据表初始化完成")

        # 查看现有表
        print("\n【步骤2: 查看可用的物理表】")
        with manager.connection.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%_aligned' = false
                ORDER BY table_name
                LIMIT 10;
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"找到 {len(tables)} 个物理表")
            for table in tables[:5]:
                print(f"  - {table}")

        # 对齐表数据（这里只是示例，实际需要真实数据）
        if tables:
            print(f"\n【步骤3: 对齐表数据】")
            print(f"（演示模式，不对齐实际数据）")
            # results = manager.align_table_data(tables[0])
            # print(f"对齐结果: {results}")
        else:
            print("\n【步骤3: 跳过数据对齐（没有物理表）】")

    print("\n演示完成！")


if __name__ == "__main__":
    # 注意：运行前需要确保 PostgreSQL 数据库已配置
    print("提示: 运行前请先配置数据库连接信息")
    # demo_database_integration()
