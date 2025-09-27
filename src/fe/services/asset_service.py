"""
Frontend Asset Service

Manages static assets including CSS, JavaScript, and other resources.
Provides asset bundling, optimization, and URL generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class AssetService:
    """Frontend asset management service."""

    def __init__(self, asset_config_path: Optional[str] = None):
        """Initialize asset service with configuration."""
        if asset_config_path is None:
            current_dir = Path(__file__).parent.parent
            asset_config_path = current_dir / "static" / "assets.json"

        self.config_path = Path(asset_config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load asset configuration."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "assets": {
                    "css": {"core": [], "features": {}, "bundles": {}},
                    "js": {"core": [], "features": {}, "bundles": {}},
                },
                "paths": {"static": "/static", "source": "src/fe/static"},
            }

    def get_css_bundle(self, bundle_name: str) -> List[str]:
        """Get CSS files for a bundle."""
        bundles = self.config.get("assets", {}).get("css", {}).get("bundles", {})
        files = bundles.get(bundle_name, [])
        return [self._asset_url(f) for f in files]

    def get_js_bundle(self, bundle_name: str) -> List[str]:
        """Get JavaScript files for a bundle."""
        bundles = self.config.get("assets", {}).get("js", {}).get("bundles", {})
        files = bundles.get(bundle_name, [])
        return [self._asset_url(f) for f in files]

    def get_feature_css(self, feature_name: str) -> List[str]:
        """Get CSS files for a specific feature."""
        features = self.config.get("assets", {}).get("css", {}).get("features", {})
        files = features.get(feature_name, [])
        return [self._asset_url(f) for f in files]

    def get_feature_js(self, feature_name: str) -> List[str]:
        """Get JavaScript files for a specific feature."""
        features = self.config.get("assets", {}).get("js", {}).get("features", {})
        files = features.get(feature_name, [])
        return [self._asset_url(f) for f in files]

    def get_core_css(self) -> List[str]:
        """Get core CSS files."""
        core = self.config.get("assets", {}).get("css", {}).get("core", [])
        return [self._asset_url(f) for f in core]

    def get_core_js(self) -> List[str]:
        """Get core JavaScript files."""
        core = self.config.get("assets", {}).get("js", {}).get("core", [])
        return [self._asset_url(f) for f in core]

    def _asset_url(self, asset_path: str) -> str:
        """Generate asset URL."""
        static_prefix = self.config.get("paths", {}).get("static", "/static")
        return f"{static_prefix}/{asset_path}"

    def get_all_css_for_page(self, page_type: str = "app") -> List[str]:
        """Get all CSS files needed for a page."""
        css_files = []
        css_files.extend(self.get_core_css())

        if page_type in self.config.get("assets", {}).get("css", {}).get("bundles", {}):
            css_files.extend(self.get_css_bundle(page_type))

        return list(
            dict.fromkeys(css_files)
        )  # Remove duplicates while preserving order

    def get_all_js_for_page(self, page_type: str = "app") -> List[str]:
        """Get all JavaScript files needed for a page."""
        js_files = []
        js_files.extend(self.get_core_js())

        if page_type in self.config.get("assets", {}).get("js", {}).get("bundles", {}):
            js_files.extend(self.get_js_bundle(page_type))

        return list(dict.fromkeys(js_files))  # Remove duplicates while preserving order
