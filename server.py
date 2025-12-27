#!/usr/bin/env python3
"""
SearXNG Search & Scraper MCP Server

A FastMCP-based MCP server that provides:
- Multi-query web search via SearXNG
- Dynamic page scraping with browser support
- TOON encoding/decoding for LLM token optimization
"""

from typing import List

from fastmcp import FastMCP
from pydantic import Field
from toon import encode
from typing_extensions import Annotated

from searxng_mcp.browser import cleanup_browser
from searxng_mcp.scraper import ScrapeConfig, scrape_pages as scrape_pages_impl
from searxng_mcp.search import search_web as search_web_impl

# Initialize FastMCP server
mcp = FastMCP(
    name="SearXNG MCP Server",
    instructions="Multi-query web search via SearXNG + dynamic page scraping with browser support + TOON encoding/decoding for LLM optimization"
)


@mcp.tool()
async def search_web(
    query_configs: Annotated[
        List[dict],
        Field(description="List of query configurations, each with 'query' and optional 'num_results' (default 5)")
    ]
) -> str:
    """
    Execute multiple web search queries via SearXNG.
    
    Connects to a self-hosted SearXNG instance and executes all queries,
    returning structured results in TOON format for token efficiency.
    Includes retry logic with exponential backoff for robust operation.
    Errors in individual queries won't fail the entire batch.
    
    Args:
        query_configs: List of dicts, each containing:
            - query: The search query string
            - num_results: Optional number of results (1-50, default 5)
        
    Returns:
        TOON-formatted string containing search results
    """
    
    try:
        results = await search_web_impl(query_configs)
        encoded_results = encode(results)
        return encoded_results
    except Exception as e:
        error_result = {
            "error": f"Search failed: {str(e)}",
            "status": "error"
        }
        return encode(error_result)


@mcp.tool()
async def scrape_pages(
    configs: Annotated[
        List[ScrapeConfig],
        Field(description="List of scrape configurations, each with URL, method, and wait_time")
    ]
) -> str:
    """
    Scrape content from multiple web pages with individual configurations.

    Supports two scraping methods per URL:
    - 'requests': Fast static HTML scraping using requests + BeautifulSoup.
      Best for simple HTML pages that don't require JavaScript.
    - 'browser': Full browser rendering using Playwright with Chromium.
      Required for JavaScript-heavy sites (React, Vue, Angular, etc.).
      The browser instance is reused across calls for better performance.

    Content is automatically cleaned by removing scripts, styles, navigation,
    footers, and other non-content elements. Output is limited to 10,000
    characters per page to prevent context overflow.
    
    Includes retry logic with exponential backoff for robust operation.

    Args:
        configs: List of ScrapeConfig objects, each with url, method, and wait_time

    Returns:
        TOON-formatted string containing scraped content for each URL
    """
    
    try:
        results = await scrape_pages_impl(configs)
        encoded_results = encode(results)
        return encoded_results
    except Exception as e:
        error_result = {
            "error": f"Scraping failed: {str(e)}",
            "status": "error"
        }
        return encode(error_result)


# Cleanup handler for graceful shutdown
async def shutdown():
    """Clean up resources on server shutdown."""
    await cleanup_browser()


if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass
    finally:
        import asyncio
        asyncio.run(shutdown())
