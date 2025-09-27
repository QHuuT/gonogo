"""
Frontend Template Service

Handles all template rendering operations for the frontend.
Provides a clean interface between backend data and frontend presentation.

This service replaces embedded template logic in backend services,
creating a proper separation of concerns.
"""

import os
from pathlib import Path
from typing import Any, List, Optional

from jinja2 import Environment, FileSystemLoader


class TemplateService:
    """Frontend template rendering service with organized template management."""

    def __init__(self, template_base_path: Optional[str] = None):
        """Initialize template service with proper frontend paths."""
        if template_base_path is None:
            # Default to frontend template directory
            current_dir = Path(__file__).parent.parent
            template_base_path = current_dir / "templates"

        # Frontend-oriented template directory structure
        template_dirs = [
            str(template_base_path),
            str(template_base_path / "components"),
            str(template_base_path / "rtm"),
            str(template_base_path / "reports"),
            str(template_base_path / "layouts"),
        ]

        # Only include directories that exist
        existing_dirs = [d for d in template_dirs if os.path.exists(d)]

        if not existing_dirs:
            raise ValueError(f"No template directories found at {template_base_path}")

        self.jinja_env = Environment(
            loader=FileSystemLoader(existing_dirs),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters and functions
        self._setup_template_helpers()

    def _setup_template_helpers(self):
        """Set up custom template filters and functions."""
        # Custom filters for common operations
        self.jinja_env.filters["format_number"] = self._format_number
        self.jinja_env.filters["status_class"] = self._get_status_class
        self.jinja_env.filters["priority_class"] = self._get_priority_class

        # Global functions
        self.jinja_env.globals["asset_url"] = self._asset_url

    def _format_number(self, value: Any) -> str:
        """Format numbers for display."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)

    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status values."""
        status_map = {
            "completed": "success",
            "in_progress": "primary",
            "planned": "warning",
            "blocked": "danger",
            "passed": "success",
            "failed": "danger",
            "skipped": "warning",
        }
        return status_map.get(status.lower(), "info")

    def _get_priority_class(self, priority: str) -> str:
        """Get CSS class for priority values."""
        priority_map = {
            "critical": "danger",
            "high": "warning",
            "medium": "primary",
            "low": "success",
        }
        return priority_map.get(priority.lower(), "info")

    def _asset_url(self, asset_path: str) -> str:
        """Generate asset URLs."""
        return f"/static/{asset_path}"

    def render_template(self, template_name: str, **context) -> str:
        """Render a template with given context."""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

    def render_component(self, component_name: str, **props) -> str:
        """Render a reusable component with props."""
        return self.render_template(f"{component_name}.html", **props)

    def get_template_list(self) -> List[str]:
        """Get list of available templates."""
        return self.jinja_env.list_templates()

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            self.jinja_env.get_template(template_name)
            return True
        except:
            return False
