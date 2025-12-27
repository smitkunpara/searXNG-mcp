# SearXNG MCP Server

A FastMCP-based MCP server for web search via SearXNG and page scraping with TOON encoding for LLM optimization.

## Features

- **Multi-query web search** via SearXNG with configurable result counts
- **Dual scraping methods**: requests (fast) and browser (JavaScript support)
- **TOON encoding** for token-efficient LLM communication
- **Modular architecture** with separated concerns
- **Retry logic** with exponential backoff for robust operation
- **Comprehensive logging** for debugging and monitoring
- **Environment variable configuration** for easy customization
- **Persistent browser instance** reuse for better performance

## Project Structure

```
searXNG mcp/
├── server.py              # Main FastMCP server entry point
├── searxng_mcp/           # Main package directory
│   ├── __init__.py        # Package initialization and exports
│   ├── config.py          # Configuration and constants
│   ├── search.py          # SearXNG search functionality
│   ├── scraper.py         # Web scraping with requests/browser
│   ├── browser.py         # Playwright browser management
│   └── utils.py           # Utility functions
├── pyproject.toml         # Project metadata and dependencies
├── .env.example           # Example environment variables
├── settings.yml           # SearXNG configuration
├── README.md              # This file
└── server_backup.py       # Backup of original server.py
```

## Prerequisites

