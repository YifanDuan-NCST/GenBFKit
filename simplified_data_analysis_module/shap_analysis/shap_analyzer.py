"""
SHAP分析器 🎯
基于XGBoost的SHAP可解释性分析
基于原始demo.py优化和封装
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb
from typing import Dict, List, Optional
import warnings
import os
import re
import matplotlib.colors as mcolors
warnings.filterwarnings('ignore')

# LOWESS平滑函数（兼容性处理）
try:
    from scipy.stats import lowess
except ImportError:
    # 新版本scipy中lowess已移动到statsmodels
    from statsmodels.nonparametric.smoothers_lowess import lowess


class SHAPAnalyzer:
    """
    SHAP分析器类
    使用XGBoost模型进行预测，并通过SHAP值进行模型解释
    
    功能特性：
    • XGBoost模型训练与超参数优化
    • SHAP主效应值计算
    • SHAP交互效应值计算
    • 多种可视化图表（重要性总览、依赖图、交互图）
    • 模型性能评估
    """

    def __init__(self, X: pd.DataFrame, y: pd.Series, 
                 test_size: float = 0.3, random_state: int = 42):
        """
        初始化SHAP分析器
        
        Args:
            X: 特征数据
            y: 目标变量
            test_size: 测试集比例
            random_state: 随机种子
        """
        self.X = X
        self.y = y
        self.test_size = test_size
        self.random_state = random_state
        
        # 模型相关
        self.model = None
        self.best_params = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # SHAP相关
        self.explainer = None
        self.shap_values = None
        self.shap_interaction_values = None
        self.feature_importance = None
        
        # 配置
        self.output_folder = "shap_analysis_output"

    def preprocess_data(self):
        """
        数据预处理
        处理缺失值和类型转换
        """
        print("🔧 开始数据预处理...")
        
        # 确保所有特征都是数值型
        for col in self.X.columns:
            if self.X[col].dtype == 'object':
                print(f"  -> 特征 '{col}' 是文本类型，进行因子化编码")
                self.X[col], _ = pd.factorize(self.X[col])
            else:
                # 转换为数值类型
                self.X[col] = pd.to_numeric(self.X[col], errors='coerce')
        
        # 填充缺失值
        for col in self.X.columns:
            if self.X[col].isnull().sum() > 0:
                median_val = self.X[col].median()
                self.X[col].fillna(median_val, inplace=True)
                print(f"  -> 特征 '{col}' 填充缺失值: {median_val:.4f}")
        
        # 划分训练集和测试集
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=self.test_size, random_state=self.random_state
        )
        print(f"✅ 数据预处理完成")
        print(f"   训练集: {self.X_train.shape[0]} 样本")
        print(f"   测试集: {self.X_test.shape[0]} 样本")

    def train_model(self, param_grid: Optional[Dict] = None, cv: int = 3):
        """
        训练XGBoost模型并进行超参数优化
        
        Args:
            param_grid: 超参数网格（可选）
            cv: 交叉验证折数
        """
        if self.X_train is None:
            self.preprocess_data()
        
        print("🚀 开始训练XGBoost模型...")
        
        if param_grid is None:
            param_grid = {
                'n_estimators': [100, 200, 500],
                'max_depth': [5, 10, 15],
                'learning_rate': [0.05, 0.1, 0.2]
            }
        
        # 初始化模型
        xgb_model = xgb.XGBRegressor(
            random_state=self.random_state, 
            eval_metric='rmse'
        )
        
        # 网格搜索
        grid_search = GridSearchCV(
            estimator=xgb_model,
            param_grid=param_grid,
            scoring='neg_mean_squared_error',
            cv=cv,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(self.X_train, self.y_train)
        
        self.model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_
        
        print(f"✅ 模型训练完成")
        print(f"   最佳参数: {self.best_params}")

    def evaluate_model(self):
        """
        评估模型性能
        """
        if self.model is None:
            print("⚠️  请先训练模型")
            return None
        
        print("📊 评估模型性能...")
        
        # 预测
        y_train_pred = self.model.predict(self.X_train)
        y_test_pred = self.model.predict(self.X_test)
        
        # 计算指标
        r2_train = r2_score(self.y_train, y_train_pred)
        rmse_train = np.sqrt(mean_squared_error(self.y_train, y_train_pred))
        mae_train = mean_absolute_error(self.y_train, y_train_pred)
        
        r2_test = r2_score(self.y_test, y_test_pred)
        rmse_test = np.sqrt(mean_squared_error(self.y_test, y_test_pred))
        mae_test = mean_absolute_error(self.y_test, y_test_pred)
        
        metrics = {
            'train_r2': r2_train,
            'train_rmse': rmse_train,
            'train_mae': mae_train,
            'test_r2': r2_test,
            'test_rmse': rmse_test,
            'test_mae': mae_test
        }
        
        print(f"   训练集: R2={r2_train:.4f}, RMSE={rmse_train:.4f}, MAE={mae_train:.4f}")
        print(f"   测试集: R2={r2_test:.4f}, RMSE={rmse_test:.4f}, MAE={mae_test:.4f}")
        
        return metrics

    def calculate_shap_values(self):
        """
        计算SHAP值（主效应和交互效应）
        """
        if self.model is None:
            print("⚠️  请先训练模型")
            return
        
        print("🔍 开始计算SHAP值...")
        
        # 创建解释器
        self.explainer = shap.TreeExplainer(self.model)
        
        # 计算主效应SHAP值
        self.shap_values = self.explainer(self.X_test).values
        print("   ✅ 主效应SHAP值计算完成")
        
        # 计算交互效应SHAP值
        self.shap_interaction_values = self.explainer.shap_interaction_values(self.X_test)
        print("   ✅ 交互效应SHAP值计算完成")
        
        # 计算特征重要性
        mean_shap = np.abs(self.shap_values).mean(axis=0)
        self.feature_importance = pd.DataFrame({
            'feature': self.X.columns,
            'mean_shap': mean_shap
        }).sort_values('mean_shap', ascending=False)

    def plot_regression_fit(self, save_path: str = None):
        """
        绘制回归拟合图
        
        Args:
            save_path: 保存路径
        """
        if self.model is None:
            print("⚠️  请先训练模型")
            return
        
        # 预测
        y_train_pred = self.model.predict(self.X_train)
        y_test_pred = self.model.predict(self.X_test)
        
        # 计算指标
        r2_train = r2_score(self.y_train, y_train_pred)
        rmse_train = np.sqrt(mean_squared_error(self.y_train, y_train_pred))
        mae_train = mean_absolute_error(self.y_train, y_train_pred)
        
        r2_test = r2_score(self.y_test, y_test_pred)
        rmse_test = np.sqrt(mean_squared_error(self.y_test, y_test_pred))
        mae_test = mean_absolute_error(self.y_test, y_test_pred)
        
        # 绘图
        fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
        ax.scatter(self.y_train, y_train_pred, alpha=0.5, label='Train', color='blue')
        ax.scatter(self.y_test, y_test_pred, alpha=0.7, label='Validation', color='red', marker='^')
        ax.plot([self.y_test.min(), self.y_test.max()], 
               [self.y_test.min(), self.y_test.max()], 
               'k--', lw=2, label='1:1 Line (y=x)')
        ax.set_xlabel('Actual Values', fontsize=12)
        ax.set_ylabel('Predicted Values', fontsize=12)
        ax.set_title('XGBoost Regression Fit', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 添加指标文本
        metrics_text = (
            f'验证集:\n'
            f'$R^2$ = {r2_test:.4f}\n'
            f'RMSE = {rmse_test:.4f}\n'
            f'MAE = {mae_test:.4f}\n\n'
            f'训练集:\n'
            f'$R^2$ = {r2_train:.4f}\n'
            f'RMSE = {rmse_train:.4f}\n'
            f'MAE = {mae_train:.4f}'
        )
        ax.text(0.95, 0.05, metrics_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 回归拟合图已保存至: {save_path}")
        else:
            save_path = os.path.join(self.output_folder, 'regression_fit.png')
            os.makedirs(self.output_folder, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 回归拟合图已保存至: {save_path}")
        
        plt.close()

    def plot_feature_importance(self, save_path: str = None):
        """
        绘制SHAP特征重要性图（蜂群图+条形图组合）
        
        Args:
            save_path: 保存路径
        """
        if self.shap_values is None:
            self.calculate_shap_values()
        
        # 按重要性排序
        sorted_features = self.feature_importance['feature'].values
        sorted_indices = [self.X.columns.get_loc(f) for f in sorted_features]
        shap_values_sorted = self.shap_values[:, sorted_indices]
        X_test_sorted = self.X_test[sorted_features]
        
        # 创建图形
        fig = plt.figure(figsize=(10, 10), dpi=300)
        ax_sw = fig.add_axes([0.32, 0.11, 0.59, 0.77])
        ax_bar = ax_sw.twiny()
        ax_bar.set_zorder(0)
        ax_sw.set_zorder(1)
        ax_sw.patch.set_alpha(0)
        
        y_pos = np.arange(len(sorted_features))[::-1]
        
        # 绘制条形图
        ax_bar.barh(y=y_pos, width=self.feature_importance['mean_shap'].values, 
                   height=0.6, color="blue", alpha=0.5, edgecolor="none", zorder=0)
        xlim_bar = self.feature_importance['mean_shap'].values.max() * 1.05
        ax_bar.set_xlim(0, xlim_bar)
        ax_bar.set_xlabel("Mean (|SHAP| value)", fontsize=10)
        ax_bar.set_yticks(y_pos)
        ax_bar.tick_params(axis='y', length=0)
        
        # 绘制蜂群图
        max_abs_shap = np.abs(shap_values_sorted).max()
        xlim_sw = max_abs_shap * 1.1
        ax_sw.set_xlim(-xlim_sw, xlim_sw)
        ax_sw.set_xlabel("SHAP value (impact on model output)", fontsize=10)
        
        expl_main = shap.Explanation(
            values=shap_values_sorted,
            data=X_test_sorted.values,
            feature_names=list(sorted_features),
            base_values=self.explainer.expected_value
        )
        
        shap.plots.beeswarm(expl_main, max_display=len(sorted_features), 
                           show=False, plot_size=None, ax=ax_sw)
        ax_sw.set_yticks(y_pos)
        ax_sw.set_yticklabels(sorted_features, fontsize=12)
        ax_sw.tick_params(axis='y', length=4)
        
        # 移除顶部和右侧边框
        ax_sw.spines['top'].set_visible(False)
        ax_sw.spines['right'].set_visible(False)
        ax_bar.spines['top'].set_visible(False)
        ax_bar.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 特征重要性图已保存至: {save_path}")
        else:
            save_path = os.path.join(self.output_folder, 'feature_importance.png')
            os.makedirs(self.output_folder, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 特征重要性图已保存至: {save_path}")
        
        plt.close()

    def plot_dependence_plots(self, save_folder: str = None):
        """
        绘制SHAP依赖图（每个特征一个）
        
        Args:
            save_folder: 保存文件夹
        """
        if self.shap_values is None:
            self.calculate_shap_values()
        
        if save_folder is None:
            save_folder = os.path.join(self.output_folder, 'dependence_plots')
        os.makedirs(save_folder, exist_ok=True)
        
        sorted_features = self.feature_importance['feature'].values
        sorted_indices = [self.X.columns.get_loc(f) for f in sorted_features]
        shap_values_sorted = self.shap_values[:, sorted_indices]
        X_test_sorted = self.X_test[sorted_features]
        
        print(f"📊 开始生成 {len(sorted_features)} 个特征的依赖图...")
        
        for i, feature_name in enumerate(sorted_features):
            x_values = X_test_sorted[feature_name]
            shap_values_for_feature = shap_values_sorted[:, i]
            
            # 创建图形
            fig, ax1 = plt.subplots(figsize=(8, 6), dpi=150)
            ax2 = ax1.twinx()
            ax2.patch.set_alpha(0)
            
            # 绘制直方图（数据分布）
            counts, bin_edges = np.histogram(x_values, bins=30)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            bin_width = bin_edges[1] - bin_edges[0]
            ax1.bar(bin_centers, counts, width=bin_width * 0.6, align='center',
                   color='#4B0082', alpha=0.3, label='Distribution')
            ax1.set_ylabel('Distribution', fontsize=12)
            ax1.set_ylim(0, counts.max() * 1.1)
            
            # 绘制SHAP值散点图
            ax2.scatter(x_values, shap_values_for_feature, alpha=0.3, s=25,
                       color='#00008B', label='Sample', zorder=2)
            ax2.axhline(0, color='black', linestyle='--', lw=1, zorder=1)
            
            # LOWESS平滑
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
            
            # 图例
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax2.legend(h2 + h1, l2 + l1, loc='upper right', fontsize=10)
            
            ax1.set_zorder(0)
            ax2.set_zorder(1)
            
            plt.tight_layout()
            
            # 保存
            sanitized_name = re.sub(r'[\\/*?:"<>|]', '_', feature_name)
            save_path = os.path.join(save_folder, f'dependence_{sanitized_name}.png')
            plt.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close()
        
        print(f"✅ 所有依赖图已保存至: {save_folder}/")

    def export_feature_importance(self, output_path: str = None):
        """
        导出特征重要性
        
        Args:
            output_path: 输出文件路径
        """
        if self.feature_importance is None:
            self.calculate_shap_values()
        
        if output_path is None:
            output_path = os.path.join(self.output_folder, 'feature_importance.csv')
            os.makedirs(self.output_folder, exist_ok=True)
        
        self.feature_importance.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 特征重要性已导出至: {output_path}")

    def run_full_analysis(self):
        """
        运行完整的SHAP分析流程
        """
        print("=" * 60)
        print("🚀 开始完整的SHAP分析流程")
        print("=" * 60)
        
        # 1. 数据预处理
        self.preprocess_data()
        
        # 2. 训练模型
        self.train_model()
        
        # 3. 评估模型
        self.evaluate_model()
        
        # 4. 计算SHAP值
        self.calculate_shap_values()
        
        # 5. 生成可视化
        self.plot_regression_fit()
        self.plot_feature_importance()
        self.plot_dependence_plots()
        
        # 6. 导出结果
        self.export_feature_importance()
        
        print("=" * 60)
        print("✅ SHAP分析完成！")
        print("=" * 60)
