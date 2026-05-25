"""
GenBFKit 时间尺度对齐模板 (Time Scale Alignment Template, TSAT)
核心模块：提供时间戳标准化、时间轴对齐、插值算法等功能
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import interpolate
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TimestampFormat(Enum):
    """时间戳格式枚举"""
    ISO8601 = "ISO8601"
    UNIX_SECONDS = "UNIX_SECONDS"
    UNIX_MILLISECONDS = "UNIX_MILLISECONDS"
    DATABASE_DATETIME = "DATABASE_DATETIME"
    UNKNOWN = "UNKNOWN"


class InterpolationMethod(Enum):
    """插值方法枚举"""
    LINEAR = "LINEAR"
    CUBIC_SPLINE = "CUBIC_SPLINE"
    FORWARD_FILL = "FORWARD_FILL"
    BACKWARD_FILL = "BACKWARD_FILL"
    NEAREST = "NEAREST"


@dataclass
class TimeAlignmentConfig:
    """时间对齐配置"""
    target_timezone: str = "UTC"
    target_frequency: str = "1S"  # 默认1秒采样
    default_interpolation: InterpolationMethod = InterpolationMethod.LINEAR
    max_gap_seconds: int = 300  # 最大允许的插值间隔（秒）
    enable_outlier_detection: bool = True  # 是否启用异常值检测
    outlier_threshold_sigma: float = 3.0  # 异常值检测阈值（σ倍数）


@dataclass
class AlignmentResult:
    """对齐结果"""
    aligned_timestamps: List[datetime]
    aligned_values: List[Optional[float]]
    original_timestamps: List[datetime]
    alignment_method: str
    missing_count: int
    interpolated_count: int
    outlier_count: int = 0  # 异常值数量
    outlier_indices: List[int] = None  # 异常值索引

    def __post_init__(self):
        if self.outlier_indices is None:
            self.outlier_indices = []


class TimestampNormalizer:
    """时间戳标准化器"""

    # ISO8601 正则表达式
    ISO8601_PATTERN = re.compile(
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
    )

    @staticmethod
    def detect_format(raw_ts: Union[str, int, float]) -> TimestampFormat:
        """
        自动检测时间戳格式

        Args:
            raw_ts: 原始时间戳

        Returns:
            TimestampFormat: 检测到的格式
        """
        if isinstance(raw_ts, (int, float)):
            # 判断是秒还是毫秒
            if raw_ts > 1e12:  # 毫秒时间戳
                return TimestampFormat.UNIX_MILLISECONDS
            else:  # 秒时间戳
                return TimestampFormat.UNIX_SECONDS

        elif isinstance(raw_ts, str):
            # 检查 ISO8601 格式
            if TimestampNormalizer.ISO8601_PATTERN.match(raw_ts):
                return TimestampFormat.ISO8601

            # 检查数据库日期时间格式
            if 'T' in raw_ts or ' ' in raw_ts:
                return TimestampFormat.DATABASE_DATETIME

        return TimestampFormat.UNKNOWN

    @staticmethod
    def normalize(
        raw_ts: Union[str, int, float],
        format_hint: Optional[TimestampFormat] = None,
        default_timezone: str = "UTC"
    ) -> datetime:
        """
        将时间戳标准化为 UTC datetime 对象

        Args:
            raw_ts: 原始时间戳
            format_hint: 格式提示（可选）
            default_timezone: 默认时区

        Returns:
            datetime: 标准化后的 UTC datetime
        """
        try:
            # 检测格式
            ts_format = format_hint or TimestampNormalizer.detect_format(raw_ts)

            if ts_format == TimestampFormat.UNIX_SECONDS:
                dt = datetime.fromtimestamp(float(raw_ts), tz=timezone.utc)

            elif ts_format == TimestampFormat.UNIX_MILLISECONDS:
                dt = datetime.fromtimestamp(float(raw_ts) / 1000, tz=timezone.utc)

            elif ts_format == TimestampFormat.ISO8601:
                dt = datetime.fromisoformat(raw_ts.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(default_timezone))
                dt = dt.astimezone(timezone.utc)

            elif ts_format == TimestampFormat.DATABASE_DATETIME:
                # 尝试常见格式
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                           '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        dt = datetime.strptime(raw_ts, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=ZoneInfo(default_timezone))
                        dt = dt.astimezone(timezone.utc)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"无法解析时间戳: {raw_ts}")

            else:
                raise ValueError(f"未知的时间戳格式: {raw_ts}")

            return dt

        except Exception as e:
            logger.error(f"时间戳标准化失败: {raw_ts}, 错误: {e}")
            raise ValueError(f"时间戳标准化失败: {e}")


class TimeAxisAligner:
    """时间轴对齐器"""

    @staticmethod
    def generate_target_timeline(
        start_time: datetime,
        end_time: datetime,
        frequency: str
    ) -> List[datetime]:
        """
        生成目标时间轴

        Args:
            start_time: 开始时间
            end_time: 结束时间
            frequency: 频率（如 '1s', '5s', '1min', '1h'）

        Returns:
            List[datetime]: 目标时间戳列表
        """
        # 转换为大写的频率参数到小写（pandas 新版本要求）
        freq_map = {
            '1S': '1s',
            '5S': '5s',
            '1M': '1min',
            '1H': '1h'
        }
        freq = freq_map.get(frequency, frequency.lower())

        timeline = pd.date_range(
            start=start_time,
            end=end_time,
            freq=freq
        ).to_pydatetime().tolist()

        return timeline

    @staticmethod
    def find_nearest_timestamp(
        target_ts: datetime,
        timeline: List[datetime]
    ) -> int:
        """
        使用二分查找找到时间轴上最近的索引

        Args:
            target_ts: 目标时间戳
            timeline: 时间轴列表

        Returns:
            int: 最近的时间戳索引
        """
        import bisect
        idx = bisect.bisect_left(timeline, target_ts)

        if idx == 0:
            return 0
        elif idx == len(timeline):
            return len(timeline) - 1
        else:
            # 比较前后哪个更近
            before = timeline[idx - 1]
            after = timeline[idx]
            if abs((target_ts - before).total_seconds()) < abs((target_ts - after).total_seconds()):
                return idx - 1
            else:
                return idx


class AdaptiveInterpolator:
    """自适应插值器"""

    @staticmethod
    def linear_interpolation(
        x_known: List[float],
        y_known: List[float],
        x_target: float
    ) -> Optional[float]:
        """
        线性插值

        Args:
            x_known: 已知时间戳（Unix时间戳）
            y_known: 已知值
            x_target: 目标时间戳（Unix时间戳）

        Returns:
            Optional[float]: 插值结果，若无法插值返回None
        """
        if len(x_known) < 2:
            return None

        try:
            # 使用 scipy 的线性插值
            f = interpolate.interp1d(x_known, y_known, kind='linear', fill_value='extrapolate')
            return float(f(x_target))
        except Exception as e:
            logger.warning(f"线性插值失败: {e}")
            return None

    @staticmethod
    def cubic_spline_interpolation(
        x_known: List[float],
        y_known: List[float],
        x_target: float
    ) -> Optional[float]:
        """
        三次样条插值

        Args:
            x_known: 已知时间戳（Unix时间戳）
            y_known: 已知值
            x_target: 目标时间戳（Unix时间戳）

        Returns:
            Optional[float]: 插值结果
        """
        if len(x_known) < 4:
            # 数据点不足，回退到线性插值
            return AdaptiveInterpolator.linear_interpolation(x_known, y_known, x_target)

        try:
            # 使用三次样条插值
            from scipy.interpolate import CubicSpline
            cs = CubicSpline(x_known, y_known)
            return float(cs(x_target))
        except Exception as e:
            logger.warning(f"三次样条插值失败，回退到线性插值: {e}")
            return AdaptiveInterpolator.linear_interpolation(x_known, y_known, x_target)

    @staticmethod
    def nearest_interpolation(
        x_known: List[float],
        y_known: List[float],
        x_target: float
    ) -> Optional[float]:
        """
        最近邻插值

        Args:
            x_known: 已知时间戳
            y_known: 已知值
            x_target: 目标时间戳

        Returns:
            Optional[float]: 最近邻的值
        """
        if not x_known:
            return None

        # 找到最近的时间戳
        idx = TimeAxisAligner.find_nearest_timestamp(
            datetime.fromtimestamp(x_target, tz=timezone.utc),
            [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in x_known]
        )
        return y_known[idx]

    @staticmethod
    def interpolate(
        timestamps: List[datetime],
        values: List[float],
        target_timestamp: datetime,
        method: InterpolationMethod = InterpolationMethod.LINEAR,
        max_gap_seconds: int = 300
    ) -> Tuple[Optional[float], str]:
        """
        执行插值

        Args:
            timestamps: 原始时间戳列表
            values: 原始值列表
            target_timestamp: 目标时间戳
            method: 插值方法
            max_gap_seconds: 最大允许间隔（秒）

        Returns:
            Tuple[Optional[float], str]: (插值结果, 状态描述)
        """
        if not timestamps or not values:
            return None, "NO_DATA"

        # 转换为 Unix 时间戳
        target_ts = target_timestamp.timestamp()
        x_known = [ts.timestamp() for ts in timestamps]

        # 检查是否已存在目标时间戳
        if target_ts in x_known:
            idx = x_known.index(target_ts)
            return values[idx], "EXACT_MATCH"

        # 找到目标时间戳前后的数据点
        import bisect
        idx = bisect.bisect_left(x_known, target_ts)

        if idx == 0:
            # 目标时间在所有数据点之前
            return None, "BEFORE_FIRST"

        elif idx == len(x_known):
            # 目标时间在所有数据点之后
            return None, "AFTER_LAST"

        else:
            # 检查间隔是否过大
            gap = x_known[idx] - x_known[idx - 1]
            if gap > max_gap_seconds:
                return None, f"GAP_TOO_LARGE ({gap:.1f}s > {max_gap_seconds}s)"

            # 根据方法执行插值
            if method == InterpolationMethod.LINEAR:
                result = AdaptiveInterpolator.linear_interpolation(
                    x_known, values, target_ts
                )
                return result, "LINEAR_INTERPOLATED"

            elif method == InterpolationMethod.CUBIC_SPLINE:
                # 取前后各2个数据点
                start_idx = max(0, idx - 2)
                end_idx = min(len(x_known), idx + 2)
                result = AdaptiveInterpolator.cubic_spline_interpolation(
                    x_known[start_idx:end_idx],
                    values[start_idx:end_idx],
                    target_ts
                )
                return result, "SPLINE_INTERPOLATED"

            elif method == InterpolationMethod.NEAREST:
                result = AdaptiveInterpolator.nearest_interpolation(
                    x_known, values, target_ts
                )
                return result, "NEAREST_NEIGHBOR"

            else:
                return None, f"UNSUPPORTED_METHOD: {method}"

    @staticmethod
    def detect_outliers(
        values: List[Optional[float]],
        threshold_sigma: float = 3.0
    ) -> Tuple[List[int], float, float]:
        """
        检测异常值（基于3σ原则）

        Args:
            values: 值列表
            threshold_sigma: 阈值倍数

        Returns:
            Tuple[List[int], float, float]: (异常值索引列表, 均值, 标准差)
        """
        # 过滤掉 None 值
        valid_values = [v for v in values if v is not None]

        if len(valid_values) < 3:
            # 数据点太少，无法计算统计量
            return [], 0.0, 0.0

        # 计算均值和标准差
        mean_val = float(np.mean(valid_values))
        std_val = float(np.std(valid_values))

        # 检测异常值
        outlier_indices = []
        for i, v in enumerate(values):
            if v is not None:
                if abs(v - mean_val) > threshold_sigma * std_val:
                    outlier_indices.append(i)

        return outlier_indices, mean_val, std_val


class MultiSourceTimeSynchronizer:
    """多源时间同步器"""

    @staticmethod
    def calculate_time_offset(
        reference_timestamps: List[datetime],
        source_timestamps: List[datetime],
        max_samples: int = 1000
    ) -> Tuple[float, float]:
        """
        计算时间偏移量（使用互相关）

        Args:
            reference_timestamps: 基准时间戳
            source_timestamps: 源时间戳
            max_samples: 最大采样数

        Returns:
            Tuple[float, float]: (时间偏移秒数, 相关系数R²)
        """
        if len(reference_timestamps) < 10 or len(source_timestamps) < 10:
            return 0.0, 0.0

        # 转换为秒数
        ref_ts = np.array([ts.timestamp() for ts in reference_timestamps[:max_samples]])
        src_ts = np.array([ts.timestamp() for ts in source_timestamps[:max_samples]])

        # 计算互相关
        correlation = np.correlate(
            (ref_ts - np.mean(ref_ts)) / np.std(ref_ts),
            (src_ts - np.mean(src_ts)) / np.std(src_ts),
            mode='full'
        )

        # 找到峰值位置
        peak_idx = np.argmax(correlation)
        offset = peak_idx - (len(src_ts) - 1)

        # 计算R²
        if len(ref_ts) == len(src_ts):
            r_squared = np.corrcoef(ref_ts, src_ts)[0, 1] ** 2
        else:
            r_squared = 0.0

        return float(offset), float(r_squared)



class TimeScaleAlignmentTemplate:
    """时间尺度对齐模板主类"""

    def __init__(self, config: TimeAlignmentConfig):
        """
        初始化时间尺度对齐模板

        Args:
            config: 对齐配置
        """
        self.config = config
        self.normalizer = TimestampNormalizer()
        self.aligner = TimeAxisAligner()
        self.interpolator = AdaptiveInterpolator()
        self.synchronizer = MultiSourceTimeSynchronizer()

        logger.info(f"时间尺度对齐模板初始化完成，目标频率: {config.target_frequency}")

    def normalize_timestamps(
        self,
        raw_timestamps: List[Union[str, int, float]],
        format_hint: Optional[TimestampFormat] = None
    ) -> List[datetime]:
        """
        批量标准化时间戳

        Args:
            raw_timestamps: 原始时间戳列表
            format_hint: 格式提示

        Returns:
            List[datetime]: 标准化后的时间戳列表
        """
        normalized = []
        failed_count = 0

        for raw_ts in raw_timestamps:
            try:
                normalized_ts = self.normalizer.normalize(
                    raw_ts,
                    format_hint,
                    self.config.target_timezone
                )
                normalized.append(normalized_ts)
            except Exception as e:
                logger.error(f"时间戳标准化失败: {raw_ts}, 错误: {e}")
                failed_count += 1

        if failed_count > 0:
            logger.warning(f"有 {failed_count} 个时间戳标准化失败")

        return normalized

    def align_time_series(
        self,
        timestamps: List[datetime],
        values: List[float],
        table_name: str = "unknown"
    ) -> AlignmentResult:
        """
        对齐时间序列

        Args:
            timestamps: 原始时间戳列表（已标准化）
            values: 原始值列表
            table_name: 表名（用于日志）

        Returns:
            AlignmentResult: 对齐结果
        """
        if len(timestamps) != len(values):
            raise ValueError("时间戳和值的数量不一致")

        if not timestamps:
            return AlignmentResult(
                aligned_timestamps=[],
                aligned_values=[],
                original_timestamps=[],
                alignment_method="NONE",
                missing_count=0,
                interpolated_count=0
            )

        logger.info(f"开始对齐表 {table_name} 的时间序列，原始数据点数: {len(timestamps)}")

        # 确定时间范围
        start_time = min(timestamps)
        end_time = max(timestamps)

        # 生成目标时间轴
        target_timeline = self.aligner.generate_target_timeline(
            start_time,
            end_time,
            self.config.target_frequency
        )

        logger.info(f"目标时间轴生成完成，时间点数: {len(target_timeline)}")

        # 对每个目标时间点进行插值
        aligned_values = []
        interpolated_count = 0
        missing_count = 0

        for target_ts in target_timeline:
            value, status = self.interpolator.interpolate(
                timestamps,
                values,
                target_ts,
                self.config.default_interpolation,
                self.config.max_gap_seconds
            )

            if value is not None:
                aligned_values.append(value)
                if "INTERPOLATED" in status:
                    interpolated_count += 1
            else:
                aligned_values.append(None)
                missing_count += 1

        logger.info(
            f"表 {table_name} 对齐完成: "
            f"插值={interpolated_count}, "
            f"缺失={missing_count}"
        )

        # 异常检测
        outlier_count = 0
        outlier_indices = []

        if self.config.enable_outlier_detection:
            outlier_indices, mean_val, std_val = AdaptiveInterpolator.detect_outliers(
                aligned_values,
                self.config.outlier_threshold_sigma
            )
            outlier_count = len(outlier_indices)

            if outlier_count > 0:
                logger.warning(
                    f"表 {table_name} 检测到 {outlier_count} 个异常值 "
                    f"(均值={mean_val:.2f}, 标准差={std_val:.2f})"
                )

        return AlignmentResult(
            aligned_timestamps=target_timeline,
            aligned_values=aligned_values,
            original_timestamps=timestamps,
            alignment_method=self.config.default_interpolation.value,
            missing_count=missing_count,
            interpolated_count=interpolated_count,
            outlier_count=outlier_count,
            outlier_indices=outlier_indices
        )

    def synchronize_multiple_sources(
        self,
        sources: Dict[str, Tuple[List[datetime], List[float]]]
    ) -> Dict[str, float]:
        """
        同步多个数据源的时间

        Args:
            sources: 数据源字典 {source_name: (timestamps, values)}

        Returns:
            Dict[str, float]: 每个源的偏移量（秒）
        """
        if not sources:
            return {}

        # 选择基准源（选择数据量最大的）
        base_source_name = max(sources.keys(), key=lambda k: len(sources[k][0]))
        base_timestamps = sources[base_source_name][0]

        logger.info(f"选择 {base_source_name} 作为时间基准源")

        offsets = {}
        offsets[base_source_name] = 0.0

        for source_name, (timestamps, values) in sources.items():
            if source_name == base_source_name:
                continue

            offset, r_squared = self.synchronizer.calculate_time_offset(
                base_timestamps,
                timestamps
            )

            if r_squared < 0.8:
                logger.warning(
                    f"源 {source_name} 与基准的时间同步相关性较低 "
                    f"(R²={r_squared:.4f})，偏移量可能不准确"
                )

            offsets[source_name] = offset
            logger.info(
                f"源 {source_name} 时间偏移: {offset:.4f}秒 (R²={r_squared:.4f})"
            )

        return offsets


def demo():
    """演示函数"""
    print("=" * 60)
    print("GenBFKit 时间尺度对齐模板演示")
    print("=" * 60)

    # 创建配置
    config = TimeAlignmentConfig(
        target_frequency="5S",  # 5秒采样
        default_interpolation=InterpolationMethod.LINEAR,
        max_gap_seconds=60
    )

    # 创建模板实例
    tsat = TimeScaleAlignmentTemplate(config)

    # 演示1: 时间戳标准化
    print("\n【演示1: 时间戳标准化】")
    raw_timestamps = [
        "2024-01-01T10:00:00Z",
        "2024-01-01T10:00:05Z",
        1704108010,  # Unix时间戳
        "2024-01-01 10:00:20",  # 数据库格式
    ]

    normalized_ts = tsat.normalize_timestamps(raw_timestamps)
    print(f"原始时间戳: {raw_timestamps}")
    print(f"标准化后: {[ts.strftime('%Y-%m-%d %H:%M:%S UTC') for ts in normalized_ts]}")

    # 演示2: 时间序列对齐
    print("\n【演示2: 时间序列对齐】")

    # 重新生成确保成功的时间戳（用于演示2）
    demo_timestamps = [
        "2024-01-01T10:00:00Z",
        "2024-01-01T10:00:05Z",
        "2024-01-01T10:00:10Z",
        "2024-01-01T10:00:15Z"
    ]
    demo_values = [25.3, 25.5, 26.1, 26.8]

    normalized_demo = tsat.normalize_timestamps(demo_timestamps)

    result = tsat.align_time_series(
        normalized_demo,
        demo_values,
        table_name="temperature_sensor_01"
    )

    print(f"对齐结果:")
    print(f"  - 对齐时间点数: {len(result.aligned_timestamps)}")
    print(f"  - 插值数量: {result.interpolated_count}")
    print(f"  - 缺失数量: {result.missing_count}")
    print(f"\n前10个对齐结果:")
    for i, (ts, val) in enumerate(zip(result.aligned_timestamps[:10],
                                        result.aligned_values[:10])):
        print(f"  {ts.strftime('%H:%M:%S')}: {val}")

    # 演示3: 多源时间同步
    print("\n【演示3: 多源时间同步】")
    sources = {
        "source_a": (
            [datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc) +
             timedelta(seconds=i*5) for i in range(10)],
            [25.0 + i * 0.1 for i in range(10)]
        ),
        "source_b": (
            [datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc) +
             timedelta(seconds=2 + i*5) for i in range(10)],  # 有2秒偏移
            [25.5 + i * 0.1 for i in range(10)]
        )
    }

    offsets = tsat.synchronize_multiple_sources(sources)
    print(f"各源时间偏移量:")
    for source, offset in offsets.items():
        print(f"  - {source}: {offset:.4f}秒")

    print("\n演示完成！")


if __name__ == "__main__":
    demo()
