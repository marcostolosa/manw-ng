"""Helpers for loading packaged JSON assets.

Assets may be shipped gzipped (``<name>.gz``) to keep the wheel small; the
loader transparently prefers the gzipped variant and falls back to the plain
``.json`` file, so callers only ever refer to the logical ``.json`` name.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_json_asset(name: str) -> Any:
    """Load ``assets/<name>``, preferring a gzipped ``<name>.gz`` if present.

    ``name`` is always the plain ``.json`` filename (e.g. ``"header_mapping.json"``).
    Raises ``FileNotFoundError`` if neither variant exists.
    """
    gz_path = ASSETS_DIR / f"{name}.gz"
    if gz_path.exists():
        with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
            return json.load(fh)

    plain_path = ASSETS_DIR / name
    with open(plain_path, "r", encoding="utf-8") as fh:
        return json.load(fh)
