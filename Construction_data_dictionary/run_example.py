from __future__ import annotations

import json
from pathlib import Path
import sys

# Allow running as a plain script: python Construction_data_dictionary/run_example.py
_pkg_dir = Path(__file__).resolve().parent
_project_root = _pkg_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from Construction_data_dictionary import DictionaryManager  # noqa: E402


def main() -> None:
    project_root = _project_root
    mgr = DictionaryManager()
    counts = mgr.load_from_project_root(project_root, overwrite=True)

    print("Loaded dictionaries from:", project_root)
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    print()

    # Show actual in-memory sizes (these are what you really "loaded")
    sizes = {
        "base_dictionary(work_types)": len(mgr.base_dict.list_all()),
        "data_category_dictionary(items)": len(mgr.category_dict.list_all()),
        "data_pool_dictionary(items)": len(mgr.pool_dict.list_all()),
        "data_pool_dictionary(pool_types)": len(mgr.pool_dict.list_pool_types()),
        "dataset_dictionary(items)": len(mgr.dataset_dict.list_all()),
        "data_attribute_dictionary(pool_types)": mgr.attr_dict.count_pool_types(),
        "data_attribute_dictionary(unique_fields)": mgr.attr_dict.count_unique_attribute_fields(),
    }
    print("In-memory sizes:")
    print(json.dumps(sizes, ensure_ascii=False, indent=2))
    print()

    work_types = mgr.get_work_types()
    print("Work types:", work_types)
    print()

    # show one worktype chain
    wt = work_types[0] if work_types else "Slag treating"
    chain = mgr.get_full_data_chain(wt, include_attributes=True)
    print(f"Sample chain for work_type={wt!r}:")
    # Console output is intentionally truncated to avoid flooding the terminal.
    print(json.dumps(chain, ensure_ascii=False, indent=2)[:4000])
    print()

    out_path = _pkg_dir / f"sample_chain_{wt.replace(' ', '_')}.json"
    out_path.write_text(json.dumps(chain, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote full chain JSON to:", out_path)


if __name__ == "__main__":
    main()

