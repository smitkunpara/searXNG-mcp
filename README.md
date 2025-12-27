# SearXNG MCP Server

A FastMCP-based MCP server for web search via SearXNG and page scraping with TOON encoding for LLM optimization.

## Prerequisites

- Python 3.10+
- A running SearXNG instance (for search functionality)

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

1. Install dependencies:
   ```bash
   uv sync
   ```

## VS Code MCP Setup

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "searxng-mcp": {
      "command": "uv",
      "args": ["run", "server.py"],
    }
  }
}
```

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
  - `method` (str, optional, default "requests"): "requests" or "browser"
  - `wait_time` (int, optional, default 3): Seconds to wait for dynamic content (browser only, 0-30)

**Returns:**
- TOON-encoded string containing scraped content for each URL with:
  - `status`: "success" or "error"
  - `method`: The scraping method used
  - `title`: Page title
  - `content`: Extracted text content (max 10,000 chars)
  - `length`: Actual content length
  - `error`: Error message (only present if status is "error")

## Features

### Dual Scraping Methods
- **requests**: Fast static HTML scraping using requests + BeautifulSoup
- **browser**: Full browser rendering using Playwright with Chromium for JavaScript-heavy sites

### Content Cleaning
Automatically removes unwanted elements:
- Scripts, styles, navigation, footers
- Elements with non-content class/ID patterns
- Normalizes whitespace for clean output

### Error Handling
Comprehensive error handling with detailed error messages:
- Connection timeouts
- HTTP errors
- Invalid JSON responses
- Playwright installation errors

### Performance Optimizations
- Persistent browser instance reuse across calls
- TOON encoding for token-efficient LLM communication
- Content length limiting (10,000 characters max per page)

## Configuration

### SearXNG Settings
The server uses the following SearXNG configuration:
- **Search formats**: html, json
- **Server settings**:
  - Secret key: my_secret_key_12345
  - Limiter: disabled
  - Image proxy: disabled
  - API enabled: true
- **General settings**:
  - Debug: disabled
  - Trusted proxies: 127.0.0.1
- **Bot detection**: disabled

### Server Configuration
The server is configured to use SearXNG at `http://localhost:8080` by default. You can modify the `searxng_url` variable in [`server.py`](server.py:164) to use a different SearXNG instance.

## Dependencies

- `requests`: For HTTP requests
- `beautifulsoup4`: For HTML parsing
- `fastmcp`: For MCP server functionality
- `pydantic`: For data validation
- `playwright` (optional): For browser-based scraping
- `toon`: For LLM token optimization

Install optional dependencies:
```bash
uv add playwright
uv run playwright install chromium
```

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