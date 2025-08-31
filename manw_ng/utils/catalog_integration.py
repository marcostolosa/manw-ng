"""
Catalog Integration Utilities for MANW-NG

Integrates the comprehensive Win32 API catalog with the existing system.
"""

import json
import csv
from typing import Dict, List, Optional, Set
from pathlib import Path


class Win32CatalogIntegration:
    """
    Integrates the comprehensive Win32 API catalog into the existing system
    """

    def __init__(self, catalog_path: str = None):
        """Initialize with catalog file path"""
        if catalog_path is None:
            # Look for catalog in assets folder
            project_root = Path(__file__).parent.parent.parent
            self.csv_path = project_root / "assets" / "win32_api_catalog.csv"
            self.json_path = project_root / "assets" / "win32_api_catalog.json"
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

    def get_functions_by_header(self, header: str) -> List[Dict]:
        """Get all functions from a specific header"""
        if not self._catalog_data:
            return []

        return [
            entry
            for entry in self._catalog_data
            if entry["header"].lower() == header.lower()
            and entry["type"] in ["function", "macro"]
        ]

    def get_all_headers(self) -> Set[str]:
        """Get all unique headers in the catalog"""
        if not self._catalog_data:
            return set()

        return {entry["header"] for entry in self._catalog_data if entry["header"]}

    def get_statistics(self) -> Dict:
        """Get catalog statistics"""
        if not self._catalog_data:
            return {}

        stats = {
            "total_entries": len(self._catalog_data),
            "by_type": {},
            "by_language": {},
            "by_header": {},
            "unique_functions": (
                len(self._function_index) if self._function_index else 0
            ),
        }

        for entry in self._catalog_data:
            # By type
            entry_type = entry["type"]
            stats["by_type"][entry_type] = stats["by_type"].get(entry_type, 0) + 1

            # By language
            lang = entry["language"]
            stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1

            # By header
            header = entry["header"]
            if header:
                stats["by_header"][header] = stats["by_header"].get(header, 0) + 1

        return stats

    def is_catalog_available(self) -> bool:
        """Check if catalog data is available"""
        return bool(self._catalog_data)


# Global catalog instance
_catalog_instance = None


def get_catalog() -> Win32CatalogIntegration:
    """Get global catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = Win32CatalogIntegration()
    return _catalog_instance


def find_function_fast(function_name: str, language: str = "en-us") -> Optional[str]:
    """
    Fast function lookup using catalog

    Returns:
        URL string or None
    """
    catalog = get_catalog()
    return catalog.get_function_url(function_name, language)
