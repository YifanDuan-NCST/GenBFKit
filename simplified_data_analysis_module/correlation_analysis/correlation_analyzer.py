"""
相关性分析器 🔗
分析参数间的相关关系，支持多种相关系数计算方法
基于原始cor_pro.py优化和封装
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
from scipy.stats import pearsonr, spearmanr, kendalltau
from typing import Dict, List, Optional, Tuple
import warnings
import os
warnings.filterwarnings('ignore')


class CorrelationAnalyzer:
    """
    相关性分析器类
    支持三种相关系数计算方法：Pearson、Spearman、Kendall
    
    可视化特性：
    • 节点大小：表示与目标变量的相关性强度
    • 节点颜色：表示相关性的方向（正/负）
    • 连线粗细：表示参数间的相关性强度
    • 连线颜色：表示相关性的方向
    • 线型：表示显著性（实线=显著，虚线=不显著）
    """

    # 颜色方案配置
    COLOR_SCHEMES = {
        1: {'nodes': plt.cm.RdBu_r, 'edges': plt.cm.PRGn},
        2: {'nodes': plt.cm.PiYG, 'edges': plt.cm.PuOr},
        3: {'nodes': plt.cm.BrBG, 'edges': plt.cm.RdBu_r},
        4: {'nodes': plt.cm.PuOr, 'edges': plt.cm.coolwarm},
        5: {'nodes': plt.cm.RdGy, 'edges': plt.cm.RdYlBu_r},
    }

    # 形状标记方案
    STYLE_SCHEMES = {
        1: {'marker': 'o'},
        2: {'marker': r'$\oplus$'},
        3: {'marker': '*'},
        4: {'marker': r'$\odot$'},
        5: {'marker': 'p'},
    }

    def __init__(self, data: pd.DataFrame, target_column: str = None):
        """
        初始化相关性分析器
        
        Args:
            data: 输入数据集（DataFrame格式）
            target_column: 目标列名（可选，用于分析特征与目标的关系）
        """
        self.data = data.copy()
        self.target_column = target_column
        
        # 默认配置
        self.method = 'pearson'
        self.scheme_index = 1
        self.style_index = 1
        
        # 计算结果存储
        self.correlation_matrix = None
        self.p_value_matrix = None
        self.target_correlations = None
        self.target_p_values = None

    def set_method(self, method: str = 'pearson'):
        """
        设置相关性分析方法
        
        Args:
            method: 'pearson', 'spearman', 或 'kendall'
        """
        method = method.lower()
        if method not in ['pearson', 'spearman', 'kendall']:
            raise ValueError(f"不支持的方法: {method}，请选择 'pearson', 'spearman', 或 'kendall'")
        self.method = method
        print(f"✅ 相关性分析方法已设置为: {method}")

    def set_visualization_style(self, scheme_index: int = 1, style_index: int = 1):
        """
        设置可视化样式
        
        Args:
            scheme_index: 颜色方案索引（1-5）
            style_index: 形状标记索引（1-5）
        """
        self.scheme_index = scheme_index
        self.style_index = style_index

    def calculate_correlation(self, X: pd.DataFrame = None, y: pd.Series = None) -> Dict:
        """
        计算相关性矩阵和P值
        
        Args:
            X: 特征数据（可选，默认使用self.data）
            y: 目标变量（可选，默认使用self.target_column）
        
        Returns:
            包含相关性矩阵和P值矩阵的字典
        """
        if X is None:
            X = self.data.select_dtypes(include=[np.number])
        
        if y is None and self.target_column:
            if self.target_column in self.data.columns:
                y = self.data[self.target_column]
                X = X.drop(columns=[self.target_column])
            else:
                print(f"⚠️  目标列 '{self.target_column}' 不在数据中")
        
        features = X.columns.tolist()
        print(f"🔍 开始计算相关性... ({len(features)} 个特征)")
        print(f"📊 使用方法: {self.method}")
        
        # 计算特征与目标的相关性
        if y is not None:
            target_corrs = []
            target_p_vals = []
            for col in features:
                r, p = self._calculate_corr_p(X[col], y, self.method)
                target_corrs.append(r)
                target_p_vals.append(p)
            
            self.target_correlations = np.array(target_corrs)
            self.target_p_values = np.array(target_p_vals)
        
        # 计算特征间的相关性矩阵
        n_feat = len(features)
        corr_matrix = np.ones((n_feat, n_feat))
        p_matrix = np.ones((n_feat, n_feat))
        
        for i in range(n_feat):
            for j in range(i + 1, n_feat):
                r, p = self._calculate_corr_p(X.iloc[:, i], X.iloc[:, j], self.method)
                corr_matrix[i, j] = corr_matrix[j, i] = r
                p_matrix[i, j] = p_matrix[j, i] = p
        
        # 对角线P值为0
        np.fill_diagonal(p_matrix, 0.0)
        
        self.correlation_matrix = corr_matrix
        self.p_value_matrix = p_matrix
        
        print("✅ 相关性计算完成")
        
        return {
            'correlation_matrix': corr_matrix,
            'p_value_matrix': p_matrix,
            'features': features
        }

    def _calculate_corr_p(self, x: pd.Series, y: pd.Series, method: str) -> Tuple[float, float]:
        """
        计算两个变量间的相关系数和P值
        
        Args:
            x: 第一个变量
            y: 第二个变量
            method: 相关性方法
        
        Returns:
            (相关系数, P值)
        """
        # 移除缺失值
        mask = ~(pd.isna(x) | pd.isna(y))
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 3:
            return 0.0, 1.0
        
        if method == 'pearson':
            return pearsonr(x_clean, y_clean)
        elif method == 'spearman':
            return spearmanr(x_clean, y_clean)
        elif method == 'kendall':
            return kendalltau(x_clean, y_clean)
        else:
            return pearsonr(x_clean, y_clean)

    def plot_correlation_network(self, save_path: str = "correlation_network.pdf",
                                X: pd.DataFrame = None, y: pd.Series = None):
        """
        绘制相关性网络图
        
        Args:
            save_path: 保存路径
            X: 特征数据
            y: 目标变量
        """
        if self.correlation_matrix is None:
            self.calculate_correlation(X, y)
        
        # 使用相关性矩阵的实际维度来获取特征列表
        n_features = self.correlation_matrix.shape[0]
        all_numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        features = all_numeric_cols[:n_features]
        
        # 如果有目标变量，使用其相关性作为节点大小
        if self.target_correlations is not None:
            importance_abs = np.abs(self.target_correlations)
            importance_signed = self.target_correlations
            p_target = self.target_p_values
        else:
            # 否则使用平均相关性
            importance_abs = np.mean(np.abs(self.correlation_matrix), axis=1)
            importance_signed = np.mean(self.correlation_matrix, axis=1)
            p_target = np.ones(len(features))
        
        # 交互矩阵（特征间相关性）
        interaction_matrix_abs = np.abs(self.correlation_matrix)
        np.fill_diagonal(interaction_matrix_abs, 0)
        interaction_matrix_signed = self.correlation_matrix
        np.fill_diagonal(interaction_matrix_signed, 0)
        
        # 获取颜色和样式方案
        current_color_scheme = self.COLOR_SCHEMES.get(self.scheme_index, self.COLOR_SCHEMES[1])
        current_style_scheme = self.STYLE_SCHEMES.get(self.style_index, self.STYLE_SCHEMES[1])
        
        cmap_nodes = current_color_scheme['nodes']
        cmap_edges = current_color_scheme['edges']
        node_marker = current_style_scheme['marker']
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'aspect': 'equal'})
        
        n_features = len(features)
        G = nx.Graph()
        G.add_nodes_from(features)
        pos = nx.circular_layout(G)
        label_pos = {k: (v * 1.1) for k, v in pos.items()}
        
        # 颜色归一化
        norm_edges = mcolors.Normalize(vmin=interaction_matrix_signed.min(),
                                       vmax=interaction_matrix_signed.max())
        norm_nodes = mcolors.Normalize(vmin=importance_signed.min(),
                                       vmax=importance_signed.max())
        
        # 宽度/大小归一化
        max_interaction_abs = np.max(interaction_matrix_abs)
        max_importance_abs = np.max(importance_abs)
        
        # 绘制连线
        interactions = []
        for i in range(n_features):
            for j in range(i + 1, n_features):
                strength_abs = interaction_matrix_abs[i, j]
                strength_signed = interaction_matrix_signed[i, j]
                p_val = self.p_value_matrix[i, j]
                if strength_abs > 0:
                    interactions.append((features[i], features[j], strength_abs, strength_signed, p_val))
        
        interactions.sort(key=lambda x: x[2])
        
        for u, v, strength_abs, strength_signed, p_val in interactions:
            color = cmap_edges(norm_edges(strength_signed))
            width = 0.5 + (strength_abs / max_interaction_abs) * 8
            alpha = 0.3 + (strength_abs / max_interaction_abs) * 0.7
            
            # 根据P值设置线型
            linestyle = '-' if p_val < 0.05 else '--'
            
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=width,
                                 edge_color=[color], style=linestyle, alpha=alpha, ax=ax)
        
        # 节点大小映射
        NODE_SIZE_MIN = 300
        NODE_SIZE_MAX = 1000
        data_min, data_max = np.min(importance_abs), np.max(importance_abs)
        
        def map_size(value):
            if data_max == data_min:
                return NODE_SIZE_MAX
            return NODE_SIZE_MIN + (value - data_min) / (data_max - data_min) * (NODE_SIZE_MAX - NODE_SIZE_MIN)
        
        # 节点颜色和大小
        node_colors = []
        node_sizes = []
        node_edge_colors = []
        node_line_widths = []
        
        for i, feat in enumerate(features):
            imp_sign = importance_signed[i]
            imp_abs = importance_abs[i]
            p_val_target = p_target[i]
            
            node_colors.append(cmap_nodes(norm_nodes(imp_sign)))
            node_sizes.append(map_size(imp_abs))
            
            if p_val_target < 0.05:
                node_edge_colors.append('black')
                node_line_widths.append(2.0)
            else:
                node_edge_colors.append('grey')
                node_line_widths.append(0.5)
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                             edgecolors=node_edge_colors, linewidths=node_line_widths,
                             node_shape=node_marker, ax=ax)
        
        # 绘制标签
        for node, (x, y) in label_pos.items():
            ha = 'left' if x > 0.1 else 'right' if x < -0.1 else 'center'
            plt.text(x, y, node, size=12, horizontalalignment=ha,
                    verticalalignment='center')
        
        ax.axis('off')
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        plt.title(f'(a) Correlation Network ({self.method.capitalize()})', 
                 y=0.95, fontsize=16, weight='bold')
        
        # 添加图例
        self._add_legends(fig, ax, max_interaction_abs, max_importance_abs, 
                         data_min, data_max, node_marker, 
                         cmap_edges, norm_edges, cmap_nodes, norm_nodes)
        
        # 保存
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
        print(f"✅ 相关性网络图已保存至: {save_path}")

    def _add_legends(self, fig, ax, max_interaction_abs, max_importance_abs, 
                    data_min, data_max, node_marker, 
                    cmap_edges, norm_edges, cmap_nodes, norm_nodes):
        """添加图例"""
        from matplotlib.lines import Line2D
        
        # 线粗细图例
        line_levels = [max_interaction_abs, max_interaction_abs * 0.5, max_interaction_abs * 0.1]
        line_labels = [f"{val:.2f}" for val in line_levels]
        legend_lines = []
        for val in line_levels:
            w = 0.5 + (val / max_interaction_abs) * 8
            legend_lines.append(Line2D([0], [0], color='black', linewidth=w, linestyle='-'))
        
        legend1 = ax.legend(legend_lines, line_labels, loc='center left',
                           bbox_to_anchor=(-0.1, 0.8),
                           title="Feature Correlation\n(Line Width)",
                           title_fontproperties={'weight': 'bold'},
                           frameon=False, labelspacing=1.5)
        ax.add_artist(legend1)
        
        # 显著性图例
        legend_sig_lines = [
            Line2D([0], [0], color='black', linewidth=2, linestyle='-', label='P < 0.05'),
            Line2D([0], [0], color='black', linewidth=2, linestyle='--', label='P ≥ 0.05')
        ]
        legend2 = ax.legend(handles=legend_sig_lines, loc='center left',
                           bbox_to_anchor=(-0.1, 0.6),
                           title="Significance\n(Line Style)",
                           title_fontproperties={'weight': 'bold'},
                           frameon=False, labelspacing=1.5)
        ax.add_artist(legend2)
        
        # 节点大小图例
        legend_vals = [data_max, (data_max + data_min) / 2, data_min]
        node_labels = [f"{val:.2f}" for val in legend_vals]
        legend_nodes = []
        
        # 定义节点大小常量
        NODE_SIZE_MIN = 300
        NODE_SIZE_MAX = 1000
        
        def map_size(value):
            if data_max == data_min:
                return NODE_SIZE_MAX
            return NODE_SIZE_MIN + (value - data_min) / (data_max - data_min) * (NODE_SIZE_MAX - NODE_SIZE_MIN)
        
        for val in legend_vals:
            area_size = map_size(val)
            diameter_size = np.sqrt(area_size)
            legend_nodes.append(Line2D([0], [0], marker=node_marker, color='w',
                                      markerfacecolor='black', markersize=diameter_size,
                                      linestyle='None'))
        
        legend3 = ax.legend(legend_nodes, node_labels, loc='center left',
                           bbox_to_anchor=(-0.1, 0.36),
                           title="Target Correlation\n(Node Size)",
                           title_fontproperties={'weight': 'bold'},
                           frameon=False, labelspacing=2.5)
        ax.add_artist(legend3)
        
        # 节点显著性图例
        legend_sig_nodes = [
            Line2D([0], [0], marker=node_marker, color='w', markerfacecolor='white',
                   markeredgecolor='black', markeredgewidth=2, markersize=10, label='P < 0.05'),
            Line2D([0], [0], marker=node_marker, color='w', markerfacecolor='white',
                   markeredgecolor='grey', markeredgewidth=0.5, markersize=10, label='P ≥ 0.05')
        ]
        legend4 = ax.legend(handles=legend_sig_nodes, loc='center left',
                           bbox_to_anchor=(-0.1, 0.15),
                           title="Node Significance",
                           title_fontproperties={'weight': 'bold'},
                           frameon=False, labelspacing=1.5)
        ax.add_artist(legend4)
        
        # 颜色条
        cbar_edge_pos = [0.82, 0.55, 0.015, 0.25]
        cax_edge = fig.add_axes(cbar_edge_pos)
        sm_edge = plt.cm.ScalarMappable(cmap=cmap_edges, norm=norm_edges)
        sm_edge.set_array([])
        cbar_edge = plt.colorbar(sm_edge, cax=cax_edge)
        cbar_edge.set_label('Interaction Value (Signed)', rotation=270, 
                           labelpad=15, fontsize=10, weight='bold')
        cbar_edge.outline.set_visible(False)
        
        cbar_node_pos = [0.82, 0.20, 0.015, 0.25]
        cax_node = fig.add_axes(cbar_node_pos)
        sm_node = plt.cm.ScalarMappable(cmap=cmap_nodes, norm=norm_nodes)
        sm_node.set_array([])
        cbar_node = plt.colorbar(sm_node, cax=cax_node)
        cbar_node.set_label('Feature Value (Signed)', rotation=270,
                           labelpad=15, fontsize=10, weight='bold')
        cbar_node.outline.set_visible(False)

    def export_correlation_matrix(self, output_path: str = "correlation_matrix.csv"):
        """
        导出相关性矩阵
        
        Args:
            output_path: 输出文件路径
        """
        if self.correlation_matrix is None:
            print("⚠️  请先调用 calculate_correlation() 方法")
            return
        
        # 使用相关性矩阵的实际维度来获取特征列表
        n_features = self.correlation_matrix.shape[0]
        all_numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        features = all_numeric_cols[:n_features]
        
        df_corr = pd.DataFrame(self.correlation_matrix, 
                              index=features, 
                              columns=features)
        df_corr.to_csv(output_path, encoding='utf-8-sig')
        print(f"✅ 相关性矩阵已导出至: {output_path}")

    def get_top_correlations(self, n: int = 10) -> pd.DataFrame:
        """
        获取相关性最强的特征对
        
        Args:
            n: 返回前n对
        
        Returns:
            包含特征对及其相关性的DataFrame
        """
        if self.correlation_matrix is None:
            self.calculate_correlation()
        
        # 使用相关性矩阵的实际维度
        n_features = self.correlation_matrix.shape[0]
        features = self.data.select_dtypes(include=[np.number]).columns.tolist()[:n_features]
        
        correlations = []
        
        for i in range(n_features):
            for j in range(i + 1, n_features):
                r = self.correlation_matrix[i, j]
                p = self.p_value_matrix[i, j]
                correlations.append({
                    '特征1': features[i],
                    '特征2': features[j],
                    '相关系数': r,
                    'P值': p,
                    '显著性': '显著' if p < 0.05 else '不显著'
                })
        
        df_corr = pd.DataFrame(correlations)
        df_corr['绝对相关系数'] = df_corr['相关系数'].abs()
        df_corr = df_corr.sort_values('绝对相关系数', ascending=False)
        
        return df_corr.head(n)
