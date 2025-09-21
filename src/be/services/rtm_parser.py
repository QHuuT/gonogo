"""
RTM Markdown Parser for migrating existing RTM data to database.

Parses Requirements Traceability Matrix markdown files and converts them to database entities.

Related Issue: US-00054 - Database models and migration foundation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..models.traceability import Epic, UserStory, Defect, Test
from ..database import get_db_session


class RTMMarkdownParser:
    """Parser for converting RTM markdown files to database entities."""

    def __init__(self):
        self.epic_pattern = r'(EP-\d{5})'
        self.user_story_pattern = r'(US-\d{5})'
        self.defect_pattern = r'(DEF-\d{5})'
        self.test_pattern = r'test[_\s]+([a-zA-Z0-9_]+)'
        self.github_issue_pattern = r'#(\d+)'

    def parse_rtm_file(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Parse an RTM markdown file and extract entities.

        Returns:
            Dict with keys: 'epics', 'user_stories', 'defects', 'tests'
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            'epics': self._extract_epics(content),
            'user_stories': self._extract_user_stories(content),
            'defects': self._extract_defects(content),
            'tests': self._extract_tests(content)
        }

    def _extract_epics(self, content: str) -> List[Dict]:
        """Extract Epic information from markdown content."""
        epics = []
        epic_matches = re.finditer(self.epic_pattern, content)

        for match in epic_matches:
            epic_id = match.group(1)
            # Find the line containing this epic
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if epic_id in line:
                    title = self._extract_title_from_line(line, epic_id)
                    description = self._extract_description(lines, i)

                    epic_data = {
                        'epic_id': epic_id,
                        'title': title or f"Epic {epic_id}",
                        'description': description,
                        'status': self._extract_status_from_context(lines, i),
                        'priority': self._extract_priority_from_context(lines, i),
                        'business_value': self._extract_business_value(lines, i)
                    }
                    epics.append(epic_data)
                    break

        return epics

    def _extract_user_stories(self, content: str) -> List[Dict]:
        """Extract User Story information from markdown content."""
        user_stories = []
        us_matches = re.finditer(self.user_story_pattern, content)

        for match in us_matches:
            us_id = match.group(1)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if us_id in line:
                    title = self._extract_title_from_line(line, us_id)
                    github_issue = self._extract_github_issue_from_context(lines, i)
                    epic_id = self._find_parent_epic(lines, i)

                    us_data = {
                        'user_story_id': us_id,
                        'title': title or f"User Story {us_id}",
                        'description': self._extract_description(lines, i),
                        'github_issue_number': github_issue,
                        'epic_reference': epic_id,  # Will be resolved to DB ID later
                        'story_points': self._extract_story_points(lines, i),
                        'priority': self._extract_priority_from_context(lines, i),
                        'implementation_status': self._extract_implementation_status(lines, i)
                    }
                    user_stories.append(us_data)
                    break

        return user_stories

    def _extract_defects(self, content: str) -> List[Dict]:
        """Extract Defect information from markdown content."""
        defects = []
        def_matches = re.finditer(self.defect_pattern, content)

        for match in def_matches:
            def_id = match.group(1)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if def_id in line:
                    title = self._extract_title_from_line(line, def_id)
                    github_issue = self._extract_github_issue_from_context(lines, i)

                    def_data = {
                        'defect_id': def_id,
                        'title': title or f"Defect {def_id}",
                        'description': self._extract_description(lines, i),
                        'github_issue_number': github_issue,
                        'severity': self._extract_severity(lines, i),
                        'priority': self._extract_priority_from_context(lines, i),
                        'status': self._extract_status_from_context(lines, i),
                        'defect_type': self._extract_defect_type(lines, i)
                    }
                    defects.append(def_data)
                    break

        return defects

    def _extract_tests(self, content: str) -> List[Dict]:
        """Extract Test information from markdown content."""
        tests = []
        # Look for test file patterns and test function patterns
        test_file_pattern = r'tests?[/\\]([a-zA-Z0-9_/\\]+\.py)'
        test_files = re.finditer(test_file_pattern, content)

        for match in test_files:
            test_path = match.group(0)
            full_path = match.group(1)

            # Extract test type from path
            test_type = 'unit'
            if 'integration' in test_path.lower():
                test_type = 'integration'
            elif 'e2e' in test_path.lower():
                test_type = 'e2e'
            elif 'security' in test_path.lower():
                test_type = 'security'
            elif 'bdd' in test_path.lower() or 'feature' in test_path.lower():
                test_type = 'bdd'

            test_data = {
                'test_type': test_type,
                'test_file_path': test_path,
                'title': f"Test: {Path(full_path).stem}",
                'description': f"Test file: {test_path}",
                'test_function_name': self._extract_test_function_from_context(content, test_path)
            }
            tests.append(test_data)

        return tests

    def _extract_title_from_line(self, line: str, entity_id: str) -> Optional[str]:
        """Extract title from a line containing an entity ID."""
        # Remove the entity ID and markdown formatting
        title = line.replace(entity_id, '').strip()
        title = re.sub(r'^#+\s*', '', title)  # Remove markdown headers
        title = re.sub(r'^\*+\s*', '', title)  # Remove bullet points
        title = re.sub(r'^\-+\s*', '', title)  # Remove dashes
        title = title.strip(':').strip()
        return title if title else None

    def _extract_description(self, lines: List[str], start_index: int) -> Optional[str]:
        """Extract description from lines following the entity line."""
        description_lines = []
        for i in range(start_index + 1, min(start_index + 5, len(lines))):
            line = lines[i].strip()
            if line and not re.match(r'^(EP-|US-|DEF-|###|##|#)', line):
                description_lines.append(line)
            elif line == '':
                continue
            else:
                break

        return ' '.join(description_lines) if description_lines else None

    def _extract_github_issue_from_context(self, lines: List[str], start_index: int) -> Optional[int]:
        """Extract GitHub issue number from surrounding context."""
        for i in range(max(0, start_index - 2), min(start_index + 3, len(lines))):
            github_match = re.search(self.github_issue_pattern, lines[i])
            if github_match:
                return int(github_match.group(1))
        return None

    def _find_parent_epic(self, lines: List[str], start_index: int) -> Optional[str]:
        """Find the parent Epic by looking backwards in the file."""
        for i in range(start_index, -1, -1):
            epic_match = re.search(self.epic_pattern, lines[i])
            if epic_match:
                return epic_match.group(1)
        return None

    def _extract_status_from_context(self, lines: List[str], start_index: int) -> str:
        """Extract status from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3]).lower()
        if 'completed' in context or 'done' in context:
            return 'completed'
        elif 'in progress' in context or 'in-progress' in context:
            return 'in_progress'
        elif 'blocked' in context:
            return 'blocked'
        else:
            return 'planned'

    def _extract_priority_from_context(self, lines: List[str], start_index: int) -> str:
        """Extract priority from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3]).lower()
        if 'critical' in context:
            return 'critical'
        elif 'high' in context:
            return 'high'
        elif 'low' in context:
            return 'low'
        else:
            return 'medium'

    def _extract_story_points(self, lines: List[str], start_index: int) -> int:
        """Extract story points from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3])
        points_match = re.search(r'(\d+)\s*points?', context, re.IGNORECASE)
        if points_match:
            return int(points_match.group(1))
        return 0

    def _extract_business_value(self, lines: List[str], start_index: int) -> Optional[str]:
        """Extract business value from context."""
        for i in range(start_index, min(start_index + 10, len(lines))):
            line = lines[i].lower()
            if 'business value' in line or 'value' in line:
                return lines[i].strip()
        return None

    def _extract_implementation_status(self, lines: List[str], start_index: int) -> str:
        """Extract implementation status from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3]).lower()
        if 'done' in context or 'completed' in context:
            return 'done'
        elif 'in review' in context or 'review' in context:
            return 'in_review'
        elif 'in progress' in context or 'in-progress' in context:
            return 'in_progress'
        elif 'blocked' in context:
            return 'blocked'
        else:
            return 'todo'

    def _extract_severity(self, lines: List[str], start_index: int) -> str:
        """Extract defect severity from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3]).lower()
        if 'critical' in context:
            return 'critical'
        elif 'high' in context:
            return 'high'
        elif 'low' in context:
            return 'low'
        else:
            return 'medium'

    def _extract_defect_type(self, lines: List[str], start_index: int) -> str:
        """Extract defect type from context."""
        context = ' '.join(lines[max(0, start_index - 1):start_index + 3]).lower()
        if 'security' in context:
            return 'security'
        elif 'performance' in context:
            return 'performance'
        elif 'regression' in context:
            return 'regression'
        elif 'enhancement' in context:
            return 'enhancement'
        else:
            return 'bug'

    def _extract_test_function_from_context(self, content: str, test_path: str) -> Optional[str]:
        """Extract test function name from context."""
        # Find lines near the test path
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if test_path in line:
                # Look for test function patterns in nearby lines
                for j in range(max(0, i - 2), min(i + 3, len(lines))):
                    func_match = re.search(r'test[_\s]+([a-zA-Z0-9_]+)', lines[j])
                    if func_match:
                        return func_match.group(1)
        return None


