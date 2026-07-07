"""
Catalog Integration Utilities for MANW-NG

Integrates the comprehensive Win32 API catalog with the existing system.
"""

import json
import csv
from typing import Dict, Optional
from pathlib import Path


class Win32CatalogIntegration:
    """
    Integrates the comprehensive Win32 API catalog into the existing system
    """

    def __init__(self, catalog_path: str = None):
        """Initialize with catalog file path"""
        if catalog_path is None:
            # Look for catalog in the package's assets folder
            package_root = Path(__file__).parent.parent
            self.csv_path = package_root / "assets" / "win32_api_catalog.csv"
            self.json_path = package_root / "assets" / "win32_api_catalog.json"
        else:
            base_path = Path(catalog_path)
            self.csv_path = base_path.with_suffix(".csv")
            self.json_path = base_path.with_suffix(".json")

        self._catalog_data = None
        self._function_index = None
        self._load_catalog()

    def _load_catalog(self):
        """Load the catalog data"""
        try:
            if self.json_path.exists():
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self._catalog_data = json.load(f)
                    self._build_function_index()
            elif self.csv_path.exists():
                self._load_from_csv()
        except Exception as e:
            print(f"Warning: Could not load catalog: {e}")
            self._catalog_data = []
            self._function_index = {}

    def _load_from_csv(self):
        """Load catalog from CSV file"""
        self._catalog_data = []
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = {
                    "name": row["Nome"],
                    "type": row["Tipo"],
                    "header": row["Header"],
                    "url": row["URL"],
                    "language": row["Idioma"],
                    "description": row.get("Descrição", ""),
                }
                self._catalog_data.append(entry)
        self._build_function_index()

    def _build_function_index(self):
        """Build fast lookup index for functions"""
        self._function_index = {}
        for entry in self._catalog_data:
            name = entry["name"].lower()
            if name not in self._function_index:
                self._function_index[name] = []
            self._function_index[name].append(entry)

    def find_function(
        self, function_name: str, language: str = "en-us"
    ) -> Optional[Dict]:
        """
        Find function in catalog

        Args:
            function_name: Name of the function to find
            language: Preferred language (en-us or pt-br)

        Returns:
            Function entry dict or None
        """
        if not self._function_index:
            return None

        name_lower = function_name.lower()

        # Direct match
        if name_lower in self._function_index:
            entries = self._function_index[name_lower]

            # Prefer requested language
            for entry in entries:
                if entry["language"] == language and entry["type"] in [
                    "function",
                    "macro",
                ]:
                    return entry

            # Fallback to any language
            for entry in entries:
                if entry["type"] in ["function", "macro"]:
                    return entry

        # Try with A/W suffix variations
        for suffix in ["a", "w", ""]:
            test_name = (
                name_lower + suffix
                if suffix
                else name_lower[:-1] if name_lower.endswith(("a", "w")) else None
            )
            if test_name and test_name in self._function_index:
                entries = self._function_index[test_name]
                for entry in entries:
                    if entry["language"] == language and entry["type"] in [
                        "function",
                        "macro",
                    ]:
                        return entry

        return None

    def get_function_url(
        self, function_name: str, language: str = "en-us"
    ) -> Optional[str]:
        """Get direct URL for a function"""
        entry = self.find_function(function_name, language)
        return entry["url"] if entry else None


# Global catalog instance
_catalog_instance = None


def get_catalog() -> Win32CatalogIntegration:
    """Get global catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = Win32CatalogIntegration()
    return _catalog_instance
