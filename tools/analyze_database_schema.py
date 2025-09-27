#!/usr/bin/env python3
"""
Analyze database schema to see all available fields
"""

import sqlite3


def analyze_schema():
    conn = sqlite3.connect("gonogo.db")
    cursor = conn.cursor()

    tables = ["user_stories", "defects", "epics", "tests"]

    for table in tables:
        print(f"\n=== {table.upper()} TABLE SCHEMA ===")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            null_str = "NOT NULL" if not_null else "NULL"
            default_str = f" DEFAULT {default}" if default else ""
            pk_str = " PRIMARY KEY" if pk else ""
            print(f"  {name}: {col_type} {null_str}{default_str}{pk_str}")

        # Get a sample record to see what's populated
        print(f"\n--- Sample {table} record ---")
        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for i, col in enumerate(columns):
                col_name = col[1]
                value = sample[i] if i < len(sample) else "N/A"
                print(f"  {col_name}: {value}")
        else:
            print("  No records found")

    conn.close()


if __name__ == "__main__":
    analyze_schema()
