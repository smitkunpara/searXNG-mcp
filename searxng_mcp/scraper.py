"""Web scraping functionality with requests and browser support."""

import asyncio
from typing import Dict, List, Literal

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from .browser import get_browser
from .config import (
    BROWSER_TIMEOUT,
    MAX_CONTENT_LENGTH,
    MAX_RETRIES,
    REQUESTS_TIMEOUT,
    RETRY_DELAY,
    USER_AGENT,
)


class ScrapeConfig(BaseModel):
    """Configuration for scraping a web page."""
    
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


async def scrape_with_requests(url: str) -> Dict:
    """
    Scrape a webpage using requests (static HTML).
    
    Args:
        url: URL to scrape
        
    Returns:
        Dictionary with status, title, content, and metadata
    """
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(MAX_RETRIES):
        try:
            
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
            original_length = len(content)
            
            # Limit content length
            truncated = False
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "..."
                truncated = True
            
            
            return {
                "status": "success",
                "method": "requests",
                "title": title,
                "content": content,
                "length": len(content),
                "original_length": original_length,
                "truncated": truncated
            }
            
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "method": "requests",
                "error": f"Request timed out after {REQUESTS_TIMEOUT} seconds",
                "title": "",
                "content": "",
                "length": 0
            }
            
        except requests.exceptions.ConnectionError as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "method": "requests",
                "error": f"Failed to connect to {url}",
                "title": "",
                "content": "",
                "length": 0
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "method": "requests",
                "error": f"HTTP error: {e.response.status_code}",
                "title": "",
                "content": "",
                "length": 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "method": "requests",
                "error": f"{type(e).__name__}: {str(e)}",
                "title": "",
                "content": "",
                "length": 0
            }
    
    # Should not reach here, but just in case
    return {
        "status": "error",
        "method": "requests",
        "error": "Max retries exceeded",
        "title": "",
        "content": "",
        "length": 0
    }


async def scrape_with_browser(url: str, wait_time: int = 3) -> Dict:
    """
    Scrape a webpage using Playwright browser (dynamic content).
    
    Args:
        url: URL to scrape
        wait_time: Seconds to wait for dynamic content
        
    Returns:
        Dictionary with status, title, content, and metadata
    """
    for attempt in range(MAX_RETRIES):
        page = None
        try:
            
            browser = await get_browser()
            page = await browser.new_page(user_agent=USER_AGENT)
            
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
            original_length = len(content)
            
            # Limit content length
            truncated = False
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "..."
                truncated = True
            
            
            return {
                "status": "success",
                "method": "browser",
                "title": title.strip() if title else "",
                "content": content,
                "length": len(content),
                "original_length": original_length,
                "truncated": truncated
            }
            
        except asyncio.TimeoutError:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "method": "browser",
                "error": f"Browser timeout after {BROWSER_TIMEOUT}ms",
                "title": "",
                "content": "",
                "length": 0
            }
            
        except RuntimeError as e:
            # Playwright not installed - don't retry
            return {
                "status": "error",
                "method": "browser",
                "error": str(e),
                "title": "",
                "content": "",
                "length": 0
            }
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "method": "browser",
                "error": f"{type(e).__name__}: {str(e)}",
                "title": "",
                "content": "",
                "length": 0
            }
            
        finally:
            # Always close the page to free resources
            if page is not None:
                try:
                    await page.close()
                except Exception as e:
                    pass
    
    # Should not reach here, but just in case
    return {
        "status": "error",
        "method": "browser",
        "error": "Max retries exceeded",
        "title": "",
        "content": "",
        "length": 0
    }


async def scrape_pages(configs: List[ScrapeConfig]) -> Dict:
    """
    Scrape content from multiple web pages with individual configurations.
    
    Args:
        configs: List of ScrapeConfig objects
        
    Returns:
        Dictionary mapping URLs to scrape results
    """
    results = {}
    
    for config in configs:
        url = config.url
        method = config.method
        wait_time = config.wait_time if method == "browser" else 0
        
        if method == "requests":
            result = await scrape_with_requests(url)
        else:
            result = await scrape_with_browser(url, wait_time)
        
        results[url] = result
    
    return results
