from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .registry import Registry, compact_key, normalize_text


@dataclass(frozen=True)
class DatasetItem:
    work_type_en: str
    category_en: str
    pool_en: str
    dataset_en: str
    dataset_zh: str = ""  # may be blank if not provided
    dataset_zh_short: str = ""  # some templates include a short Chinese label column


class DatasetDictionary:
    """
    Dataset dictionary.
    Source (example): dataset_dictionary.xlsx / dataset_dictionary - 示例.xlsx

    Typical columns:
      - Work type
      - data category
      - data pool
      - dataset (English parameter name)
      - optional Chinese columns for category/pool/dataset.
    """

    def __init__(self) -> None:
        self.registry: Registry[str, DatasetItem] = Registry(
            name="dataset_dictionary(pool->dataset)",
            key_fn=lambda d: compact_key(d.work_type_en, d.category_en, d.pool_en, d.dataset_en),
        )

    # ---- CRUD
    def add(
        self,
        work_type_en: str,
        category_en: str,
        pool_en: str,
        dataset_en: str,
        *,
        dataset_zh: str = "",
        dataset_zh_short: str = "",
        overwrite: bool = False,
    ) -> str:
        item = DatasetItem(
            work_type_en=normalize_text(work_type_en),
            category_en=normalize_text(category_en),
            pool_en=normalize_text(pool_en),
            dataset_en=normalize_text(dataset_en),
            dataset_zh=normalize_text(dataset_zh),
            dataset_zh_short=normalize_text(dataset_zh_short),
        )
        return self.registry.add(item, overwrite=overwrite)

    def get(self, work_type_en: str, category_en: str, pool_en: str, dataset_en: str) -> DatasetItem:
        return self.registry.get(compact_key(work_type_en, category_en, pool_en, dataset_en))

    def try_get(self, work_type_en: str, category_en: str, pool_en: str, dataset_en: str) -> Optional[DatasetItem]:
        """Best-effort get that returns None instead of raising."""
        return self.registry.try_get(compact_key(work_type_en, category_en, pool_en, dataset_en))

    def exists(self, work_type_en: str, category_en: str, pool_en: str, dataset_en: str) -> bool:
        """Check if a dataset entry exists."""
        return self.registry.exists(compact_key(work_type_en, category_en, pool_en, dataset_en))

    def update(
        self,
        work_type_en: str,
        category_en: str,
        pool_en: str,
        dataset_en: str,
        *,
        dataset_zh: Optional[str] = None,
        dataset_zh_short: Optional[str] = None,
    ) -> None:
        key = compact_key(work_type_en, category_en, pool_en, dataset_en)
        old = self.registry.get(key)
        self.registry.update(
            key,
            DatasetItem(
                work_type_en=old.work_type_en,
                category_en=old.category_en,
                pool_en=old.pool_en,
                dataset_en=old.dataset_en,
                dataset_zh=old.dataset_zh if dataset_zh is None else normalize_text(dataset_zh),
                dataset_zh_short=old.dataset_zh_short if dataset_zh_short is None else normalize_text(dataset_zh_short),
            ),
        )

    def delete(self, work_type_en: str, category_en: str, pool_en: str, dataset_en: str) -> None:
        self.registry.delete(compact_key(work_type_en, category_en, pool_en, dataset_en))

    def list_all(self) -> List[DatasetItem]:
        return self.registry.values()

    def list_by_pool(self, work_type_en: str, category_en: str, pool_en: str) -> List[DatasetItem]:
        wt = normalize_text(work_type_en)
        cat = normalize_text(category_en)
        pool = normalize_text(pool_en)
        return self.registry.find(predicate=lambda d: d.work_type_en == wt and d.category_en == cat and d.pool_en == pool)

    def list_pools_by_category(self, work_type_en: str, category_en: str) -> List[str]:
        """List unique pool types used under (work_type, category)."""
        wt = normalize_text(work_type_en)
        cat = normalize_text(category_en)
        pools = {d.pool_en for d in self.registry.values() if d.work_type_en == wt and d.category_en == cat and d.pool_en}
        return sorted(pools)

    # ---- IO
    def load_from_excel(self, path: str | Path, *, sheet_name: str = "Sheet1", overwrite: bool = True) -> int:
        # Excel structure: Row1=title, Row2=description, Row3=headers, Row4=header descriptions, Row5+=data
        # Use header=2 to set row3 as column names, skiprows=[3] to skip row4 (description row)
        df = pd.read_excel(Path(path), sheet_name=sheet_name, header=2, skiprows=[3])
        df = df.rename(columns={c: normalize_text(c) for c in df.columns})
        df = df.dropna(axis=1, how='all')  # Remove empty columns

        col_wt = next((c for c in df.columns if normalize_text(c).lower() in {"work type", "work_type", "worktype"}), None)
        col_cat_en = next((c for c in df.columns if normalize_text(c).lower() in {"data category", "data_category"}), None)
        col_pool_en = next((c for c in df.columns if normalize_text(c).lower() in {"data pool", "data_pool"}), None)
        col_dataset_en = next((c for c in df.columns if normalize_text(c).lower() in {"dataset"}), None)

        # Detect Chinese columns by header text patterns
        # Sheet4 columns: Work Type, Data Category, Data Pool, Dataset, Dataset 中文名, Dataset 简称, 备注
        # Chinese name column: looks for "Dataset 中文名"
        col_dataset_zh = next(
            (c for c in df.columns if "dataset" in c.lower() and "中文" in c),
            None
        )
        # Short name column: looks for "Dataset 简称"
        col_dataset_zh_short = next(
            (c for c in df.columns if "dataset" in c.lower() and ("简称" in c or "short" in c.lower())),
            None
        )
        # Fallback: if not found by pattern, look for any Chinese column
        if col_dataset_zh is None:
            col_dataset_zh = next(
                (c for c in df.columns
                 if c not in {col_wt, col_cat_en, col_pool_en, col_dataset_en}
                 and normalize_text(c)
                 and ("中文" in c or "名称" in c or "说明" in c)),
                None
            )
        if col_dataset_zh_short is None:
            col_dataset_zh_short = next(
                (c for c in df.columns
                 if c not in {col_wt, col_cat_en, col_pool_en, col_dataset_en, col_dataset_zh}
                 and normalize_text(c)
                 and ("简称" in c or "short" in c.lower())),
                None
            )

        if col_wt is None or col_cat_en is None or col_pool_en is None or col_dataset_en is None:
            raise ValueError("dataset_dictionary: missing required columns (Work type, data category, data pool, dataset)")

        items: List[DatasetItem] = []
        for _, r in df.iterrows():
            wt = normalize_text(r.get(col_wt))
            cat_en = normalize_text(r.get(col_cat_en))
            pool_en = normalize_text(r.get(col_pool_en))
            dataset_en = normalize_text(r.get(col_dataset_en))
            if not wt or not cat_en or not pool_en or not dataset_en:
                continue
            zh = normalize_text(r.get(col_dataset_zh)) if col_dataset_zh else ""
            zh_short = normalize_text(r.get(col_dataset_zh_short)) if col_dataset_zh_short else ""
            items.append(
                DatasetItem(
                    work_type_en=wt,
                    category_en=cat_en,
                    pool_en=pool_en,
                    dataset_en=dataset_en,
                    dataset_zh=zh,
                    dataset_zh_short=zh_short,
                )
            )

        return self.registry.add_many(items, overwrite=overwrite)

    def save_json(self, path: str | Path) -> None:
        self.registry.save_json(path)

