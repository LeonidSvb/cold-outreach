#!/usr/bin/env python3
"""
Test OLD scraper version (before GPT fixes)
"""
import sys
import importlib.util
from pathlib import Path

# Load old scraper module
old_scraper_path = Path(__file__).parent / "scraper_OLD.py"
spec = importlib.util.spec_from_file_location("scraper_old", old_scraper_path)
scraper_old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper_old)

# Now run the main function from old scraper
if __name__ == "__main__":
    # Pass command line args
    sys.argv = [
        "scraper_OLD.py",
        "--input", r"C:\Users\79818\Downloads\NZ_test_100.csv",
        "--workers", "50",
        "--max-pages", "5",
        "--scraping-mode", "deep_search",
        "--email-format", "separate"
    ]

    # Run old scraper
    scraper_old.main()
