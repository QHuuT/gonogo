#!/usr/bin/env python3
"""
Database Inspector Tool

Simple utility to examine SQLite databases created by the logging and testing systems.
Provides table listings, schema information, and data browsing capabilities.

Usage:
    python tools/db_inspector.py
    python tools/db_inspector.py --db quality/logs/test_failures.db
    python tools/db_inspector.py --table test_failures --limit 10
"""

import sqlite3
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import json


def find_databases() -> List[Path]:
    """Find all SQLite database files in the quality folder."""
    quality_dir = Path("quality")
    if not quality_dir.exists():
        return []

    db_files = []
    for db_file in quality_dir.rglob("*.db"):
        if db_file.is_file():
            db_files.append(db_file)

    return sorted(db_files)


def get_tables(db_path: Path) -> List[str]:
    """Get list of tables in the database."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error accessing database {db_path}: {e}")
        return []


def get_table_schema(db_path: Path, table_name: str) -> List[Dict[str, Any]]:
    """Get schema information for a table."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default': row[4],
                    'primary_key': bool(row[5])
                })
            return columns
    except sqlite3.Error as e:
        print(f"Error getting schema for {table_name}: {e}")
        return []


def get_table_data(db_path: Path, table_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get data from a table."""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error getting data from {table_name}: {e}")
        return []


def get_table_count(db_path: Path, table_name: str) -> int:
    """Get row count for a table."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
    except sqlite3.Error as e:
        print(f"Error counting rows in {table_name}: {e}")
        return 0


def display_database_overview():
    """Display overview of all databases."""
    print("Database Overview")
    print("=" * 50)

    databases = find_databases()
    if not databases:
        print("No SQLite databases found in quality/ folder.")
        return

    for db_path in databases:
        print(f"\n[DB] {db_path}")
        try:
            # Get file size
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"   Size: {size_mb:.2f} MB")

            # Get tables
            tables = get_tables(db_path)
            print(f"   Tables: {len(tables)}")

            for table in tables:
                count = get_table_count(db_path, table)
                print(f"   - {table}: {count} rows")

        except Exception as e:
            print(f"   Error: {e}")


def display_table_schema(db_path: Path, table_name: str):
    """Display detailed schema for a table."""
    print(f"Schema for {table_name} in {db_path}")
    print("=" * 60)

    schema = get_table_schema(db_path, table_name)
    if not schema:
        print("No schema information available.")
        return

    print(f"{'Column':<20} {'Type':<15} {'Null':<6} {'Key':<6} {'Default':<15}")
    print("-" * 70)

    for col in schema:
        null_str = "NO" if col['not_null'] else "YES"
        key_str = "PRI" if col['primary_key'] else ""
        default_str = str(col['default']) if col['default'] is not None else ""

        print(f"{col['name']:<20} {col['type']:<15} {null_str:<6} {key_str:<6} {default_str:<15}")


def display_table_data(db_path: Path, table_name: str, limit: int = 10):
    """Display data from a table."""
    print(f"Data from {table_name} (limit {limit})")
    print("=" * 60)

    data = get_table_data(db_path, table_name, limit)
    if not data:
        print("No data available.")
        return

    total_count = get_table_count(db_path, table_name)
    print(f"Showing {len(data)} of {total_count} total rows\n")

    # Display data in a readable format
    for i, row in enumerate(data, 1):
        print(f"Row {i}:")
        for key, value in row.items():
            # Truncate long values for readability
            if isinstance(value, str) and len(value) > 100:
                value = value[:97] + "..."
            print(f"  {key}: {value}")
        print()


def interactive_browser(db_path: Path):
    """Interactive database browser."""
    print(f"Interactive Browser for {db_path}")
    print("Commands: tables, schema <table>, data <table> [limit], count <table>, quit")
    print("=" * 60)

    while True:
        try:
            command = input("\ndb> ").strip().split()
            if not command:
                continue

            cmd = command[0].lower()

            if cmd == "quit" or cmd == "exit":
                break
            elif cmd == "tables":
                tables = get_tables(db_path)
                print(f"Tables: {', '.join(tables)}")
            elif cmd == "schema" and len(command) > 1:
                display_table_schema(db_path, command[1])
            elif cmd == "data" and len(command) > 1:
                limit = int(command[2]) if len(command) > 2 else 10
                display_table_data(db_path, command[1], limit)
            elif cmd == "count" and len(command) > 1:
                count = get_table_count(db_path, command[1])
                print(f"{command[1]}: {count} rows")
            else:
                print("Unknown command. Use: tables, schema <table>, data <table> [limit], count <table>, quit")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Inspect SQLite databases in quality/ folder")
    parser.add_argument('--db', type=Path, help='Specific database file to inspect')
    parser.add_argument('--table', help='Specific table to examine')
    parser.add_argument('--limit', type=int, default=10, help='Limit rows when displaying data')
    parser.add_argument('--schema', action='store_true', help='Show table schema')
    parser.add_argument('--data', action='store_true', help='Show table data')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive browser mode')

    args = parser.parse_args()

    # If no specific database, show overview
    if not args.db:
        display_database_overview()
        return

    # Check if database exists
    if not args.db.exists():
        print(f"Database file not found: {args.db}")
        return

    # Interactive mode
    if args.interactive:
        interactive_browser(args.db)
        return

    # Show tables if no specific table requested
    if not args.table:
        print(f"[DB] {args.db}")
        tables = get_tables(args.db)
        print(f"Tables: {', '.join(tables)}")

        # Show basic info for each table
        for table in tables:
            count = get_table_count(args.db, table)
            print(f"  - {table}: {count} rows")
        return

    # Show specific table information
    if args.schema:
        display_table_schema(args.db, args.table)

    if args.data:
        display_table_data(args.db, args.table, args.limit)

    # Default: show both schema and data
    if not args.schema and not args.data:
        display_table_schema(args.db, args.table)
        print()
        display_table_data(args.db, args.table, args.limit)


if __name__ == "__main__":
    main()