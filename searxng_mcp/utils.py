"""Utility functions for the SearXNG MCP Server."""

from functools import wraps
from typing import Any, Callable


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in async functions.
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped function with exception handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise
    return wrapper


def format_error(error: Exception, context: str = "") -> dict:
    """
    Format an exception into a standardized error dictionary.
    
    Args:
        error: The exception to format
        context: Additional context about where the error occurred
        
    Returns:
        Dictionary with error details
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    result = {
        "status": "error",
        "error_type": error_type,
        "error": error_msg
    }
    
    if context:
        result["context"] = context
    
    return result
