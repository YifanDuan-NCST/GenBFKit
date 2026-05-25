from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .registry import Registry, compact_key, normalize_text


@dataclass(frozen=True)
class DataCategory:
    work_type_en: str
    category_en: str
    category_zh: str = ""


class DataCategoryDictionary:
    """
    Data category dictionary.
    Source (example): data_category_dictionary.xlsx
    Columns include:
      - Work type
      - 中文字段（工艺系统-下属设备-功能）
      - Data category(Process system - Subordinate equipment - function)
    """

    def __init__(self) -> None:
        self.registry: Registry[str, DataCategory] = Registry(
            name="data_category_dictionary(work_type->category)",
            key_fn=lambda c: compact_key(c.work_type_en, c.category_en),
        )

    # ---- CRUD
    def add(self, work_type_en: str, category_en: str, *, category_zh: str = "", overwrite: bool = False) -> str:
        item = DataCategory(
            work_type_en=normalize_text(work_type_en),
            category_en=normalize_text(category_en),
            category_zh=normalize_text(category_zh),
        )
        return self.registry.add(item, overwrite=overwrite)

    def get(self, work_type_en: str, category_en: str) -> DataCategory:
        return self.registry.get(compact_key(work_type_en, category_en))

    def exists(self, work_type_en: str, category_en: str) -> bool:
        """Check if a category exists under the given work type."""
        return self.registry.exists(compact_key(work_type_en, category_en))

    def update(
        self,
        work_type_en: str,
        category_en: str,
        *,
        category_zh: Optional[str] = None,
    ) -> None:
        key = compact_key(work_type_en, category_en)
        old = self.registry.get(key)
        self.registry.update(
            key,
            DataCategory(
                work_type_en=old.work_type_en,
                category_en=old.category_en,
                category_zh=old.category_zh if category_zh is None else normalize_text(category_zh),
            ),
        )

    def delete(self, work_type_en: str, category_en: str) -> None:
        self.registry.delete(compact_key(work_type_en, category_en))

    def list_all(self) -> List[DataCategory]:
        return self.registry.values()

    def list_by_work_type(self, work_type_en: str) -> List[DataCategory]:
        wt = normalize_text(work_type_en)
        return self.registry.find(predicate=lambda c: c.work_type_en == wt)

    # ---- IO
    def load_from_excel(self, path: str | Path, *, sheet_name: str = "Sheet1", overwrite: bool = True) -> int:
        # Excel structure: Row1=title, Row2=description, Row3=headers, Row4=header descriptions, Row5+=data
        # Use header=2 to set row3 as column names, skiprows=[3] to skip row4 (description row)
        df = pd.read_excel(Path(path), sheet_name=sheet_name, header=2, skiprows=[3])
        df = df.rename(columns={c: normalize_text(c) for c in df.columns})
        df = df.dropna(axis=1, how='all')  # Remove empty columns

        col_wt = next((c for c in df.columns if normalize_text(c).lower() in {"work type", "work_type", "worktype"}), None)
        col_en = next((c for c in df.columns if "data category" in c or normalize_text(c).lower() in {"data category", "data_category"}), None)
        col_zh = next((c for c in df.columns if "中文" in c or c.lower() in {"chinese_name", "chinese", "zh"}), None)

        if col_wt is None or col_en is None:
            raise ValueError("data_category_dictionary: missing required columns (Work type, Data category)")

        items: List[DataCategory] = []
        for _, r in df.iterrows():
            wt = normalize_text(r.get(col_wt))
            en = normalize_text(r.get(col_en))
            if not wt or not en:
                continue
            zh = normalize_text(r.get(col_zh)) if col_zh else ""
            items.append(DataCategory(work_type_en=wt, category_en=en, category_zh=zh))

        return self.registry.add_many(items, overwrite=overwrite)

    def save_json(self, path: str | Path) -> None:
        self.registry.save_json(path)

