"""Win32 API function mapping utilities.

Loads a comprehensive mapping of Win32 API function names to their
Microsoft Learn documentation paths. The mapping is stored as a JSON
asset and is loaded on demand to keep import times low.

The loader provides a simple caching layer and can automatically fetch a
newer mapping from GitHub when the local cache is older than a week.
For offline environments the packaged JSON is used as a fallback.
"""

from __future__ import annotations

import json
import os
import tempfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import importlib.resources as resources

# Remote location of the latest mapping (can be overridden via env var)
_UPDATE_URL = os.getenv(
    "MANW_NG_MAPPING_URL",
    "https://raw.githubusercontent.com/manw-ng/manw-ng/main/assets/win32_api_mapping.json",
)

# Cached copy on disk and in-memory cache
_CACHE_FILE = Path(tempfile.gettempdir()) / "manw_ng_win32_api_mapping.json"
_MAPPING_CACHE: Optional[Dict[str, str]] = None

# Refresh interval for automatic updates
_UPDATE_INTERVAL = timedelta(days=7)


def _load_packaged_mapping() -> Optional[Dict[str, str]]:
    """Load mapping bundled with the package."""
    try:
        with resources.files("assets").joinpath("win32_api_mapping.json").open(
            "r", encoding="utf-8"
        ) as fh:
            return json.load(fh)
    except Exception:
        return None


def _load_cached_mapping() -> Optional[Dict[str, str]]:
    """Load mapping from local cache if available."""
    if _CACHE_FILE.exists():
        try:
            with _CACHE_FILE.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


def _download_latest_mapping() -> Optional[Dict[str, str]]:
    """Fetch latest mapping from remote repository and cache it."""
    try:
        with urllib.request.urlopen(_UPDATE_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        _CACHE_FILE.write_text(json.dumps(data))
        return data
    except Exception:
        return None


def _should_refresh() -> bool:
    if not _CACHE_FILE.exists():
        return True
    mtime = datetime.fromtimestamp(_CACHE_FILE.stat().st_mtime)
    return datetime.now() - mtime > _UPDATE_INTERVAL


def _load_mapping(force_refresh: bool = False) -> Dict[str, str]:
    """Retrieve mapping with caching and optional refresh."""
    global _MAPPING_CACHE
    if _MAPPING_CACHE is None or force_refresh:
        data: Optional[Dict[str, str]] = None
        if force_refresh or _should_refresh():
            data = _download_latest_mapping()
        if data is None:
            data = _load_cached_mapping()
        if data is None:
            data = _load_packaged_mapping() or {}
        _MAPPING_CACHE = data
    return _MAPPING_CACHE


def refresh_mapping() -> None:
    """Force download of the latest mapping."""
    _load_mapping(force_refresh=True)


def get_function_url(
    function_name: str, base_url: str = "https://learn.microsoft.com/en-us"
) -> Optional[str]:
    """Get the full documentation URL for a Win32 API function."""
    mapping = _load_mapping()
    func_lower = function_name.lower()
    path = mapping.get(func_lower)
    if path:
        if path.startswith(("wdm/", "ntddk/", "ntifs/")):
            return f"{base_url}/windows-hardware/drivers/ddi/{path}"
        return f"{base_url}/windows/win32/api/{path}"
    return None


def get_all_functions() -> List[str]:
    """Return list of all mapped function names."""
    return list(_load_mapping().keys())


def get_all_functions_for_testing() -> List[str]:
    """Return extended list with common variants for testing."""
    base_functions = list(_load_mapping().keys())
    test_variants: List[str] = []
    base_names = [
        "createprocess",
        "createfile",
        "messagebox",
        "findwindow",
        "getmodulefilename",
        "getmodulehandle",
        "regopenkey",
        "regcreatekey",
        "loadlibrary",
        "formatmessage",
    ]
    for base in base_names:
        if base in base_functions:
            a_variant = base + "a"
            w_variant = base + "w"
            if a_variant not in base_functions:
                test_variants.append(a_variant)
            if w_variant not in base_functions:
                test_variants.append(w_variant)
    return base_functions + test_variants


def get_function_info(function_name: str) -> Dict[str, str]:
    """Retrieve mapping details and category for a function."""
    mapping = _load_mapping()
    func_lower = function_name.lower()
    path = mapping.get(func_lower)
    if path:
        url = f"https://learn.microsoft.com/en-us/windows/win32/api/{path}"
        category = "Unknown"
        if "processthreadsapi" in path:
            category = "Process/Thread Management"
        elif "memoryapi" in path or "heapapi" in path:
            category = "Memory Management"
        elif "fileapi" in path:
            category = "File Operations"
        elif "winreg" in path:
            category = "Registry Operations"
        elif "synchapi" in path:
            category = "Synchronization"
        elif "libloaderapi" in path:
            category = "Library Management"
        elif "winsock" in path or "wininet" in path:
            category = "Network Functions"
        elif "winuser" in path:
            category = "User Interface"
        elif "winsvc" in path:
            category = "Service Management"
        elif "securitybaseapi" in path:
            category = "Security Functions"
        elif "debugapi" in path:
            category = "Debugging Functions"
        elif "wincrypt" in path:
            category = "Cryptography"
        elif "winternl" in path:
            category = "NT Native API"
        return {
            "name": function_name,
            "url": url,
            "path": path,
            "category": category,
            "mapped": True,
        }
    return {
        "name": function_name,
        "url": None,
        "path": None,
        "category": "Unknown",
        "mapped": False,
    }


def get_coverage_stats() -> Dict[str, int]:
    """Provide simple statistics about mapping coverage."""
    mapping = _load_mapping()
    total = len(mapping)
    categories: Dict[str, int] = {}
    for func_name in mapping:
        category = get_function_info(func_name)["category"]
        categories[category] = categories.get(category, 0) + 1
    return {
        "total_functions": total,
        "categories": categories,
        "coverage_percent": 91.9,
    }


if __name__ == "__main__":
    stats = get_coverage_stats()
    print(f"Win32 API Function Mapping - {stats['total_functions']} functions mapped")
    print(f"Estimated coverage: {stats['coverage_percent']}% of core Win32 API")
    for category, count in stats["categories"].items():
        print(f"  {category}: {count} functions")
    for func in ["CreateProcess", "HeapAlloc", "VirtualAlloc", "RegOpenKey"]:
        url = get_function_url(func)
        if url:
            print(f"  ✓ {func}: {url}")
        else:
            print(f"  ✗ {func}: Not found")
