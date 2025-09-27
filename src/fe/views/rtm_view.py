"""
RTM View Controller

Handles Requirements Traceability Matrix presentation logic.
Transforms backend RTM data into frontend-ready format.
"""

from typing import Any, Dict, List

from .base_view import BaseView


class RTMView(BaseView):
    """RTM-specific view controller."""

    def prepare_data(self, epics_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw epic data into RTM frontend format."""
        prepared_data = {
            "epics": [],
            "metadata": {
                "total_epics": len(epics_data),
                "total_user_stories": 0,
                "total_tests": 0,
                "total_defects": 0,
            },
        }

        for epic_data in epics_data:
            # Prepare epic data
            epic = self._prepare_epic_data(epic_data)
            prepared_data["epics"].append(epic)

            # Update metadata
            prepared_data["metadata"]["total_user_stories"] += epic["metrics"][
                "user_stories_count"
            ]
            prepared_data["metadata"]["total_tests"] += epic["metrics"]["tests_count"]
            prepared_data["metadata"]["total_defects"] += epic["metrics"][
                "defects_count"
            ]

        return prepared_data

    def _prepare_epic_data(self, epic_data: Dict) -> Dict[str, Any]:
        """Prepare individual epic data for frontend."""
        epic = epic_data.get("epic", {})
        user_stories = epic_data.get("user_stories", [])
        tests = epic_data.get("tests", [])
        defects = epic_data.get("defects", [])

        # Calculate metrics
        metrics = self._calculate_epic_metrics(user_stories, tests, defects)

        # Generate components
        component_badges = self._generate_component_badges(epic)
        epic_title_link = self._generate_epic_title_link(epic)

        return {
            "epic": epic,
            "user_stories": user_stories,
            "tests": tests,
            "defects": defects,
            "metrics": metrics,
            "component_badges": component_badges,
            "epic_title_link": epic_title_link,
            "progress": metrics["progress"],
        }

    def _calculate_epic_metrics(
        self, user_stories: List, tests: List, defects: List
    ) -> Dict[str, Any]:
        """Calculate metrics for an epic."""
        # User story metrics
        user_stories_count = len(user_stories)
        completed_stories = sum(
            1 for us in user_stories if us.get("status") == "completed"
        )
        total_points = sum(us.get("story_points", 0) for us in user_stories)
        completed_points = sum(
            us.get("story_points", 0)
            for us in user_stories
            if us.get("status") == "completed"
        )

        # Test metrics
        tests_count = len(tests)
        tests_passed = sum(1 for t in tests if t.get("status") == "passed")
        tests_failed = sum(1 for t in tests if t.get("status") == "failed")
        tests_not_run = tests_count - tests_passed - tests_failed
        test_pass_rate = (tests_passed / tests_count * 100) if tests_count > 0 else 0

        # Defect metrics
        defects_count = len(defects)

        # Progress calculation
        progress = (completed_points / total_points * 100) if total_points > 0 else 0

        return {
            "user_stories_count": user_stories_count,
            "completed_stories": completed_stories,
            "total_points": total_points,
            "completed_points": completed_points,
            "tests_count": tests_count,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_not_run": tests_not_run,
            "test_pass_rate": test_pass_rate,
            "defects_count": defects_count,
            "progress": progress,
        }

    def _generate_component_badges(self, epic: Dict) -> str:
        """Generate component badges HTML."""
        components = epic.get("components", [])
        if isinstance(components, str):
            components = [
                comp.strip() for comp in components.split(",") if comp.strip()
            ]

        badges_html = []
        for component in components:
            component_class = self._get_component_class(component)
            badges_html.append(
                f'<span class="component-badge {component_class}">{component}</span>'
            )

        return " ".join(badges_html)

    def _get_component_class(self, component: str) -> str:
        """Map component to CSS class."""
        component_map = {
            "frontend": "frontend",
            "backend": "backend",
            "database": "database",
            "security": "security",
            "testing": "testing",
            "ci-cd": "ci-cd",
            "documentation": "documentation",
        }
        return component_map.get(component.lower(), "default")

    def _generate_epic_title_link(self, epic: Dict) -> str:
        """Generate epic title link HTML."""
        epic_id = epic.get("epic_id", "")
        title = epic.get("title", "Untitled Epic")
        return f'<a href="/epic/{epic_id}" class="epic-title-link">{title}</a>'

    def render_epic_overview(self, epic_data: Dict) -> str:
        """Render epic overview metrics dashboard."""
        metrics = epic_data["metrics"]
        metric_cards = self.component_service.build_metric_cards_for_overview(metrics)

        return self.component_service.render_metrics_dashboard(
            title="Overview Metrics",
            metric_cards=metric_cards,
            section_label="Epic Metrics Overview",
        )

    def render_epic_card_header(self, epic_data: Dict) -> str:
        """Render epic card header."""
        return self.component_service.render_epic_card_header(
            epic=epic_data["epic"],
            epic_title_link=epic_data["epic_title_link"],
            component_string=epic_data["epic"].get("components", ""),
            component_badges=epic_data["component_badges"],
            progress=epic_data["progress"],
        )
