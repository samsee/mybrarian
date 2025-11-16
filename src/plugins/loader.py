"""
Plugin loading and registry for dynamic plugin management.
"""

import importlib
from pathlib import Path
from typing import List, Dict, Optional, Type, Any
import yaml

from .base import BasePlugin
from .adapters import SyncPluginAdapter


class PluginRegistry:
    """
    Registry for managing plugin instances.

    Stores plugin instances and provides methods to query and access them.
    """

    def __init__(self):
        """Initialize an empty plugin registry."""
        self._plugins: List[tuple[BasePlugin, Dict[str, Any]]] = []

    def register(self, plugin: BasePlugin, metadata: Dict[str, Any]) -> None:
        """
        Register a plugin with its metadata.

        Args:
            plugin: Plugin instance to register
            metadata: Plugin metadata (priority, enabled, etc.)
        """
        self._plugins.append((plugin, metadata))

    def get_enabled_by_priority(self) -> List[BasePlugin]:
        """
        Get all enabled plugins sorted by priority.

        Returns:
            List of enabled plugins in priority order (lowest number first)
        """
        enabled = [
            (plugin, meta)
            for plugin, meta in self._plugins
            if meta.get('enabled', True)
        ]

        enabled.sort(key=lambda x: x[1].get('priority', 999))

        return [plugin for plugin, _ in enabled]

    def get_all(self) -> List[BasePlugin]:
        """
        Get all registered plugins regardless of status.

        Returns:
            List of all plugins
        """
        return [plugin for plugin, _ in self._plugins]

    def get_by_name(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by its name.

        Args:
            name: Name of the plugin to find

        Returns:
            Plugin instance or None if not found
        """
        for plugin, _ in self._plugins:
            if plugin.name == name:
                return plugin
        return None

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()

    def __len__(self) -> int:
        """Return the number of registered plugins."""
        return len(self._plugins)


class PluginLoader:
    """
    Loads plugins dynamically from configuration.

    Reads config.yaml and instantiates plugin classes based on
    module and class specifications.
    """

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> Dict:
        """
        Load configuration from config.yaml.

        Args:
            config_path: Path to config file (defaults to project root)

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: config.yaml not found at {config_path}")
            return {'sources': []}
        except yaml.YAMLError as e:
            print(f"Warning: config.yaml parsing error: {e}")
            return {'sources': []}

    @staticmethod
    def load_plugin_class(module_path: str, class_name: str) -> Type[BasePlugin]:
        """
        Dynamically import and return a plugin class.

        Args:
            module_path: Python module path (e.g., "src.sources.aladin")
            class_name: Name of the plugin class

        Returns:
            Plugin class

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If class not found in module
        """
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)

        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(
                f"{class_name} is not a subclass of BasePlugin"
            )

        return plugin_class

    @staticmethod
    def create_registry(config: Optional[Dict] = None) -> PluginRegistry:
        """
        Create a plugin registry from configuration.

        Args:
            config: Configuration dictionary (loads from file if None)

        Returns:
            PluginRegistry with loaded plugins
        """
        if config is None:
            config = PluginLoader.load_config()

        registry = PluginRegistry()
        sources = config.get('sources', [])

        for source_config in sources:
            try:
                plugin = PluginLoader._load_plugin_from_config(source_config)
                if plugin:
                    registry.register(plugin, source_config)
            except Exception as e:
                print(f"Error loading plugin {source_config.get('name', 'Unknown')}: {e}")

        return registry

    @staticmethod
    def _load_plugin_from_config(source_config: Dict) -> Optional[BasePlugin]:
        """
        Load a single plugin from source configuration.

        Args:
            source_config: Source configuration dictionary

        Returns:
            Plugin instance or None if loading failed
        """
        module_path = source_config.get('module')
        class_name = source_config.get('class')

        if not module_path or not class_name:
            print(f"Warning: Missing module or class in config for {source_config.get('name')}")
            return None

        try:
            plugin_class = PluginLoader.load_plugin_class(module_path, class_name)
            plugin_instance = plugin_class(config=source_config)

            is_sync = source_config.get('is_sync', False)
            if is_sync:
                plugin_instance = SyncPluginAdapter(plugin_instance)

            return plugin_instance

        except (ImportError, AttributeError, TypeError) as e:
            print(f"Error loading {class_name} from {module_path}: {e}")
            return None
