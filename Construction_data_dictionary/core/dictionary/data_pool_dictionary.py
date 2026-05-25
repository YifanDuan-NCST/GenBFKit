from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .registry import Registry, compact_key, normalize_text


@dataclass(frozen=True)
class DataPool:
    work_type_en: str
    category_en: str
    pool_en: str
    category_zh: str = ""
    pool_zh: str = ""


class DataPoolDictionary:
    """
    Data pool dictionary.
    Source (example): data_pool_dictionary.xlsx
    Columns include:
      - Work type
      - data category
      - data pool
      - plus Chinese columns for category/pool (may appear as mojibake on some systems)
    """

    def __init__(self) -> None:
        self.registry: Registry[str, DataPool] = Registry(
            name="data_pool_dictionary(category->pool)",
            key_fn=lambda p: compact_key(p.work_type_en, p.category_en, p.pool_en),
        )

    # ---- CRUD
    def add(
        self,
        work_type_en: str,
        category_en: str,
        pool_en: str,
        *,
        category_zh: str = "",
        pool_zh: str = "",
        overwrite: bool = False,
    ) -> str:
        item = DataPool(
            work_type_en=normalize_text(work_type_en),
            category_en=normalize_text(category_en),
            pool_en=normalize_text(pool_en),
            category_zh=normalize_text(category_zh),
            pool_zh=normalize_text(pool_zh),
        )
        return self.registry.add(item, overwrite=overwrite)

    def get(self, work_type_en: str, category_en: str, pool_en: str) -> DataPool:
        return self.registry.get(compact_key(work_type_en, category_en, pool_en))

    def update(
        self,
        work_type_en: str,
        category_en: str,
        pool_en: str,
        *,
        category_zh: Optional[str] = None,
        pool_zh: Optional[str] = None,
    ) -> None:
        key = compact_key(work_type_en, category_en, pool_en)
        old = self.registry.get(key)
        self.registry.update(
            key,
            DataPool(
                work_type_en=old.work_type_en,
                category_en=old.category_en,
                pool_en=old.pool_en,
                category_zh=old.category_zh if category_zh is None else normalize_text(category_zh),
                pool_zh=old.pool_zh if pool_zh is None else normalize_text(pool_zh),
            ),
        )

    def try_get(self, work_type_en: str, category_en: str, pool_en: str) -> Optional[DataPool]:
        """Best-effort get that returns None instead of raising."""
        return self.registry.try_get(compact_key(work_type_en, category_en, pool_en))

    def exists(self, work_type_en: str, category_en: str, pool_en: str) -> bool:
        """Check if a pool entry exists."""
        return self.registry.exists(compact_key(work_type_en, category_en, pool_en))

    def delete(self, work_type_en: str, category_en: str, pool_en: str) -> None:
        self.registry.delete(compact_key(work_type_en, category_en, pool_en))

    def list_all(self) -> List[DataPool]:
        return self.registry.values()

    def list_by_category(self, work_type_en: str, category_en: str) -> List[DataPool]:
        wt = normalize_text(work_type_en)
        cat = normalize_text(category_en)
        return self.registry.find(predicate=lambda p: p.work_type_en == wt and p.category_en == cat)

    # ---- Pool-type utilities (global pool type list)
    def add_pool_type(self, pool_en: str, *, pool_zh: str = "", overwrite: bool = False) -> str:
        """
        Add a global pool type (e.g. "Continuous time-series data").

        We store it using empty work_type/category so the key collapses to pool_en only.
        """
        return self.add("", "", pool_en, pool_zh=pool_zh, overwrite=overwrite)

    def get_pool_type(self, pool_en: str) -> DataPool:
        """Get a global pool type item by pool_en."""
        return self.registry.get(compact_key(pool_en))

    def try_get_pool_type(self, pool_en: str) -> Optional[DataPool]:
        """Best-effort get for a global pool type."""
        key = compact_key(pool_en)
        return self.registry.try_get(key)

    def list_pool_types(self) -> List[str]:
        """
        List unique global pool type names (pool_en) that have empty work_type/category keys.

        This returns the 9 base pool types regardless of how they were loaded
        (prebuilt_default or add_pool_type).
        """
        return [
            item.pool_en
            for item in self.registry.values()
            if not item.work_type_en and not item.category_en and item.pool_en
        ]

    # ---- IO
    def load_from_excel(self, path: str | Path, *, sheet_name: str = "Sheet1", overwrite: bool = True) -> int:
        # Excel structure: Row1=title, Row2=description, Row3=headers, Row4=header descriptions, Row5+=data
        # Use header=2 to set row3 as column names, skiprows=[3] to skip row4 (description row)
        df = pd.read_excel(Path(path), sheet_name=sheet_name, header=2, skiprows=[3])
        df = df.rename(columns={c: normalize_text(c) for c in df.columns})
        df = df.dropna(axis=1, how='all')  # Remove empty columns
        # Forward fill merged cells (Work type / data category may be NaN)
        df = df.ffill()

        col_wt = next((c for c in df.columns if normalize_text(c).lower() in {"work type", "work_type", "worktype"}), None)
        col_cat_en = next((c for c in df.columns if normalize_text(c).lower() in {"data category", "data_category"}), None)
        col_pool_en = next((c for c in df.columns if normalize_text(c).lower() in {"data pool", "data_pool"}), None)

        # Detect Chinese columns by header text patterns
        # Sheet3 columns: Work Type, Data Category, Data Pool, Data Pool 中文名, 是否预构建, 备注
        col_pool_zh = next((c for c in df.columns if "data pool" in c.lower() and "中文" in c), None)
        # If not found by pattern, use fallback: look for any Chinese column that's not a key column
        if col_pool_zh is None:
            col_pool_zh = next(
                (c for c in df.columns
                 if c not in {col_wt, col_cat_en, col_pool_en}
                 and normalize_text(c)
                 and ("中文" in c or "名称" in c or "说明" in c)),
                None
            )
        # Category Chinese name is rare in Pool sheet, skip it for now
        col_cat_zh = None

        if col_wt is None or col_cat_en is None or col_pool_en is None:
            raise ValueError("data_pool_dictionary: missing required columns (Work type, data category, data pool)")

        items: List[DataPool] = []
        for _, r in df.iterrows():
            wt = normalize_text(r.get(col_wt))
            cat_en = normalize_text(r.get(col_cat_en))
            pool_en = normalize_text(r.get(col_pool_en))
            if not wt or not cat_en or not pool_en:
                continue
            cat_zh = normalize_text(r.get(col_cat_zh)) if col_cat_zh else ""
            pool_zh = normalize_text(r.get(col_pool_zh)) if col_pool_zh else ""
            items.append(
                DataPool(
                    work_type_en=wt,
                    category_en=cat_en,
                    pool_en=pool_en,
                    category_zh=cat_zh,
                    pool_zh=pool_zh,
                )
            )

        return self.registry.add_many(items, overwrite=overwrite)

    def save_json(self, path: str | Path) -> None:
        self.registry.save_json(path)

