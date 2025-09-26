# 🗄️ Database Exploration Guide

**Complete guide to exploring and analyzing SQLite databases in the gonogo project**

## 🎯 Quick Start - DB Browser for SQLite (Recommended)

### **Installation**
```bash
# Download and install DB Browser for SQLite:
# Website: https://sqlitebrowser.org/
# Windows: winget install DBBrowserForSQLite.DBBrowserForSQLite
# macOS: brew install --cask db-browser-for-sqlite
# Ubuntu: sudo apt install sqlitebrowser
```

### **Open RTM Database**
```
1. Launch DB Browser for SQLite
2. File → Open Database
3. Navigate to project root
4. Select: gonogo.db

Key tabs to explore:
- Database Structure: See all tables and schemas
- Browse Data: View/filter table contents
- Execute SQL: Run custom queries
- Plot: Create charts from results
```

## 📍 Database Locations

### **Main RTM Database (Primary)**
```bash
gonogo.db                               # Root directory - all RTM data
src/be/gonogo.db                        # Backup/secondary RTM database
```

### **Test-Related Databases**
```bash
quality/logs/test_failures.db           # Test failure tracking and analysis
quality/logs/demo_test_failures.db      # Demo test failure data
```

### **Archive and Development Databases**
```bash
quality/archives/archive_metadata.db    # Archive management metadata
test_rtm.db                             # Development test database
```

## 🔧 Database Access Methods

### **Option 1: DB Browser for SQLite (GUI - Recommended)**
**Best for**: Visual exploration, interactive filtering, chart creation

#### **GUI Features:**
- **Database Structure tab**: View all tables and schemas
- **Browse Data tab**: View table contents with sorting/filtering
- **Execute SQL tab**: Run custom queries with F5
- **Plot tab**: Create charts from query results
- **Export options**: CSV, JSON, SQL dumps

#### **Quick Tips:**
- Use filter boxes at top of columns to search data
- Click column headers to sort data
- Right-click any table → "Show schema" to see table structure
- Use Ctrl+A to select all query text
- Save frequently used queries with "Save SQL file"

### **Option 2: SQLite Command Line**
**Best for**: Automation, scripting, advanced SQL queries

```bash
# Connect to main RTM database
sqlite3 gonogo.db

# Essential SQLite commands (once connected):
.help                                   # Show all SQLite commands
.tables                                 # List all tables
.schema table_name                      # Show table structure
.headers on                            # Show column headers in output
.mode column                           # Format output as aligned columns
.mode csv                              # Format output as CSV
.width 15 30 10                        # Set column widths
.output filename.txt                    # Redirect output to file
.output stdout                         # Reset output to terminal
.quit                                  # Exit SQLite
```

### **Option 3: Project Database Inspector Tool**
**Best for**: Quick overview, automated inspection

```bash
# Overview of all databases
python tools/db_inspector.py

# Inspect specific database
python tools/db_inspector.py --db gonogo.db
python tools/db_inspector.py --db quality/logs/test_failures.db

# Interactive browser mode
python tools/db_inspector.py --interactive
```

## 📊 RTM Database Schema Exploration

### **Main Tables Overview**
```sql
-- RTM Database Tables (gonogo.db)
epics                 -- Epic definitions and status
user_stories          -- User stories linked to epics
tests                 -- Test files linked to epics/stories
defects               -- Defect tracking and management
github_sync_records   -- GitHub synchronization logs

-- Test Database Tables (quality/logs/test_*.db)
test_executions       -- Test run results and timing
test_failures         -- Failed test analysis and patterns
log_entries           -- Structured test execution logs
```

### **Using DB Browser for SQLite:**
```
1. Open gonogo.db in DB Browser for SQLite
2. Click "Database Structure" tab to see all tables
3. Right-click any table → "Show schema" to see table structure
4. Click "Browse Data" tab and select table to view contents
5. Use filter boxes at top of columns to search data
6. Click column headers to sort data
```