- Python 3.10+
- A running SearXNG instance (for search functionality)
- [uv](https://github.com/astral-sh/uv) for dependency management

### Starting SearXNG with Docker

Start SearXNG on localhost:8080:

```bash
docker run -d \
  --name searxng \
  -p 8080:8080 \
  -e SEARXNG_SETTINGS__search__formats=html,json \
  -e SEARXNG_SETTINGS__server__secret_key=my_secret_key_12345 \
  -e SEARXNG_SETTINGS__server__limiter=false \
  -e SEARXNG_SETTINGS__server__image_proxy=false \
  -e SEARXNG_SETTINGS__server__public_instance=true \
  -e SEARXNG_SETTINGS__general__debug=false \
  -e SEARXNG_SETTINGS__server__api_enabled=true \
  -e SEARXNG_SETTINGS__general__trusted_proxies=127.0.0.1 \
  -e SEARXNG_SETTINGS__botdetection__enabled=false \
  searxng/searxng
```

Verify it's running: `curl "http://localhost:8080/search?q=test&format=json"`

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Install Playwright for browser scraping (optional):**
   ```bash
   uv run playwright install chromium
   ```

4. **Run the server:**
   ```bash
   uv run server.py
   ```

## VS Code MCP Setup

Create `.vscode/mcp.json` in your workspace with full configuration:

```json
{
  "servers": {
    "searxng-mcp": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "c:/Users/smitk/Desktop/searXNG mcp",
      "env": {
        "SEARXNG_URL": "http://localhost:8080",
        "REQUESTS_TIMEOUT": "10",
        "BROWSER_TIMEOUT": "30000",
        "MAX_CONTENT_LENGTH": "10000",
        "MAX_NUM_RESULTS": "50",
        "MAX_RETRIES": "3",
        "RETRY_DELAY": "1.0"
      }
    }
  }
}
```

### Kilo Code MCP Setup

If using Kilo Code editor, create `.kilocode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "searxng-mcp": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "c:/Users/smitk/Desktop/searXNG mcp",
      "alwaysAllow": ["search_web", "scrape_pages"],
      "disabled": false,
      "env": {
        "SEARXNG_URL": "http://localhost:8080",
        "REQUESTS_TIMEOUT": "10",
        "BROWSER_TIMEOUT": "30000",
        "MAX_CONTENT_LENGTH": "10000",
        "MAX_NUM_RESULTS": "50",
        "MAX_RETRIES": "3",
        "RETRY_DELAY": "1.0"
      }
    }
  }
}
```

### Environment Variables

The MCP server supports the following environment variables (also available in `.env.example`):

- `SEARXNG_URL`: SearXNG instance URL (default: `http://localhost:8080`)
- `REQUESTS_TIMEOUT`: HTTP request timeout in seconds (default: `10`)
- `BROWSER_TIMEOUT`: Browser operation timeout in milliseconds (default: `30000`)
- `MAX_CONTENT_LENGTH`: Maximum scraped content length in characters (default: `10000`)
- `MAX_NUM_RESULTS`: Maximum search results per query (default: `50`)
- `MAX_RETRIES`: Maximum retry attempts for failed requests (default: `3`)
- `RETRY_DELAY`: Delay between retries in seconds (default: `1.0`)

## Tools

### search_web
Execute multiple web search queries via SearXNG with TOON encoding for token efficiency.

**Input:**
- `query_configs` (list[dict], required): List of query configurations, each containing:
  - `query` (str, required): The search query string
  - `num_results` (int, optional, default 5): Number of results per query (1-50)

**Returns:**
- TOON-encoded string containing search results with:
  - `status`: "success" or "error"
  - `count`: Number of results returned
  - `results`: List of result objects with title, url, content
  - `error`: Error message (only present if status is "error")

**Headers:**
The server automatically includes the following headers in requests:
- `User-Agent`: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
- `X-Forwarded-For`: 127.0.0.1
- `X-Real-IP`: 127.0.0.1

### scrape_pages
Scrape content from multiple web pages with browser support and TOON encoding.

**Input:**
- `configs` (list[ScrapeConfig], required): List of scrape configurations
  - `url` (str, required): URL to scrape
  - `method` (str, optional, default "requests"): Scraping method
    - `"requests"` - Fast static HTML scraping (for traditional server-rendered sites)
    - `"browser"` - Full browser rendering with Playwright (for JavaScript apps like React, Next.js, Vue, Angular)
  - `wait_time` (int, optional, default 3): Seconds to wait for JavaScript to load (only used with `"browser"` method, ignored for `"requests"`, range: 0-30)

**When to use each method:**
- **Use `"requests"`** for: Traditional websites, server-rendered content, static HTML pages, blogs, documentation sites
- **Use `"browser"`** for: Single Page Applications (SPAs), Next.js/React apps, Vue/Angular apps, sites with dynamic JavaScript content, client-side rendered pages

**Example:**
```json
[
  {"url": "https://python.org", "method": "requests"},
  {"url": "https://getrepeat.io", "method": "browser", "wait_time": 3}
]
```

**Returns:**
- TOON-encoded string containing scraped content indexed by `{index}_{url}_{method}` format
- Each result includes:
  - `status`: "success" or "error"
  - `method`: The scraping method used ("requests" or "browser")
  - `title`: Page title
  - `content`: Extracted text content (max 10,000 chars by default)
  - `length`: Actual content length after truncation
  - `original_length`: Original content length before truncation
  - `truncated`: Boolean indicating if content was truncated
  - `error`: Error message (only present if status is "error")

**Note:** Results are keyed by index, URL, and method to support scraping the same URL with different methods.

## Features

### Dual Scraping Methods
- **requests**: Fast static HTML scraping using requests + BeautifulSoup
  - Best for: Traditional server-rendered websites, static content
  - Pros: Fast, lightweight, no browser overhead
  - Cons: Cannot execute JavaScript, won't work with SPAs
  
- **browser**: Full browser rendering using Playwright with Chromium
  - Best for: JavaScript-heavy sites (React, Next.js, Vue, Angular)
  - Pros: Executes JavaScript, sees the fully rendered page
  - Cons: Slower, requires browser installation and more resources

## Configuration

All settings can be configured via environment variables. Copy [.env.example](.env.example) to `.env` and customize:

```bash
# SearXNG Configuration
SEARXNG_URL=http://localhost:8080

# Timeout Settings
REQUESTS_TIMEOUT=10          # seconds
BROWSER_TIMEOUT=30000        # milliseconds

# Content Limits
MAX_CONTENT_LENGTH=10000     # characters per page
MAX_NUM_RESULTS=50           # maximum search results per query

# Retry Configuration
MAX_RETRIES=3                # retry attempts
RETRY_DELAY=1.0              # seconds between retries

## Dependencies

Core dependencies (auto-installed with `uv sync`):
- `fastmcp`: MCP server framework
- `requests`: HTTP requests
- `beautifulsoup4` & `lxml`: HTML parsing
- `pydantic`: Data validation
- `playwright`: Browser automation (optional for browser scraping)
- `python-toon`: Token optimization
- `python-dotenv`: Environment variable management

## Improvements Made

### Logic Fixes
✅ **num_results validation**: Now properly validates and clamps to 1-50 range
✅ **Retry logic**: Added exponential backoff for failed requests
✅ **Browser cleanup**: Proper resource cleanup on shutdown
✅ **Configurable SearXNG URL**: Via environment variables
✅ **Error handling**: Comprehensive try-catch blocks with detailed error messages

### Code Quality
✅ **Modular architecture**: Separated into config, search, scraper, browser, utils modules
✅ **Logging**: Comprehensive logging throughout
✅ **Type hints**: Full type annotations
✅ **Documentation**: Detailed docstrings for all functions

### New Features
✅ **Environment variables**: Configurable via .env file
✅ **Retry logic**: Automatic retries with exponential backoff
✅ **Better error messages**: Contextual error information
✅ **Content metadata**: Tracks original length, truncation status
✅ **Browser stability**: Better error handling and connection checks

### Content Cleaning
Automatically removes unwanted elements:
- Scripts, styles, navigation, footers
- Elements with non-content class/ID patterns
- Normalizes whitespace for clean output

### Performance Optimizations
- Persistent browser instance reuse across calls
- TOON encoding for token-efficient LLM communication
- Content length limiting (configurable per page)
- Exponential backoff retry strategy

## Usage Examples

### Search Web Example
```python
# Search for Python token efficient MCP tools
query_configs = [
    {
        "query": "Python token efficient MCP tool",
        "num_results": 5
    }
]
results = search_web(query_configs)
```

### Scrape Pages Example
```python
# Scrape a simple HTML page
configs = [
    {
        "url": "https://www.python.org",
        "method": "requests",
        "wait_time": 3
    }
]
results = scrape_pages(configs)