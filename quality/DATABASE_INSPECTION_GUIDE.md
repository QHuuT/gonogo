# Database Inspection Guide

This guide explains how to examine and analyze SQLite databases created by the testing and logging systems in the gonogo project.

## 📁 Database Locations

The project creates several SQLite databases:

```
quality/
├── logs/
│   ├── test_failures.db           # Real test failure tracking
│   ├── demo_test_failures.db      # Demo failure data
│   └── structured_logs.db         # Test execution logs (if enabled)
└── archives/
    └── archive_metadata.db        # Archive management metadata
```

## 🔧 Tools Available

### 1. Database Inspector Tool (Recommended)
**Location**: `tools/db_inspector.py`
**Best for**: Quick exploration, interactive browsing, automated inspection

### 2. SQLite CLI
**Best for**: Advanced SQL queries, database administration

### 3. Python Scripts
**Best for**: Programmatic access, automation, custom analysis

## 🚀 Quick Start

### Overview of All Databases
```bash
# Show all databases with basic stats
python tools/db_inspector.py
```

**Example Output**:
```
Database Overview
==================================================

[DB] quality\logs\demo_test_failures.db
   Size: 0.06 MB
   Tables: 3
   - test_failures: 25 rows
   - sqlite_sequence: 1 rows
   - failure_patterns: 0 rows

[DB] quality\archives\archive_metadata.db
   Size: 0.01 MB
   Tables: 2
   - archived_items: 0 rows
   - sqlite_sequence: 0 rows
```

### Examine Specific Database
```bash
# List tables in a database
python tools/db_inspector.py --db quality/logs/demo_test_failures.db

# View table structure
python tools/db_inspector.py --db quality/logs/demo_test_failures.db --table test_failures --schema

# View table data (limit 5 rows)
python tools/db_inspector.py --db quality/logs/demo_test_failures.db --table test_failures --data --limit 5
```

## 📊 Database Inspector Tool Reference

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--db PATH` | Specify database file | `--db quality/logs/test_failures.db` |
| `--table NAME` | Target specific table | `--table test_failures` |
| `--schema` | Show table structure | `--schema` |
| `--data` | Show table data | `--data` |
| `--limit N` | Limit rows displayed | `--limit 10` |
| `--interactive` or `-i` | Interactive browser mode | `-i` |

### Usage Examples

#### Basic Inspection
```bash
# Overview of all databases
python tools/db_inspector.py

# Tables in specific database
python tools/db_inspector.py --db quality/logs/test_failures.db

# Complete table info (schema + data)
python tools/db_inspector.py --db quality/logs/test_failures.db --table test_failures

# Just the schema
python tools/db_inspector.py --db quality/logs/test_failures.db --table test_failures --schema

# Just the data (first 3 rows)
python tools/db_inspector.py --db quality/logs/test_failures.db --table test_failures --data --limit 3
```

#### Interactive Mode
```bash
# Start interactive browser
python tools/db_inspector.py --db quality/logs/test_failures.db --interactive
```

**Interactive Commands**:
```
db> tables                    # List all tables
db> schema test_failures      # Show table structure
db> data test_failures 10     # Show 10 rows of data
db> count test_failures       # Get total row count
db> quit                      # Exit interactive mode
```

## 🗂️ Database Schemas Reference

### Test Failures Database

**Tables**: `test_failures`, `failure_patterns`, `sqlite_sequence`

#### test_failures Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `test_id` | TEXT | Full test identifier (file::function) |
| `test_name` | TEXT | Test function name |
| `test_file` | TEXT | Test file path |
| `failure_message` | TEXT | Error message |
| `stack_trace` | TEXT | Full stack trace |
| `category` | TEXT | Failure category (assertion_error, import_error, etc.) |
| `severity` | TEXT | Severity level (low, medium, high, critical) |
| `error_hash` | TEXT | Normalized error hash for grouping |
| `first_seen` | TEXT | First occurrence timestamp |
| `last_seen` | TEXT | Latest occurrence timestamp |
| `occurrence_count` | INTEGER | Number of times this failure occurred |
| `environment_info` | TEXT | Python version, OS, session info |
| `coverage_info` | TEXT | Coverage data if available |
| `execution_mode` | TEXT | Test execution mode (silent, verbose, etc.) |
| `session_id` | TEXT | Test session identifier |
| `metadata` | TEXT | JSON metadata (duration, retry count, etc.) |
| `created_at` | TEXT | Record creation timestamp |
| `updated_at` | TEXT | Last update timestamp |

### Archive Metadata Database

**Tables**: `archived_items`, `sqlite_sequence`

#### archived_items Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `original_path` | TEXT | Original file path |
| `archive_path` | TEXT | Archived file location |
| `file_type` | TEXT | File extension |
| `original_size` | INTEGER | Original file size in bytes |
| `compressed_size` | INTEGER | Compressed size in bytes |
| `compression_ratio` | REAL | Compression efficiency |
| `archived_at` | TEXT | Archive timestamp |
| `retention_policy` | TEXT | Applied retention policy |
| `metadata` | TEXT | JSON metadata about archiving |

## 🔍 Common Inspection Tasks

### 1. Finding Recent Test Failures
```bash
# Interactive mode for exploration
python tools/db_inspector.py --db quality/logs/test_failures.db -i

