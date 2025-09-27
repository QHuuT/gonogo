"""
Frontend/Backend Interface Definitions

Defines clear contracts and data structures for communication
between backend services and frontend presentation layer.

This ensures type safety and clear separation of concerns.
"""

from .data_contracts import EpicData, TestData, DefectData, UserStoryData
from .service_interfaces import BackendDataProvider, FrontendRenderer

__all__ = [
    "EpicData",
    "TestData",
    "DefectData",
    "UserStoryData",
    "BackendDataProvider",
    "FrontendRenderer",
]
