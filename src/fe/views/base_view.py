"""
Base View Class

Provides common functionality for all frontend views.
Establishes the contract between backend data and frontend presentation.
"""

from typing import Any, Dict, List
from abc import ABC, abstractmethod

from ..services import TemplateService, ComponentService, AssetService


class BaseView(ABC):
    """Base class for all frontend views."""

    def __init__(self):
        """Initialize view with frontend services."""
        self.template_service = TemplateService()
        self.component_service = ComponentService(self.template_service)
        self.asset_service = AssetService()

    def render_page(self, template_name: str, page_type: str = "app", **context) -> str:
        """Render a complete page with assets and layout."""
        # Get assets for page
        css_files = self.asset_service.get_all_css_for_page(page_type)
        js_files = self.asset_service.get_all_js_for_page(page_type)

        # Add assets to context
        context.update(
            {"css_files": css_files, "js_files": js_files, "page_type": page_type}
        )

        return self.template_service.render_template(template_name, **context)

    def render_component(self, component_name: str, **props) -> str:
        """Render a single component."""
        return self.component_service.render_template(f"{component_name}.html", **props)

    @abstractmethod
    def prepare_data(self, raw_data: Any) -> Dict[str, Any]:
        """Transform raw backend data into frontend-ready format."""
        pass

    def get_page_assets(self, page_type: str) -> Dict[str, List[str]]:
        """Get all assets needed for a page type."""
        return {
            "css": self.asset_service.get_all_css_for_page(page_type),
            "js": self.asset_service.get_all_js_for_page(page_type),
        }