### **Using Command Line:**
```bash
sqlite3 gonogo.db << EOF
-- Show all tables in RTM database
.tables

-- Show table structures
.schema epics
.schema user_stories
.schema tests
.schema defects
.schema github_sync_records

-- Quick row counts for each table
SELECT 'epics' as table_name, COUNT(*) as row_count FROM epics
UNION ALL
SELECT 'user_stories', COUNT(*) FROM user_stories
UNION ALL
SELECT 'tests', COUNT(*) FROM tests
UNION ALL
SELECT 'defects', COUNT(*) FROM defects
UNION ALL
SELECT 'github_sync_records', COUNT(*) FROM github_sync_records;
EOF
```

## 🔍 Useful Exploration Queries

### **Epic Analysis**

**Using DB Browser for SQLite:**
```
1. Click "Execute SQL" tab
2. Copy and paste any of the SQL queries below
3. Click "Execute" button (F5) to run
4. Results appear in bottom panel
5. Right-click results → "Export" to save as CSV
```

**SQL Queries (use in DB Browser or command line):**
```sql
-- Epic overview with progress metrics
SELECT
    epic_id,
    title,
    status,
    priority,
    created_at,
    updated_at
FROM epics
ORDER BY priority DESC, created_at DESC;

-- Epic progress calculation
SELECT
    e.epic_id,
    e.title,
    COUNT(us.id) as total_stories,
    SUM(CASE WHEN us.implementation_status = 'completed' THEN 1 ELSE 0 END) as completed_stories,
    SUM(us.story_points) as total_points,
    SUM(CASE WHEN us.implementation_status = 'completed' THEN us.story_points ELSE 0 END) as completed_points,
    ROUND(
        (SUM(CASE WHEN us.implementation_status = 'completed' THEN us.story_points ELSE 0 END) * 100.0) /
        NULLIF(SUM(us.story_points), 0), 1
    ) as completion_percentage
FROM epics e
LEFT JOIN user_stories us ON e.id = us.epic_id
GROUP BY e.id, e.epic_id, e.title
ORDER BY completion_percentage DESC;
```

### **User Story Analysis**
```sql
-- User stories by status
SELECT
    implementation_status,
    COUNT(*) as count,
    SUM(story_points) as total_points
FROM user_stories
GROUP BY implementation_status
ORDER BY count DESC;

-- User stories for specific epic
SELECT
    us.user_story_id,
    us.title,
    us.implementation_status,
    us.story_points,
    us.github_issue_number
FROM user_stories us
JOIN epics e ON us.epic_id = e.id
WHERE e.epic_id = 'EP-00005'  -- Change epic ID as needed
ORDER BY us.user_story_id;
```

### **Test Coverage Analysis**
```sql
-- Test distribution by type
SELECT
    test_type,
    COUNT(*) as test_count,
    COUNT(DISTINCT epic_id) as epics_covered
FROM tests
GROUP BY test_type
ORDER BY test_count DESC;

-- Tests linked to specific epic
SELECT
    t.test_file,
    t.test_type,
    t.title,
    t.last_execution_status,
    t.last_execution_time
FROM tests t
JOIN epics e ON t.epic_id = e.id
WHERE e.epic_id = 'EP-00005'  -- Change epic ID as needed
ORDER BY t.test_type, t.test_file;

-- Tests without epic links (orphaned tests)
SELECT
    test_file,
    test_type,
    title
FROM tests
WHERE epic_id IS NULL
ORDER BY test_type, test_file;
```

### **Defect Analysis**
```sql
-- Defect summary by priority and status
SELECT
    priority,
    status,
    COUNT(*) as count
FROM defects
GROUP BY priority, status
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    CASE status
        WHEN 'open' THEN 1
        WHEN 'in_progress' THEN 2
        WHEN 'resolved' THEN 3
        WHEN 'closed' THEN 4
    END;

-- Recent defects with epic context
SELECT
    d.defect_id,
    d.title,
    d.priority,
    d.status,
    e.epic_id,
    d.created_at
FROM defects d
LEFT JOIN epics e ON d.epic_id = e.id
ORDER BY d.created_at DESC
LIMIT 10;
```

