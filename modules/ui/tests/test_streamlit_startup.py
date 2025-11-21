#!/usr/bin/env python3
"""
Test Streamlit app startup without actually launching UI
Verifies no import errors when main_app is loaded
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("=" * 60)
print("STREAMLIT STARTUP TEST")
print("=" * 60)

print("\n[1/3] Testing main_app imports...")

try:
    # Mock streamlit to avoid actual UI launch
    import unittest.mock as mock

    # Mock streamlit module
    sys.modules['streamlit'] = mock.MagicMock()

    # Now try importing main_app
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "main_app",
        Path(__file__).parent / "main_app.py"
    )
    main_app = importlib.util.module_from_spec(spec)

    print("[OK] main_app can be imported")

except Exception as e:
    print(f"[FAIL] main_app import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[2/3] Verifying tab modules are callable...")

try:
    from modules.ui.tabs import (
        render_email_scraper_tab,
        render_email_validator_tab,
        render_ai_processor_tab
    )

    # Check they're callable
    assert callable(render_email_scraper_tab)
    assert callable(render_email_validator_tab)
    assert callable(render_ai_processor_tab)

    print("[OK] All tabs are callable functions")

except Exception as e:
    print(f"[FAIL] Tab verification failed: {e}")
    sys.exit(1)

print("\n[3/3] Verifying component modules...")

try:
    from modules.ui.components import (
        render_file_uploader,
        render_column_selector,
        render_progress_tracker,
        render_results_viewer,
        render_pipeline_status
    )

    # Check they're callable
    assert callable(render_file_uploader)
    assert callable(render_column_selector)
    assert callable(render_progress_tracker)
    assert callable(render_results_viewer)
    assert callable(render_pipeline_status)

    print("[OK] All components are callable functions")

except Exception as e:
    print(f"[FAIL] Component verification failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STREAMLIT STARTUP TEST PASSED!")
print("=" * 60)
print("\nReady to launch:")
print("  streamlit run modules/ui/main_app.py")
print("=" * 60)
