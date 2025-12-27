"""SearXNG MCP Server Package.

A FastMCP-based MCP server that provides:
- Multi-query web search via SearXNG
- Dynamic page scraping with browser support
- TOON encoding/decoding for LLM token optimization
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "you@example.com"

# Import main components for easy access
from .config import *
from .browser import *
from .scraper import *
from .search import *
from .utils import *

__all__ = [
    # Config
    "USER_AGENT", "REQUESTS_TIMEOUT", "BROWSER_TIMEOUT",
    "MAX_CONTENT_LENGTH", "MAX_NUM_RESULTS", "SEARXNG_URL",
    "MAX_RETRIES", "RETRY_DELAY",
    
    # Browser
    "get_browser", "cleanup_browser", "is_browser_available",
    
    # Scraper
    "ScrapeConfig", "scrape_pages", "clean_html",
    
    # Search
    "search_web", "validate_num_results",
    
    # Utils
    "handle_exceptions", "format_error"
]