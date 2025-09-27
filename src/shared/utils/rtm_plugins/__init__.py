"""
RTM Plugins Package

Plugin system for extending RTM automation functionality.
Supports link generators, validators, and parsers.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RTMPlugin(ABC):
    """Base class for all RTM plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled by default."""
        return True


class PluginManager:
    """Manages RTM plugins discovery and loading."""

    def __init__(self):
        self.plugins: Dict[str, RTMPlugin] = {}
        self.plugin_types = {
            "link_generators": [],
            "validators": [],
            "parsers": [],
        }

    def discover_plugins(self, plugin_dir: str = None) -> None:
        """Discover and load plugins from specified directory."""
        if plugin_dir is None:
            import os

            plugin_dir = os.path.dirname(__file__)

        # Discover plugins in each subdirectory
        for plugin_type in self.plugin_types.keys():
            type_dir = os.path.join(plugin_dir, plugin_type)
            if os.path.exists(type_dir):
                self._load_plugins_from_dir(type_dir, plugin_type)

    def _load_plugins_from_dir(self, directory: str, plugin_type: str) -> None:
        """Load plugins from a specific directory."""
        import importlib.util

        for item in os.listdir(directory):
            if item.startswith("__") or not item.endswith(".py"):
                continue

            module_path = os.path.join(directory, item)
            module_name = item[:-3]  # Remove .py extension

            try:
                spec = importlib.util.spec_from_file_location(
                    module_name, module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find plugin classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, RTMPlugin)
                        and attr != RTMPlugin
                    ):

                        plugin_instance = attr()
                        self.register_plugin(plugin_instance, plugin_type)

            except Exception as e:
                print(f"Warning: Failed to load plugin {module_name}: {e}")

    def register_plugin(self, plugin: RTMPlugin, plugin_type: str) -> None:
        """Register a plugin instance."""
        if plugin_type not in self.plugin_types:
            raise ValueError(f"Unknown plugin type: {plugin_type}")

        self.plugins[plugin.name] = plugin
        self.plugin_types[plugin_type].append(plugin)

    def get_plugins_by_type(self, plugin_type: str) -> List[RTMPlugin]:
        """Get all plugins of a specific type."""
        return self.plugin_types.get(plugin_type, [])

    def get_plugin(self, name: str) -> RTMPlugin:
        """Get a specific plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> Dict[str, Any]:
        """List all discovered plugins."""
        result = {}
        for plugin_type, plugins in self.plugin_types.items():
            result[plugin_type] = [
                {
    
                    "name": p.name,
                    "version": p.version,
                    "description": p.description,
                    "enabled": p.enabled,
                
}
                for p in plugins
            ]
        return result
