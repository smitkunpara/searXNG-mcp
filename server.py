#!/usr/bin/env python3
"""
SearXNG Search & Scraper MCP Server

A FastMCP-based MCP server that provides:
- Multi-query web search via SearXNG
- Dynamic page scraping with browser support
- TOON encoding/decoding for LLM token optimization
"""

import asyncio
from typing import Annotated, List, Literal

import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from toon import encode, decode

# Initialize FastMCP server
mcp = FastMCP(
    name="SearXNG MCP Server",
    instructions="Multi-query web search via SearXNG + dynamic page scraping with browser support + TOON encoding/decoding for LLM optimization"
)

# Global browser instance for reuse across calls
_playwright_instance = None
_browser_instance = None

# Constants
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUESTS_TIMEOUT = 10  # seconds
BROWSER_TIMEOUT = 30000  # milliseconds for Playwright
MAX_CONTENT_LENGTH = 10000  # characters


class ScrapeConfig(BaseModel):
    url: str
    method: Literal["requests", "browser"] = "requests"
    wait_time: Annotated[
        int,
        Field(
            default=3,
            ge=0,
            le=30,
            description="Seconds to wait for dynamic content (ignored for requests method)"
        )
    ] = 3


async def get_browser():
    """
    Get or create a persistent browser instance.
    
    The browser is created once and reused across all scraping calls
    for better performance.
    
    Returns:
        Browser: Playwright browser instance
        
    Raises:
        RuntimeError: If Playwright is not installed
    """
    global _playwright_instance, _browser_instance
    
    # Return existing browser if still connected
    if _browser_instance is not None and _browser_instance.is_connected():
        return _browser_instance
    
    # Import Playwright - raise helpful error if not installed
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed. Run:\n"
            "  uv add playwright\n"
            "  uv run playwright install chromium"
        )
    
    # Start Playwright if needed
    if _playwright_instance is None:
        _playwright_instance = await async_playwright().start()
    
    # Launch browser
    _browser_instance = await _playwright_instance.chromium.launch(headless=True)
    
    return _browser_instance


def clean_html(soup: BeautifulSoup) -> str:
    """
    Remove unwanted tags and extract clean text from HTML.
    
    Removes scripts, styles, navigation, footers, and other non-content
    elements to extract only the main text content.
    
    Args:
        soup: BeautifulSoup parsed HTML document
        
    Returns:
        Clean text content with normalized whitespace
    """
    # Remove unwanted elements by tag name
    unwanted_tags = [
        'script', 'style', 'nav', 'footer', 'header',
        'aside', 'noscript', 'iframe', 'form', 'button',
        'meta', 'link', 'svg', 'img', 'video', 'audio'
    ]
    for tag in soup.find_all(unwanted_tags):
        tag.decompose()
    
    # Remove elements with common non-content class names
    non_content_patterns = [
        'nav', 'footer', 'header', 'sidebar', 'menu',
        'ad', 'advertisement', 'cookie', 'popup', 'modal'
    ]
    for element in soup.find_all(class_=lambda x: x and any(
        pattern in str(x).lower() for pattern in non_content_patterns
    )):
        element.decompose()
    
    # Remove elements with common non-content IDs
    for element in soup.find_all(id=lambda x: x and any(
        pattern in str(x).lower() for pattern in non_content_patterns
    )):
        element.decompose()
    
    # Get text content with space separator
    text = soup.get_text(separator=' ', strip=True)
    
    # Normalize whitespace (collapse multiple spaces/newlines)
    text = ' '.join(text.split())
    
    return text


