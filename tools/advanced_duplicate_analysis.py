#!/usr/bin/env python3
"""
Analyse avancée des 477 entrées excédentaires restantes après déduplication.
Identifie les patterns d'import multiple et autres causes de surplus.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability.test import Test
from sqlalchemy import func, distinct, and_


def analyze_remaining_excess():
    """Analyse les 477 entrées excédentaires restantes."""
    print("Advanced Analysis of Remaining Excess Entries")
    print("=" * 60)

    session = get_db_session()
    try:
        total_tests = session.query(Test).count()
        print(f"Current total tests: {total_tests}")
        print("Expected actual tests: 377")
        print(f"Excess entries: {total_tests - 377}")

        # 1. Analyze by test_type distribution
        print("\n1. Distribution by test_type:")
        type_counts = (
            session.query(Test.test_type, func.count(Test.id).label("count"))
            .group_by(Test.test_type)
            .order_by(func.count(Test.id).desc())
            .all()
        )

        for test_type, count in type_counts:
            print(f"   {test_type or 'NULL'}: {count} entries")

        # 2. Analyze by file patterns
        print("\n2. Top file patterns with most entries:")
        file_counts = (
            session.query(Test.test_file_path, func.count(Test.id).label("count"))
            .group_by(Test.test_file_path)
            .order_by(func.count(Test.id).desc())
            .limit(20)
            .all()
        )

        for file_path, count in file_counts:
            print(f"   {file_path or 'NULL'}: {count} entries")

        # 3. Look for NULL function names (these might be BDD scenarios)
        null_function_names = (
            session.query(Test).filter(Test.test_function_name.is_(None)).count()
        )
        print(f"\n3. Tests with NULL function names: {null_function_names}")

        if null_function_names > 0:
            print("   These might be BDD scenarios with scenario names instead:")
            bdd_scenarios = (
                session.query(
                    Test.bdd_scenario_name, func.count(Test.id).label("count")
                )
                .filter(Test.test_function_name.is_(None))
                .group_by(Test.bdd_scenario_name)
                .limit(10)
                .all()
            )

            for scenario, count in bdd_scenarios:
                print(f"   Scenario '{scenario}': {count} entries")

        # 4. Check for tests with both function name and scenario name
        dual_name_tests = (
            session.query(Test)
            .filter(
                and_(
                    Test.test_function_name.isnot(None),
                    Test.bdd_scenario_name.isnot(None),
                )
            )
            .count()
        )
        print(f"\n4. Tests withboth function_name and scenario_name: {dual_name_tests}")

        # 5. Analyze Epic assignment patterns
        print("\n5. Epic assignment patterns:")
        epic_patterns = (
            session.query(Test.epic_id, func.count(Test.id).label("count"))
            .group_by(Test.epic_id)
            .order_by(func.count(Test.id).desc())
            .all()
        )

        for epic_id, count in epic_patterns[:10]:
            print(f"   Epic {epic_id or 'NULL'}: {count} tests")

        # 6. Look for potential import artifacts
        print("\n6. Potential import artifacts:")

        # Tests in non-existent directories
        bdd_step_tests = (
            session.query(Test)
            .filter(Test.test_file_path.like("%step_definitions%"))
            .count()
        )
        print(f"   BDD step definition files: {bdd_step_tests}")

        # Tests with generic names that might be artifacts
        generic_names = ["test_", "step", "scenario", "when_", "given_", "then_"]
        for generic in generic_names:
            count = (
                session.query(Test)
                .filter(Test.test_function_name.like(f"%{generic}%"))
                .count()
            )
            if count > 50:  # Only show high counts
                print(f"   Tests containing '{generic}': {count}")

        # 7. Check for component distribution
        print("\n7. Component distribution:")
        component_counts = (
            session.query(Test.component, func.count(Test.id).label("count"))
            .group_by(Test.component)
            .order_by(func.count(Test.id).desc())
            .all()
        )

        for component, count in component_counts:
            print(f"   {component or 'NULL'}: {count} entries")

        # 8. Identify truly suspicious entries
        print("\n8. Suspicious patterns analysis:")

        # Tests with identical names in multiple files (beyond what we've already cleaned)
        suspicious_names = (
            session.query(
                Test.test_function_name,
                func.count(distinct(Test.test_file_path)).label("file_count"),
                func.count(Test.id).label("total_count"),
            )
            .filter(Test.test_function_name.isnot(None))
            .group_by(Test.test_function_name)
            .having(func.count(distinct(Test.test_file_path)) > 3)
            .order_by(func.count(Test.id).desc())
            .limit(10)
            .all()
        )

        print("   Functions appearing in 4+ different files:")
        for func_name, file_count, total_count in suspicious_names:
            print(f"   '{func_name}'in {file_count} files, {total_count} total entries")

        return {
            "total": total_tests,
            "excess": total_tests - 377,
            "null_functions": null_function_names,
            "bdd_steps": bdd_step_tests,
            "dual_names": dual_name_tests,
        }

    finally:
        session.close()


def suggest_cleanup_strategies(analysis):
    """Suggère des stratégies de nettoyage basées sur l'analyse."""
    print("\n" + "=" * 60)
    print("CLEANUP STRATEGY SUGGESTIONS")
    print("=" * 60)

    excess = analysis["excess"]
    print(f"Target: Remove {excess} excess entries to reach 377 actual tests")

    strategies = []

    if analysis["bdd_steps"] > 100:
        strategies.append(
            f"1. Remove BDD step definition artifacts ({analysis['bdd_steps']} entries)"
        )
        strategies.append("   - These appear to be import artifacts from step files")

    if analysis["null_functions"] > 50:
        strategies.append(
            f"2. Analyze NULL function name entries ({analysis['null_functions']} entries)"
        )
        strategies.append("   - May be duplicate BDD scenarios or malformed imports")

    if analysis["dual_names"] > 0:
        strategies.append(
            f"3. Resolve dual-name tests ({analysis['dual_names']} entries)"
        )
        strategies.append("   - Tests with both function_name and scenario_name")

    strategies.append("4. Deep file-by-file verification:")
    strategies.append("   - Compare DB entries with actual file contents")
    strategies.append("   - Remove entries for functions that don't exist in files")

    strategies.append("5. Epic-based cleanup:")
    strategies.append("   - Remove unassigned tests that may be orphaned imports")

    for strategy in strategies:
        print(strategy)

    print("\nRecommended next steps:")
    print("1. Focus on BDD step definitions cleanup first")
    print("2. Implement file content verification")
    print("3. Remove malformed entries with NULL critical fields")


if __name__ == "__main__":
    analysis = analyze_remaining_excess()
    suggest_cleanup_strategies(analysis)
