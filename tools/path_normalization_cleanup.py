#!/usr/bin/env python3
"""
Normalisation des chemins de fichiers dans la DB RTM.
Elimine les doublons causés par les différents path separators (\ vs /).
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import get_db_session
from be.models.traceability.test import Test
from collections import defaultdict


def normalize_paths_cleanup():
    """Normalise les chemins et supprime les doublons de path separators."""
    print("Path Normalization Cleanup")
    print("=" * 60)

    session = get_db_session()
    try:
        # 1. Identifier les doublons de path separators
        print("1. Identifying path separator duplicates...")

        all_tests = session.query(Test).all()
        path_groups = defaultdict(list)

        for test in all_tests:
            if test.test_file_path:
                # Normaliser vers Unix style
                normalized_path = test.test_file_path.replace("\\", "/")
                key = (normalized_path, test.test_function_name)
                path_groups[key].append(test)

        # 2. Identifier les vrais doublons
        duplicates = {k: v for k, v in path_groups.items() if len(v) > 1}

        print(f"Found {len(duplicates)} function+path combinations with duplicates")

        total_excess = sum(len(tests) - 1 for tests in duplicates.values())
        print(f"Total excess entries from path separators: {total_excess}")

        # 3. Montrer quelques exemples
        print("\nTop 10 path separator duplicates:")
        sorted_duplicates = sorted(
            duplicates.items(), key=lambda x: len(x[1]), reverse=True
        )
        for (norm_path, func_name), tests in sorted_duplicates[:10]:
            paths = [t.test_file_path for t in tests]
            unique_paths = set(paths)
            print(f"  {func_name} in {norm_path}: {len(tests)} copies")
            for path in unique_paths:
                count = paths.count(path)
                print(f"    '{path}': {count} times")

        return duplicates, total_excess

    finally:
        session.close()


def execute_path_normalization(duplicates, dry_run=True):
    """Execute la normalisation des chemins."""
    print(
        f"\n{'DRY RUN - ' if dry_run else ''}Normalizing paths and removing duplicates..."
    )

    session = get_db_session()
    try:
        removed_count = 0
        normalized_count = 0

        for (normalized_path, func_name), tests in duplicates.items():
            if len(tests) > 1:
                # Choisir le meilleur test (même logique que déduplication)
                best_test = choose_best_test(tests)

                # Normaliser le chemin du meilleur test
                if best_test.test_file_path != normalized_path:
                    if not dry_run:
                        best_test.test_file_path = normalized_path
                    normalized_count += 1

                # Supprimer les autres
                to_remove = [t for t in tests if t.id != best_test.id]

                if to_remove:
                    print(
                        f"  {func_name}: keeping ID {best_test.id}, removing {len(to_remove)} duplicates"
                    )

                    if not dry_run:
                        for test in to_remove:
                            session.delete(test)

                    removed_count += len(to_remove)

        if not dry_run:
            session.commit()

        print(f"Normalized {normalized_count} paths")
        print(f"Removed {removed_count} path separator duplicates")

        return removed_count, normalized_count

    finally:
        session.close()


def choose_best_test(tests):
    """Choisit le meilleur test parmi les duplicatas."""
    # Même logique que dans deduplication_system.py
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

        # +1 préférence pour Unix style paths
        if (
            test.test_file_path
            and "/" in test.test_file_path
            and "\\" not in test.test_file_path
        ):
            score += 1

        # +1 si plus récent (approximation avec ID plus élevé)
        score += test.id * 0.001

        if score > best_score:
            best_score = score
            best_test = test

    return best_test


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RTM Path Normalization Cleanup")
    parser.add_argument(
        "--live", action="store_true", help="Execute live run (default: dry run)"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm live run without prompt"
    )
    args = parser.parse_args()

    if args.live and not args.confirm:
        try:
            confirm = input(
                "This will permanently modify file paths in the database. Continue? (yes/no): "
            )
            if confirm.lower() != "yes":
                print("Aborted.")
                return
        except EOFError:
            print(
                "No input available. Use --confirm flag for non-interactive execution."
            )
            return

    # Step 1: Analyze
    duplicates, total_excess = normalize_paths_cleanup()

    # Step 2: Execute cleanup
    removed_count, normalized_count = execute_path_normalization(
        duplicates, dry_run=not args.live
    )

    print(f"\n{'=' * 60}")
    print("PATH NORMALIZATION SUMMARY")
    print("=" * 60)
    print(f"Path separator duplicates found: {len(duplicates)}")
    print(f"Excess entries from path separators: {total_excess}")
    print(f"Paths normalized: {normalized_count}")
    print(f"Duplicate entries removed: {removed_count}")

    if args.live:
        session = get_db_session()
        try:
            final_count = session.query(Test).count()
            print(f"Final test count: {final_count}")
            remaining_excess = final_count - 377
            print(f"Remaining excess after cleanup: {remaining_excess}")

            if remaining_excess <= 50:
                print("Cleanup nearly complete! Remaining excess is minimal.")
            else:
                print(
                    f"Further investigation needed for {remaining_excess} remaining entries."
                )

        finally:
            session.close()
    else:
        print("DRY RUN completed. Use --live --confirm to execute changes.")


if __name__ == "__main__":
    main()
