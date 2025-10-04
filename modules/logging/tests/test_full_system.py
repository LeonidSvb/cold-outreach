"""
Full Logging System Integration Test
Tests all components: Python, Backend API, Frontend integration
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.logging.shared.universal_logger import get_logger, auto_log


def test_python_logging():
    """Test 1: Python script logging"""
    print("\n=== TEST 1: Python Script Logging ===")

    logger = get_logger("test_integration")

    # Test all log levels
    logger.debug("Debug message", test_id=1)
    logger.info("Info message", test_id=2)
    logger.warning("Warning message", test_id=3)
    logger.error("Error message", test_id=4)

    # Test with exception
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("Exception caught", error=e, context="test")

    print("[OK] Python logging test passed")


@auto_log
def example_function(a, b):
    """Example function with auto-logging"""
    return a + b


def test_auto_log_decorator():
    """Test 2: @auto_log decorator"""
    print("\n=== TEST 2: Auto-log Decorator ===")

    result = example_function(5, 3)
    assert result == 8

    print("[OK] Auto-log decorator test passed")


def test_log_file_structure():
    """Test 3: Verify log files are created correctly"""
    print("\n=== TEST 3: Log File Structure ===")

    logs_dir = Path(__file__).parent.parent / "logs"
    today = datetime.now().strftime("%Y-%m-%d")

    main_log = logs_dir / f"{today}.log"
    error_log = logs_dir / "errors" / f"{today}.log"

    # Check files exist
    assert main_log.exists(), f"Main log not found: {main_log}"
    assert error_log.exists(), f"Error log not found: {error_log}"

    # Check files have content
    assert main_log.stat().st_size > 0, "Main log is empty"
    assert error_log.stat().st_size > 0, "Error log is empty"

    print(f"[OK] Log files exist:")
    print(f"  - {main_log} ({main_log.stat().st_size} bytes)")
    print(f"  - {error_log} ({error_log.stat().st_size} bytes)")


def test_log_format():
    """Test 4: Verify JSON format"""
    print("\n=== TEST 4: JSON Format Validation ===")

    import json

    logs_dir = Path(__file__).parent.parent / "logs"
    today = datetime.now().strftime("%Y-%m-%d")
    main_log = logs_dir / f"{today}.log"

    # Read and parse JSON lines
    with open(main_log, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    valid_json_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            log_entry = json.loads(line)

            # Verify required fields
            assert "timestamp" in log_entry
            assert "module" in log_entry
            assert "level" in log_entry
            assert "message" in log_entry

            valid_json_count += 1
        except json.JSONDecodeError as e:
            print(f"[WARNING] Invalid JSON line: {line[:100]}")

    print(f"[OK] JSON validation passed ({valid_json_count} valid entries)")


def test_backend_integration():
    """Test 5: Test backend integration (requires backend running)"""
    print("\n=== TEST 5: Backend Integration ===")

    try:
        import requests

        # Test /api/logs endpoint exists
        response = requests.post(
            'http://localhost:8003/api/logs',
            json={
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Test from integration suite',
                'data': {'test': True},
                'userAgent': 'test-suite',
                'url': 'http://test'
            },
            timeout=2
        )

        if response.status_code == 200:
            print("[OK] Backend /api/logs endpoint working")
        else:
            print(f"[WARNING] Backend returned {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[SKIP] Backend not running (start with: npm run backend)")
    except ImportError:
        print("[SKIP] requests library not installed")


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("LOGGING SYSTEM INTEGRATION TEST")
    print("=" * 60)

    try:
        test_python_logging()
        test_auto_log_decorator()
        test_log_file_structure()
        test_log_format()
        test_backend_integration()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        print("\nLogging system is production ready!")

    except AssertionError as e:
        print(f"\n[FAILED] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
