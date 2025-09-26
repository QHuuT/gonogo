"""
Regression test for Pydantic and FastAPI deprecation warning fixes.

Tests that the codebase doesn't generate Pydantic V2 deprecation warnings
or FastAPI on_event deprecation warnings after the fixes applied in 2025-09-26.

This test ensures that:
- No PydanticDeprecatedSince20 warnings for class-based config
- No PydanticDeprecatedSince20 warnings for Field extra kwargs
- No FastAPI DeprecationWarning for on_event usage
- All models use modern ConfigDict patterns
- All FastAPI apps use lifespan context managers
"""

import warnings
from contextlib import redirect_stderr
from io import StringIO

import pytest


def test_no_pydantic_class_config_warnings():
    """Test that importing Pydantic models doesn't generate class-based config warnings."""

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Import modules that previously had class Config deprecation warnings
        from src.be.api.capabilities import CapabilityResponse
        from src.be.api.epic_dependencies import DependencyCreate, DependencyResponse
        from src.security.gdpr.models import ConsentRequest, DataSubjectRequestResponse

        # Check that no PydanticDeprecatedSince20 warnings were generated
        pydantic_warnings = [
            w for w in warning_list
            if "PydanticDeprecatedSince20" in str(w.message) and
               "class-based `config` is deprecated" in str(w.message)
        ]

        assert len(pydantic_warnings) == 0, (
            f"Found {len(pydantic_warnings)} Pydantic class config deprecation warnings: "
            f"{[str(w.message) for w in pydantic_warnings]}"
        )


def test_no_pydantic_field_extra_kwargs_warnings():
    """Test that Field definitions don't generate extra kwargs deprecation warnings."""

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Import modules that previously had Field extra kwargs warnings
        from src.be.api.capabilities import CapabilityCreate

        # Check that no Field extra kwargs warnings were generated
        field_warnings = [
            w for w in warning_list
            if "PydanticDeprecatedSince20" in str(w.message) and
               "extra keyword arguments on `Field`" in str(w.message)
        ]

        assert len(field_warnings) == 0, (
            f"Found {len(field_warnings)} Pydantic Field extra kwargs warnings: "
            f"{[str(w.message) for w in field_warnings]}"
        )


def test_no_fastapi_on_event_warnings():
    """Test that FastAPI app doesn't generate on_event deprecation warnings."""

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Import the FastAPI app that previously used @app.on_event()
        from src.be.main import app

        # Check that no FastAPI on_event warnings were generated
        fastapi_warnings = [
            w for w in warning_list
            if "DeprecationWarning" in str(w.category.__name__) and
               "on_event is deprecated" in str(w.message)
        ]

        assert len(fastapi_warnings) == 0, (
            f"Found {len(fastapi_warnings)} FastAPI on_event deprecation warnings: "
            f"{[str(w.message) for w in fastapi_warnings]}"
        )


def test_models_use_modern_configdict():
    """Test that Pydantic models use modern ConfigDict instead of class Config."""

    # Test capabilities models
    from src.be.api.capabilities import CapabilityResponse
    assert hasattr(CapabilityResponse, 'model_config'), (
        "CapabilityResponse should use model_config instead of class Config"
    )
    assert CapabilityResponse.model_config['from_attributes'] is True

    # Test epic dependencies models
    from src.be.api.epic_dependencies import DependencyCreate, DependencyResponse
    assert hasattr(DependencyCreate, 'model_config'), (
        "DependencyCreate should use model_config instead of class Config"
    )
    assert hasattr(DependencyResponse, 'model_config'), (
        "DependencyResponse should use model_config instead of class Config"
    )
    assert DependencyResponse.model_config['from_attributes'] is True

    # Test GDPR models
    from src.security.gdpr.models import DataSubjectRequestCreate, DataSubjectRequestResponse
    assert hasattr(DataSubjectRequestCreate, 'model_config'), (
        "DataSubjectRequestCreate should use model_config instead of class Config"
    )
    assert hasattr(DataSubjectRequestResponse, 'model_config'), (
        "DataSubjectRequestResponse should use model_config instead of class Config"
    )
    assert DataSubjectRequestResponse.model_config['from_attributes'] is True


def test_fastapi_uses_lifespan_pattern():
    """Test that FastAPI app uses lifespan context manager instead of on_event."""

    from src.be.main import app

    # Check that the app has a lifespan configured through the router
    assert hasattr(app.router, 'lifespan_context'), (
        "FastAPI app should use lifespan context manager instead of @app.on_event()"
    )


def test_field_uses_json_schema_extra():
    """Test that Field definitions use json_schema_extra instead of example parameter."""

    from src.be.api.epic_dependencies import DependencyCreate

    # Check that the model config has json_schema_extra defined
    assert hasattr(DependencyCreate, 'model_config'), (
        "DependencyCreate should have model_config defined"
    )

    # The json_schema_extra should be in the ConfigDict
    config = DependencyCreate.model_config
    assert 'json_schema_extra' in config, (
        "DependencyCreate should use json_schema_extra instead of Field example parameter"
    )


def test_comprehensive_import_without_warnings():
    """
    Comprehensive test that imports all major modules and ensures no deprecation warnings.

    This test provides broad coverage to catch any missed deprecation patterns.
    """

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Import all major API modules
        from src.be import main
        from src.be.api import capabilities, epic_dependencies
        from src.security.gdpr import models

        # Filter for the specific deprecation warnings we fixed
        relevant_warnings = [
            w for w in warning_list
            if any([
                "PydanticDeprecatedSince20" in str(w.message),
                ("DeprecationWarning" in str(w.category.__name__) and
                 "on_event is deprecated" in str(w.message))
            ])
        ]

        assert len(relevant_warnings) == 0, (
            f"Found {len(relevant_warnings)} deprecation warnings after fixes: "
            f"{[f'{w.category.__name__}: {w.message}' for w in relevant_warnings]}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])