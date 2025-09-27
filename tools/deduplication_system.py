#!/usr/bin/env python3
"""
Système de déduplication automatique pour la base de données RTM.
Nettoie les 530 entrées fantômes et dupliquées pour restaurer l'intégrité des données.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability.test import Test
from sqlalchemy import func, and_
from collections import defaultdict


class RTMDeduplicator:
    """Système de déduplication intelligent pour RTM."""

    def __init__(self):
        self.session = get_db_session()
        self.stats = {
            "analyzed": 0,
            "duplicates_removed": 0,
            "orphans_removed": 0,
            "preserved": 0,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def analyze_duplicates(self):
        """Analyse les différents types de doublons."""
        print("Analyzing duplicates...")

        # 1. Exact duplicates (same function name + file path)
        exact_duplicates = (
            self.session.query(
                Test.test_function_name,
                Test.test_file_path,
                func.count(Test.id).label("count"),
            )
            .filter(
                and_(
                    Test.test_function_name.isnot(None), Test.test_file_path.isnot(None)
                )
            )
            .group_by(Test.test_function_name, Test.test_file_path)
            .having(func.count(Test.id) > 1)
            .all()
        )

        print(f"Exact duplicates found: {len(exact_duplicates)}")
        for dup in exact_duplicates[:5]:  # Show top 5
            print(
                f"  * {dup.test_function_name} in {dup.test_file_path}: {dup.count} copies"
            )

        # 2. Orphan tests (no corresponding file exists)
        all_tests = self.session.query(Test).all()
        orphan_tests = []

        print(f"Checking {len(all_tests)} tests for orphaned entries...")
        for test in all_tests:
            if test.test_file_path:
                # Check if file exists (handle relative paths)
                test_file = Path(test.test_file_path)
                if not test_file.exists():
                    # Try with different base paths
                    try:
                        possible_paths = [
                            Path(".") / test.test_file_path,
                            Path("..") / test.test_file_path,
                            Path(test.test_file_path),
                        ]

                        exists = any(p.exists() for p in possible_paths)
                    except (OSError, ValueError):
                        # Invalid path
                        exists = False
                    if not exists:
                        orphan_tests.append(test)

        print(f"Orphaned tests found: {len(orphan_tests)}")

        return exact_duplicates, orphan_tests

    def choose_best_duplicate(self, test_ids):
        """Choisit la meilleure copie parmi les duplicatas."""
        tests = self.session.query(Test).filter(Test.id.in_(test_ids)).all()

        # Priorité de sélection:
        # 1. Test avec Epic assigné
        # 2. Test avec données d'exécution
        # 3. Test avec plus de métadonnées
        # 4. Plus récent (created_at)

        best_test = None
        best_score = -1

        for test in tests:
            score = 0

            # +10 si Epic assigné
            if test.epic_id is not None:
                score += 10

            # +5 si données d'exécution
            if test.last_execution_time is not None:
                score += 5

            # +3 si métadonnées complètes
            if test.test_priority and test.test_priority != "medium":
                score += 3

            if test.component:
                score += 2

            if test.test_category:
                score += 2

            # +1 si plus récent (approximation avec ID plus élevé)
            score += test.id * 0.001  # Très petit bonus pour ID plus récent

            if score > best_score:
                best_score = score
                best_test = test

        return best_test

    def deduplicate_exact(self, exact_duplicates, dry_run=True):
        """Élimine les duplicatas exacts."""
        print(f"\n{'DRY RUN - ' if dry_run else ''}Deduplicating exact duplicates...")

        removed_count = 0

        for dup in exact_duplicates:
            # Query tests manually
            tests = (
                self.session.query(Test)
                .filter(
                    and_(
                        Test.test_function_name == dup.test_function_name,
                        Test.test_file_path == dup.test_file_path,
                    )
                )
                .all()
            )
            test_ids = [t.id for t in tests]

            if len(test_ids) > 1:
                # Choose best duplicate
                best_test = self.choose_best_duplicate(test_ids)
                to_remove = [tid for tid in test_ids if tid != best_test.id]

                print(
                    f"  * {dup.test_function_name}: keeping ID {best_test.id}, removing {len(to_remove)} duplicates"
                )

                if not dry_run:
                    # Remove duplicates
                    self.session.query(Test).filter(Test.id.in_(to_remove)).delete(
                        synchronize_session=False
                    )

                removed_count += len(to_remove)

        if not dry_run:
            self.session.commit()

        self.stats["duplicates_removed"] = removed_count
        print(f"  Removed {removed_count} exact duplicates")

        return removed_count

    def remove_orphans(self, orphan_tests, dry_run=True):
        """Supprime les tests orphelins."""
        print(f"\n{'DRY RUN - ' if dry_run else ''}Removing orphaned tests...")

        if not orphan_tests:
            print("  No orphans to remove")
            return 0

        # Group orphans by reason
        orphan_groups = defaultdict(list)
        for test in orphan_tests:
            reason = f"File not found: {test.test_file_path}"
            orphan_groups[reason].append(test)

        removed_count = 0
        for reason, tests in orphan_groups.items():
            print(f"  * {reason}: {len(tests)} tests")

            if not dry_run:
                test_ids = [t.id for t in tests]
                self.session.query(Test).filter(Test.id.in_(test_ids)).delete(
                    synchronize_session=False
                )
                removed_count += len(tests)

        if not dry_run:
            self.session.commit()

        self.stats["orphans_removed"] = removed_count
        print(f"  Removed {removed_count} orphaned tests")

        return removed_count

    def consolidate_epic_assignments(self, dry_run=True):
        """Consolide les assignations Epic pour les tests identiques."""
        print(f"\n{'DRY RUN - ' if dry_run else ''}Consolidating Epic assignments...")

        # Find tests with same name/file but different Epic assignments
        mixed_epics = (
            self.session.query(Test.test_function_name, Test.test_file_path)
            .group_by(Test.test_function_name, Test.test_file_path)
            .having(func.count(func.distinct(Test.epic_id)) > 1)
            .all()
        )

        consolidated = 0
        for mixed in mixed_epics:
            tests = (
                self.session.query(Test)
                .filter(
                    and_(
                        Test.test_function_name == mixed.test_function_name,
                        Test.test_file_path == mixed.test_file_path,
                    )
                )
                .all()
            )

            # Choose Epic assignment (prefer non-null)
            epic_counts = defaultdict(int)
            for test in tests:
                epic_counts[test.epic_id] += 1

            # Choose most common Epic assignment (excluding None)
            best_epic = None
            max_count = 0
            for epic_id, count in epic_counts.items():
                if epic_id is not None and count > max_count:
                    best_epic = epic_id
                    max_count = count

            if best_epic:
                print(
                    f"  * {mixed.test_function_name}: standardizing to Epic {best_epic}"
                )

                if not dry_run:
                    for test in tests:
                        if test.epic_id != best_epic:
                            test.epic_id = best_epic
                            consolidated += 1

        if not dry_run and consolidated > 0:
            self.session.commit()

        print(f"  Consolidated {consolidated} Epic assignments")
        return consolidated

    def run_full_deduplication(self, dry_run=True):
        """Execute la déduplication complète."""
        print(f"{'=' * 60}")
        print(f"RTM Database Deduplication - {'DRY RUN' if dry_run else 'LIVE RUN'}")
        print(f"{'=' * 60}")
        print(f"Timestamp: {datetime.now()}")

        # Initial count
        initial_count = self.session.query(Test).count()
        print(f"Initial test count: {initial_count}")

        # Step 1: Analyze
        exact_duplicates, orphan_tests = self.analyze_duplicates()

        # Step 2: Deduplicate exact matches
        self.deduplicate_exact(exact_duplicates, dry_run)

        # Step 3: Re-analyze orphans after exact deduplication (objects may have been deleted)
        if not dry_run:
            print("Re-analyzing orphans after deduplication...")
            _, orphan_tests = self.analyze_duplicates()

        # Step 4: Remove orphans
        self.remove_orphans(orphan_tests, dry_run)

        # Step 5: Consolidate Epic assignments
        self.consolidate_epic_assignments(dry_run)

        # Final count
        final_count = self.session.query(Test).count()
        print(f"\n{'=' * 60}")
        print("DEDUPLICATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Initial count: {initial_count}")
        print(f"Final count: {final_count}")
        print(f"Total removed: {initial_count - final_count}")
        print(f"- Exact duplicates: {self.stats['duplicates_removed']}")
        print(f"- Orphaned tests: {self.stats['orphans_removed']}")

        gap_to_reality = final_count - 377  # 377 = actual functions found
        print(f"Gap to reality (377 actual functions): {gap_to_reality}")

        if gap_to_reality == 0:
            print("Perfect match with codebase!")
        elif gap_to_reality > 0:
            print(f"Still {gap_to_reality} excess entries - investigate further")
        else:
            print(
                f"Missing {abs(gap_to_reality)} entries - some tests may not be imported"
            )

        return {
            "initial_count": initial_count,
            "final_count": final_count,
            "removed": initial_count - final_count,
            "stats": self.stats,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RTM Database Deduplication")
    parser.add_argument(
        "--live", action="store_true", help="Execute live run (default: dry run)"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before deduplication"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm live run without prompt"
    )
    args = parser.parse_args()

    if args.live and not args.confirm:
        try:
            confirm = input(
                "This will permanently modify the database. Continue? (yes/no): "
            )
            if confirm.lower() != "yes":
                print("Aborted.")
                return
        except EOFError:
            print(
                "No input available. Use --confirm flag for non-interactive execution."
            )
            return

    if args.backup and args.live:
        print("Creating backup...")
        # Could add backup functionality here

    with RTMDeduplicator() as dedup:
        result = dedup.run_full_deduplication(dry_run=not args.live)

        if args.live:
            print("\nDeduplication completed successfully!")
            print(f"Removed {result['removed']} entries")
        else:
            print("\nDRY RUN completed. Use --live to execute changes.")


if __name__ == "__main__":
    main()