@mcp.tool()
def search_web(
    query_configs: Annotated[
        List[dict],
        Field(description="List of query configurations, each with 'query' and optional 'num_results' (default 5)")
    ]
) -> str:
    """
    Execute multiple web search queries via SearXNG.
    
    Connects to a self-hosted SearXNG instance and executes all queries,
    returning structured results in TOON format for token efficiency.
    Includes random delays between queries to be polite to the search server.
    Errors in individual queries won't fail the entire batch.
    
    Args:
        query_configs: List of dicts, each containing:
            - query: The search query string
            - num_results: Optional number of results (1-50, default 5)
        
    Returns:
        TOON-formatted string containing search results
    """
    searxng_url = "http://localhost:8080"  # Use local SearXNG instance
    results = {}
    headers = {
        "User-Agent": USER_AGENT,
        "X-Forwarded-For": "127.0.0.1",
        "X-Real-IP": "127.0.0.1"
    }
    
    for i, config in enumerate(query_configs):
        query = config["query"]
        num_results = config.get("num_results", 5)
        try:
            # Build the search URL
            search_url = f"{searxng_url.rstrip('/')}/search"
            params = {
                "q": query,
                "format": "json",
            }
            
            # Execute the search request
            response = requests.get(
                search_url,
                params=params,
                headers=headers,
                timeout=REQUESTS_TIMEOUT
            )
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            search_results = data.get("results", [])[:num_results]
            
            # Format results into clean structure
            formatted_results = []
            for item in search_results:
                formatted_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })
            
            results[query] = {
                "status": "success",
                "count": len(formatted_results),
                "results": formatted_results
            }
            
        except requests.exceptions.Timeout:
            results[query] = {
                "status": "error",
                "error": "Request timed out after 10 seconds",
                "count": 0,
                "results": []
            }
        except requests.exceptions.ConnectionError:
            results[query] = {
                "status": "error",
                "error": f"Failed to connect to SearXNG at {searxng_url}",
                "count": 0,
                "results": []
            }
        except requests.exceptions.HTTPError as e:
            results[query] = {
                "status": "error",
                "error": f"HTTP error: {e.response.status_code}",
                "count": 0,
                "results": []
            }
        except ValueError as e:
            results[query] = {
                "status": "error",
                "error": f"Invalid JSON response from SearXNG: {str(e)}",
                "count": 0,
                "results": []
            }
        except Exception as e:
            results[query] = {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "count": 0,
                "results": []
            }
        
        # No delay needed for local SearXNG
        
    return encode(results)


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

    Args:
        configs: List of ScrapeConfig objects, each with url, method, and wait_time

    Returns:
        TOON-formatted string containing scraped content for each URL
    """
    results = {}
    headers = {"User-Agent": USER_AGENT}

    for i, config in enumerate(configs):
        url = config.url
        method = config.method
        wait_time = config.wait_time if method == "browser" else 0  # Ignore wait_time for requests
        try:
            if method == "requests":
                # ===== Static HTML Scraping =====
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=REQUESTS_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # Handle encoding properly
                response.encoding = response.apparent_encoding or 'utf-8'
                
                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")
                
                # Extract title
                title = ""
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                
                # Extract and clean content
                content = clean_html(soup)
                
                # Limit content length
                if len(content) > MAX_CONTENT_LENGTH:
                    content = content[:MAX_CONTENT_LENGTH] + "..."
                
                results[url] = {
                    "status": "success",
                    "method": "requests",
                    "title": title,
                    "content": content,
                    "length": len(content)
                }
                
            else:
                # ===== Browser-Based Scraping =====
                browser = await get_browser()
                page = await browser.new_page(user_agent=USER_AGENT)
                
                try:
                    # Navigate to URL and wait for network to be idle
                    await page.goto(
                        url,
                        timeout=BROWSER_TIMEOUT,
                        wait_until="networkidle"
                    )
                    
                    # Additional wait for dynamic content (AJAX, lazy loading, etc.)
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    
                    # Get rendered HTML and title
                    html = await page.content()
                    title = await page.title() or ""
                    
                    # Parse rendered HTML
                    soup = BeautifulSoup(html, "lxml")
                    content = clean_html(soup)
                    
                    # Limit content length
                    if len(content) > MAX_CONTENT_LENGTH:
                        content = content[:MAX_CONTENT_LENGTH] + "..."
                    
                    results[url] = {
                        "status": "success",
                        "method": "browser",
                        "title": title.strip() if title else "",
                        "content": content,
                        "length": len(content)
                    }
                    
                finally:
                    # Always close the page to free resources
                    await page.close()
                    
        except requests.exceptions.Timeout:
            results[url] = {
                "status": "error",
                "method": method,
                "error": "Request timed out after 10 seconds",
                "title": "",
                "content": "",
                "length": 0
            }
        except requests.exceptions.ConnectionError:
            results[url] = {
                "status": "error",
                "method": method,
                "error": f"Failed to connect to {url}",
                "title": "",
                "content": "",
                "length": 0
            }
        except requests.exceptions.HTTPError as e:
            results[url] = {
                "status": "error",
                "method": method,
                "error": f"HTTP error: {e.response.status_code}",
                "title": "",
                "content": "",
                "length": 0
            }
        except RuntimeError as e:
            # Playwright not installed
            results[url] = {
                "status": "error",
                "method": method,
                "error": str(e),
                "title": "",
                "content": "",
                "length": 0
            }
        except Exception as e:
            error_type = type(e).__name__
            results[url] = {
                "status": "error",
                "method": method,
                "error": f"{error_type}: {str(e)}",
                "title": "",
                "content": "",
                "length": 0
            }
        
        # No delay needed for local scraping
        
    return encode(results)


async def cleanup_browser():
    """
    Clean up browser resources.
    
    Should be called when shutting down the server to properly
    close the browser and Playwright instances.
    """
    global _playwright_instance, _browser_instance
    
    if _browser_instance is not None:
        await _browser_instance.close()
        _browser_instance = None
    
    if _playwright_instance is not None:
        await _playwright_instance.stop()
        _playwright_instance = None


if __name__ == "__main__":
    mcp.run()