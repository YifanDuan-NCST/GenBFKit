"""
测试脚本 - 验证所有分析功能 ✅
"""

import os
import sys
import pandas as pd

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simplified_data_analysis_module.data_generator import MockDataGenerator
from simplified_data_analysis_module.statistical_analysis import StatisticalAnalyzer
from simplified_data_analysis_module.correlation_analysis import CorrelationAnalyzer
from simplified_data_analysis_module.shap_analysis import SHAPAnalyzer


def test_statistical_analysis(data):
    """测试统计指标分析"""
    print("\n" + "=" * 60)
    print("📊 测试1: 统计指标分析")
    print("=" * 60)
    
    try:
        analyzer = StatisticalAnalyzer(data)
        metrics = analyzer.calculate_all_metrics()
        print(f"✅ 计算完成，共 {len(metrics)} 个参数")
        print("\n前5个参数的指标:")
        print(metrics.head())
        
        # 生成报告
        report = analyzer.generate_report('statistical_report.txt')
        print("✅ 报告生成成功")
        
        # 绘制图表
        analyzer.plot_metrics('statistical_plots')
        print("✅ 图表生成成功")
        
        # 导出结果
        analyzer.export_metrics('statistical_metrics.csv')
        print("✅ CSV导出成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_correlation_analysis(data):
    """测试相关性分析"""
    print("\n" + "=" * 60)
    print("🔗 测试2: 相关性分析")
    print("=" * 60)
    
    try:
        # 分离特征和目标变量
        target_col = '铁水温度'
        X = data.drop(columns=[target_col])
        y = data[target_col]
        
        analyzer = CorrelationAnalyzer(data, target_column=target_col)
        
        # 测试Pearson方法
        analyzer.set_method('pearson')
        results = analyzer.calculate_correlation()
        print("✅ Pearson相关性计算完成")
        
        # 获取Top相关性
        top_corr = analyzer.get_top_correlations(n=5)
        print("\n相关性最强的5对参数:")
        print(top_corr)
        
        # 绘制网络图
        analyzer.plot_correlation_network('correlation_network_pearson.pdf')
        print("✅ Pearson网络图生成成功")
        
        # 测试Spearman方法
        analyzer.set_method('spearman')
        analyzer.calculate_correlation()
        analyzer.plot_correlation_network('correlation_network_spearman.pdf')
        print("✅ Spearman网络图生成成功")
        
        # 导出相关性矩阵
        analyzer.export_correlation_matrix('correlation_matrix.csv')
        print("✅ 相关性矩阵导出成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_shap_analysis(data):
    """测试SHAP分析"""
    print("\n" + "=" * 60)
    print("🎯 测试3: SHAP分析")
    print("=" * 60)
    
    try:
        # 分离特征和目标变量
        target_col = '铁水温度'
        X = data.drop(columns=[target_col])
        y = data[target_col]
        
        # 减少样本数量以加快测试速度
        X_sample = X.sample(n=500, random_state=42)
        y_sample = y.loc[X_sample.index]
        
        analyzer = SHAPAnalyzer(X_sample, y_sample, test_size=0.3, random_state=42)
        
        # 预处理
        analyzer.preprocess_data()
        print("✅ 数据预处理完成")
        
        # 训练模型
        analyzer.train_model(param_grid={
            'n_estimators': [100, 200],
            'max_depth': [5, 10],
            'learning_rate': [0.1, 0.2]
        })
        print("✅ 模型训练完成")
        
        # 评估模型
        metrics = analyzer.evaluate_model()
        if metrics:
            print(f"✅ 模型评估完成 (R2={metrics['test_r2']:.4f})")
        
        # 计算SHAP值
        analyzer.calculate_shap_values()
        print("✅ SHAP值计算完成")
        
        # 绘制回归拟合图
        analyzer.plot_regression_fit('shap_regression_fit.png')
        print("✅ 回归拟合图生成成功")
        
        # 绘制特征重要性图
        analyzer.plot_feature_importance('shap_feature_importance.png')
        print("✅ 特征重要性图生成成功")
        
        # 绘制依赖图（只画前3个特征以节省时间）
        print("正在生成依赖图（前3个特征）...")
        sorted_features = analyzer.feature_importance['feature'].values[:3]
        
        if analyzer.shap_values is not None:
            import matplotlib.pyplot as plt
            import numpy as np
            import re
            
            # LOWESS平滑函数（兼容性处理）
            try:
                from scipy.stats import lowess
            except ImportError:
                from statsmodels.nonparametric.smoothers_lowess import lowess
            
            os.makedirs('shap_dependence_plots', exist_ok=True)
            
            sorted_indices = [analyzer.X.columns.get_loc(f) for f in sorted_features]
            shap_values_sorted = analyzer.shap_values[:, sorted_indices]
            X_test_sorted = analyzer.X_test[sorted_features]
            
            for i, feature_name in enumerate(sorted_features):
                x_values = X_test_sorted[feature_name]
                shap_values_for_feature = shap_values_sorted[:, i]
                
                fig, ax1 = plt.subplots(figsize=(8, 6), dpi=150)
                ax2 = ax1.twinx()
                ax2.patch.set_alpha(0)
                
                counts, bin_edges = np.histogram(x_values, bins=30)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                bin_width = bin_edges[1] - bin_edges[0]
                ax1.bar(bin_centers, counts, width=bin_width * 0.6, align='center',
                       color='#4B0082', alpha=0.3, label='Distribution')
                ax1.set_ylabel('Distribution', fontsize=12)
                ax1.set_ylim(0, counts.max() * 1.1)
                
                ax2.scatter(x_values, shap_values_for_feature, alpha=0.3, s=25,
                           color='#00008B', label='Sample', zorder=2)
                ax2.axhline(0, color='black', linestyle='--', lw=1, zorder=1)
                
                if len(x_values) > 1:
                    try:
                        smoothed = lowess(shap_values_for_feature, x_values, frac=0.3)
                        ax2.plot(smoothed[:, 0], smoothed[:, 1], color='#9400D3', 
                                lw=2, label='LOWESS Fit', zorder=4)
                    except:
                        pass
                
                ax2.set_ylabel('SHAP value', fontsize=12)
                y_max = np.abs(shap_values_for_feature).max() * 1.15
                if y_max < 1e-6:
                    y_max = 1
                ax2.set_ylim(-y_max, y_max)
                ax1.set_xlabel(f'{feature_name}', fontsize=12)
                
                h1, l1 = ax1.get_legend_handles_labels()
                h2, l2 = ax2.get_legend_handles_labels()
                ax2.legend(h2 + h1, l2 + l1, loc='upper right', fontsize=10)
                
                ax1.set_zorder(0)
                ax2.set_zorder(1)
                
                plt.tight_layout()
                
                sanitized_name = re.sub(r'[\\/*?:"<>|]', '_', feature_name)
                save_path = f'shap_dependence_plots/dependence_{sanitized_name}.png'
                plt.savefig(save_path, dpi=200, bbox_inches='tight')
                plt.close()
        
        print("✅ 依赖图生成成功")
        
        # 导出特征重要性
        analyzer.export_feature_importance('shap_feature_importance.csv')
        print("✅ 特征重要性导出成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🚀 开始测试 GenBFKit 简易数据分析模块")
    print("=" * 60)
    
    # 创建输出目录
    os.makedirs('test_output', exist_ok=True)
    os.chdir('test_output')
    
    # 步骤1: 生成测试数据
    print("\n🎲 生成测试数据...")
    try:
        generator = MockDataGenerator(n_samples=1000, random_state=42)
        data = generator.generate_blast_furnace_data()
        
        # 保存数据
        data.to_excel('test_data.xlsx', index=False, engine='openpyxl')
        print(f"✅ 测试数据生成完成，形状: {data.shape}")
        print(f"   参数: {list(data.columns)}")
    except Exception as e:
        print(f"❌ 数据生成失败: {str(e)}")
        return
    
    # 步骤2: 测试统计指标分析
    test1_result = test_statistical_analysis(data)
    
    # 步骤3: 测试相关性分析
    test2_result = test_correlation_analysis(data)
    
    # 步骤4: 测试SHAP分析
    test3_result = test_shap_analysis(data)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"📊 统计指标分析: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"🔗 相关性分析: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"🎯 SHAP分析: {'✅ 通过' if test3_result else '❌ 失败'}")
    
    all_passed = test1_result and test2_result and test3_result
    if all_passed:
        print("\n🎉 所有测试通过！")
        print("📁 测试结果已保存到: test_output/")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
