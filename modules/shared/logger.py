#!/usr/bin/env python3
"""
=== SHARED LOGGER ===
Version: 1.0.0 | Created: 2025-09-25

PURPOSE:
Shared logging utilities for all modules with auto-log decorator functionality.
"""

import time
import functools
from typing import Any, Callable

def auto_log(module_name: str):
    """
    Auto-log decorator for tracking function execution

    Args:
        module_name: Name of the module for logging context
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                print(f"[{module_name}] {func.__name__} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"[{module_name}] {func.__name__} failed after {execution_time:.2f}s: {e}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                print(f"[{module_name}] {func.__name__} completed in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"[{module_name}] {func.__name__} failed after {execution_time:.2f}s: {e}")
                raise

        # Return appropriate wrapper based on whether function is async
        if hasattr(func, '_is_coroutine'):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator