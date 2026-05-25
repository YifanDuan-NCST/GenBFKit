"""
高炉数据字典 桑葚图（Sankey）绘制脚本

数据流向：Work type → Data category（中文）→ 数据池（中文）
- 默认读取同目录下的 bf_sankey.csv 进行绘图。
- 若传入 --from-json，则先从 prebuilt_full.json 生成 bf_sankey.csv 再绘图。

用法：
  python sankey.py                    # 使用已有 bf_sankey.csv 绘图
  python sankey.py --from-json        # 从上一级目录的 prebuilt_full.json 生成 CSV 后绘图
  python sankey.py --from-json path/to/prebuilt_full.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd

# 脚本所在目录（graph/），保证 CSV/HTML/PNG 输出在同一目录
SCRIPT_DIR = Path(__file__).resolve().parent


def ensure_csv_from_json(json_path: Path | None = None) -> Path:
    """若需要从 JSON 生成 CSV，则调用 build_sankey_data 并返回 CSV 路径。"""
    from build_sankey_data import (
        DEFAULT_JSON_PATH,
        load_prebuilt,
        build_sankey_links,
        write_csv,
    )
    jpath = json_path or DEFAULT_JSON_PATH
    if not jpath.exists():
        raise FileNotFoundError(f"未找到全量数据文件: {jpath}")
    data = load_prebuilt(jpath)
    rows = build_sankey_links(data, jpath)
    csv_path = SCRIPT_DIR / "bf_sankey.csv"
    write_csv(rows, csv_path)
    print(f"已从 {jpath} 生成 {csv_path}（共 {len(rows)} 条链路）")
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="高炉数据字典 桑葚图")
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="先从 prebuilt_full.json 生成 bf_sankey.csv 再绘图",
    )
    parser.add_argument(
        "--json-path",
        default=None,
        metavar="PATH",
        help="全量 JSON 路径（仅在与 --from-json 同时使用时生效，默认使用上一级目录的 prebuilt_full.json）",
    )
    args = parser.parse_args()

    # 工作目录切到脚本目录，便于读写 bf_sankey.csv
    import os
    os.chdir(SCRIPT_DIR)

    if args.from_json:
        json_path = Path(args.json_path).resolve() if args.json_path else None
        csv_path = ensure_csv_from_json(json_path)
    else:
        csv_path = SCRIPT_DIR / "bf_sankey.csv"

    if not csv_path.exists():
        print("未找到 bf_sankey.csv。请先运行: python build_sankey_data.py")
        sys.exit(1)

    # ---------------------- 1. 读取 CSV（统一 UTF-8，避免中文乱码）----------------------
    df = pd.read_csv(csv_path, encoding="utf-8")

    # ---------------------- 2. 节点与链路 ----------------------
    all_nodes = pd.concat([df["source"], df["target"]]).unique()
    node_dict = {node: idx for idx, node in enumerate(all_nodes)}

    link_source = [node_dict[src] for src in df["source"]]
    link_target = [node_dict[tgt] for tgt in df["target"]]
    link_value = df["value"].tolist()

    # ---------------------- 3. 桑葚图 ----------------------
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_nodes,
                    color="#69b3a2",
                ),
                link=dict(
                    source=link_source,
                    target=link_target,
                    value=link_value,
                    color="rgba(105, 179, 162, 0.3)",
                ),
            )
        ]
    )

    fig.update_layout(
        title_text="Blast Furnace Data Dictionary Sankey Diagram: Work type -> Category -> Pool -> Dataset",
        font_size=10,
        width=1600,
        height=900,
        title_x=0.5,
    )

    # ---------------------- 4. 输出 ----------------------
    html_path = SCRIPT_DIR / "高炉数据池桑葚图.html"
    png_path = SCRIPT_DIR / "高炉数据池桑葚图.png"

    fig.write_html(str(html_path))
    print(f"已保存: {html_path}")

    try:
        fig.write_image(str(png_path), scale=2)
        print(f"已保存: {png_path}")
    except Exception as e:
        print(f"PNG 导出跳过（需安装 kaleido: pip install kaleido）: {e}")

    fig.show()


if __name__ == "__main__":
    main()
