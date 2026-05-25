import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import re

# Basic Configuration (Arial Font)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.rcParams['figure.facecolor'] = 'white'

# Figure size adapted for 90-degree rotation
fig, ax = plt.subplots(1, 1, figsize=(8, 18))

# Article file path configuration
article_files = {
    "Article 1": "data/data_Article_1.xlsx",
    "Article 2": "data/data_Article_2.xlsx",
    "Article 3": "data/data_Article_3.xlsx"
}

def read_single_column_params_with_order(file_path):
    """
    Read single column parameters from Excel file, remove duplicates while keeping the original order.
    :param file_path: Path of the Excel file
    :return: Unique parameters list with original order
    """
    try:
        df = pd.read_excel(file_path)
        if df.shape[1] != 1:
            print(f"⚠️ File {file_path} has {df.shape[1]} columns. Will read the first column automatically.")

        param_col = df.iloc[:, 0]
        raw_params = param_col.dropna().tolist()

        cleaned_params = []
        for param in raw_params:
            if isinstance(param, str) and param.strip() not in ['', '-', '—', 'NA', 'nan']:
                cleaned_param = re.sub(r'\s+', ' ', param.strip())
                cleaned_param = re.sub(r'[^\w\s\u4e00-\u9fa5./-]', '', cleaned_param)
                cleaned_params.append(cleaned_param)

        seen = set()
        ordered_unique_params = []
        for param in cleaned_params:
            if param not in seen:
                seen.add(param)
                ordered_unique_params.append(param)

        print(f"✅ Successfully read {file_path}: {len(ordered_unique_params)} valid parameters.")
        return ordered_unique_params

    except Exception as e:
        print(f"❌ Failed to read {file_path}: {str(e)}")
        print("Solutions: 1. Close the Excel file 2. Ensure format is .xlsx 3. Check file has data")
        exit()

# Batch read parameters for all articles
all_article_params = {}
for article_name, file_path in article_files.items():
    all_article_params[article_name] = read_single_column_params_with_order(file_path)

articles_list = list(all_article_params.keys())
article_count = len(articles_list)

# Global parameters deduplication with original order
global_raw_params = []
for article_params in all_article_params.values():
    global_raw_params.extend(article_params)

global_seen = set()
global_ordered_unique_params = []
for param in global_raw_params:
    if param not in global_seen:
        global_seen.add(param)
        global_ordered_unique_params.append(param)

# Classify parameters by category with original order
param_belong_articles = {}
for param in global_ordered_unique_params:
    belong_articles = [art for art in articles_list if param in all_article_params[art]]
    param_belong_articles[param] = set(belong_articles)

# Define 6 parameter categories
categories = [
    ("article1_only", {"Article 1"}),
    ("article1_2_share", {"Article 1", "Article 2"}),
    ("article2_only", {"Article 2"}),
    ("article2_3_share", {"Article 2", "Article 3"}),
    ("article3_only", {"Article 3"}),
    ("all_3_share", {"Article 1", "Article 2", "Article 3"})
]

# Initialize category lists
article1_only = []
article1_2_share = []
article2_only = []
article2_3_share = []
article3_only = []
all_3_share = []

# Classify parameters into corresponding categories
for param in global_ordered_unique_params:
    belong_set = param_belong_articles[param]
    if belong_set == categories[0][1]:
        article1_only.append(param)
    elif belong_set == categories[1][1]:
        article1_2_share.append(param)
    elif belong_set == categories[2][1]:
        article2_only.append(param)
    elif belong_set == categories[3][1]:
        article2_3_share.append(param)
    elif belong_set == categories[4][1]:
        article3_only.append(param)
    elif belong_set == categories[5][1]:
        all_3_share.append(param)

# Concatenate sorted parameters list
sorted_params = article1_only + article1_2_share + article2_only + article2_3_share + article3_only + all_3_share
total_params = len(sorted_params)

# Print category statistics
print(f"\n📊 Global Stats: {total_params} unique parameters across 3 articles")
print(f"   - Article 1 only: {len(article1_only)}")
print(f"   - Article 1 & 2 share: {len(article1_2_share)}")
print(f"   - Article 2 only: {len(article2_only)}")
print(f"   - Article 2 & 3 share: {len(article2_3_share)}")
print(f"   - Article 3 only: {len(article3_only)}")
print(f"   - All 3 articles share: {len(all_3_share)}")

# Category color mapping (independent color for Article2/3 only)
category_color_dict = {
    frozenset({"Article 1"}): 1,
    frozenset({"Article 2"}): 2,
    frozenset({"Article 3"}): 3,
    frozenset({"Article 1", "Article 2"}): 4,
    frozenset({"Article 2", "Article 3"}): 5,
    frozenset({"Article 1", "Article 2", "Article 3"}): 6,
    "not_present": 0
}

# Discrete color list (7 colors for 7 categories, index 0-6)
colors = [
    '#F5F5F5',  # 0: Not present (light gray)
    '#1B4F93',  # 1: Article1 only (dark blue)
    '#FCF54C',  # 2: Article2 only (bright yellow)
    '#B39DDB',  # 3: Article3 only (light purple)
    '#F5A89A',  # 4: Article1 & 2 share (light red)
    '#67BF7F',  # 5: Article2 & 3 share (light green)
    '#8B0016'   # 6: All 3 articles share (dark red)
]
cmap = ListedColormap(colors)

# Build multi-category heatmap matrix
heatmap_matrix = np.zeros((total_params, article_count), dtype=int)
for i, param in enumerate(sorted_params):
    belong_set = param_belong_articles[param]
    for j, article in enumerate(articles_list):
        if param in all_article_params[article]:
            heatmap_matrix[i, j] = category_color_dict[frozenset(belong_set)]
        else:
            heatmap_matrix[i, j] = category_color_dict["not_present"]

# Plot heatmap (90-degree rotation layout)
im = ax.imshow(heatmap_matrix, cmap=cmap, aspect='auto')

# X-axis configuration (Article labels, no bold, center alignment)
ax.set_xticks(range(article_count))
article_labels = [f'Article {i + 1}' for i, art in enumerate(articles_list)]
ax.set_xticklabels(
    article_labels,
    fontsize=8,
    ha='center',
    va='top',
    fontfamily='Arial'
)
ax.xaxis.set_ticks_position('bottom')

# Y-axis configuration (Parameter labels, no bold)
ax.set_yticks(range(total_params))
ax.set_yticklabels(
    sorted_params,
    fontsize=8,
    rotation=0,
    ha='right',
    fontfamily='Arial'
)

# Grid configuration
ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#CCCCCC')

# Save as PNG and SVG format
png_save_path = 'Parameter_Heatmap_MultiColor.png'
svg_save_path = 'Parameter_Heatmap_MultiColor.svg'
plt.tight_layout()
plt.savefig(png_save_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig(svg_save_path, format='svg', bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()

print(f"\n🎉 Heatmap generated successfully!")
print(f"   - PNG saved to: {png_save_path}")
print(f"   - SVG saved to: {svg_save_path}")