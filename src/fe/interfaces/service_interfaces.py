"""
Service Interface Definitions

Defines abstract interfaces for backend and frontend services
to ensure proper separation of concerns and testability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .data_contracts import RTMMatrixData, FailureReportData, FilterData


class BackendDataProvider(ABC):
    """Interface for backend services that provide data to frontend."""

    @abstractmethod
    def get_rtm_data(self, filters: FilterData) -> RTMMatrixData:
        """Get RTM matrix data with applied filters."""
        pass

    @abstractmethod
    def get_failure_report_data(self, days: int = 30) -> FailureReportData:
        """Get failure report data for specified time period."""
        pass

    @abstractmethod
    def validate_filters(self, filters: FilterData) -> bool:
        """Validate that provided filters are valid."""
        pass


class FrontendRenderer(ABC):
    """Interface for frontend rendering services."""

    @abstractmethod
    def render_rtm_matrix(self, data: RTMMatrixData) -> str:
        """Render RTM matrix as HTML."""
        pass

    @abstractmethod
    def render_failure_report(self, data: FailureReportData) -> str:
        """Render failure report as HTML."""
        pass

    @abstractmethod
    def render_component(self, component_name: str, **props) -> str:
        """Render individual component."""
        pass


class AssetManager(ABC):
    """Interface for asset management services."""

    @abstractmethod
    def get_css_files(self, page_type: str) -> List[str]:
        """Get CSS files for page type."""
        pass

    @abstractmethod
    def get_js_files(self, page_type: str) -> List[str]:
        """Get JavaScript files for page type."""
        pass

    @abstractmethod
    def optimize_assets(self, asset_type: str) -> bool:
        """Optimize assets (minify, compress)."""
        pass


class TemplateManager(ABC):
    """Interface for template management services."""

    @abstractmethod
    def render_template(self, template_name: str, **context) -> str:
        """Render template with context."""
        pass

    @abstractmethod
    def template_exists(self, template_name: str) -> bool:
        """Check if template exists."""
        pass

    @abstractmethod
    def get_template_list(self) -> List[str]:
        """Get list of available templates."""
        pass


# Implementation contracts for specific services
class RTMServiceInterface(ABC):
    """Interface specifically for RTM-related operations."""

    @abstractmethod
    def generate_epic_metrics(self, epic_id: str) -> Dict[str, Any]:
        """Generate metrics for a specific epic."""
        pass

    @abstractmethod
    def generate_overview_dashboard(self, epic_data: Dict) -> str:
        """Generate overview metrics dashboard HTML."""
        pass

    @abstractmethod
    def generate_epic_card_header(self, epic_data: Dict) -> str:
        """Generate epic card header HTML."""
        pass


class ReportingServiceInterface(ABC):
    """Interface specifically for reporting operations."""

    @abstractmethod
    def generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily failure summary."""
        pass

    @abstractmethod
    def generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML report from data."""
        pass

    @abstractmethod
    def detect_failure_patterns(self, days: int = 30) -> List[Dict]:
        """Detect failure patterns in data."""
        pass
