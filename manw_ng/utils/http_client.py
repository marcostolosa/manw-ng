"""Asynchronous HTTP client with caching, proxy and user-agent rotation support."""

from __future__ import annotations

import aiohttp
import asyncio
import hashlib
import random
from pathlib import Path
from typing import Iterable, Optional

from .smart_url_generator import SmartURLGenerator


class HTTPClient:
    """Small aiohttp wrapper providing disk caching and stealth features."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        proxies: Optional[Iterable[str]] = None,
        rate_limit: int = 5,
        rotate_user_agent: bool = False,
    ) -> None:
        self.proxies = list(proxies) if proxies else []
        self.rotate_user_agent = rotate_user_agent
        if user_agent is None:
            temp_generator = SmartURLGenerator()
            self.user_agent = temp_generator.user_agents[0]
        else:
            self.user_agent = user_agent
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.cache_dir = Path(".cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def _request(
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
            # Use user agents from SmartURLGenerator
            temp_generator = SmartURLGenerator()
            headers["User-Agent"] = random.choice(temp_generator.user_agents)
        proxy = random.choice(self.proxies) if self.proxies else None

        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, params=params, proxy=proxy, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    if return_json:
                        return await resp.json()
                    text = await resp.text()
                    if method.upper() == "GET" and not return_json:
                        cache_path.write_text(text)
                    return text

    def get(self, url: str, **kwargs):
        """Synchronous wrapper for GET requests."""
        return asyncio.run(self._request("GET", url, **kwargs))

    def post(self, url: str, **kwargs):
        return asyncio.run(self._request("POST", url, **kwargs))
