"""
Pydantic models for API request/response
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AladinBook(BaseModel):
    """Aladin book candidate"""
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    pubDate: Optional[str] = None
    isbn13: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    categoryName: Optional[str] = None
    mainTitle: Optional[str] = None


class AladinSearchResponse(BaseModel):
    """Response model for Aladin book search"""
    query: str
    total_count: int
    books: List[AladinBook]


class BookResult(BaseModel):
    """Single book search result"""
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    availability: Optional[str] = None
    url: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class SourceResult(BaseModel):
    """Results from a single source"""
    source_name: str
    priority: int
    success: bool
    error_message: Optional[str] = None
    results: List[BookResult] = []
    result_count: int = 0


class SearchResponse(BaseModel):
    """Response model for book search"""
    query: str
    isbn: Optional[str] = None
    selected_title: Optional[str] = None
    total_sources: int
    sources: List[SourceResult]


class SourceInfo(BaseModel):
    """Information about a search source"""
    name: str
    priority: int
    enabled: bool
    supports_isbn: bool
    supports_title: bool
    config: Dict[str, Any] = {}


class SourcesResponse(BaseModel):
    """Response model for sources list"""
    total_count: int
    enabled_count: int
    sources: List[SourceInfo]


class ConfigResponse(BaseModel):
    """Response model for config"""
    sources: List[Dict[str, Any]]
    app_settings: Dict[str, Any]