# Then in interactive mode:
db> data test_failures 5
```

### 2. Analyzing Failure Patterns
```python
# Python script for custom analysis
import sqlite3

conn = sqlite3.connect('quality/logs/test_failures.db')
conn.row_factory = sqlite3.Row

# Group failures by category
cursor = conn.execute("""
    SELECT category, COUNT(*) as count,
           AVG(occurrence_count) as avg_occurrences
    FROM test_failures
    GROUP BY category
    ORDER BY count DESC
""")

print("Failure Analysis:")
for row in cursor.fetchall():
    print(f"  {row['category']}: {row['count']} unique failures, avg {row['avg_occurrences']:.1f} occurrences")

conn.close()
```

### 3. Checking Archive Status
```bash
# View archive metadata
python tools/db_inspector.py --db quality/archives/archive_metadata.db --table archived_items --data --limit 10
```

### 4. Finding Flaky Tests
```python
# Python script to find frequently failing tests
import sqlite3

conn = sqlite3.connect('quality/logs/test_failures.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT test_name, test_file, occurrence_count,
           failure_message, last_seen
    FROM test_failures
    WHERE occurrence_count > 3
    ORDER BY occurrence_count DESC
""")

print("Potentially Flaky Tests (>3 failures):")
for row in cursor.fetchall():
    print(f"  {row['test_name']} ({row['occurrence_count']} failures)")
    print(f"    File: {row['test_file']}")
    print(f"    Last: {row['last_seen']}")
    print(f"    Error: {row['failure_message'][:100]}...")
    print()

conn.close()
```

## 🛠️ Advanced Usage

### Custom SQL Queries
```bash
# Use SQLite CLI for advanced queries
sqlite3 quality/logs/test_failures.db

# Example queries:
.mode column
.headers on

-- Recent failures in last 24 hours
SELECT test_name, category, last_seen
FROM test_failures
WHERE datetime(last_seen) > datetime('now', '-1 day')
ORDER BY last_seen DESC;

-- Failure frequency by category
SELECT category, COUNT(*) as unique_failures,
       SUM(occurrence_count) as total_occurrences
FROM test_failures
GROUP BY category;

-- Most problematic test files
SELECT test_file, COUNT(*) as failure_types,
       SUM(occurrence_count) as total_failures
FROM test_failures
GROUP BY test_file
ORDER BY total_failures DESC;
```

### Backup and Export
```bash
# Backup database
cp quality/logs/test_failures.db quality/logs/test_failures_backup_$(date +%Y%m%d).db

# Export to CSV
sqlite3 -header -csv quality/logs/test_failures.db "SELECT * FROM test_failures;" > failures_export.csv

# Export specific analysis
sqlite3 -header -csv quality/logs/test_failures.db "
SELECT test_name, category, occurrence_count, last_seen
FROM test_failures
ORDER BY occurrence_count DESC
" > failure_analysis.csv
```

## 🔧 Troubleshooting

### Database Locked Error
```bash
# If you get "database is locked" errors:
# 1. Close any other connections to the database
# 2. Wait a moment and retry
# 3. Check if any test processes are still running
```

### No Data Found
```bash
# If databases are empty:
# 1. Run some tests to generate failure data:
python tools/failure_tracking_demo.py

# 2. Or run real tests that might fail:
pytest tests/ -v

# 3. Check if databases were created:
python tools/db_inspector.py
```

### Unicode Display Issues
```bash
# If you see encoding errors on Windows:
# 1. Use the database inspector tool (handles encoding)
# 2. Or set console encoding:
chcp 65001
```

## 📈 Integration with Quality Reports

### Generating Reports from Database Data
```bash
# Generate failure analysis report
python tools/failure_tracking_demo.py

# Generate log correlation report (if log data exists)
python tools/log_correlation_demo.py

# View generated reports
ls quality/reports/failure_*.html
ls quality/reports/log_correlation_*.json
```

### Monitoring Database Growth
```bash
# Check database sizes
python tools/db_inspector.py | grep "Size:"

# Archive old data if databases get large
python tools/archive_cleanup.py --metrics
```

## 🎯 Best Practices

### Regular Inspection
```bash
# Daily health check
python tools/db_inspector.py

# Weekly detailed analysis
python tools/db_inspector.py --db quality/logs/test_failures.db --table test_failures --data --limit 20
```

### Data Cleanup
```bash
# Clean old test data periodically
# (This would be part of archive management - US-00032)
python tools/archive_cleanup.py --apply
```

### Performance Monitoring
- Monitor database file sizes
- Archive old data when databases exceed reasonable sizes
- Use LIMIT clauses when querying large datasets
- Close database connections properly in scripts

## 🔗 Related Documentation

- **[Quality Reports Guide](README.md)** - Overview of all quality reports
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and thresholds
- **[Development Workflow](../docs/technical/development-workflow.md)** - Testing procedures
- **[Archive Management](US-00032)** - Future enhanced archiving capabilities

---

**Last Updated**: 2025-09-20
**Version**: EP-00006 Database Inspection Tools
**Related**: US-00025 (Failure Tracking), US-00028 (Archive Management)