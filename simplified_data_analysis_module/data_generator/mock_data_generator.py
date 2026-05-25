"""
虚拟数据生成器 🎲
生成模拟的高炉运行数据，用于功能验证
"""

import numpy as np
import pandas as pd
import os
from typing import Optional


class MockDataGenerator:
    """
    模拟数据生成器类
    生成高炉工况的模拟数据，包含多种参数和相关性关系
    """

    def __init__(self, n_samples: int = 1000, random_state: int = 42):
        """
        初始化数据生成器
        
        Args:
            n_samples: 生成样本数量
            random_state: 随机种子
        """
        self.n_samples = n_samples
        self.random_state = random_state
        np.random.seed(random_state)

    def generate_blast_furnace_data(self) -> pd.DataFrame:
        """
        生成高炉工况模拟数据
        
        Returns:
            包含多个高炉参数的DataFrame
        """
        print("🎲 开始生成高炉工况模拟数据...")
        print(f"   样本数量: {self.n_samples}")
        
        data = {}
        
        # 1. 温度相关参数（高度正相关）
        base_temp = np.random.normal(1500, 50, self.n_samples)
        data['风温'] = base_temp
        data['炉顶温度'] = base_temp * 0.7 + np.random.normal(200, 30, self.n_samples)
        data['热风温度'] = base_temp * 0.9 + np.random.normal(100, 20, self.n_samples)
        
        # 2. 压力相关参数
        base_pressure = np.random.normal(0.35, 0.05, self.n_samples)
        data['热风压力'] = base_pressure
        data['炉顶压力'] = base_pressure * 0.8 + np.random.normal(0.05, 0.01, self.n_samples)
        data['冷风压力'] = base_pressure * 0.6 + np.random.normal(0.03, 0.01, self.n_samples)
        
        # 3. 流量相关参数
        base_flow = np.random.normal(5000, 500, self.n_samples)
        data['风量'] = base_flow
        data['富氧流量'] = base_flow * 0.1 + np.random.normal(500, 100, self.n_samples)
        data['喷煤量'] = base_flow * 0.15 + np.random.normal(750, 150, self.n_samples)
        
        # 4. 成分相关参数
        data['CO含量'] = np.random.normal(25, 3, self.n_samples)
        data['CO2含量'] = np.random.normal(18, 2, self.n_samples)
        data['H2含量'] = np.random.normal(3, 0.5, self.n_samples)
        
        # 5. 装料相关参数
        data['焦比'] = np.random.normal(350, 30, self.n_samples)
        data['煤比'] = np.random.normal(150, 20, self.n_samples)
        data['矿焦比'] = data['焦比'] / data['煤比'] * 0.5 + np.random.normal(0.1, 0.02, self.n_samples)
        
        # 6. 目标变量（铁水温度）
        # 目标变量与多个特征相关
        data['铁水温度'] = (
            0.3 * data['风温'] +
            0.2 * data['热风温度'] +
            0.15 * data['热风压力'] * 100 +
            0.1 * data['风量'] / 100 +
            0.05 * data['焦比'] +
            0.05 * data['煤比'] +
            0.1 * data['CO含量'] * 5 +
            np.random.normal(1450, 30, self.n_samples)
        )
        
        df = pd.DataFrame(data)
        print(f"✅ 数据生成完成，共 {len(data)} 个参数")
        
        return df

    def generate_synthetic_data_with_patterns(self) -> pd.DataFrame:
        """
        生成具有特定模式的数据（用于测试统计指标）
        
        Returns:
            包含不同分布特征的DataFrame
        """
        print("🎲 生成具有特定模式的测试数据...")
        
        data = {}
        
        # 1. 正态分布（偏度≈0，峰度≈0）
        data['正态分布参数'] = np.random.normal(100, 10, self.n_samples)
        
        # 2. 右偏分布（偏度>0）
        data['右偏分布参数'] = np.random.exponential(50, self.n_samples)
        
        # 3. 左偏分布（偏度<0）
        data['左偏分布参数'] = -np.random.exponential(50, self.n_samples) + 100
        
        # 4. 尖峰分布（峰度>0）
        data['尖峰分布参数'] = np.random.normal(100, 5, self.n_samples)
        
        # 5. 平峰分布（峰度<0）
        data['平峰分布参数'] = np.random.uniform(80, 120, self.n_samples)
        
        # 6. 高变异参数
        data['高变异参数'] = np.random.normal(100, 50, self.n_samples)
        
        # 7. 低变异参数
        data['低变异参数'] = np.random.normal(100, 2, self.n_samples)
        
        # 8. 周期性参数
        t = np.linspace(0, 4 * np.pi, self.n_samples)
        data['周期性参数'] = 100 + 20 * np.sin(t) + np.random.normal(0, 5, self.n_samples)
        
        # 9. 趋势性参数
        data['趋势性参数'] = 100 + 0.1 * np.arange(self.n_samples) + np.random.normal(0, 10, self.n_samples)
        
        # 10. 目标变量
        data['目标变量'] = (
            0.2 * data['正态分布参数'] +
            0.15 * data['右偏分布参数'] +
            0.15 * data['周期性参数'] +
            0.1 * data['趋势性参数'] +
            0.4 * np.random.normal(100, 10, self.n_samples)
        )
        
        df = pd.DataFrame(data)
        print(f"✅ 测试数据生成完成，共 {len(data)} 个参数")
        
        return df

    def generate_simple_test_data(self, n_features: int = 10) -> pd.DataFrame:
        """
        生成简单的测试数据
        
        Args:
            n_features: 特征数量
        
        Returns:
            包含n_features个特征的DataFrame
        """
        print(f"🎲 生成简单测试数据（{n_features}个特征）...")
        
        data = {}
        
        # 生成特征
        for i in range(n_features):
            # 随机选择分布类型
            dist_type = np.random.choice(['normal', 'uniform', 'exponential'])
            
            if dist_type == 'normal':
                data[f'特征_{i+1}'] = np.random.normal(
                    loc=np.random.uniform(50, 150),
                    scale=np.random.uniform(5, 20),
                    size=self.n_samples
                )
            elif dist_type == 'uniform':
                data[f'特征_{i+1}'] = np.random.uniform(
                    low=np.random.uniform(50, 100),
                    high=np.random.uniform(100, 150),
                    size=self.n_samples
                )
            else:  # exponential
                data[f'特征_{i+1}'] = np.random.exponential(
                    scale=np.random.uniform(10, 30),
                    size=self.n_samples
                )
        
        # 生成目标变量（与部分特征相关）
        selected_features = np.random.choice(n_features, size=int(n_features * 0.6), replace=False)
        data['目标变量'] = 50
        
        for idx in selected_features:
            coeff = np.random.uniform(0.1, 0.5)
            data['目标变量'] += coeff * data[f'特征_{idx+1}']
        
        data['目标变量'] += np.random.normal(0, 10, self.n_samples)
        
        df = pd.DataFrame(data)
        print(f"✅ 简单测试数据生成完成")
        
        return df

    def save_to_excel(self, df: pd.DataFrame, filename: str = "mock_data.xlsx"):
        """
        保存数据到Excel文件
        
        Args:
            df: 要保存的DataFrame
            filename: 文件名
        """
        output_path = os.path.join(os.path.dirname(__file__), filename)
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"✅ 数据已保存至: {output_path}")
        
        return output_path