class RTMDataMigrator:
    """Migrates parsed RTM data to the database."""

    def __init__(self):
        self.parser = RTMMarkdownParser()
        self.epic_id_mapping = {}  # Maps epic_id strings to database IDs

    def migrate_from_file(self, file_path: str) -> Dict[str, int]:
        """
        Migrate RTM data from a markdown file to the database.

        Returns:
            Dict with counts of migrated entities
        """
        parsed_data = self.parser.parse_rtm_file(file_path)
        db = get_db_session()

        try:
            # Migrate in order: Epics -> UserStories -> Tests -> Defects
            epic_count = self._migrate_epics(db, parsed_data['epics'])
            us_count = self._migrate_user_stories(db, parsed_data['user_stories'])
            test_count = self._migrate_tests(db, parsed_data['tests'])
            defect_count = self._migrate_defects(db, parsed_data['defects'])

            db.commit()

            return {
                'epics': epic_count,
                'user_stories': us_count,
                'tests': test_count,
                'defects': defect_count
            }

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _migrate_epics(self, db, epic_data: List[Dict]) -> int:
        """Migrate Epic data to database."""
        count = 0
        for data in epic_data:
            # Check if epic already exists
            existing = db.query(Epic).filter(Epic.epic_id == data['epic_id']).first()
            if existing:
                continue

            epic = Epic(
                epic_id=data['epic_id'],
                title=data['title'],
                description=data.get('description'),
                business_value=data.get('business_value'),
                status=data.get('status', 'planned'),
                priority=data.get('priority', 'medium')
            )
            db.add(epic)
            db.flush()  # Get the ID without committing
            self.epic_id_mapping[data['epic_id']] = epic.id
            count += 1

        return count

    def _migrate_user_stories(self, db, us_data: List[Dict]) -> int:
        """Migrate User Story data to database."""
        count = 0
        for data in us_data:
            # Skip if no GitHub issue number
            if not data.get('github_issue_number'):
                continue

            # Check if user story already exists
            existing = db.query(UserStory).filter(
                UserStory.user_story_id == data['user_story_id']
            ).first()
            if existing:
                continue

            # Resolve epic reference
            epic_db_id = None
            if data.get('epic_reference'):
                epic_db_id = self.epic_id_mapping.get(data['epic_reference'])

            if epic_db_id:  # Only create if we have a valid epic reference
                us = UserStory(
                    user_story_id=data['user_story_id'],
                    epic_id=epic_db_id,
                    github_issue_number=data['github_issue_number'],
                    title=data['title'],
                    description=data.get('description'),
                    story_points=data.get('story_points', 0),
                    priority=data.get('priority', 'medium'),
                    implementation_status=data.get('implementation_status', 'todo')
                )
                db.add(us)
                count += 1

        return count

    def _migrate_tests(self, db, test_data: List[Dict]) -> int:
        """Migrate Test data to database."""
        count = 0
        for data in test_data:
            # Check if test already exists
            existing = db.query(Test).filter(
                Test.test_file_path == data['test_file_path']
            ).first()
            if existing:
                continue

            test = Test(
                test_type=data['test_type'],
                test_file_path=data['test_file_path'],
                title=data['title'],
                description=data.get('description'),
                test_function_name=data.get('test_function_name')
            )
            db.add(test)
            count += 1

        return count

    def _migrate_defects(self, db, defect_data: List[Dict]) -> int:
        """Migrate Defect data to database."""
        count = 0
        for data in defect_data:
            # Skip if no GitHub issue number
            if not data.get('github_issue_number'):
                continue

            # Check if defect already exists
            existing = db.query(Defect).filter(
                Defect.defect_id == data['defect_id']
            ).first()
            if existing:
                continue

            defect = Defect(
                defect_id=data['defect_id'],
                github_issue_number=data['github_issue_number'],
                title=data['title'],
                description=data.get('description'),
                severity=data.get('severity', 'medium'),
                priority=data.get('priority', 'medium'),
                status=data.get('status', 'planned'),
                defect_type=data.get('defect_type', 'bug')
            )
            db.add(defect)
            count += 1

        return count