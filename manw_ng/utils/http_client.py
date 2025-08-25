"""HTTP client with caching and basic stealth features.

Historically this project relied on :mod:`aiohttp` for asynchronous HTTP
requests.  The GitHub CI environment, however, does not install
``aiohttp`` by default which caused imports to fail.  To keep the client
lightweight and compatible with the CI pipeline we now implement a
purely synchronous version based on :mod:`requests`.  The interface
remains the same so existing code continues to work without modification.
"""
from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path
from typing import Iterable, Optional

import requests

from .url_verifier import USER_AGENTS


class HTTPClient:
    """Small ``requests`` wrapper providing disk caching and stealth features."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        proxies: Optional[Iterable[str]] = None,
        rate_limit: int = 5,
        rotate_user_agent: bool = False,
    ) -> None:
        self.proxies = list(proxies) if proxies else []
        self.rotate_user_agent = rotate_user_agent
        self.user_agent = user_agent or random.choice(USER_AGENTS)
        self.rate_limit = rate_limit
        self._last_request = 0.0
        self.cache_dir = Path(".cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()

    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        return_json: bool = False,
    ):
        cache_path = self.cache_dir / (hashlib.md5(url.encode()).hexdigest() + ".html")
        if method.upper() == "GET" and not return_json and cache_path.exists():
            return cache_path.read_text()

        headers = {"User-Agent": self.user_agent}
        if self.rotate_user_agent:
            headers["User-Agent"] = random.choice(USER_AGENTS)
        proxy = random.choice(self.proxies) if self.proxies else None
        proxies = {"http": proxy, "https": proxy} if proxy else None

        # Simple rate limiting
        if self.rate_limit > 0:
            elapsed = time.time() - self._last_request
            wait = max(0, 1 / self.rate_limit - elapsed)
            if wait > 0:
                time.sleep(wait)

        response = self.session.request(
            method, url, params=params, headers=headers, proxies=proxies, timeout=10
        )
        self._last_request = time.time()
        response.raise_for_status()

        if return_json:
            return response.json()

        text = response.text
        if method.upper() == "GET" and not return_json:
            cache_path.write_text(text)
        return text

    # ------------------------------------------------------------------
    def get(self, url: str, **kwargs):
        """Perform a GET request."""
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        """Perform a POST request."""
        return self._request("POST", url, **kwargs)

