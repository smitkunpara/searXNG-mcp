"""Browser management for web scraping with Playwright."""

import asyncio
from typing import Optional

# Global browser instance for reuse across calls
_playwright_instance = None
_browser_instance = None


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
    if _browser_instance is not None:
        try:
            if _browser_instance.is_connected():
                return _browser_instance
        except Exception as e:
            _browser_instance = None
    
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
    _browser_instance = await _playwright_instance.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']  # Better compatibility
    )
    
    return _browser_instance


async def cleanup_browser():
    """
    Clean up browser resources.
    
    Should be called when shutting down the server to properly
    close the browser and Playwright instances.
    """
    global _playwright_instance, _browser_instance
    
    if _browser_instance is not None:
        try:
            await _browser_instance.close()
        except Exception as e:
            pass
        finally:
            _browser_instance = None
    
    if _playwright_instance is not None:
        try:
            await _playwright_instance.stop()
        except Exception as e:
            pass
        finally:
            _playwright_instance = None


async def is_browser_available() -> bool:
    """Check if browser is available and working."""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        return False
