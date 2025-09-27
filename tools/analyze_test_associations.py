#!/usr/bin/env python3
"""
Test Association Discovery Tool

Scans all test files to discover existing US/Epic/Component associations
from various patterns (BDD headers, docstrings, file paths).
"""

import re
import json
from pathlib import Path
from typing import Dict, Set
from collections import defaultdict


class TestAssociationAnalyzer:
    def __init__(self, test_root="tests"):
        self.test_root = Path(test_root)
        self.associations = defaultdict(
            lambda: {
                "user_stories": set(),
                "epics": set(),
                "components": set(),
                "defects": set(),
                "test_type": None,
                "file_path": None,
            }
        )

    def analyze_all_tests(self):
        """Scan all test files and discover associations."""
        print("Analyzing test files for associations...")
        print()

        # Find all test files
        test_files = list(self.test_root.rglob("test_*.py"))
        test_files += list(self.test_root.rglob("*_test.py"))
        feature_files = list(self.test_root.rglob("*.feature"))

        print(
            f"Found {len(test_files)}test files and {len(feature_files)} feature files"
        )
        print()

        # Analyze Python test files
        for test_file in test_files:
            self._analyze_test_file(test_file)

        # Analyze BDD feature files
        for feature_file in feature_files:
            self._analyze_feature_file(feature_file)

        return self.associations

    def _analyze_test_file(self, file_path: Path):
        """Analyze a single Python test file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = file_path.relative_to(self.test_root)
            key = str(relative_path)

            # Determine test type from path
            test_type = self._determine_test_type(file_path)
            self.associations[key]["test_type"] = test_type
            self.associations[key]["file_path"] = str(file_path)

            # Extract from docstring patterns
            us_from_docstring = self._extract_us_from_docstring(content)
            epic_from_docstring = self._extract_epic_from_docstring(content)
            defects_from_docstring = self._extract_defects_from_docstring(content)

            self.associations[key]["user_stories"].update(us_from_docstring)
            self.associations[key]["epics"].update(epic_from_docstring)
            self.associations[key]["defects"].update(defects_from_docstring)

            # Infer component from path
            component = self._infer_component_from_path(file_path)
            if component:
                self.associations[key]["components"].add(component)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _analyze_feature_file(self, file_path: Path):
        """Analyze a BDD feature file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = file_path.relative_to(self.test_root)
            key = str(relative_path)

            self.associations[key]["test_type"] = "bdd"
            self.associations[key]["file_path"] = str(file_path)

            # Extract from BDD header comments
            us_from_bdd = self._extract_us_from_bdd_header(content)
            self.associations[key]["user_stories"].update(us_from_bdd)

            # Extract epic from BDD header
            epic_from_bdd = self._extract_epic_from_bdd_header(content)
            if epic_from_bdd:
                self.associations[key]["epics"].add(epic_from_bdd)

            defects_from_bdd = self._extract_defects_from_docstring(content)
            self.associations[key]["defects"].update(defects_from_bdd)

            # Infer component from tags
            components = self._extract_components_from_bdd_tags(content)
            self.associations[key]["components"].update(components)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _determine_test_type(self, file_path: Path) -> str:
        """Determine test type from file path."""
        path_str = str(file_path)
        if "/unit/" in path_str or "\\unit\\" in path_str:
            return "unit"
        elif "/integration/" in path_str or "\\integration\\" in path_str:
            return "integration"
        elif "/e2e/" in path_str or "\\e2e\\" in path_str:
            return "e2e"
        elif "/functional/" in path_str or "\\functional\\" in path_str:
            return "functional"
        elif "/bdd/" in path_str or "\\bdd\\" in path_str:
            return "bdd"
        else:
            return "unknown"

    def _extract_us_from_docstring(self, content: str) -> Set[str]:
        """Extract US references from docstrings."""
        us_refs = set()

        # Pattern: Related Issue: US-00054
        pattern1 = re.findall(r"Related Issue:\s*(US-\d{5})", content, re.IGNORECASE)
        us_refs.update(pattern1)

        # Pattern: US-00054 anywhere in docstring
        pattern2 = re.findall(r"(US-\d{5})", content)
        us_refs.update(pattern2)

        return us_refs

    def _extract_epic_from_docstring(self, content: str) -> Set[str]:
        """Extract Epic references from docstrings."""
        epic_refs = set()

        # Pattern: Parent Epic: EP-00005
        pattern1 = re.findall(r"Parent Epic:\s*(EP-\d{5})", content, re.IGNORECASE)
        epic_refs.update(pattern1)

        # Pattern: EP-00005 anywhere in docstring
        pattern2 = re.findall(r"(EP-\d{5})", content)
        epic_refs.update(pattern2)

        return epic_refs

    def _extract_defects_from_docstring(self, content: str) -> Set[str]:
        """Extract defect references from docstrings."""
        defect_refs = set(re.findall(r"(DEF-\d{3,5})", content, re.IGNORECASE))
        return {f"DEF-{match.upper().split('-')[-1].zfill(5)}" for match in defect_refs}

    def _extract_us_from_bdd_header(self, content: str) -> Set[str]:
        """Extract US references from BDD feature file headers."""
        us_refs = set()

        # Pattern: # Linked to: US-001, US-002
        pattern = re.findall(r"#\s*Linked to:\s*([^\n]+)", content, re.IGNORECASE)
        for match in pattern:
            # Extract all US-XXX patterns from the line
            us_matches = re.findall(r"US-(\d{3,5})", match)
            for us_num in us_matches:
                # Normalize to US-00XXX format
                us_refs.add(f"US-{us_num.zfill(5)}")

        return us_refs

    def _extract_epic_from_bdd_header(self, content: str) -> str:
        """Extract Epic reference from BDD feature file headers."""
        # Pattern: # Linked to: US-001, US-002 (Epic Name)
        pattern = re.search(r"#\s*Linked to:.*?\(([^)]+)\)", content, re.IGNORECASE)
        if pattern:
            epic_name = pattern.group(1).strip()
            # Try to map epic name to epic ID (manual mapping for known epics)
            epic_mapping = {
                "Blog Content Epic": "EP-00001",
                "Comment System Epic": "EP-00002",
                "Privacy and Consent Epic": "EP-00003",
                "GitHub Workflow Integration": "EP-00004",
                "Requirements Traceability Matrix Automation": "EP-00005",
            }
            return epic_mapping.get(epic_name, None)
        return None

    def _extract_components_from_bdd_tags(self, content: str) -> Set[str]:
        """Extract component tags from BDD feature files."""
        components = set()

        # Look for component tags like @backend, @frontend
        tags = re.findall(r"@(\w+)", content)

        component_keywords = [
            "backend",
            "frontend",
            "database",
            "security",
            "auth",
            "blog",
            "comment",
            "gdpr",
            "api",
            "ui",
        ]

        for tag in tags:
            if tag.lower() in component_keywords:
                if tag.lower() in ["auth", "blog", "comment", "api"]:
                    components.add("backend")
                elif tag.lower() in ["ui"]:
                    components.add("frontend")
                elif tag.lower() in ["gdpr", "security"]:
                    components.add("security")
                else:
                    components.add(tag.lower())

        return components

    def _infer_component_from_path(self, file_path: Path) -> str:
        """Infer component from file path."""
        path_str = str(file_path).lower()

        if "/backend/" in path_str or "\\backend\\" in path_str:
            return "backend"
        elif "/frontend/" in path_str or "\\frontend\\" in path_str:
            return "frontend"
        elif "/database/" in path_str or "\\database\\" in path_str:
            return "database"
        elif "/security/" in path_str or "\\security\\" in path_str:
            return "security"
        elif "/shared/" in path_str or "\\shared\\" in path_str:
            return "shared"

        # Infer from keywords in path
        if "auth" in path_str or "login" in path_str:
            return "backend"
        elif "blog" in path_str or "post" in path_str:
            return "backend"
        elif "comment" in path_str:
            return "backend"
        elif "gdpr" in path_str:
            return "security"
        elif "rtm" in path_str:
            return "backend"

        return None

    def generate_report(self, associations: Dict):
        """Generate a human-readable report."""
        print("\n" + "=" * 80)
        print("TEST ASSOCIATION ANALYSIS REPORT")
        print("=" * 80 + "\n")

        # Count statistics
        total_tests = len(associations)
        tests_with_us = sum(1 for a in associations.values() if a["user_stories"])
        tests_with_epic = sum(1 for a in associations.values() if a["epics"])
        tests_with_component = sum(1 for a in associations.values() if a["components"])
        tests_with_defects = sum(1 for a in associations.values() if a["defects"])

        print("STATISTICS:")
        print(f"   Total test files analyzed: {total_tests}")
        print(f"   Tests with User Story associations: {tests_with_us}")
        print(f"   Tests with Epic associations: {tests_with_epic}")
        print(f"   Tests with Component assignments: {tests_with_component}")
        print(f"   Tests with Defect references: {tests_with_defects}")
        print(f"   Orphaned tests:{total_tests - max(tests_with_us, tests_with_epic)}")
        print()

        # Test type breakdown
        test_types = defaultdict(int)
        for assoc in associations.values():
            test_types[assoc["test_type"]] += 1

        print("TEST TYPE DISTRIBUTION:")
        for test_type, count in sorted(test_types.items()):
            print(f"   {test_type}: {count}")
        print()

        # User story coverage
        all_us = set()
        for assoc in associations.values():
            all_us.update(assoc["user_stories"])

        print(f"DISCOVERED USER STORIES: {len(all_us)}")
        if all_us:
            for us in sorted(all_us):
                test_count = sum(
                    1 for a in associations.values() if us in a["user_stories"]
                )
                print(f"   {us}: {test_count} test(s)")
        print()

        # Sample associations
        print("SAMPLE ASSOCIATIONS (first 5):")
        for i, (key, assoc) in enumerate(list(associations.items())[:5]):
            if assoc["user_stories"] or assoc["epics"]:
                print(f"\n   File: {key}")
                print(f"   Type: {assoc['test_type']}")
                if assoc["user_stories"]:
                    print(f"   User Stories:{', '.join(sorted(assoc['user_stories']))}")
                if assoc["epics"]:
                    print(f"   Epics: {', '.join(sorted(assoc['epics']))}")
                if assoc["components"]:
                    print(f"   Components: {', '.join(sorted(assoc['components']))}")
                if assoc["defects"]:
                    print(f"   Defects: {', '.join(sorted(assoc['defects']))}")
        print()

    def save_mapping(self, associations: Dict, output_file="test_associations.json"):
        """Save associations to JSON file."""
        # Convert sets to lists for JSON serialization
        serializable = {}
        for key, value in associations.items():
            serializable[key] = {
                "user_stories": list(value["user_stories"]),
                "epics": list(value["epics"]),
                "components": list(value["components"]),
                "defects": list(value["defects"]),
                "test_type": value["test_type"],
                "file_path": value["file_path"],
            }

        with open(output_file, "w") as f:
            json.dump(serializable, f, indent=2)

        print(f"Saved associations to {output_file}")


if __name__ == "__main__":
    analyzer = TestAssociationAnalyzer()
    associations = analyzer.analyze_all_tests()
    analyzer.generate_report(associations)
    analyzer.save_mapping(associations)
