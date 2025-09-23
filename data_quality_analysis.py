#!/usr/bin/env python3
"""
Data Quality Analysis for GoNoGo Database
Comprehensive data scientist evaluation of database integrity
"""

import re
from collections import defaultdict
from sqlalchemy import create_engine, text, inspect

class DataQualityAnalyzer:
    def __init__(self, db_url='sqlite:///./gonogo.db'):
        self.engine = create_engine(db_url)
        self.conn = self.engine.connect()
        self.issues = defaultdict(list)

    def analyze_all(self):
        """Run all data quality checks."""
        print("="*80)
        print("DATA QUALITY ANALYSIS - GoNoGo Database")
        print("="*80)

        self.check_orphaned_records()
        self.check_referential_integrity()
        self.check_duplicate_records()
        self.check_data_completeness()
        self.check_data_consistency()
        self.check_invalid_values()
        self.check_data_format_issues()

        self.print_summary()

    def check_orphaned_records(self):
        """Check for orphaned records (missing FK relationships)."""
        print("\n1. ORPHANED RECORDS CHECK")
        print("-" * 80)

        # Tests without Epic
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM tests WHERE epic_id IS NULL
        """))
        orphaned_tests = result.scalar()

        # User Stories without Epic
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM user_stories WHERE epic_id IS NULL
        """))
        orphaned_us = result.scalar()

        # Defects without test or epic
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM defects WHERE test_id IS NULL AND epic_id IS NULL
        """))
        orphaned_defects = result.scalar()

        print(f"  Tests without Epic: {orphaned_tests}")
        print(f"  User Stories without Epic: {orphaned_us}")
        print(f"  Defects without Test/Epic: {orphaned_defects}")

        if orphaned_tests > 0:
            # Check if they're BDD
            result = self.conn.execute(text("""
                SELECT test_type, COUNT(*)
                FROM tests WHERE epic_id IS NULL
                GROUP BY test_type
            """))
            breakdown = result.fetchall()
            print(f"  Breakdown: {dict(breakdown)}")

            for test_type, count in breakdown:
                if test_type != 'bdd':
                    self.issues['orphaned_records'].append(
                        f"{count} {test_type} tests without epic"
                    )

        if orphaned_us > 0:
            self.issues['orphaned_records'].append(f"{orphaned_us} user stories without epic")
        if orphaned_defects > 0:
            self.issues['orphaned_records'].append(f"{orphaned_defects} defects without test/epic")

    def check_referential_integrity(self):
        """Check for broken foreign key references."""
        print("\n2. REFERENTIAL INTEGRITY CHECK")
        print("-" * 80)

        # Tests with invalid epic_id
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM tests t
            WHERE t.epic_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM epics e WHERE e.id = t.epic_id)
        """))
        invalid_test_epic = result.scalar()

        # User stories with invalid epic_id
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM user_stories us
            WHERE us.epic_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM epics e WHERE e.id = us.epic_id)
        """))
        invalid_us_epic = result.scalar()

        # Defects with invalid test_id
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM defects d
            WHERE d.test_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM tests t WHERE t.id = d.test_id)
        """))
        invalid_defect_test = result.scalar()

        print(f"  Tests with invalid epic_id: {invalid_test_epic}")
        print(f"  User Stories with invalid epic_id: {invalid_us_epic}")
        print(f"  Defects with invalid test_id: {invalid_defect_test}")

        if invalid_test_epic > 0:
            self.issues['referential_integrity'].append(f"{invalid_test_epic} tests reference non-existent epics")
        if invalid_us_epic > 0:
            self.issues['referential_integrity'].append(f"{invalid_us_epic} user stories reference non-existent epics")
        if invalid_defect_test > 0:
            self.issues['referential_integrity'].append(f"{invalid_defect_test} defects reference non-existent tests")

    def check_duplicate_records(self):
        """Check for duplicate records."""
        print("\n3. DUPLICATE RECORDS CHECK")
        print("-" * 80)

        # Duplicate epics by epic_id
        result = self.conn.execute(text("""
            SELECT epic_id, COUNT(*) as count
            FROM epics
            GROUP BY epic_id
            HAVING COUNT(*) > 1
        """))
        dup_epics = result.fetchall()

        # Duplicate user stories by github_issue_number
        result = self.conn.execute(text("""
            SELECT github_issue_number, COUNT(*) as count
            FROM user_stories
            WHERE github_issue_number IS NOT NULL
            GROUP BY github_issue_number
            HAVING COUNT(*) > 1
        """))
        dup_us = result.fetchall()

        # Duplicate tests by file_path + function_name
        result = self.conn.execute(text("""
            SELECT test_file_path, test_function_name, COUNT(*) as count
            FROM tests
            WHERE test_function_name IS NOT NULL
            GROUP BY test_file_path, test_function_name
            HAVING COUNT(*) > 1
        """))
        dup_tests = result.fetchall()

        print(f"  Duplicate epics: {len(dup_epics)}")
        if dup_epics:
            for epic_id, count in dup_epics:
                print(f"    {epic_id}: {count} records")
                self.issues['duplicates'].append(f"Epic {epic_id} has {count} duplicate records")

        print(f"  Duplicate user stories: {len(dup_us)}")
        if dup_us:
            for issue_num, count in dup_us:
                print(f"    GitHub #{issue_num}: {count} records")
                self.issues['duplicates'].append(f"User story GitHub #{issue_num} has {count} duplicates")

        print(f"  Duplicate tests: {len(dup_tests)}")
        if dup_tests:
            for file_path, func_name, count in dup_tests[:5]:
                print(f"    {file_path}::{func_name}: {count} records")
                self.issues['duplicates'].append(f"Test {func_name} has {count} duplicates")

    def check_data_completeness(self):
        """Check for missing required data."""
        print("\n4. DATA COMPLETENESS CHECK")
        print("-" * 80)

        # Epics without title
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM epics WHERE title IS NULL OR title = ''
        """))
        epics_no_title = result.scalar()

        # Tests without test_function_name
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM tests
            WHERE test_function_name IS NULL AND test_type != 'bdd'
        """))
        tests_no_func = result.scalar()

        # Tests without file path
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM tests WHERE test_file_path IS NULL OR test_file_path = ''
        """))
        tests_no_path = result.scalar()

        # User stories without title
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM user_stories WHERE title IS NULL OR title = ''
        """))
        us_no_title = result.scalar()

        print(f"  Epics without title: {epics_no_title}")
        print(f"  Non-BDD tests without function name: {tests_no_func}")
        print(f"  Tests without file path: {tests_no_path}")
        print(f"  User stories without title: {us_no_title}")

        if epics_no_title > 0:
            self.issues['data_completeness'].append(f"{epics_no_title} epics missing title")
        if tests_no_func > 0:
            self.issues['data_completeness'].append(f"{tests_no_func} non-BDD tests missing function name")
        if tests_no_path > 0:
            self.issues['data_completeness'].append(f"{tests_no_path} tests missing file path")
        if us_no_title > 0:
            self.issues['data_completeness'].append(f"{us_no_title} user stories missing title")

    def check_data_consistency(self):
        """Check for inconsistent data values."""
        print("\n5. DATA CONSISTENCY CHECK")
        print("-" * 80)

        # Check epic_id format consistency
        result = self.conn.execute(text("""
            SELECT epic_id FROM epics WHERE epic_id NOT LIKE 'EP-%'
        """))
        invalid_epic_format = result.fetchall()

        # Check test_type values
        result = self.conn.execute(text("""
            SELECT DISTINCT test_type FROM tests
        """))
        test_types = [row[0] for row in result.fetchall()]
        valid_types = {'unit', 'integration', 'e2e', 'bdd', 'security', 'functional'}
        invalid_types = [t for t in test_types if t not in valid_types]

        # Check status values
        result = self.conn.execute(text("""
            SELECT DISTINCT status FROM epics
        """))
        epic_statuses = [row[0] for row in result.fetchall()]
        valid_statuses = {'planned', 'in_progress', 'completed', 'on_hold', 'cancelled'}
        invalid_statuses = [s for s in epic_statuses if s and s not in valid_statuses]

        print(f"  Invalid epic_id formats: {len(invalid_epic_format)}")
        if invalid_epic_format:
            for row in invalid_epic_format:
                print(f"    {row[0]}")
                self.issues['data_consistency'].append(f"Invalid epic_id format: {row[0]}")

        print(f"  Invalid test types: {invalid_types if invalid_types else 'None'}")
        if invalid_types:
            self.issues['data_consistency'].append(f"Invalid test types: {invalid_types}")

        print(f"  Invalid epic statuses: {invalid_statuses if invalid_statuses else 'None'}")
        if invalid_statuses:
            self.issues['data_consistency'].append(f"Invalid epic statuses: {invalid_statuses}")

    def check_invalid_values(self):
        """Check for logically invalid values."""
        print("\n6. INVALID VALUES CHECK")
        print("-" * 80)

        # Negative values where they shouldn't be
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM epics
            WHERE total_story_points < 0 OR completed_story_points < 0
        """))
        negative_points = result.scalar()

        # Completion percentage > 100
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM epics WHERE completion_percentage > 100
        """))
        invalid_completion = result.scalar()

        # Completed > Total story points
        result = self.conn.execute(text("""
            SELECT epic_id, total_story_points, completed_story_points
            FROM epics
            WHERE completed_story_points > total_story_points
        """))
        invalid_points = result.fetchall()

        # Tests with negative execution duration
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM tests WHERE execution_duration_ms < 0
        """))
        negative_duration = result.scalar()

        print(f"  Epics with negative story points: {negative_points}")
        print(f"  Epics with completion > 100%: {invalid_completion}")
        print(f"  Epics with completed > total points: {len(invalid_points)}")
        print(f"  Tests with negative duration: {negative_duration}")

        if negative_points > 0:
            self.issues['invalid_values'].append(f"{negative_points} epics with negative story points")
        if invalid_completion > 0:
            self.issues['invalid_values'].append(f"{invalid_completion} epics with >100% completion")
        if invalid_points:
            for epic_id, total, completed in invalid_points:
                self.issues['invalid_values'].append(f"Epic {epic_id}: completed ({completed}) > total ({total})")
        if negative_duration > 0:
            self.issues['invalid_values'].append(f"{negative_duration} tests with negative duration")

    def check_data_format_issues(self):
        """Check for data format and encoding issues."""
        print("\n7. DATA FORMAT ISSUES CHECK")
        print("-" * 80)

        # Check for path inconsistencies (backslash vs forward slash)
        result = self.conn.execute(text("""
            SELECT test_file_path FROM tests
            WHERE test_file_path LIKE '%\\%'
            LIMIT 5
        """))
        backslash_paths = result.fetchall()

        result = self.conn.execute(text("""
            SELECT test_file_path FROM tests
            WHERE test_file_path LIKE '%/%'
            LIMIT 5
        """))
        forward_paths = result.fetchall()

        # Check for GitHub issue number format issues
        result = self.conn.execute(text("""
            SELECT github_issue_number FROM user_stories
            WHERE github_issue_number IS NOT NULL
            AND github_issue_number <= 0
        """))
        invalid_issue_nums = result.fetchall()

        # Check for JSON fields that might be corrupted
        result = self.conn.execute(text("""
            SELECT COUNT(*) FROM epics
            WHERE affects_versions IS NOT NULL
            AND affects_versions NOT LIKE '[%]'
            AND affects_versions NOT LIKE '{%}'
            AND affects_versions != ''
        """))
        invalid_json = result.scalar()

        print(f"  Paths with backslashes: {len(backslash_paths)}")
        print(f"  Paths with forward slashes: {len(forward_paths)}")

        if backslash_paths and forward_paths:
            self.issues['data_format'].append("Mixed path separators (backslash and forward slash)")

        print(f"  Invalid GitHub issue numbers: {len(invalid_issue_nums)}")
        if invalid_issue_nums:
            self.issues['data_format'].append(f"{len(invalid_issue_nums)} invalid GitHub issue numbers")

        print(f"  Invalid JSON format fields: {invalid_json}")
        if invalid_json > 0:
            self.issues['data_format'].append(f"{invalid_json} fields with invalid JSON format")

    def print_summary(self):
        """Print summary of all issues found."""
        print("\n" + "="*80)
        print("DATA QUALITY SUMMARY")
        print("="*80)

        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            print("\nSUCCESS: NO DATA QUALITY ISSUES FOUND - Database is clean!")
        else:
            print(f"\nWARNING: FOUND {total_issues} DATA QUALITY ISSUES:\n")

            for category, issue_list in self.issues.items():
                if issue_list:
                    print(f"\n{category.upper().replace('_', ' ')}:")
                    for issue in issue_list:
                        print(f"  - {issue}")

        print("\n" + "="*80)

    def close(self):
        """Close database connection."""
        self.conn.close()


if __name__ == '__main__':
    analyzer = DataQualityAnalyzer()
    analyzer.analyze_all()
    analyzer.close()