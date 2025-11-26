#!/usr/bin/env python3
"""
=== UNIVERSAL PROGRESS TRACKER ===
Version: 1.0.0 | Created: 2025-11-21

PURPOSE:
Universal real-time progress tracking for any long-running operation.
Writes progress to JSON file that can be read by UI in real-time.

FEATURES:
- Thread-safe progress updates
- Auto-calculates ETA
- Tracks custom metrics
- JSON file for UI integration
- Automatic cleanup

USAGE:
    from modules.shared.progress_tracker import ProgressTracker

    # Create tracker
    tracker = ProgressTracker(
        total=100,
        operation_name="Email Scraping",
        progress_file="temp/scraping_progress.json"
    )

    # Update progress
    tracker.update(
        processed=50,
        custom_stats={"emails_found": 25, "pages_processed": 150}
    )

    # Complete
    tracker.complete()
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


class ProgressTracker:
    """
    Thread-safe progress tracker with real-time JSON updates
    """

    def __init__(
        self,
        total: int,
        operation_name: str = "Processing",
        progress_file: Optional[str] = None,
        auto_update_interval: float = 1.0
    ):
        """
        Initialize progress tracker

        Args:
            total: Total number of items to process
            operation_name: Name of the operation (e.g., "Email Scraping")
            progress_file: Path to JSON file for progress updates
            auto_update_interval: Seconds between auto-updates (default: 1.0)
        """
        self.total = total
        self.operation_name = operation_name
        self.auto_update_interval = auto_update_interval

        # Progress state
        self.processed = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.custom_stats = {}
        self.is_complete = False

        # Thread safety
        self._lock = threading.Lock()

        # Progress file
        if progress_file:
            self.progress_file = Path(progress_file)
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Default to temp directory
            temp_dir = Path(__file__).parent.parent.parent / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.progress_file = temp_dir / f"progress_{timestamp}.json"

        # Write initial state
        self._write_progress()

    def update(
        self,
        processed: Optional[int] = None,
        increment: int = 1,
        custom_stats: Optional[Dict[str, Any]] = None
    ):
        """
        Update progress

        Args:
            processed: Absolute number of processed items (if provided)
            increment: Increment processed count by this amount (if processed not provided)
            custom_stats: Dictionary with custom metrics to track
        """
        with self._lock:
            # Update processed count
            if processed is not None:
                self.processed = processed
            else:
                self.processed += increment

            # Update custom stats
            if custom_stats:
                self.custom_stats.update(custom_stats)

            # Check if should write to file (throttle updates)
            current_time = time.time()
            if current_time - self.last_update_time >= self.auto_update_interval:
                self._write_progress()
                self.last_update_time = current_time

    def complete(self, final_stats: Optional[Dict[str, Any]] = None):
        """
        Mark operation as complete

        Args:
            final_stats: Optional final statistics
        """
        with self._lock:
            self.is_complete = True
            if final_stats:
                self.custom_stats.update(final_stats)
            self._write_progress()

    def _write_progress(self):
        """
        Write current progress to JSON file (internal, call with lock held)
        """
        elapsed = time.time() - self.start_time

        # Calculate progress percentage
        if self.total > 0:
            progress_pct = (self.processed / self.total) * 100
        else:
            progress_pct = 0

        # Calculate ETA
        if self.processed > 0 and not self.is_complete:
            rate = self.processed / elapsed
            remaining = self.total - self.processed
            eta_seconds = remaining / rate if rate > 0 else 0
            eta_str = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta_seconds = 0
            eta_str = "Calculating..." if not self.is_complete else "Complete"

        # Calculate speed
        speed = self.processed / elapsed if elapsed > 0 else 0

        # Build progress data
        progress_data = {
            "operation_name": self.operation_name,
            "status": "complete" if self.is_complete else "running",
            "total": self.total,
            "processed": self.processed,
            "remaining": self.total - self.processed,
            "progress_pct": round(progress_pct, 1),
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_str": str(timedelta(seconds=int(elapsed))),
            "eta_seconds": round(eta_seconds, 1),
            "eta_str": eta_str,
            "speed": round(speed, 2),
            "speed_unit": "items/sec",
            "timestamp": datetime.now().isoformat(),
            "custom_stats": self.custom_stats
        }

        # Write to file
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            # Don't crash if can't write progress
            pass

    def get_progress_file(self) -> Path:
        """Get path to progress file"""
        return self.progress_file

    def cleanup(self):
        """Remove progress file"""
        try:
            if self.progress_file.exists():
                self.progress_file.unlink()
        except Exception:
            pass

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        if not self.is_complete:
            self.complete()
        return False


def read_progress(progress_file: str) -> Optional[Dict[str, Any]]:
    """
    Read progress from JSON file

    Args:
        progress_file: Path to progress JSON file

    Returns:
        Progress data dictionary or None if file doesn't exist
    """
    try:
        with open(progress_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
