import json
import re

# Simulate the exact name generation logic from dynamic_tables.py
RESERVED_WORDS = {
    "all", "analyse", "analyze", "and", "any", "array", "as", "asc",
    "asymmetric", "authorization", "between", "binary", "both", "case",
    "cast", "check", "collate", "collation", "column", "concurrently",
    "constraint", "create", "cross", "current_catalog", "current_date",
    "current_role", "current_schema", "current_time", "current_timestamp",
    "current_user", "default", "deferrable", "desc", "distinct", "do",
    "else", "end", "except", "false", "fetch", "for", "foreign", "from",
    "full", "grant", "group", "having", "ilike", "in", "initially",
    "inner", "intersect", "into", "is", "isnull", "join", "lateral",
    "leading", "left", "like", "limit", "localtime", "localtimestamp",
    "natural", "not", "notnull", "null", "offset", "on", "only",
    "or", "order", "outer", "overlaps", "placing", "primary",
    "references", "returning", "right", "select", "session_user",
    "similar", "some", "symmetric", "table", "tablesample", "then",
    "to", "trailing", "true", "union", "unique", "user", "using",
    "variadic", "verbose", "when", "where", "window", "with",
}

def normalize_name(name):
    if not name:
        return "unnamed"
    result = name.lower()
    result = re.sub(r'[\s&%#\-\.\/\\]+', '_', result)
    result = re.sub(r'[()（）\[\]「」『』〈〉《》【】{}]', '_', result)
    result = re.sub(r'[_]+', '_', result)
    result = result.strip('_')
    if result and result[0].isdigit():
        result = 't_' + result
    if result in RESERVED_WORDS:
        result = result + '_col'
    if len(result) > 50:
        result = result[:50].rstrip('_')
    return result

def generate_table_name(work_type, category, pool, dataset):
    wt = normalize_name(work_type)
    cat = normalize_name(category)
    pl = normalize_name(pool)
    ds = normalize_name(dataset)
    full_name = f"{wt}_{cat}_{pl}_{ds}"
    if len(full_name) > 63:
        parts = [wt, cat, pl, ds]
        max_part_len = (63 - 3) // 4
        truncated = [p[:max_part_len] if len(p) > max_part_len else p for p in parts]
        full_name = "_".join(truncated)
    return full_name

with open('prebuilt_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

datasets = data.get('datasets', [])

from collections import Counter, defaultdict

# Generate table names
for ds in datasets:
    ds['_generated_table_name'] = generate_table_name(
        ds['work_type_en'],
        ds['category_en'],
        ds['pool_en'],
        ds['dataset_en']
    )

# Check 4-tuple uniqueness (what the code checks)
four_tuples = [(ds['work_type_en'], ds['category_en'], ds['pool_en'], ds['dataset_en']) for ds in datasets]
four_tuple_counts = Counter(four_tuples)
print(f"Total datasets: {len(datasets)}")
print(f"Unique 4-tuples: {len(set(four_tuples))}")

# Check table_name uniqueness (what the DB enforces)
table_names = [ds['_generated_table_name'] for ds in datasets]
name_counts = Counter(table_names)
print(f"\nUnique generated table_names: {len(set(table_names))}")
print(f"Table_names with duplicates: {sum(1 for c in name_counts.values() if c > 1)}")

# Show the collision example
target_name = 'slag_treating_slag_granulatio_continuous_time_t_1_slag_yard_p'
colliding = [ds for ds in datasets if ds['_generated_table_name'] == target_name]
print(f"\nDatasets colliding on '{target_name}': {len(colliding)}")
for ds in colliding:
    print(f"  - {ds['dataset_en']}")
    print(f"    cat={ds['category_en'][:50]}...")
    print(f"    ds_name={ds['dataset_en'][:50]}...")

# Check if any datasets have non-empty table_name in JSON
non_empty = [(ds['dataset_en'], ds['table_name']) for ds in datasets if ds.get('table_name', '')]
print(f"\nDatasets with non-empty table_name in JSON: {len(non_empty)}")
if non_empty:
    for en, tn in non_empty[:5]:
        print(f"  {en}: '{tn}'")

# Check what happens with same-category, same-dataset collisions
print("\nTop 5 most common generated table_names:")
for name, cnt in name_counts.most_common(5):
    print(f"  [{cnt}x] {name}")
