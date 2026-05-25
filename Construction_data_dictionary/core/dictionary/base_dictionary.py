from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .registry import Registry, normalize_text


@dataclass(frozen=True)
class WorkType:
    work_type_en: str
    work_type_zh: str = ""
    no: Optional[int] = None


class BaseDictionary:
    """
    WorkType dictionary.
    Source (example): base_dictionary.xlsx
    Columns: No., Chinese_name, Work type
    """

    def __init__(self) -> None:
        self.registry: Registry[str, WorkType] = Registry(
            name="base_dictionary(work_type)",
            key_fn=lambda w: normalize_text(w.work_type_en),
        )

    # ---- CRUD
    def add(self, work_type_en: str, *, work_type_zh: str = "", no: Optional[int] = None, overwrite: bool = False) -> str:
        item = WorkType(work_type_en=normalize_text(work_type_en), work_type_zh=normalize_text(work_type_zh), no=no)
        return self.registry.add(item, overwrite=overwrite)

    def get(self, work_type_en: str) -> WorkType:
        return self.registry.get(normalize_text(work_type_en))

    def exists(self, work_type_en: str) -> bool:
        """Check if a work type exists."""
        return self.registry.exists(normalize_text(work_type_en))

    def update(self, work_type_en: str, *, work_type_zh: Optional[str] = None, no: Optional[int] = None) -> None:
        key = normalize_text(work_type_en)
        old = self.registry.get(key)
        self.registry.update(
            key,
            WorkType(
                work_type_en=old.work_type_en,
                work_type_zh=old.work_type_zh if work_type_zh is None else normalize_text(work_type_zh),
                no=old.no if no is None else no,
            ),
        )

    def delete(self, work_type_en: str) -> None:
        self.registry.delete(normalize_text(work_type_en))

    def list_all(self) -> List[WorkType]:
        return self.registry.values()

    # ---- IO
    def load_from_excel(self, path: str | Path, *, sheet_name: str = "Sheet1", overwrite: bool = True) -> int:
        # Excel structure: Row1=title, Row2=description, Row3=headers, Row4=header descriptions, Row5+=data
        # Use header=2 to set row3 as column names, skiprows=[3] to skip row4 (description row)
        df = pd.read_excel(Path(path), sheet_name=sheet_name, header=2, skiprows=[3])
        df = df.rename(columns={c: normalize_text(c) for c in df.columns})
        # Skip empty columns
        df = df.dropna(axis=1, how='all')
        # tolerate multiple common headers
        col_no = next((c for c in df.columns if c.lower() in {"no.", "no", "编号"}), None)
        col_zh = next((c for c in df.columns if "中文" in c or c.lower() in {"chinese_name", "chinese"}), None)
        col_en = next((c for c in df.columns if c.lower() in {"work type", "work_type", "worktype"}), None)
        if col_en is None:
            raise ValueError("base_dictionary: missing 'Work type' column")

        items: List[WorkType] = []
        for _, r in df.iterrows():
            en = normalize_text(r.get(col_en))
            if not en:
                continue
            zh = normalize_text(r.get(col_zh)) if col_zh else ""
            no_val = r.get(col_no) if col_no else None
            try:
                no_int = int(no_val) if no_val is not None and str(no_val) != "nan" else None
            except Exception:
                no_int = None
            items.append(WorkType(work_type_en=en, work_type_zh=zh, no=no_int))

        return self.registry.add_many(items, overwrite=overwrite)

    def save_json(self, path: str | Path) -> None:
        self.registry.save_json(path)

