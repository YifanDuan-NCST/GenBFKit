import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def create_binary_heatmap(excel_input_path, pdf_output_path, svg_output_path):
    """
    修复边框问题：通过网格实现小方块细边框，优化外围边框和刻度线，隐藏坐标名称
    横轴：datapool类型，纵轴：id，尺寸：宽4.1cm，高11.9cm，字体Arial
    """
    # 1. 基础配置
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    # 图形尺寸（厘米转英寸，matplotlib默认单位）
    width_cm = 4.1
    height_cm = 11.9
    width_in = width_cm / 2.54
    height_in = height_cm / 2.54

    # 2. 读取并处理数据
    df = pd.read_excel(excel_input_path)
    y_labels = df['id'].values  # 纵轴：id列表
    x_labels = df.columns[1:].tolist()  # 横轴：datapool类型列表
    data = df.iloc[:, 1:].values  # 0/1数据矩阵（行数=id数，列数=datapool类型数）
    n_rows, n_cols = data.shape  # 获取数据矩阵的行数和列数

    # 3. 创建图形与基础热力图（无额外参数，避免参数错误）
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    cmap = ListedColormap(['#e74c3c', '#3498db'])  # 0=红色，1=蓝色
    im = ax.imshow(data, cmap=cmap, aspect='auto')  # 仅传递基础参数

    # 4. 关键修复：添加小方块细边框（通过网格实现）
    # 网格线位置：在每个小方块的边界（x从-0.5到n_cols-0.5，y从-0.5到n_rows-0.5）
    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    # 配置网格（小方块边框）：细线条、黑色、只显示次网格
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.2)
    # 隐藏主网格（避免干扰）
    ax.grid(which='major', visible=False)

    # 5. 配置坐标轴与刻度
    # 设置主刻度（对应datapool类型和id）
    # ax.set_xticks(np.arange(n_cols))
    # ax.set_yticks(np.arange(n_rows))
    # ax.set_xticklabels(x_labels, fontsize=6)  # 横轴刻度标签（datapool类型）
    # ax.set_yticklabels(y_labels, fontsize=6)  # 纵轴刻度标签（id）
    # 旋转横轴标签，避免文字重叠
    # plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

    # 6. 调整外围边框（比内部小方块边框更细）
    for spine in ax.spines.values():
        spine.set_linewidth(0.1)  # 外围边框粗细（0.2，小于内部0.5）
        spine.set_color('black')  # 边框颜色

    # 7. 调整刻度线（细线条，避免视觉干扰）
    ax.tick_params(
        axis='both',
        which='major',
        width=0.1,  # 刻度线粗细
        length=1,   # 刻度线长度（可按需调整）
        # pad=2       # 刻度标签与刻度线的距离，避免拥挤
    )

    # 8. 隐藏坐标名称（不设置xlabel和ylabel即可）
    # 不添加 ax.set_xlabel() 和 ax.set_ylabel()，完全隐藏坐标名称

    # 9. 优化布局与保存文件（矢量格式保证边框清晰度）
    plt.tight_layout()
    plt.savefig(pdf_output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(svg_output_path, format='svg', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"热力图生成完成！")
    print(f"PDF文件路径：{pdf_output_path}")
    print(f"SVG文件路径：{svg_output_path}")

# ------------------- 程序调用入口 -------------------
if __name__ == "__main__":
    # 请根据你的文件实际路径修改以下参数
    INPUT_EXCEL = "data.xlsx"  # 输入Excel文件路径
    OUTPUT_PDF = "heatmap_with_border.pdf"  # 输出PDF路径
    OUTPUT_SVG = "heatmap_with_border.svg"  # 输出SVG路径

    create_binary_heatmap(INPUT_EXCEL, OUTPUT_PDF, OUTPUT_SVG)