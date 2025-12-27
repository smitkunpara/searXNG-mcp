"""Configuration settings for the SearXNG MCP Server."""

import os
from typing import Final

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, using system env vars only

# Server configuration
USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Timeout settings
REQUESTS_TIMEOUT: Final[int] = int(os.getenv("REQUESTS_TIMEOUT", "10"))  # seconds
BROWSER_TIMEOUT: Final[int] = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # milliseconds

# Content limits
MAX_CONTENT_LENGTH: Final[int] = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))  # characters
MAX_NUM_RESULTS: Final[int] = int(os.getenv("MAX_NUM_RESULTS", "50"))

# SearXNG configuration
SEARXNG_URL: Final[str] = os.getenv("SEARXNG_URL", "http://localhost:8080")

# Retry configuration
MAX_RETRIES: Final[int] = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY: Final[float] = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds
