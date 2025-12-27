"""SearXNG web search functionality."""

import asyncio
from typing import Dict, List

import requests

from .config import (
    MAX_NUM_RESULTS,
    MAX_RETRIES,
    REQUESTS_TIMEOUT,
    RETRY_DELAY,
    SEARXNG_URL,
    USER_AGENT,
)


def validate_num_results(num_results: int) -> int:
    """
    Validate and clamp num_results to acceptable range.
    
    Args:
        num_results: Requested number of results
        
    Returns:
        Validated number of results (1-MAX_NUM_RESULTS)
    """
    if num_results < 1:
        return 1
    if num_results > MAX_NUM_RESULTS:
        return MAX_NUM_RESULTS
    return num_results


async def search_query(query: str, num_results: int = 5, searxng_url: str = SEARXNG_URL) -> Dict:
    """
    Execute a single search query via SearXNG.
    
    Args:
        query: Search query string
        num_results: Number of results to return (1-50)
        searxng_url: SearXNG instance URL
        
    Returns:
        Dictionary with status and results
    """
    # Validate num_results
    num_results = validate_num_results(num_results)
    
    headers = {
        "User-Agent": USER_AGENT,
        "X-Forwarded-For": "127.0.0.1",
        "X-Real-IP": "127.0.0.1"
    }
    
    for attempt in range(MAX_RETRIES):
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
            
            
            return {
                "status": "success",
                "count": len(formatted_results),
                "results": formatted_results
            }
            
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "error": f"Request timed out after {REQUESTS_TIMEOUT} seconds",
                "count": 0,
                "results": []
            }
            
        except requests.exceptions.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return {
                "status": "error",
                "error": f"Failed to connect to SearXNG at {searxng_url}",
                "count": 0,
                "results": []
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "error": f"HTTP error: {e.response.status_code}",
                "count": 0,
                "results": []
            }
            
        except ValueError as e:
            return {
                "status": "error",
                "error": f"Invalid JSON response from SearXNG: {str(e)}",
                "count": 0,
                "results": []
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "count": 0,
                "results": []
            }
    
    # Should not reach here, but just in case
    return {
        "status": "error",
        "error": "Max retries exceeded",
        "count": 0,
        "results": []
    }


async def search_web(query_configs: List[dict]) -> Dict:
    """
    Execute multiple web search queries via SearXNG.
    
    Args:
        query_configs: List of dicts, each containing:
            - query: The search query string
            - num_results: Optional number of results (1-50, default 5)
        
    Returns:
        Dictionary mapping queries to their results
    """
    results = {}
    
    for config in query_configs:
        query = config.get("query")
        if not query:
            results["<missing_query>"] = {
                "status": "error",
                "error": "Query field is required",
                "count": 0,
                "results": []
            }
            continue
        
        num_results = config.get("num_results", 5)
        result = await search_query(query, num_results)
        results[query] = result
    
    return results
