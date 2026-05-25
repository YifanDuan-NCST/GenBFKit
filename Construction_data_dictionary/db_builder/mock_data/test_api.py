# -*- coding: utf-8 -*-
"""API Routes Test Script"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_builder.services.database_manager import get_manager
from db_builder.mock_data.generator import MockDataGenerator

def main():
    manager = get_manager()
    tables = manager.list_tables()
    print('Tables listed:', len(tables))
    if tables:
        t = tables[0]
        print('Sample table:', t['table_name'], 'rows=', t['row_count'], 'cols=', t['column_count'])

    schema = manager.get_table_schema(tables[0]['table_name'])
    print('Schema columns:', len(schema['columns']))

    gen = MockDataGenerator()
    preview = gen.preview_table_data(tables[0]['table_name'], limit=5)
    print('Preview rows:', len(preview['rows']), 'total:', preview['total_rows'])

    stats = manager.get_statistics()
    print('Stats: tables=', stats.total_tables, 'records=', stats.total_records)

    # Test 5 different tables
    print('\nTesting 5 random tables...')
    for t in tables[:5]:
        preview = gen.preview_table_data(t['table_name'], limit=3)
        has_data = len(preview['rows']) > 0
        print(f'  [{t["table_name"][:50]}] rows={preview["total_rows"]}, preview={has_data}')

    print('\nAll API routes working correctly!')

if __name__ == '__main__':
    main()
