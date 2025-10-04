"""
Test script for Universal Logger
Demonstrates all logging levels and features
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.logging.shared.universal_logger import get_logger

def test_basic_logging():
    """Test basic logging functionality"""
    print("=== Testing Basic Logging ===\n")

    logger = get_logger("test_module")

    # Test INFO
    logger.info("Test script started", test_id=1, environment="development")
    print("[OK] INFO log written")

    # Test DEBUG
    logger.debug("Processing test data", records=100, batch_size=20)
    print("[OK] DEBUG log written")

    # Test WARNING
    logger.warning("Rate limit approaching", remaining_calls=5, limit=100)
    print("[OK] WARNING log written")

    # Test ERROR without exception
    logger.error("API call failed", status_code=500, endpoint="/api/test")
    print("[OK] ERROR log written (no exception)")

    # Test ERROR with exception
    try:
        raise ValueError("Invalid configuration value")
    except Exception as e:
        logger.error("Configuration error occurred", error=e, config_key="api_key")
        print("[OK] ERROR log written (with exception)")

    print("\n=== All tests completed ===\n")


def test_multiple_modules():
    """Test logging from multiple modules"""
    print("=== Testing Multiple Modules ===\n")

    logger1 = get_logger("apollo_module")
    logger2 = get_logger("instantly_module")
    logger3 = get_logger("frontend")

    logger1.info("Apollo lead collection started", leads_count=50)
    logger2.info("Instantly campaign sync started", campaigns=4)
    logger3.error("File upload failed", filename="test.csv", size_mb=2.5)

    print("[OK] Multiple module logs written\n")


def show_log_files():
    """Show what log files were created"""
    print("=== Log Files Created ===\n")

    logs_dir = Path("data/logs")
    errors_dir = logs_dir / "errors"

    # Show main logs
    print("Main logs:")
    for log_file in sorted(logs_dir.glob("*.log")):
        size = log_file.stat().st_size
        print(f"  - {log_file.name} ({size} bytes)")

    # Show error logs
    print("\nError logs:")
    for log_file in sorted(errors_dir.glob("*.log")):
        size = log_file.stat().st_size
        print(f"  - errors/{log_file.name} ({size} bytes)")

    print()


if __name__ == "__main__":
    test_basic_logging()
    test_multiple_modules()
    show_log_files()

    print("SUCCESS: Logger testing complete!")
    print("\nTo view logs, open:")
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"  - data/logs/{today}.log")
    print(f"  - data/logs/errors/{today}.log")
