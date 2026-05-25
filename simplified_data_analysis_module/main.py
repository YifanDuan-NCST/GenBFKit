"""
主入口文件 - 快速开始使用GenBFKit简易数据分析模块 🚀
"""

import os
import sys
import pandas as pd

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from simplified_data_analysis_module.data_generator import MockDataGenerator
from simplified_data_analysis_module.statistical_analysis import StatisticalAnalyzer
from simplified_data_analysis_module.correlation_analysis import CorrelationAnalyzer
from simplified_data_analysis_module.shap_analysis import SHAPAnalyzer


def quick_start_demo():
    """
    快速开始演示
    使用模拟数据演示所有功能
    """
    print("=" * 70)
    print("🚀 GenBFKit 简易数据分析模块 - 快速开始演示")
    print("=" * 70)
    
    # 步骤1: 生成测试数据
    print("\n🎲 步骤1: 生成模拟数据...")
    generator = MockDataGenerator(n_samples=1000, random_state=42)
    data = generator.generate_blast_furnace_data()
    print(f"✅ 数据生成完成: {data.shape}")
    print(f"   参数列表: {list(data.columns)[:5]}...")
    
    # 步骤2: 统计指标分析
    print("\n📊 步骤2: 统计指标分析...")
    stat_analyzer = StatisticalAnalyzer(data)
    metrics = stat_analyzer.calculate_all_metrics()
    print(f"✅ 计算完成，共 {len(metrics)} 个参数")
    
    # 生成报告和图表
    stat_analyzer.generate_report('demo_statistical_report.txt')
    stat_analyzer.plot_metrics('demo_statistical_plots')
    stat_analyzer.export_metrics('demo_statistical_metrics.csv')
    print("✅ 报告、图表和CSV已生成")
    
    # 步骤3: 相关性分析
    print("\n🔗 步骤3: 相关性分析...")
    target_col = '铁水温度'
    X = data.drop(columns=[target_col])
    y = data[target_col]
    
    corr_analyzer = CorrelationAnalyzer(data, target_column=target_col)
    corr_analyzer.set_method('pearson')
    corr_analyzer.calculate_correlation()
    
    # 获取Top相关性
    top_corr = corr_analyzer.get_top_correlations(n=5)
    print("✅ 相关性最强的5对参数:")
    print(top_corr)
    
    # 绘制网络图
    corr_analyzer.plot_correlation_network('demo_correlation_network.pdf')
    corr_analyzer.export_correlation_matrix('demo_correlation_matrix.csv')
    print("✅ 网络图和相关性矩阵已生成")
    
    # 步骤4: SHAP分析（可选，计算时间较长）
    print("\n🎯 步骤4: SHAP分析（此步骤可能需要较长时间）...")
    print("   按Enter继续，或按Ctrl+C跳过...")
    try:
        input()
        
        # 减少样本数量以加快演示
        X_sample = X.sample(n=500, random_state=42)
        y_sample = y.loc[X_sample.index]
        
        shap_analyzer = SHAPAnalyzer(X_sample, y_sample, test_size=0.3, random_state=42)
        shap_analyzer.run_full_analysis()
        print("✅ SHAP分析完成")
    except KeyboardInterrupt:
        print("\n⏭️  已跳过SHAP分析")
    
    print("\n" + "=" * 70)
    print("🎉 演示完成！所有结果已保存到当前目录")
    print("=" * 70)


def analyze_custom_data(data_path: str, target_column: str):
    """
    分析自定义数据
    
    Args:
        data_path: 数据文件路径（Excel或CSV）
        target_column: 目标列名
    """
    print("=" * 70)
    print("🔍 分析自定义数据")
    print("=" * 70)
    
    # 加载数据
    print(f"\n📂 正在加载数据: {data_path}")
    if data_path.endswith('.xlsx') or data_path.endswith('.xls'):
        data = pd.read_excel(data_path, engine='openpyxl')
    elif data_path.endswith('.csv'):
        data = pd.read_csv(data_path)
    else:
        raise ValueError("不支持的数据格式，请使用Excel或CSV文件")
    
    print(f"✅ 数据加载完成: {data.shape}")
    
    # 检查目标列
    if target_column not in data.columns:
        raise ValueError(f"目标列 '{target_column}' 不在数据中")
    
    # 统计指标分析
    print("\n📊 统计指标分析...")
    stat_analyzer = StatisticalAnalyzer(data)
    stat_analyzer.calculate_all_metrics()
    stat_analyzer.generate_report(f'{target_column}_statistical_report.txt')
    stat_analyzer.plot_metrics(f'{target_column}_statistical_plots')
    stat_analyzer.export_metrics(f'{target_column}_statistical_metrics.csv')
    
    # 相关性分析
    print("\n🔗 相关性分析...")
    X = data.drop(columns=[target_column])
    y = data[target_column]
    
    corr_analyzer = CorrelationAnalyzer(data, target_column=target_col)
    corr_analyzer.set_method('pearson')
    corr_analyzer.calculate_correlation()
    corr_analyzer.plot_correlation_network(f'{target_column}_correlation_network.pdf')
    corr_analyzer.export_correlation_matrix(f'{target_column}_correlation_matrix.csv')
    
    # SHAP分析
    print("\n🎯 SHAP分析...")
    print("   注意: SHAP分析可能需要较长时间")
    shap_analyzer = SHAPAnalyzer(X, y, test_size=0.3, random_state=42)
    shap_analyzer.run_full_analysis()
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='GenBFKit 简易数据分析模块')
    parser.add_argument('--demo', action='store_true', help='运行快速演示')
    parser.add_argument('--data', type=str, help='自定义数据文件路径')
    parser.add_argument('--target', type=str, help='目标列名')
    
    args = parser.parse_args()
    
    if args.demo:
        quick_start_demo()
    elif args.data and args.target:
        analyze_custom_data(args.data, args.target)
    else:
        print("👋 欢迎使用 GenBFKit 简易数据分析模块！")
        print("\n使用方式:")
        print("  1. 运行快速演示: python main.py --demo")
        print("  2. 分析自定义数据: python main.py --data <数据文件> --target <目标列>")
        print("\n示例:")
        print("  python main.py --demo")
        print("  python main.py --data my_data.xlsx --target 铁水温度")
