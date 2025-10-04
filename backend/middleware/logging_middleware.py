"""
Logging Middleware for FastAPI Backend
Logs all API requests and responses with timing information
"""

from fastapi import Request
from modules.logging.shared.universal_logger import get_logger
import time

logger = get_logger("fastapi_backend")


async def log_requests(request: Request, call_next):
    """
    Middleware to log all API requests and responses

    Logs:
        - Request: method, path, client IP
        - Response: status code, duration
        - Errors: full error details
    """

    start_time = time.time()

    # Log incoming request
    logger.info(
        "API Request",
        method=request.method,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown"
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log successful response
        logger.info(
            "API Response",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )

        return response

    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time

        # Log error
        logger.error(
            "API Error",
            method=request.method,
            path=str(request.url.path),
            error=e,
            duration_ms=round(duration * 1000, 2)
        )

        # Re-raise exception for FastAPI error handling
        raise
