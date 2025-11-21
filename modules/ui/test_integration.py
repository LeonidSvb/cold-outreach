#!/usr/bin/env python3
"""
Integration test for unified UI platform
Tests all imports and basic functionality
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("=" * 60)
print("UNIFIED UI PLATFORM - INTEGRATION TEST")
print("=" * 60)

# Test 1: Import components
print("\n[1/6] Testing component imports...")
try:
    from modules.ui.components import (
        render_file_uploader,
        render_column_selector,
        render_progress_tracker,
        render_results_viewer,
        render_pipeline_status
    )
    print("[OK] All components imported successfully")
except ImportError as e:
    print(f"[FAIL] Component import failed: {e}")
    sys.exit(1)

# Test 2: Import tabs
print("\n[2/6] Testing tab imports...")
try:
    from modules.ui.tabs import (
        render_email_scraper_tab,
        render_email_validator_tab,
        render_ai_processor_tab
    )
    print("[OK] All tabs imported successfully")
except ImportError as e:
    print(f"[FAIL] Tab import failed: {e}")
    sys.exit(1)

# Test 3: Import shared styles
print("\n[3/6] Testing shared styles import...")
try:
    from modules.shared.streamlit_styles import (
        init_page_config,
        apply_common_styles,
        create_header
    )
    print("[OK] Shared styles imported successfully")
except ImportError as e:
    print(f"[FAIL] Shared styles import failed: {e}")
    sys.exit(1)

# Test 4: Check module structure
print("\n[4/6] Checking module structure...")

required_dirs = [
    "modules/ui/components",
    "modules/ui/tabs",
    "modules/ui/results"
]

for dir_path in required_dirs:
    full_path = Path(__file__).parent.parent.parent / dir_path
    if full_path.exists():
        print(f"  [OK] {dir_path}")
    else:
        print(f"  [FAIL] {dir_path} not found")
        sys.exit(1)

# Test 5: Check required files
print("\n[5/6] Checking required files...")

required_files = [
    "modules/ui/__init__.py",
    "modules/ui/main_app.py",
    "modules/ui/README.md",
    "modules/ui/components/__init__.py",
    "modules/ui/components/file_uploader.py",
    "modules/ui/components/column_selector.py",
    "modules/ui/components/progress_tracker.py",
    "modules/ui/components/results_viewer.py",
    "modules/ui/components/pipeline_status.py",
    "modules/ui/tabs/__init__.py",
    "modules/ui/tabs/email_scraper_tab.py",
    "modules/ui/tabs/email_validator_tab.py",
    "modules/ui/tabs/ai_processor_tab.py"
]

for file_path in required_files:
    full_path = Path(__file__).parent.parent.parent / file_path
    if full_path.exists():
        print(f"  [OK] {file_path}")
    else:
        print(f"  [FAIL] {file_path} not found")
        sys.exit(1)

# Test 6: Validate function signatures
print("\n[6/6] Validating component signatures...")

import inspect

# Check file_uploader
sig = inspect.signature(render_file_uploader)
params = list(sig.parameters.keys())
assert 'label' in params, "file_uploader missing 'label' parameter"
assert 'key_prefix' in params, "file_uploader missing 'key_prefix' parameter"
print("  [OK] render_file_uploader signature valid")

# Check column_selector
sig = inspect.signature(render_column_selector)
params = list(sig.parameters.keys())
assert 'columns' in params, "column_selector missing 'columns' parameter"
assert 'multiselect' in params, "column_selector missing 'multiselect' parameter"
print("  [OK] render_column_selector signature valid")

# Check progress_tracker
sig = inspect.signature(render_progress_tracker)
params = list(sig.parameters.keys())
assert 'total' in params, "progress_tracker missing 'total' parameter"
assert 'processed' in params, "progress_tracker missing 'processed' parameter"
print("  [OK] render_progress_tracker signature valid")

# Check results_viewer
sig = inspect.signature(render_results_viewer)
params = list(sig.parameters.keys())
assert 'df' in params, "results_viewer missing 'df' parameter"
print("  [OK] render_results_viewer signature valid")

# Test 7: Check tab signatures
print("\n[7/7] Validating tab signatures...")

# All tabs should have no required parameters
for tab_func in [render_email_scraper_tab, render_email_validator_tab, render_ai_processor_tab]:
    sig = inspect.signature(tab_func)
    required_params = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]

    if len(required_params) == 0:
        print(f"  [OK] {tab_func.__name__} signature valid")
    else:
        print(f"  [FAIL] {tab_func.__name__} has required parameters: {[p.name for p in required_params]}")
        sys.exit(1)

# Final summary
print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nThe unified UI platform is ready to use.")
print("Run with: streamlit run modules/ui/main_app.py")
print("=" * 60)
