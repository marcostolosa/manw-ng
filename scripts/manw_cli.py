#!/usr/bin/env python3
"""
MANW-NG Command Line Interface
==============================

Simple CLI for Win32 API function scraping.
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from manw_ng.core.scraper import Win32APIScraper
from manw_ng.utils.complete_win32_api_mapping import get_function_url, get_all_functions


def scrape_function(function_name: str, output_format: str = "rich") -> bool:
    """Scrape a Win32 API function"""
    try:
        scraper = Win32APIScraper(language="us", quiet=(output_format == "json"))

        result = scraper.scrape_function(function_name)

        if not result:
            print(f"FAILED to scrape function: {function_name}")
            return False

        # Format output
        if output_format == "json":
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            from manw_ng.output.simple_formatter import format_function_rich

            output = format_function_rich(result)

        print(output)
        return True

    except Exception as e:
        print(f"ERROR scraping function: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="MANW-NG Win32 API Scraper")

    parser.add_argument("function", nargs="?", help="Function name to scrape")
    parser.add_argument(
        "--output", choices=["rich", "json"], default="rich", help="Output format"
    )
    parser.add_argument("--stats", action="store_true", help="Show mapping statistics")

    args = parser.parse_args()

    if args.stats:
        mapped_functions = len(get_all_functions())
        print(f"MANW-NG Statistics:")
        print(f"Mapped Functions: {mapped_functions}")
        return 0

    if not args.function:
        parser.print_help()
        return 1

    success = scrape_function(args.function, args.output)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
