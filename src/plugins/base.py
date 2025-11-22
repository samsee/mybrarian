"""
Plugin base classes and interfaces for the book search system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional, Any


class QueryType(Enum):
    """Types of search queries supported by plugins."""
    AUTO = "auto"       # Plugin auto-detects ISBN vs title
    ISBN = "isbn"       # Search by ISBN only
    TITLE = "title"     # Search by title only


class BasePlugin(ABC):
    """
    Abstract base class for all search source plugins.

    Each plugin must implement:
    - search(): Perform the search operation
    - format_results(): Format results for display

    Plugins should declare their capabilities via class attributes:
    - name: Human-readable name of the source
    - supports_isbn: Whether the plugin can search by ISBN
    - supports_title: Whether the plugin can search by title
    - cli_command: CLI command name (e.g., "search-local" for "python -m src search-local")
    - cli_help: Help text for CLI command
    """

    name: str = "Unknown Plugin"
    supports_isbn: bool = False
    supports_title: bool = False
    cli_command: Optional[str] = None
    cli_help: Optional[str] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin with optional configuration.

        Args:
            config: Plugin-specific configuration from config.yaml
        """
        self.config = config or {}

    @abstractmethod
    async def search(
        self,
        query: str,
        query_type: QueryType = QueryType.AUTO,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for books using the provided query.

        Args:
            query: Search query (ISBN or title)
            query_type: Type of query (AUTO, ISBN, or TITLE)
            max_results: Maximum number of results to return

        Returns:
            List of search results as dictionaries
        """
        pass

    @abstractmethod
    def format_results(self, results: List[Dict]) -> None:
        """
        Format and print search results to console.

        Args:
            results: Search results from search() method
        """
        pass

    def validate_query_type(self, query_type: QueryType) -> bool:
        """
        Check if the plugin supports the given query type.

        Args:
            query_type: Query type to validate

        Returns:
            True if supported, False otherwise
        """
        if query_type == QueryType.AUTO:
            return self.supports_isbn or self.supports_title
        elif query_type == QueryType.ISBN:
            return self.supports_isbn
        elif query_type == QueryType.TITLE:
            return self.supports_title
        return False

    def detect_query_type(self, query: str) -> QueryType:
        """
        Auto-detect query type from the query string.

        Args:
            query: Search query

        Returns:
            Detected QueryType (ISBN or TITLE)
        """
        clean_query = query.replace("-", "").replace(" ", "")

        if clean_query.isdigit() and len(clean_query) in [10, 13]:
            return QueryType.ISBN

        return QueryType.TITLE

    def __str__(self) -> str:
        return f"{self.name} (ISBN: {self.supports_isbn}, Title: {self.supports_title})"
