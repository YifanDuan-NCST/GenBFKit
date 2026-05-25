"""
统计指标分析器 📈
计算数据集的关键统计指标
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class StatisticalAnalyzer:
    """
    统计分析器类
    提供5个关键统计指标的计算与可视化功能
    
    指标说明：
    1. 均值（Mean）：数据的中心趋势
    2. 标准差（Standard Deviation）：数据的离散程度
    3. 变异系数（Coefficient of Variation）：相对变异程度
    4. 偏度（Skewness）：数据分布的不对称性
    5. 峰度（Kurtosis）：数据分布的尖锐程度
    """

    def __init__(self, data: pd.DataFrame):
        """
        初始化统计分析器
        
        Args:
            data: 要分析的数据集（DataFrame格式）
        """
        self.data = data.copy()
        self.metrics = None

    def calculate_all_metrics(self) -> pd.DataFrame:
        """
        计算所有统计指标
        
        Returns:
            包含所有指标的DataFrame
        """
        print("🔍 开始计算统计指标...")
        
        results = []
        
        for column in self.data.columns:
            # 只处理数值型数据
            if not pd.api.types.is_numeric_dtype(self.data[column]):
                print(f"⚠️  跳过非数值列: {column}")
                continue
            
            col_data = self.data[column].dropna()
            
            if len(col_data) == 0:
                print(f"⚠️  列 {column} 无有效数据，跳过")
                continue
            
            # 1. 均值
            mean_val = col_data.mean()
            
            # 2. 标准差
            std_val = col_data.std()
            
            # 3. 变异系数 (CV = std / mean)
            cv_val = (std_val / mean_val * 100) if mean_val != 0 else 0
            
            # 4. 偏度
            skew_val = stats.skew(col_data)
            
            # 5. 峰度
            kurtosis_val = stats.kurtosis(col_data)
            
            results.append({
                '参数名': column,
                '均值': round(mean_val, 4),
                '标准差': round(std_val, 4),
                '变异系数(%)': round(cv_val, 4),
                '偏度': round(skew_val, 4),
                '峰度': round(kurtosis_val, 4),
                '数据量': len(col_data)
            })
        
        self.metrics = pd.DataFrame(results)
        print(f"✅ 成功计算 {len(results)} 个参数的统计指标")
        
        return self.metrics

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        生成统计分析报告
        
        Args:
            output_path: 报告保存路径（可选）
        
        Returns:
            报告文本内容
        """
        if self.metrics is None:
            self.calculate_all_metrics()
        
        report = "=" * 80 + "\n"
        report += "📊 统计分析报告\n"
        report += "=" * 80 + "\n\n"
        
        report += f"📅 分析时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"📈 分析参数数量: {len(self.metrics)}\n\n"
        
        # 指标解释
        report += "📖 指标说明:\n"
        report += "  • 均值: 数据的中心位置，反映整体水平\n"
        report += "  • 标准差: 数据的离散程度，值越大表示数据越分散\n"
        report += "  • 变异系数: 相对变异程度，值越大表示相对波动越大\n"
        report += "  • 偏度: 数据分布的不对称性，>0右偏，<0左偏，=0对称\n"
        report += "  • 峰度: 数据分布的尖锐程度，>3尖锐，<3平坦，=3正态分布\n\n"
        
        report += "=" * 80 + "\n"
        report += "📋 详细指标结果\n"
        report += "=" * 80 + "\n\n"
        
        # 详细结果
        for idx, row in self.metrics.iterrows():
            param_name = row['参数名']
            report += f"\n【{param_name}】\n"
            report += f"  均值: {row['均值']:.4f}\n"
            report += f"  标准差: {row['标准差']:.4f}\n"
            report += f"  变异系数: {row['变异系数(%)']:.4f}%\n"
            
            # 偏度解读
            skew_val = row['偏度']
            if skew_val > 0.5:
                skew_interp = "右偏（长尾在右侧）"
            elif skew_val < -0.5:
                skew_interp = "左偏（长尾在左侧）"
            else:
                skew_interp = "接近对称分布"
            report += f"  偏度: {skew_val:.4f} - {skew_interp}\n"
            
            # 峰度解读
            kurt_val = row['峰度']
            if kurt_val > 1:
                kurt_interp = "尖峰（数据集中在均值附近）"
            elif kurt_val < -1:
                kurt_interp = "平峰（数据分布较分散）"
            else:
                kurt_interp = "接近正态分布"
            report += f"  峰度: {kurt_val:.4f} - {kurt_interp}\n"
            report += f"  数据量: {int(row['数据量'])}\n"
        
        # 关键发现
        report += "\n" + "=" * 80 + "\n"
        report += "🔍 关键发现\n"
        report += "=" * 80 + "\n\n"
        
        # 变异系数最大的3个参数
        top_cv = self.metrics.nlargest(3, '变异系数(%)')
        report += "🎯 变异系数最大的参数（最不稳定）:\n"
        for idx, row in top_cv.iterrows():
            report += f"  {row['参数名']}: {row['变异系数(%)']:.2f}%\n"
        
        # 偏度最显著的参数
        max_skew = self.metrics.loc[self.metrics['偏度'].abs().idxmax()]
        report += f"\n🔄 偏度最显著的参数: {max_skew['参数名']} (偏度={max_skew['偏度']:.2f})\n"
        
        # 峰度最显著的参数
        max_kurt = self.metrics.loc[self.metrics['峰度'].abs().idxmax()]
        report += f"🔺 峰度最显著的参数: {max_kurt['参数名']} (峰度={max_kurt['峰度']:.2f})\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存至: {output_path}")
        
        return report

    def plot_metrics(self, save_folder: str = "statistical_plots"):
        """
        绘制统计指标的可视化图表
        
        Args:
            save_folder: 图表保存文件夹
        """
        import os
        os.makedirs(save_folder, exist_ok=True)
        
        if self.metrics is None:
            self.calculate_all_metrics()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        print("📊 开始生成统计指标可视化图表...")
        
        # 1. 均值和标准差对比图
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = np.arange(len(self.metrics))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, self.metrics['均值'], width, 
                      label='均值', color='skyblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, self.metrics['标准差'], width, 
                      label='标准差', color='salmon', alpha=0.8)
        
        ax.set_xlabel('参数', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.set_title('各参数均值与标准差对比', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(self.metrics['参数名'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        mean_std_path = os.path.join(save_folder, 'mean_std_comparison.png')
        plt.savefig(mean_std_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 保存图表: {mean_std_path}")
        
        # 2. 变异系数排序图
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sorted_cv = self.metrics.sort_values('变异系数(%)', ascending=True)
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sorted_cv)))
        
        bars = ax.barh(sorted_cv['参数名'], sorted_cv['变异系数(%)'], 
                      color=colors, alpha=0.8)
        ax.set_xlabel('变异系数 (%)', fontsize=12)
        ax.set_ylabel('参数', fontsize=12)
        ax.set_title('各参数变异系数排序（从稳定到波动）', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # 添加数值标签
        for i, (bar, val) in enumerate(zip(bars, sorted_cv['变异系数(%)'])):
            ax.text(val, i, f' {val:.1f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        cv_path = os.path.join(save_folder, 'coefficient_of_variation.png')
        plt.savefig(cv_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 保存图表: {cv_path}")
        
        # 3. 偏度与峰度散点图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        scatter = ax.scatter(self.metrics['偏度'], self.metrics['峰度'], 
                           c=self.metrics['变异系数(%)'], 
                           s=100, alpha=0.6, 
                           cmap='viridis')
        
        # 添加参考线
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=0.5, color='red', linestyle=':', linewidth=1, alpha=0.5, label='右偏阈值')
        ax.axvline(x=-0.5, color='blue', linestyle=':', linewidth=1, alpha=0.5, label='左偏阈值')
        
        ax.set_xlabel('偏度 (Skewness)', fontsize=12)
        ax.set_ylabel('峰度 (Kurtosis)', fontsize=12)
        ax.set_title('各参数偏度与峰度分布', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('变异系数 (%)', fontsize=10)
        
        # 添加参数标签
        for i, param in enumerate(self.metrics['参数名']):
            ax.annotate(param, 
                       (self.metrics['偏度'][i], self.metrics['峰度'][i]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        skew_kurt_path = os.path.join(save_folder, 'skewness_kurtosis_scatter.png')
        plt.savefig(skew_kurt_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 保存图表: {skew_kurt_path}")
        
        # 4. 数据分布热图（归一化后）
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 对每个参数进行归一化（Z-score标准化）
        normalized_data = self.data.select_dtypes(include=[np.number]).apply(
            lambda x: (x - x.mean()) / x.std()
        )
        
        sns.heatmap(normalized_data.iloc[:50],  # 只显示前50行以避免过于密集
                   cmap='coolwarm', center=0,
                   cbar_kws={'label': 'Z-score'},
                   ax=ax)
        ax.set_title('数据分布热图（前50行，Z-score标准化）', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        heatmap_path = os.path.join(save_folder, 'data_distribution_heatmap.png')
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 保存图表: {heatmap_path}")
        
        print(f"✅ 所有图表已保存至: {save_folder}/")

    def export_metrics(self, output_path: str = "statistical_metrics.csv"):
        """
        导出统计指标到CSV文件
        
        Args:
            output_path: 输出文件路径
        """
        if self.metrics is None:
            self.calculate_all_metrics()
        
        self.metrics.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 统计指标已导出至: {output_path}")
