"""
Plugin system for the book search application.

This package provides a plugin-based architecture for search sources,
allowing easy extension and configuration of new sources without
modifying core application code.

Usage:
    from src.plugins import PluginLoader, PluginRegistry, QueryType

    # Load plugins from config
    registry = PluginLoader.create_registry()

    # Get enabled plugins by priority
    for plugin in registry.get_enabled_by_priority():
        results = await plugin.search("Python", QueryType.TITLE)
        plugin.format_results(results)
"""

from .base import BasePlugin, QueryType
from .loader import PluginLoader, PluginRegistry
from .adapters import SyncPluginAdapter

__all__ = [
    'BasePlugin',
    'QueryType',
    'PluginLoader',
    'PluginRegistry',
    'SyncPluginAdapter',
]
