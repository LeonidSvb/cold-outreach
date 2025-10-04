"""
Universal Logger for Cold Outreach Platform
Provides centralized logging for Python scripts, FastAPI backend, and Next.js frontend
"""

import logging
import json
import time
import functools
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, Callable


class UniversalLogger:
    """
    Simple centralized logger with daily rotation
    - Automatically creates daily log files (YYYY-MM-DD.log)
    - Separate error file for quick debugging
    - JSON structured logs for easy parsing
    - No external dependencies
    - Zero maintenance required
    """

    _instances: Dict[str, 'UniversalLogger'] = {}

    def __init__(self, module_name: str):
        self.module_name = module_name

        # Store logs inside logging module (modular architecture)
        module_dir = Path(__file__).parent.parent  # modules/logging/
        self.logs_dir = module_dir / "logs"
        self.errors_dir = self.logs_dir / "errors"

        # Create directories if not exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.errors_dir.mkdir(parents=True, exist_ok=True)

        # Setup Python logger
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Get current day for log file
        self._current_day = self._get_current_day()
        self._setup_handlers(self._current_day)

    def _get_current_day(self) -> str:
        """Get current day string in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")

    def _setup_handlers(self, day: str):
        """Setup file handlers for main log and error log"""
        main_log = self.logs_dir / f"{day}.log"
        error_log = self.errors_dir / f"{day}.log"

        # Main log handler (all levels)
        main_handler = logging.FileHandler(main_log, encoding='utf-8')
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(main_handler)

        # Error log handler (errors only)
        error_handler = logging.FileHandler(error_log, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(error_handler)

    def _check_day_rotation(self):
        """Check if day changed and rotate log files if needed"""
        current_day = self._get_current_day()
        if current_day != self._current_day:
            # Day changed - close old handlers and open new ones
            self.logger.handlers.clear()
            self._current_day = current_day
            self._setup_handlers(current_day)

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal log method with structured JSON data"""
        self._check_day_rotation()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": self.module_name,
            "level": level,
            "message": message
        }

        if extra:
            log_entry.update(extra)

        # Call appropriate log level
        log_func = getattr(self.logger, level.lower())
        log_func(json.dumps(log_entry, ensure_ascii=False))

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error with optional exception details"""
        extra = kwargs.copy()
        if error:
            extra["error_type"] = type(error).__name__
            extra["error_details"] = str(error)

        self._log("ERROR", message, extra)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, kwargs if kwargs else None)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("INFO", message, kwargs if kwargs else None)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, kwargs if kwargs else None)


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs raw JSON (already formatted by UniversalLogger)"""

    def format(self, record):
        return record.getMessage()


def get_logger(module_name: str) -> UniversalLogger:
    """
    Get or create logger instance for a module
    Uses singleton pattern to avoid duplicate loggers

    Usage:
        logger = get_logger(__name__)
        logger.info("Script started", lead_count=100)
        logger.error("API failed", error=e, status_code=500)
    """
    if module_name not in UniversalLogger._instances:
        UniversalLogger._instances[module_name] = UniversalLogger(module_name)
    return UniversalLogger._instances[module_name]


def auto_log(func: Callable) -> Callable:
    """
    Auto-log decorator for tracking function execution time and errors
    Replaces old modules/shared/logger.py @auto_log decorator

    Usage:
        @auto_log
        def process_leads(count: int):
            # Function logic
            pass

    Logs:
        - Function start (DEBUG level)
        - Function completion with duration (INFO level)
        - Function errors with duration (ERROR level)
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        start_time = time.time()

        logger.debug(f"{func.__name__} started")

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} completed",
                duration_seconds=round(duration, 2)
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                error=e,
                duration_seconds=round(duration, 2)
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        start_time = time.time()

        logger.debug(f"{func.__name__} started")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} completed",
                duration_seconds=round(duration, 2)
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                error=e,
                duration_seconds=round(duration, 2)
            )
            raise

    # Return appropriate wrapper based on whether function is async
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
