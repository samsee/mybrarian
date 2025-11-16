"""
Adapters for converting between sync and async plugin interfaces.
"""

import asyncio
from typing import List, Dict
from .base import BasePlugin, QueryType


class SyncPluginAdapter(BasePlugin):
    """
    Adapter that wraps a synchronous plugin and provides async interface.

    This allows synchronous plugins (like local file search) to work
    seamlessly with the async plugin system.
    """

    def __init__(self, sync_plugin: BasePlugin):
        """
        Initialize the adapter with a synchronous plugin.

        Args:
            sync_plugin: The synchronous plugin to wrap
        """
        super().__init__(sync_plugin.config)
        self._sync_plugin = sync_plugin

        self.name = sync_plugin.name
        self.supports_isbn = sync_plugin.supports_isbn
        self.supports_title = sync_plugin.supports_title

    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Run the synchronous search method in a thread pool.

        Args:
            query: Search query (ISBN or title)
            query_type: Type of query (AUTO, ISBN, or TITLE)
            max_results: Maximum number of results to return

        Returns:
            List of search results as dictionaries
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: asyncio.run(
                self._sync_plugin.search(query, query_type, max_results)
            ) if asyncio.iscoroutinefunction(self._sync_plugin.search)
            else self._call_sync_search(query, query_type, max_results)
        )

    def _call_sync_search(
        self,
        query: str,
        query_type: QueryType,
        max_results: int
    ) -> List[Dict]:
        """
        Call the synchronous search method directly.

        Args:
            query: Search query
            query_type: Type of query
            max_results: Maximum results

        Returns:
            Search results
        """
        return self._sync_plugin.search(query, query_type, max_results)

    def format_results(self, results: List[Dict]) -> None:
        """
        Delegate result formatting to the wrapped plugin.

        Args:
            results: Search results to format
        """
        self._sync_plugin.format_results(results)

    def __str__(self) -> str:
        return f"SyncAdapter({self._sync_plugin})"