def main():
    """
    主函数：生成并保存测试数据
    """
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'mock_data')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成高炉工况数据
    print("\n" + "=" * 60)
    print("生成高炉工况模拟数据")
    print("=" * 60)
    generator = MockDataGenerator(n_samples=1000, random_state=42)
    bf_data = generator.generate_blast_furnace_data()
    bf_path = os.path.join(output_dir, 'blast_furnace_mock_data.xlsx')
    bf_data.to_excel(bf_path, index=False, engine='openpyxl')
    print(f"\n✅ 高炉工况数据已保存至: {bf_path}")
    print(f"   数据形状: {bf_data.shape}")
    print(f"   参数列表: {list(bf_data.columns)}")
    
    # 生成特定模式数据
    print("\n" + "=" * 60)
    print("生成特定模式测试数据")
    print("=" * 60)
    pattern_data = generator.generate_synthetic_data_with_patterns()
    pattern_path = os.path.join(output_dir, 'pattern_test_data.xlsx')
    pattern_data.to_excel(pattern_path, index=False, engine='openpyxl')
    print(f"\n✅ 特定模式数据已保存至: {pattern_path}")
    print(f"   数据形状: {pattern_data.shape}")
    print(f"   参数列表: {list(pattern_data.columns)}")
    
    # 生成简单测试数据
    print("\n" + "=" * 60)
    print("生成简单测试数据")
    print("=" * 60)
    simple_data = generator.generate_simple_test_data(n_features=15)
    simple_path = os.path.join(output_dir, 'simple_test_data.xlsx')
    simple_data.to_excel(simple_path, index=False, engine='openpyxl')
    print(f"\n✅ 简单测试数据已保存至: {simple_path}")
    print(f"   数据形状: {simple_data.shape}")
    print(f"   参数列表: {list(simple_data.columns)}")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试数据生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
