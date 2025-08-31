#!/usr/bin/env python3
"""
Continuous URL Validation System for MANW-NG

Automatically discovers and validates real working URLs,
updating the enhanced classifier database accordingly.
"""

import json
import requests
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ContinuousURLValidator:
    """Continuously validates and updates URL mappings"""

    def __init__(self, delay_between_requests: float = 1.0):
        self.delay = delay_between_requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Load current mappings
        self.mapping_file = Path("assets/complete_function_mapping.json")
        self.load_current_mappings()

        # Statistics
        self.validated_count = 0
        self.updated_count = 0
        self.failed_count = 0

    def load_current_mappings(self):
        """Load current function-to-header mappings"""
        if self.mapping_file.exists():
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                self.current_mappings = json.load(f)
        else:
            self.current_mappings = {}

        print(f"Loaded {len(self.current_mappings):,} existing mappings")

    def validate_url(self, url: str, timeout: int = 10) -> bool:
        """Check if URL returns 200 OK"""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate_possible_urls(self, function_name: str, header: str) -> List[str]:
        """Generate possible URL variations for a function"""
        func_lower = function_name.lower()
        header_lower = header.lower()

        base_patterns = [
            f"https://learn.microsoft.com/en-us/windows/win32/api/{header_lower}/nf-{header_lower}-{func_lower}",
            f"https://learn.microsoft.com/en-us/windows/desktop/api/{header_lower}/nf-{header_lower}-{func_lower}",
            f"https://learn.microsoft.com/en-us/windows/win32/{header_lower}/{header_lower}/nf-{header_lower}-{func_lower}",
            f"https://learn.microsoft.com/en-us/windows/win32/shell/{header_lower}/nf-{header_lower}-{func_lower}",
            f"https://learn.microsoft.com/en-us/windows/win32/multimedia/{header_lower}/nf-{header_lower}-{func_lower}",
        ]

        # Add driver pattern for suspected driver functions
        if any(prefix in func_lower for prefix in ["zw", "rtl", "io", "mm", "ke"]):
            base_patterns.append(
                f"https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/{header_lower}/nf-{header_lower}-{func_lower}"
            )

        return base_patterns

    def discover_working_url(
        self, function_name: str, predicted_header: str
    ) -> Optional[str]:
        """Discover the actual working URL for a function"""
        possible_urls = self.generate_possible_urls(function_name, predicted_header)

        print(f"  Testing {len(possible_urls)} URL patterns for {function_name}")

        for url in possible_urls:
            if self.validate_url(url):
                print(f"    OK: {url}")
                return url
            else:
                print(f"    NO: {url}")

            time.sleep(self.delay)

        return None

    def validate_sample_functions(self, sample_size: int = 20) -> Dict[str, str]:
        """Validate a random sample of functions and discover working URLs"""
        from manw_ng.ml.enhanced_classifier import enhanced_ml_classifier

        # Load test database
        test_db_file = Path("assets/comprehensive_test_db.json")
        if not test_db_file.exists():
            print("Error: comprehensive_test_db.json not found")
            return {}

        with open(test_db_file, "r", encoding="utf-8") as f:
            test_db = json.load(f)

        # Get random sample of functions
        all_functions = []
        for header, functions in test_db.items():
            for func in functions:
                all_functions.append((func, header))

        sample = random.sample(all_functions, min(sample_size, len(all_functions)))
        print(f"Validating {len(sample)} random functions...")

        new_mappings = {}

        for func_name, expected_header in sample:
            print(f"\nTesting: {func_name}")

            # Get ML prediction
            predictions = enhanced_ml_classifier.predict_headers(func_name, top_k=1)

            if predictions:
                predicted_header, confidence = predictions[0]
                print(f"  Predicted: {predicted_header} ({confidence:.2f})")

                # Try to find working URL
                working_url = self.discover_working_url(func_name, predicted_header)

                if working_url:
                    # Extract actual header from working URL
                    if "/api/" in working_url:
                        # Standard pattern: .../api/{header}/nf-{header}-{func}
                        parts = working_url.split("/api/")[1].split("/")
                        if len(parts) >= 1:
                            actual_header = parts[0]
                            new_mappings[func_name.lower()] = actual_header
                            print(f"  DISCOVERED: {func_name} -> {actual_header}")
                            self.validated_count += 1

                            if (
                                func_name.lower() not in self.current_mappings
                                or self.current_mappings[func_name.lower()]
                                != actual_header
                            ):
                                self.updated_count += 1
                else:
                    print(f"  FAILED: No working URL found for {func_name}")
                    self.failed_count += 1
            else:
                print(f"  ERROR: No prediction for {func_name}")
                self.failed_count += 1

            # Small delay between functions
            time.sleep(self.delay)

        return new_mappings

    def update_mappings(self, new_mappings: Dict[str, str]) -> int:
        """Update the mapping file with new discovered mappings"""
        if not new_mappings:
            return 0

        updated_count = 0

        for func, header in new_mappings.items():
            if (
                func not in self.current_mappings
                or self.current_mappings[func] != header
            ):
                self.current_mappings[func] = header
                updated_count += 1

        # Save updated mappings
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.current_mappings, f, indent=2, ensure_ascii=False)

        print(f"\nUpdated {updated_count} mappings in {self.mapping_file}")
        print(f"Total mappings now: {len(self.current_mappings):,}")

        return updated_count

    def generate_report(self) -> str:
        """Generate validation report"""
        total_tested = self.validated_count + self.failed_count
        success_rate = (
            (self.validated_count / total_tested) * 100 if total_tested > 0 else 0
        )

        report = f"""
CONTINUOUS URL VALIDATION REPORT
================================

Functions Tested: {total_tested}
Successfully Validated: {self.validated_count}
Failed Validations: {self.failed_count}
New/Updated Mappings: {self.updated_count}
Success Rate: {success_rate:.1f}%

Total Database Size: {len(self.current_mappings):,} mappings
        """

        return report


def main():
    print("MANW-NG Continuous URL Validator")
    print("=" * 40)

    validator = ContinuousURLValidator(delay_between_requests=0.8)

    # Validate sample of functions
    sample_size = 15  # Conservative for CI/CD
    new_mappings = validator.validate_sample_functions(sample_size)

    # Update database
    validator.update_mappings(new_mappings)

    # Generate report
    report = validator.generate_report()
    print(report)

    # Return success based on validation results
    if validator.validated_count > 0:
        print("SUCCESS: Found working URLs and updated database")
        return 0
    else:
        print("WARNING: No new working URLs discovered")
        return 1


if __name__ == "__main__":
    exit(main())
