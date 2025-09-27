"""
Frontend Views Module

Contains view controllers that handle the presentation layer.
These views act as the interface between backend data and frontend templates.

Architecture:
- Views receive data from backend services
- Views use frontend services to render templates
- Views handle presentation logic only (no business logic)
- Views define clear contracts with backend APIs
"""

from .rtm_view import RTMView
from .reports_view import ReportsView

__all__ = ["RTMView", "ReportsView"]
