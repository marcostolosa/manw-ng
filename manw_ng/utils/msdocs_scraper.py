"""High level Microsoft Docs scraper for Win32/WDK symbols.

This module implements a robust scraper that resolves a symbol to its
official documentation page, extracts metadata, expands the header's TOC
and returns all entities contained in that header.  Both Portuguese and
English locales are supported.

The implementation purposely avoids external dependencies other than
``requests`` and ``BeautifulSoup`` so that it can be used as a small
utility or imported as a library.

Example
-------
>>> from manw_ng.utils.msdocs_scraper import MSDocsScraper
>>> scraper = MSDocsScraper()
>>> entries = scraper.scrape_symbol("CreateFileW")
>>> len(entries)  # doctest: +SKIP
120
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .complete_win32_api_mapping import get_function_url_fast
from .smart_url_generator import SmartURLGenerator

log = logging.getLogger(__name__)


@dataclass
class TOCEntry:
    """Metadata for a single entity extracted from Microsoft Docs."""

    name: str
    type: str
    header: str
    locale: str
    url: str
    uid: str
    asset_id: str
    topic: str
    source_area: str


WIN32_BASE = "https://learn.microsoft.com"
LOCALES = {"pt-br", "en-us"}


def _swap_locale(url: str, locale: str) -> str:
    """Return ``url`` with the locale segment swapped."""
    if locale not in LOCALES:
        raise ValueError(f"unsupported locale: {locale}")
    parsed = urlparse(url)
    parts = parsed.path.split("/")
    if len(parts) > 1 and parts[1] in LOCALES:
        parts[1] = locale
    else:
        parts.insert(1, locale)
    new_path = "/".join(part for part in parts if part)
    return parsed._replace(path="/" + new_path).geturl()


SDK_PATTERNS = {
    "function": re.compile(r"/windows/win32/api/([^/]+)/nf-\1-([^/]+)$"),
    "struct": re.compile(r"/windows/win32/api/([^/]+)/ns-\1-([^/]+)$"),
    "enum": re.compile(r"/windows/win32/api/([^/]+)/ne-\1-([^/]+)$"),
    "interface": re.compile(r"/windows/win32/api/([^/]+)/nn-\1-([^/]+)$"),
    "method": re.compile(
        r"/windows/win32/api/([^/]+)/nf-\1-([^-]+)-([^/]+)$"
    ),
}

DDI_PATTERNS = {
    "function": re.compile(
        r"/windows-hardware/drivers/ddi/([^/]+)/nf-\1-([^/]+)$"
    ),
    "struct": re.compile(
        r"/windows-hardware/drivers/ddi/([^/]+)/ns-\1-([^/]+)$"
    ),
    "enum": re.compile(
        r"/windows-hardware/drivers/ddi/([^/]+)/ne-\1-([^/]+)$"
    ),
}


def classify_url(url: str) -> Tuple[str, str, str]:
    """Return ``(type, header, source_area)`` for ``url``.

    ``type`` is one of ``function``, ``struct``, ``enum``, ``interface``,
    ``method`` or ``concept/const``. ``source_area`` is ``SDK``, ``DDI`` or
    ``ThemedSection``.
    """

    for typ, pattern in SDK_PATTERNS.items():
        m = pattern.search(url)
        if m:
            header = m.group(1)
            return typ, header, "SDK"
    for typ, pattern in DDI_PATTERNS.items():
        m = pattern.search(url)
        if m:
            header = m.group(1)
            return typ, header, "DDI"
    if "/windows/win32/" in url:
        return "concept/const", "", "ThemedSection"
    return "concept/const", "", "ThemedSection"


class MSDocsScraper:
    """Scraper implementing the specification from user instructions."""

    def __init__(self, locale: str = "pt-br", *, max_retries: int = 3, delay: float = 0.5) -> None:
        if locale not in LOCALES:
            raise ValueError("locale must be 'pt-br' or 'en-us'")
        self.locale = locale
        self.session = requests.Session()
        self.max_retries = max_retries
        self.delay = delay
        self.smart = SmartURLGenerator()

    # ------------------------------------------------------------------
    # Network helpers
    def _get(self, url: str) -> Optional[requests.Response]:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp
            except Exception as exc:  # pragma: no cover - network errors
                log.warning("error fetching %s: %s", url, exc)
                time.sleep(self.delay * attempt)
        return None

    # ------------------------------------------------------------------
    # Symbol resolution
    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """Return the documentation URL for ``symbol``.

        The resolver first consults the local catalog, then tries the
        smart URL generator and finally falls back to a web search.
        """

        url = get_function_url_fast(symbol, self.locale)
        if url and self._get(url):
            return url

        urls = self.smart.generate_possible_urls(symbol)
        for candidate in urls:
            url = f"{WIN32_BASE}/{self.locale}/windows/win32/api/{candidate}"
            if self._get(url):
                return url

        search = self._site_search(symbol)
        if search and self._get(search):
            return search
        return None

    def _site_search(self, symbol: str) -> Optional[str]:  # pragma: no cover - network
        query = f'site:learn.microsoft.com "{symbol}" "Syntax"'
        resp = self._get("https://www.bing.com/search?q=" + requests.utils.quote(query))
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        a = soup.select_one("li.b_algo h2 a")
        return a["href"] if a else None

    # ------------------------------------------------------------------
    def _parse_page(self, url: str) -> Optional[Tuple[BeautifulSoup, Dict[str, str]]]:
        resp = self._get(url)
        if not resp:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        metas = {}
        for key in [
            "UID",
            "asset_id",
            "req.header",
            "ms.topic",
            "toc_rel",
            "breadcrumb_path",
        ]:
            tag = soup.select_one(f'meta[name="{key}"]')
            if tag and tag.get("content"):
                metas[key] = tag["content"]
        link = soup.select_one('link[rel="canonical"]')
        if link and link.get("href"):
            metas["canonical"] = link["href"]
        return soup, metas

    def _fetch_toc(self, url: str, metas: Dict[str, str]) -> Optional[Dict]:
        toc_rel = metas.get("toc_rel") or metas.get("breadcrumb_path")
        if not toc_rel:
            return None
        toc_url = urljoin(url, toc_rel)
        resp = self._get(toc_url)
        if not resp:
            return None
        try:
            return resp.json()
        except Exception as exc:  # pragma: no cover - JSON errors
            log.warning("invalid toc.json at %s: %s", toc_url, exc)
            return None

    def _walk_toc(self, toc: Dict, base_url: str) -> Iterator[Tuple[str, str]]:
        def _walk(node: Dict) -> Iterator[Tuple[str, str]]:
            href = node.get("href")
            name = node.get("name", "")
            if href:
                yield name, urljoin(base_url, href)
            for key in ("items", "children"):
                for child in node.get(key, []) or []:
                    yield from _walk(child)

        for item in toc.get("items") or toc.get("children") or []:
            yield from _walk(item)

    # ------------------------------------------------------------------
    def scrape_symbol(self, symbol: str) -> List[TOCEntry]:
        url = self.resolve_symbol(symbol)
        if not url:
            raise RuntimeError(f"could not resolve symbol {symbol}")

        page = self._parse_page(url)
        if not page:
            raise RuntimeError(f"failed to load {url}")
        soup, metas = page
        toc = self._fetch_toc(url, metas)
        if not toc:
            raise RuntimeError("toc.json not found")

        entries: List[TOCEntry] = []
        for _, href in self._walk_toc(toc, url):
            for locale in LOCALES:
                loc_url = _swap_locale(href, locale)
                page = self._parse_page(loc_url)
                if not page:
                    continue
                psoup, pmeta = page
                h1 = psoup.find("h1")
                name = h1.get_text(strip=True) if h1 else href.rsplit("/", 1)[-1]
                typ, header, area = classify_url(loc_url)
                entry = TOCEntry(
                    name=name,
                    type=typ,
                    header=pmeta.get("req.header", header),
                    locale=locale,
                    url=loc_url,
                    uid=pmeta.get("UID", ""),
                    asset_id=pmeta.get("asset_id", ""),
                    topic=pmeta.get("ms.topic", ""),
                    source_area=area,
                )
                entries.append(entry)
        return entries

    # ------------------------------------------------------------------
    def output_csv(self, entries: Iterable[TOCEntry]) -> None:
        writer = csv.writer(sys.stdout)
        writer.writerow(
            [
                "name",
                "type",
                "header",
                "locale",
                "url",
                "uid",
                "asset_id",
                "topic",
                "source_area",
            ]
        )
        for e in entries:
            writer.writerow(
                [
                    e.name,
                    e.type,
                    e.header,
                    e.locale,
                    e.url,
                    e.uid,
                    e.asset_id,
                    e.topic,
                    e.source_area,
                ]
            )

    def print_summary(self, entries: Iterable[TOCEntry]) -> None:
        entries = list(entries)
        total = len(entries)
        by_type = Counter(e.type for e in entries)
        by_header = Counter(e.header for e in entries)
        by_locale = Counter(e.locale for e in entries)
        by_area = Counter(e.source_area for e in entries)

        summary_lines = [
            f"Total entries: {total}",
            "By type:",
        ]
        summary_lines.extend(f"  {k}: {v}" for k, v in by_type.items())
        summary_lines.append("By header:")
        summary_lines.extend(f"  {k}: {v}" for k, v in by_header.items())
        summary_lines.append("By locale:")
        summary_lines.extend(f"  {k}: {v}" for k, v in by_locale.items())
        summary_lines.append("By source_area:")
        summary_lines.extend(f"  {k}: {v}" for k, v in by_area.items())

        for line in summary_lines[:10]:
            print(line, file=sys.stdout)


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover - CLI glue
    import argparse

    parser = argparse.ArgumentParser(description="Microsoft Docs scraper")
    parser.add_argument("symbol", help="Symbol to resolve")
    parser.add_argument(
        "-l", "--locale", choices=sorted(LOCALES), default="pt-br", help="Preferred locale"
    )
    args = parser.parse_args(argv)

    scraper = MSDocsScraper(locale=args.locale)
    entries = scraper.scrape_symbol(args.symbol)
    scraper.output_csv(entries)
    scraper.print_summary(entries)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
