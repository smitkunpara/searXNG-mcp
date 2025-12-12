# SearXNG MCP Server

A FastMCP-based MCP server for web search via SearXNG and page scraping.

## Prerequisites

- Python 3.10+
- A running SearXNG instance (for search functionality)

### Starting SearXNG with Docker

Copy the provided `settings.yml` and start SearXNG:

```bash
docker run -d \
  --name searxng \
  -p 8888:8080 \
  -v $(pwd)/settings.yml:/etc/searxng/settings.yml \
  -e SEARXNG_BASE_URL=http://localhost:8888 \
  searxng/searxng
```

Verify it's running: `curl "http://localhost:8888/search?q=test&format=json"`

## Quick Start

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Start the MCP server:
   ```bash
   uv run searxng-mcp
   ```

## VS Code MCP Setup

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "searxng-mcp": {
      "command": "uv",
      "args": ["run", "searxng-mcp"],
      "cwd": "c:/Users/smitk/Desktop/searXNG mcp"
    }
  }
}
```

## Tools

### search_web
Execute multiple web search queries via SearXNG.

**Input:**
- `queries` (list[str], required): List of search queries
- `num_results` (int, optional, default 10): Number of results per query (1-50)
- `searxng_url` (str, optional, default "http://localhost:8888"): SearXNG instance URL

### scrape_pages
Scrape content from multiple web pages.

**Input:**
- `configs` (list[object], required): List of scrape configurations
  - `url` (str, required): URL to scrape
  - `method` (str, optional, default "requests"): "requests" or "browser"
  - `wait_time` (int, optional, default 3): Seconds to wait for dynamic content (browser only, 0-30)

## Tools

### search_web
Execute multiple web search queries via SearXNG.

**Input:**
- `queries` (list[str], required): List of search queries
- `num_results` (int, optional, default 10): Number of results per query (1-50)
- `searxng_url` (str, optional, default "http://localhost:8888"): SearXNG instance URL

### scrape_pages
Scrape content from multiple web pages.

**Input:**
- `configs` (list[object], required): List of scrape configurations
  - `url` (str, required): URL to scrape
  - `method` (str, optional, default "requests"): "requests" or "browser"
  - `wait_time` (int, optional, default 3): Seconds to wait for dynamic content (browser only, 0-30)
