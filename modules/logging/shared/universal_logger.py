"""
Universal Logger for Cold Outreach Platform
Provides centralized logging for Python scripts, FastAPI backend, and Next.js frontend

Features:
- Daily log rotation with JSON structured logs
- Separate error logs for quick debugging
- ExecutionTracker for script-level monitoring
- Optional Supabase integration
- Performance tracking with @auto_log decorator
"""

import logging
import json
import time
import functools
import os
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

    def track_execution(self, script_name: str):
        """
        Context manager for tracking script execution

        Usage:
            with logger.track_execution("apollo-collector"):
                # Your script logic
                process_leads()

        Automatically logs:
        - Script start
        - Script completion with duration
        - Script failure with error details
        """
        return ExecutionTracker(self, script_name)

    def log_to_supabase(self, table: str = "logs", run_id: Optional[str] = None):
        """
        Optional: Send log entry to Supabase
        Only works if SUPABASE_URL and SUPABASE_SERVICE_KEY are set in environment

        Usage:
            logger.info("Processing data", count=100)
            logger.log_to_supabase(run_id="uuid-here")  # Optional
        """
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_key:
            return  # Silently skip if not configured

        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)

            # Note: This is optional and doesn't affect file logging
            # Implement only if you need UI visualization

        except ImportError:
            pass  # Supabase client not installed, skip
        except Exception:
            pass  # Any other error, skip silently


class ExecutionTracker:
    """
    Context manager for tracking script execution with automatic logging

    Features:
    - Logs script start time
    - Logs completion with duration and results
    - Logs failures with error details
    - Automatically calculates execution metrics

    Usage:
        logger = get_logger(__name__)

        with logger.track_execution("apollo-lead-collector") as tracker:
            leads = fetch_leads()
            tracker.add_metric("leads_fetched", len(leads))
            process_leads(leads)
            tracker.add_metric("leads_processed", len(leads))
    """

    def __init__(self, logger: 'UniversalLogger', script_name: str):
        self.logger = logger
        self.script_name = script_name
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"{self.script_name} started", script=self.script_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0

        if exc_type:
            # Script failed
            self.logger.error(
                f"{self.script_name} failed",
                script=self.script_name,
                duration_seconds=round(duration, 2),
                error_type=exc_type.__name__,
                error_details=str(exc_val),
                **self.metrics
            )
        else:
            # Script succeeded
            self.logger.info(
                f"{self.script_name} completed successfully",
                script=self.script_name,
                duration_seconds=round(duration, 2),
                **self.metrics
            )

        return False  # Don't suppress exceptions

    def add_metric(self, key: str, value: Any):
        """
        Add custom metric to track

        Usage:
            tracker.add_metric("api_cost_usd", 0.05)
            tracker.add_metric("records_processed", 150)
        """
        self.metrics[key] = value

    def add_metrics(self, **metrics):
        """
        Add multiple metrics at once

        Usage:
            tracker.add_metrics(
                api_calls=10,
                cost_usd=0.05,
                records=150
            )
        """
        self.metrics.update(metrics)


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
