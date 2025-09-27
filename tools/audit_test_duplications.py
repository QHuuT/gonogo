#!/usr/bin/env python3
"""
Audit des duplications dans la base de données RTM des tests.
Analyse les 907 entrées vs 432 fonctions réelles pour identifier causes et solutions.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability.test import Test
from sqlalchemy import func
from collections import defaultdict


def analyze_test_duplications():
    """Analyse les duplications de tests dans la DB RTM."""
    print("RTM Test Duplication Analysis")
    print("=" * 50)

    session = get_db_session()
    try:
        # 1. Total count
        total_tests = session.query(Test).count()
        print(f"Total test entries in DB: {total_tests}")

        # 2. Duplications by test_function_name + test_file_path
        duplicates_query = (
            session.query(
                Test.test_function_name,
                Test.test_file_path,
                func.count(Test.id).label("count"),
            )
            .group_by(Test.test_function_name, Test.test_file_path)
            .having(func.count(Test.id) > 1)
            .order_by(func.count(Test.id).desc())
        )

        duplicates = duplicates_query.all()
        total_duplicate_entries = sum(
            dup.count - 1 for dup in duplicates
        )  # -1 car on garde 1 copie

        print(f"Unique test+file combinations with duplicates: {len(duplicates)}")
        print(f"Excess entries to remove: {total_duplicate_entries}")
        print(f"Expected final count: {total_tests - total_duplicate_entries}")

        # 3. Top 10 most duplicated
        print("\nTop 10 most duplicated tests:")
        for dup in duplicates[:10]:
            print(
                f"   * {dup.test_function_name}"
                f"({dup.test_file_path}): {dup.count} copies"
            )

        # 4. Duplications by file
        file_duplications = defaultdict(int)
        for dup in duplicates:
            file_duplications[dup.test_file_path] += dup.count - 1

        print("\nFiles with most duplicate entries:")
        sorted_files = sorted(
            file_duplications.items(), key=lambda x: x[1], reverse=True
        )
        for file_path, excess_count in sorted_files[:10]:
            print(f"   * {file_path}: {excess_count} excess entries")

        # 5. Analysis by Epic assignment
        print("\nEpic assignment analysis:")
        tests_with_epic = session.query(Test).filter(Test.epic_id.isnot(None)).count()
        tests_without_epic = session.query(Test).filter(Test.epic_id.is_(None)).count()
        print(f"   * Tests with Epic: {tests_with_epic}")
        print(f"   * Tests without Epic: {tests_without_epic}")

        # 6. Potential causes analysis
        print("\nPotential duplication causes:")

        # Check for tests with different epic assignments but same name+file
        mixed_epic_query = (
            session.query(Test.test_function_name, Test.test_file_path)
            .group_by(Test.test_function_name, Test.test_file_path)
            .having(func.count(func.distinct(Test.epic_id)) > 1)
        )
        mixed_epic_count = mixed_epic_query.count()
        print(f"   * Tests with different Epic assignments: {mixed_epic_count}")

        # Check for different markers for same test
        mixed_markers_query = (
            session.query(Test.test_function_name, Test.test_file_path)
            .group_by(Test.test_function_name, Test.test_file_path)
            .having(func.count(func.distinct(Test.test_type)) > 1)
        )
        mixed_markers_count = mixed_markers_query.count()
        print(f"   * Tests with different test_type markers: {mixed_markers_count}")

        return {
            "total_tests": total_tests,
            "duplicates": len(duplicates),
            "excess_entries": total_duplicate_entries,
            "expected_final": total_tests - total_duplicate_entries,
            "top_duplicates": duplicates[:10],
        }
    finally:
        session.close()


def count_actual_test_functions():
    """Compte les vraies fonctions de test dans les fichiers."""
    print("\nCounting actual test functions in codebase...")

    test_dirs = [
        Path("tests/unit"),
        Path("tests/integration"),
        Path("tests/security"),
        Path("tests/e2e"),
    ]

    total_functions = 0
    for test_dir in test_dirs:
        if test_dir.exists():
            py_files = list(test_dir.rglob("test_*.py"))
            print(f"   {test_dir}: {len(py_files)} files")

            for py_file in py_files:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    functions = [
                        line
                        for line in content.split("\n")
                        if line.strip().startswith("def test_")
                    ]
                    total_functions += len(functions)
                    if len(functions) > 0:
                        print(f"      *{py_file.name}: {len(functions)} test functions")
                except Exception as e:
                    print(f"      ERROR reading {py_file}: {e}")

    print(f"Total actual test functions found: {total_functions}")
    return total_functions


if __name__ == "__main__":
    analysis = analyze_test_duplications()
    actual_count = count_actual_test_functions()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Database entries: {analysis['total_tests']}")
    print(f"Actual functions: {actual_count}")
    print(f"Excess entries: {analysis['excess_entries']}")
    print(f"Expected after cleanup: {analysis['expected_final']}")
    print(f"Gap from reality: {analysis['expected_final'] - actual_count}")

    if analysis["expected_final"] == actual_count:
        print("Perfect match expected after deduplication!")
    else:
        print("Additional investigation needed after basic deduplication")
