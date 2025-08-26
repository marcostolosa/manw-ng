#!/usr/bin/env python3
"""
Automated Win32 API Tests for MANW-NG

Tests comprehensive functionality across different API categories.
"""

import json
import sys
import os
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from manw_ng.core.scraper import Win32APIScraper
from manw_ng.output.formatters import JSONFormatter


class TestResults:
    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def add_result(
        self, function_name, success, url=None, error=None, category="unknown"
    ):
        self.results.append(
            {
                "function": function_name,
                "success": success,
                "url": url,
                "error": error,
                "category": category,
                "timestamp": time.time(),
            }
        )

    def get_summary(self):
        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        failed = total - success
        duration = time.time() - self.start_time

        return {
            "total_tests": total,
            "successful": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "duration_seconds": round(duration, 2),
            "results": self.results,
        }


def test_function(scraper, function_name, category="unknown"):
    """Test a single function and return result"""
    try:
        result = scraper.scrape_function(function_name)

        if result and result.get("documentation_found") is True:
            return True, result.get("url"), None
        else:
            return False, None, "Documentation not found"
    except Exception as e:
        return False, None, str(e)


def main():
    """Run comprehensive Win32 API tests"""
    print("MANW-NG Automated Win32 API Tests")
    print("=" * 40)

    # Test functions across different categories
    test_functions = [
        # Win32 API Functions
        ("CreateProcessW", "process_management"),
        ("VirtualAlloc", "memory_management"),
        ("CreateFileW", "file_operations"),
        ("RegOpenKeyEx", "registry"),
        ("CreateWindow", "ui_management"),
        # Native API Functions (WDK/DDI)
        ("NtAllocateVirtualMemory", "native_api"),
        ("ZwCreateFile", "native_api"),
        ("RtlInitUnicodeString", "native_api"),
        # UI Controls
        ("CreateToolbarEx", "ui_controls"),
        ("GetStockObject", "gdi"),
        # Previously failing functions (regression tests)
        ("GetCommandLineA", "process_environment"),
        ("DeleteDC", "gdi"),
        ("InternetOpenA", "networking"),
    ]

    # Initialize scraper and test results
    scraper = Win32APIScraper(language="us", quiet=True)
    results = TestResults()

    print(f"Testing {len(test_functions)} functions...")
    print()

    # Run tests
    for i, (function_name, category) in enumerate(test_functions, 1):
        print(
            f"[{i:2d}/{len(test_functions)}] Testing {function_name:<20} ",
            end="",
            flush=True,
        )

        success, url, error = test_function(scraper, function_name, category)
        results.add_result(function_name, success, url, error, category)

        if success:
            print("PASS")
        else:
            print(f"FAIL - {error}")

    # Generate summary
    summary = results.get_summary()

    print()
    print("=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    print(f"Total Tests:    {summary['total_tests']}")
    print(f"Successful:     {summary['successful']}")
    print(f"Failed:         {summary['failed']}")
    print(f"Success Rate:   {summary['success_rate']:.1f}%")
    print(f"Duration:       {summary['duration_seconds']:.2f}s")

    # Category breakdown
    categories = {}
    for result in results.results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if result["success"]:
            categories[cat]["success"] += 1

    print()
    print("BY CATEGORY:")
    for cat, stats in categories.items():
        rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {cat:<20} {stats['success']}/{stats['total']} ({rate:.0f}%)")

    # Save detailed results
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"win32_tests_report_{timestamp}.json"

    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print(f"Detailed report saved: {report_file}")

    # Exit with appropriate code
    if summary["failed"] > 0:
        print()
        print("Some tests failed!")
        sys.exit(1)
    else:
        print()
        print("All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
