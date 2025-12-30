"""
FastAPI application for integrated book search system
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv

from src.models import (
    SearchResponse, SourceResult, BookResult,
    SourcesResponse, SourceInfo, ConfigResponse,
    AladinSearchResponse, AladinBook
)
from src.config import ConfigManager
from src.plugins import PluginLoader, QueryType
from src.sources.aladin import search_aladin
from src.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

app = FastAPI(
    title="MyBrarian - Integrated Book Search API",
    description="ISBN 또는 도서명으로 여러 소스를 통합 검색하여 도서의 이용 가능 여부를 확인하는 시스템",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_manager = ConfigManager()

# Config cache for performance
_config_cache = None


def get_config():
    """Get config with in-memory caching"""
    global _config_cache
    if _config_cache is None:
        _config_cache = config_manager.load_config()
    return _config_cache


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "MyBrarian Book Search API",
        "version": "0.1.0"
    }


@app.get("/books/search", response_model=AladinSearchResponse, tags=["Search"])
async def search_books_aladin(
    q: str = Query(..., description="Search query (title or ISBN)", min_length=1),
    max_results: int = Query(10, description="Maximum number of results", ge=1, le=50)
):
    """
    Step 1: Search books in Aladin API

    Returns a list of book candidates. User should select one book
    and then use POST /books/search with the ISBN to search all sources.
    """
    logger.info(f"Aladin search request: query='{q}', max_results={max_results}")

    try:
        results = await search_aladin(q, max_results=max_results)

        if not results:
            raise HTTPException(status_code=404, detail="No books found in Aladin")

        books = [AladinBook(**book) for book in results]

        return AladinSearchResponse(
            query=q,
            total_count=len(books),
            books=books
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aladin search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Aladin search failed: {str(e)}")


@app.post("/books/search", response_model=SearchResponse, tags=["Search"])
async def search_books_by_selection(
    isbn: str = Query(..., description="ISBN of the selected book"),
    title: str = Query(..., description="Title of the selected book"),
    main_title: str = Query(None, description="Main title without subtitle"),
    max_results: int = Query(5, description="Maximum results per source", ge=1, le=50)
):
    """
    Step 2: Search all sources with selected book

    After selecting a book from GET /books/search, use this endpoint
    to search all enabled sources. Provide both ISBN and title since
    some sources only support one or the other.
    """
    logger.info(f"Integrated search: isbn='{isbn}', title='{title}'")

    try:
        # Load config and create plugin registry
        config = get_config()
        registry = PluginLoader.create_registry(config)

        if len(registry) == 0:
            raise HTTPException(status_code=503, detail="No enabled sources in config.yaml")

        # Use main_title if provided, otherwise use full title
        search_title = main_title if main_title else title

        # Search each enabled plugin by priority
        enabled_plugins = registry.get_enabled_by_priority()
        sources_results = []

        for plugin in enabled_plugins:
            source_config = next(
                (s for s in config.get('sources', []) if s.get('name') == plugin.name),
                {}
            )
            priority = source_config.get('priority', 999)

            try:
                # Determine query and type
                query_to_use = None
                query_type = None

                if plugin.supports_isbn and isbn:
                    query_to_use = isbn
                    query_type = QueryType.ISBN
                elif plugin.supports_title:
                    query_to_use = search_title
                    query_type = QueryType.TITLE
                else:
                    logger.debug(f"{plugin.name}: No supported query type, skipping")
                    continue

                # Execute search
                logger.debug(f"{plugin.name} search: query={query_to_use}, type={query_type}")
                results = await plugin.search(query_to_use, query_type, max_results)

                # Retry with title if ISBN search fails
                if not results and query_type == QueryType.ISBN and plugin.supports_title:
                    logger.debug(f"{plugin.name}: ISBN search failed, retrying with title")
                    results = await plugin.search(search_title, QueryType.TITLE, max_results)

                # Convert results to BookResult models
                book_results = []
                for result in results:
                    book_results.append(BookResult(
                        title=result.get('title'),
                        author=result.get('author'),
                        isbn=result.get('isbn'),
                        availability=result.get('availability'),
                        url=result.get('url'),
                        additional_info={k: v for k, v in result.items()
                                       if k not in ['title', 'author', 'isbn', 'availability', 'url']}
                    ))

                sources_results.append(SourceResult(
                    source_name=plugin.name,
                    priority=priority,
                    success=True,
                    results=book_results,
                    result_count=len(book_results)
                ))

                # Cleanup plugin resources
                if hasattr(plugin, 'close'):
                    await plugin.close()

            except Exception as e:
                logger.error(f"{plugin.name} search error: {str(e)}", exc_info=True)
                sources_results.append(SourceResult(
                    source_name=plugin.name,
                    priority=priority,
                    success=False,
                    error_message=str(e),
                    result_count=0
                ))

        return SearchResponse(
            query=f"{title} (ISBN: {isbn})",
            isbn=isbn,
            selected_title=title,
            total_sources=len(sources_results),
            sources=sources_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search API error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/search", response_model=SearchResponse, tags=["Search"], deprecated=True)
async def search_books(
    q: str = Query(..., description="Search query (title or ISBN)", min_length=1),
    max_results: int = Query(5, description="Maximum results per source", ge=1, le=50),
    auto_select: bool = Query(False, description="Auto-select first book from Aladin if only one result")
):
    """
    [DEPRECATED] Use GET /books/search then POST /books/search instead

    This endpoint automatically selects the first book from Aladin,
    which may not be what you want. Use the two-step API for better control:
    1. GET /books/search - Get book candidates
    2. POST /books/search - Search all sources with selected book
    """
    logger.info(f"API search request: query='{q}', max_results={max_results}")

    try:
        # Step 1: Search Aladin to get book info
        aladin_results = await search_aladin(q, max_results=10)

        if not aladin_results:
            raise HTTPException(status_code=404, detail="No books found in Aladin")

        # Auto-select logic
        if len(aladin_results) == 1 or auto_select:
            selected_book = aladin_results[0]
        else:
            # For API, return first result (CLI handles user selection)
            selected_book = aladin_results[0]

        isbn = selected_book.get('isbn13') or selected_book.get('isbn')
        title = selected_book.get('title', 'N/A')
        main_title = selected_book.get('mainTitle', title)

        if not isbn:
            raise HTTPException(status_code=400, detail="Could not extract ISBN from search results")

        logger.info(f"Selected book: {title} (ISBN: {isbn})")

        # Step 2: Load config and create plugin registry
        config = get_config()
        registry = PluginLoader.create_registry(config)

        if len(registry) == 0:
            raise HTTPException(status_code=503, detail="No enabled sources in config.yaml")

        # Step 3: Search each enabled plugin by priority
        enabled_plugins = registry.get_enabled_by_priority()
        sources_results = []

        for plugin in enabled_plugins:
            source_config = next(
                (s for s in config.get('sources', []) if s.get('name') == plugin.name),
                {}
            )
            priority = source_config.get('priority', 999)

            try:
                # Determine query type
                query_to_use = q
                query_type = QueryType.AUTO

                if isbn and plugin.supports_isbn:
                    query_to_use = isbn
                    query_type = QueryType.ISBN
                elif not plugin.supports_isbn and plugin.supports_title:
                    query_to_use = main_title if main_title else q
                    query_type = QueryType.TITLE

                # Validate query type
                if not plugin.validate_query_type(query_type):
                    logger.debug(f"{plugin.name}: Query type not supported, skipping")
                    continue

                # Execute search
                logger.debug(f"{plugin.name} search: query={query_to_use}, type={query_type}")
                results = await plugin.search(query_to_use, query_type, max_results)

                # Retry with title if ISBN search fails
                if not results and query_type == QueryType.ISBN and plugin.supports_title:
                    logger.debug(f"{plugin.name}: ISBN search failed, retrying with title")
                    query_to_use = main_title if main_title else q
                    results = await plugin.search(query_to_use, QueryType.TITLE, max_results)

                # Convert results to BookResult models
                book_results = []
                for result in results:
                    book_results.append(BookResult(
                        title=result.get('title'),
                        author=result.get('author'),
                        isbn=result.get('isbn'),
                        availability=result.get('availability'),
                        url=result.get('url'),
                        additional_info={k: v for k, v in result.items()
                                       if k not in ['title', 'author', 'isbn', 'availability', 'url']}
                    ))

                sources_results.append(SourceResult(
                    source_name=plugin.name,
                    priority=priority,
                    success=True,
                    results=book_results,
                    result_count=len(book_results)
                ))

                # Cleanup plugin resources
                if hasattr(plugin, 'close'):
                    await plugin.close()

            except Exception as e:
                logger.error(f"{plugin.name} search error: {str(e)}", exc_info=True)
                sources_results.append(SourceResult(
                    source_name=plugin.name,
                    priority=priority,
                    success=False,
                    error_message=str(e),
                    result_count=0
                ))

        return SearchResponse(
            query=q,
            isbn=isbn,
            selected_title=title,
            total_sources=len(sources_results),
            sources=sources_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search API error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sources", response_model=SourcesResponse, tags=["Configuration"])
async def get_sources():
    """Get list of all configured sources"""
    try:
        config = get_config()
        registry = PluginLoader.create_registry(config)

        sources_info = []
        for source_config in config.get('sources', []):
            source_name = source_config.get('name')
            plugin = registry.get_by_name(source_name)

            sources_info.append(SourceInfo(
                name=source_name,
                priority=source_config.get('priority', 999),
                enabled=source_config.get('enabled', False),
                supports_isbn=plugin.supports_isbn if plugin else False,
                supports_title=plugin.supports_title if plugin else False,
                config={k: v for k, v in source_config.items()
                       if k not in ['name', 'priority', 'enabled']}
            ))

        enabled_count = sum(1 for s in sources_info if s.enabled)

        return SourcesResponse(
            total_count=len(sources_info),
            enabled_count=enabled_count,
            sources=sources_info
        )

    except Exception as e:
        logger.error(f"Get sources error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")


@app.get("/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_config_endpoint():
    """Get current configuration (read-only)"""
    try:
        config = get_config()
        return ConfigResponse(
            sources=config.get('sources', []),
            app_settings=config.get('app_settings', {})
        )
    except Exception as e:
        logger.error(f"Get config error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