### **GitHub Sync Analysis**
```sql
-- Recent GitHub sync activity
SELECT
    sync_timestamp,
    entity_type,
    entity_id,
    operation,
    success
FROM github_sync_records
ORDER BY sync_timestamp DESC
LIMIT 20;

-- Sync success rate by entity type
SELECT
    entity_type,
    COUNT(*) as total_syncs,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_syncs,
    ROUND((SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) as success_rate
FROM github_sync_records
GROUP BY entity_type;
```

## 🔍 Advanced Exploration Techniques

### **Cross-Table Analysis**
```sql
-- Epic health dashboard
SELECT
    e.epic_id,
    e.title,
    e.status as epic_status,
    COUNT(DISTINCT us.id) as user_stories,
    COUNT(DISTINCT t.id) as tests,
    COUNT(DISTINCT d.id) as defects,
    COUNT(DISTINCT CASE WHEN d.status IN ('open', 'in_progress') THEN d.id END) as open_defects
FROM epics e
LEFT JOIN user_stories us ON e.id = us.epic_id
LEFT JOIN tests t ON e.id = t.epic_id
LEFT JOIN defects d ON e.id = d.epic_id
GROUP BY e.id, e.epic_id, e.title, e.status
ORDER BY open_defects DESC, defects DESC;
```

### **Testing Quality Metrics**
```sql
-- Test execution quality by epic
SELECT
    e.epic_id,
    COUNT(t.id) as total_tests,
    SUM(CASE WHEN t.last_execution_status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
    SUM(CASE WHEN t.last_execution_status = 'failed' THEN 1 ELSE 0 END) as failed_tests,
    SUM(CASE WHEN t.last_execution_status IS NULL THEN 1 ELSE 0 END) as not_run_tests,
    ROUND(
        (SUM(CASE WHEN t.last_execution_status = 'passed' THEN 1 ELSE 0 END) * 100.0) /
        NULLIF(COUNT(t.id), 0), 1
    ) as pass_rate
FROM epics e
LEFT JOIN tests t ON e.id = t.epic_id
GROUP BY e.id, e.epic_id
HAVING COUNT(t.id) > 0
ORDER BY pass_rate DESC;
```

## 💾 Data Export and Backup

### **Using DB Browser**
```
1. Right-click results → "Export" to save as CSV
2. File → Export → Database to SQL file (complete backup)
3. File → Export → Table to CSV (specific table)
```

### **Using Command Line**
```bash
# Export entire database to SQL dump
sqlite3 gonogo.db .dump > gonogo_backup.sql

# Export specific table to CSV
sqlite3 gonogo.db << EOF
.headers on
.mode csv
.output epics_export.csv
SELECT * FROM epics;
.quit
EOF

# Create database backup
sqlite3 gonogo.db ".backup gonogo_backup.db"

# Import data from SQL dump
sqlite3 new_database.db < gonogo_backup.sql
```

## 🔧 Database Maintenance

### **Health Checks**
```bash
# Using project tools
python tools/rtm-db.py admin health-check
python tools/rtm-db.py admin validate

# Using SQLite CLI
sqlite3 gonogo.db "PRAGMA integrity_check;"
sqlite3 gonogo.db "PRAGMA foreign_key_check;"
```

### **Database Statistics**
```sql
-- Database size and page info
PRAGMA page_count;
PRAGMA page_size;
PRAGMA freelist_count;

-- Table row counts
SELECT name, COUNT(*) as row_count
FROM (
    SELECT 'epics' as name UNION ALL SELECT 'user_stories' UNION ALL
    SELECT 'tests' UNION ALL SELECT 'defects' UNION ALL SELECT 'github_sync_records'
) tables
JOIN (
    SELECT 'epics' as name, COUNT(*) as count FROM epics UNION ALL
    SELECT 'user_stories', COUNT(*) FROM user_stories UNION ALL
    SELECT 'tests', COUNT(*) FROM tests UNION ALL
    SELECT 'defects', COUNT(*) FROM defects UNION ALL
    SELECT 'github_sync_records', COUNT(*) FROM github_sync_records
) counts ON tables.name = counts.name;
```

