#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANW-NG: Win32 API Documentation Scraper (Next Generation)

Thin entry-point shim. All logic lives in manw_ng.cli so it's importable for
packaging (`pip install -e .` provides a `manw-ng` console command too).

Author: Marcos Tolosa
License: MIT
"""

from manw_ng.cli import main

if __name__ == "__main__":
    main()
