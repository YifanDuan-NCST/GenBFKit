from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .registry import Registry, compact_key, normalize_text


@dataclass(frozen=True)
class AttributeTemplate:
    """
    One attribute template for a pool type.
    Example: pool_type="Continuous time-series data"
    """

    pool_type: str
    attributes: Dict[str, str]  # attribute_id -> attribute_name


class DataAttributeDictionary:
    """
    Data attribute dictionary (template-by-pool-type).

    Source (example): data_attribute_dictionary.xlsx
      - first column: "data pool" (attribute_1, attribute_2, ...)
      - other columns: pool types (Binary status data / Continuous time-series data / ...)
        values are the attribute names used when creating DB columns.
    """

    def __init__(self) -> None:
        self.registry: Registry[str, AttributeTemplate] = Registry(
            name="data_attribute_dictionary(pool_type->attributes)",
            key_fn=lambda t: normalize_text(t.pool_type),
        )

    # ---- CRUD (pool-type level)
    def add_pool_type(self, pool_type: str, *, overwrite: bool = False) -> str:
        pt = normalize_text(pool_type)
        tmpl = AttributeTemplate(pool_type=pt, attributes={})
        return self.registry.add(tmpl, overwrite=overwrite)

    def get_pool_type(self, pool_type: str) -> AttributeTemplate:
        return self.registry.get(normalize_text(pool_type))

    def list_pool_types(self) -> List[str]:
        return self.registry.keys()

    # ---- CRUD (attribute level)
    def set_attribute(self, pool_type: str, attribute_id: str, attribute_name: str) -> None:
        pt = normalize_text(pool_type)
        attr_id = normalize_text(attribute_id)
        attr_name = normalize_text(attribute_name)
        old = self.registry.get(pt)
        new_attrs = dict(old.attributes)
        new_attrs[attr_id] = attr_name
        self.registry.update(pt, AttributeTemplate(pool_type=old.pool_type, attributes=new_attrs))

    def delete_attribute(self, pool_type: str, attribute_id: str) -> None:
        pt = normalize_text(pool_type)
        attr_id = normalize_text(attribute_id)
        old = self.registry.get(pt)
        if attr_id not in old.attributes:
            return
        new_attrs = dict(old.attributes)
        del new_attrs[attr_id]
        self.registry.update(pt, AttributeTemplate(pool_type=old.pool_type, attributes=new_attrs))

    def get_attributes_for_pool_type(self, pool_type: str) -> Dict[str, str]:
        return dict(self.registry.get(normalize_text(pool_type)).attributes)

    def count_unique_attribute_fields(self) -> int:
        """
        Count unique attribute field names across all pool types.

        In the Excel template, attribute_id (attribute_1..) are stable, while the
        *field names* (cell values) can differ by pool type. This returns the
        number of distinct non-empty field names across all templates.
        """
        values = set()
        for pt in self.registry.values():
            for v in pt.attributes.values():
                s = normalize_text(v)
                if s:
                    values.add(s)
        return len(values)

    def count_pool_types(self) -> int:
        """Return the number of registered pool types (i.e. attribute templates)."""
        return len(self.registry)

    # ---- IO
    def load_from_excel(self, path: str | Path, *, sheet_name: str = "Sheet1", overwrite: bool = True) -> int:
        # Excel structure: Row1=title, Row2=description, Row3=headers, Row4=header descriptions, Row5+=data
        # Use header=2 to set row3 as column names, skiprows=[3] to skip row4 (description row)
        df = pd.read_excel(Path(path), sheet_name=sheet_name, header=2, skiprows=[3])
        df = df.rename(columns={c: normalize_text(c) for c in df.columns})
        df = df.dropna(axis=1, how='all')  # Remove empty columns

        # Detect columns by header text patterns
        # Sheet5 columns: Data Pool, Attribute ID, Attribute Name, Attribute Name 中文名, Attribute Description, 备注
        col_pool = next((c for c in df.columns if "data pool" in c.lower() or "pool" in c.lower()), None)
        col_attr_id = next((c for c in df.columns if "attribute" in c.lower() and "id" in c.lower()), None)
        col_attr_name = next((c for c in df.columns if "attribute" in c.lower() and "name" in c.lower() and "中文" not in c), None)
        col_attr_name_zh = next((c for c in df.columns if "attribute" in c.lower() and "中文" in c), None)

        if col_pool is None or col_attr_id is None:
            raise ValueError("data_attribute_dictionary: missing required columns (Data Pool, Attribute ID)")

        # Group by pool type and collect attributes
        pool_attrs: Dict[str, Dict[str, str]] = {}
        for _, r in df.iterrows():
            pool_type = normalize_text(r.get(col_pool))
            attr_id = normalize_text(r.get(col_attr_id))
            if not pool_type or not attr_id:
                continue

            if pool_type not in pool_attrs:
                pool_attrs[pool_type] = {}

            # Use English name as attribute value (Attribute Name column), Chinese name as reference
            attr_name = ""
            if col_attr_name:
                attr_name = normalize_text(r.get(col_attr_name)) or ""
            # Chinese name is for reference only, not used as attribute value
            # if col_attr_name_zh:
            #     attr_name_zh = normalize_text(r.get(col_attr_name_zh)) or ""

            if attr_name:
                pool_attrs[pool_type][attr_id] = attr_name

        # Create attribute templates
        templates: List[AttributeTemplate] = []
        for pool_type, attrs in pool_attrs.items():
            if attrs:
                templates.append(AttributeTemplate(pool_type=pool_type, attributes=attrs))

        return self.registry.add_many(templates, overwrite=overwrite)

    def save_json(self, path: str | Path) -> None:
        self.registry.save_json(path)