### **Performance Optimization**
```bash
# Optimize database (rebuild indexes, reclaim space)
sqlite3 gonogo.db "VACUUM;"

# Update table statistics
sqlite3 gonogo.db "ANALYZE;"
```

## 🎯 Quick Investigation Commands

### **One-Line Queries**
```bash
# Quick epic status check
sqlite3 gonogo.db "SELECT epic_id, status, COUNT(*) FROM epics GROUP BY status;"

# Find failing tests
sqlite3 gonogo.db "SELECT epic_id, test_file, last_execution_status FROM tests WHERE last_execution_status = 'failed';"

# Check recent activity
sqlite3 gonogo.db "SELECT entity_type, COUNT(*) FROM github_sync_records WHERE date(sync_timestamp) = date('now') GROUP BY entity_type;"

# Find high-priority open defects
sqlite3 gonogo.db "SELECT defect_id, title, priority FROM defects WHERE status IN ('open', 'in_progress') AND priority IN ('critical', 'high');"
```

## 📊 Test Failure Database Exploration

### **Analyzing Test Failures**
```bash
# Connect to test failures database
sqlite3 quality/logs/test_failures.db

# Common failure analysis queries
.mode column
.headers on

-- Group failures by category
SELECT category, COUNT(*) as failure_count,
       AVG(occurrence_count) as avg_occurrences
FROM test_failures
GROUP BY category
ORDER BY failure_count DESC;

-- Find flaky tests (frequently failing)
SELECT test_name, test_file, occurrence_count,
       last_seen, category
FROM test_failures
WHERE occurrence_count > 3
ORDER BY occurrence_count DESC;

-- Recent failure trends
SELECT DATE(last_seen) as failure_date,
       COUNT(*) as failures_that_day
FROM test_failures
WHERE last_seen >= date('now', '-7 days')
GROUP BY DATE(last_seen)
ORDER BY failure_date DESC;
```

### **Custom Analysis with Python**
```python
import sqlite3

# Connect to test failures database
conn = sqlite3.connect('quality/logs/test_failures.db')
conn.row_factory = sqlite3.Row

# Analyze failure patterns
cursor = conn.execute("""
    SELECT test_name, category, occurrence_count,
           last_seen, error_message
    FROM test_failures
    WHERE occurrence_count > 2
    ORDER BY occurrence_count DESC
""")

for row in cursor:
    print(f"Test: {row['test_name']}")
    print(f"  Category: {row['category']}")
    print(f"  Occurrences: {row['occurrence_count']}")
    print(f"  Last seen: {row['last_seen']}")
    print("---")

conn.close()
```

## 🔗 Related Tools and Documentation

### **RTM Database Tools**
- `python tools/rtm-db.py --help` - RTM database management CLI
- `python tools/github_sync_manager.py --help` - GitHub synchronization
- `python tools/rtm_report_generator.py --html` - Generate RTM reports

### **Related Documentation**
- [Quality Reports Guide](README.md) - Complete quality reporting overview
- [Testing Guide](TESTING_GUIDE.md) - Testing workflows and RTM integration
- [RTM Guide](RTM_GUIDE.md) - RTM dashboard and web interface
- [Debug Reports](debug_reports/) - Detailed debugging analysis and regression prevention
- [Quick Reference](QUICK_REFERENCE.md) - Common database commands

---

**Last Updated**: 2024-09-22
**Purpose**: Consolidated database exploration guide combining DATABASE_INSPECTION_GUIDE.md and TESTING_GUIDE.md database sections