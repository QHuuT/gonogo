"""
Frontend Component Service

Provides high-level component generation methods.
This service knows how to build complex UI components from data,
abstracting the template details from backend services.
"""

from typing import Any, Dict, List, Optional

from .template_service import TemplateService


class ComponentService:
    """High-level component generation service."""

    def __init__(self, template_service: Optional[TemplateService] = None):
        """Initialize component service."""
        self.template_service = template_service or TemplateService()

    def render_metric_card(
        self,
        card_type: str,
        number: Any,
        label: str,
        description: str = "",
        aria_label: str = "",
    ) -> str:
        """Render a metric card component."""
        return self.template_service.render_component(
            "metric_card",
            card_type=card_type,
            number=number,
            label=label,
            description=description,
            aria_label=aria_label or f"{label} metric",
        )

    def render_metrics_dashboard(
        self,
        title: str,
        metric_cards: List[str],
        heading_level: str = "3",
        section_label: str = "",
    ) -> str:
        """Render a metrics dashboard with multiple cards."""
        return self.template_service.render_component(
            "metrics_dashboard",
            dashboard_title=title,
            heading_level=heading_level,
            section_label=section_label or f"{title} Overview",
            metric_cards="\n                        ".join(metric_cards),
        )

    def render_epic_card_header(
        self,
        epic: Any,
        epic_title_link: str,
        component_string: str,
        component_badges: str,
        progress: float,
    ) -> str:
        """Render an epic card header component."""
        return self.template_service.render_component(
            "epic_card_header",
            epic=epic,
            epic_title_link=epic_title_link,
            component_string=component_string,
            component_badges=component_badges,
            progress=progress,
        )

    def render_filter_button(
        self,
        button_type: str,
        data_attr: str,
        data_value: str,
        filter_group: str,
        filter_value: str,
        onclick_handler: str,
        label: str,
        active: bool = False,
    ) -> str:
        """Render a filter button component."""
        return self.template_service.render_component(
            "filter_button",
            button_type=button_type,
            data_attr=data_attr,
            data_value=data_value,
            filter_group=filter_group,
            filter_value=filter_value,
            onclick_handler=onclick_handler,
            label=label,
            active=active,
        )

    def render_filter_section(
        self,
        filter_type: str,
        title: str,
        filter_buttons: List[str],
        aria_label: str = "",
    ) -> str:
        """Render a filter section with multiple buttons."""
        return self.template_service.render_component(
            "filter_section",
            filter_type=filter_type,
            title=title,
            aria_label=aria_label or f"{filter_type} Filters",
            filter_buttons="\n        ".join(filter_buttons),
        )

    def render_collapsible_section(
        self,
        section_type: str,
        section_id: str,
        epic_id: str,
        title: str,
        count: int,
        content: str,
        aria_label: str = "",
    ) -> str:
        """Render a collapsible section component."""
        return self.template_service.render_component(
            "collapsible_section",
            section_type=section_type,
            section_id=section_id,
            epic_id=epic_id,
            title=title,
            count=count,
            aria_label=aria_label or section_type,
            content=content,
        )

    def build_metric_cards_for_overview(self, metrics: Dict[str, Any]) -> List[str]:
        """Build metric cards for overview dashboard."""
        cards = []

        # User Stories card
        if "user_stories_count" in metrics:
            cards.append(
                self.render_metric_card(
                    card_type="info",
                    number=metrics["user_stories_count"],
                    label="User Stories",
                    description="Total stories in epic",
                )
            )

        # Story Points card
        if "completed_points" in metrics and "total_points" in metrics:
            completed = metrics["completed_points"]
            total = metrics["total_points"]
            card_type = (
                "success"
                if completed == total
                else "warning"
                if completed > 0
                else "info"
            )
            cards.append(
                self.render_metric_card(
                    card_type=card_type,
                    number=f"{completed}/{total}",
                    label="Story Points",
                    description="Completed vs Total",
                )
            )

        # Tests card
        if "tests_count" in metrics:
            cards.append(
                self.render_metric_card(
                    card_type="success" if metrics["tests_count"] > 0 else "info",
                    number=metrics["tests_count"],
                    label="Tests",
                    description="Total test cases",
                )
            )

        # Test Pass Rate card
        if "test_pass_rate" in metrics:
            rate = metrics["test_pass_rate"]
            card_type = (
                "success" if rate >= 80 else "warning" if rate >= 60 else "danger"
            )
            description = ""
            if "tests_passed" in metrics:
                description = f"{metrics['tests_passed']} passed, {metrics.get('tests_failed', 0)} failed, {metrics.get('tests_not_run', 0)} not run"

            cards.append(
                self.render_metric_card(
                    card_type=card_type,
                    number=f"{rate:.1f}%",
                    label="Pass Rate",
                    description=description,
                )
            )

        # Defects card
        if "defects_count" in metrics:
            cards.append(
                self.render_metric_card(
                    card_type="danger" if metrics["defects_count"] > 0 else "success",
                    number=metrics["defects_count"],
                    label="Defects",
                    description="Open issues to resolve",
                )
            )

        return cards
