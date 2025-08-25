"""Asynchronous HTTP client with persistent session, caching and stealth features."""

from __future__ import annotations

import aiohttp
import asyncio
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Iterable, Optional

from .smart_url_generator import SmartURLGenerator


class HTTPClient:
    """aiohttp wrapper providing disk caching and stealth capabilities."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        proxies: Optional[Iterable[str]] = None,
        rate_limit: int = 5,
        rotate_user_agent: bool = False,
        cache_ttl: int = 60 * 60 * 24 * 7,
    ) -> None:
        self.proxies = list(proxies) if proxies else []
        self.rotate_user_agent = rotate_user_agent
        if user_agent is None:
            temp_generator = SmartURLGenerator()
            self.user_agent = temp_generator.user_agents[0]
        else:
            self.user_agent = user_agent
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.cache_dir = Path("~/.cache/manw-ng").expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl

        # Persistent event loop and session
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.session = aiohttp.ClientSession()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        return_json: bool = False,
        use_cache: bool = True,
    ):
        cache_path = self.cache_dir / (hashlib.md5(url.encode()).hexdigest() + ".json")
        cache_data = None
        headers = {"User-Agent": self.user_agent}
        if use_cache and method.upper() == "GET" and cache_path.exists():
            try:
                cache_data = json.loads(cache_path.read_text())
                age = time.time() - cache_data.get("timestamp", 0)
                if age < self.cache_ttl and not return_json:
                    return cache_data.get("content", "")
                if cache_data.get("etag"):
                    headers["If-None-Match"] = cache_data["etag"]
                if cache_data.get("last_modified"):
                    headers["If-Modified-Since"] = cache_data["last_modified"]
            except Exception:
                cache_data = None

        if self.rotate_user_agent:
            temp_generator = SmartURLGenerator()
            headers["User-Agent"] = random.choice(temp_generator.user_agents)
        proxy = random.choice(self.proxies) if self.proxies else None

        async with self.semaphore:
            async with self.session.request(
                method, url, params=params, proxy=proxy, headers=headers
            ) as resp:
                if resp.status == 304 and cache_data:
                    cache_data["timestamp"] = time.time()
                    cache_path.write_text(json.dumps(cache_data))
                    return cache_data.get("content", "")
                resp.raise_for_status()
                if method.upper() == "HEAD":
                    return resp.status
                if return_json:
                    data = await resp.json()
                else:
                    data = await resp.text()
                if (
                    use_cache
                    and method.upper() == "GET"
                    and not return_json
                    and resp.headers.get("ETag")
                ):
                    cache_payload = {
                        "content": data,
                        "etag": resp.headers.get("ETag"),
                        "last_modified": resp.headers.get("Last-Modified"),
                        "timestamp": time.time(),
                    }
                    cache_path.write_text(json.dumps(cache_payload))
                return data

    def request(self, method: str, url: str, **kwargs):
        return self.loop.run_until_complete(self._request(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        """Synchronous wrapper for GET requests."""
        return self.request("GET", url, **kwargs)

    def head(self, url: str, **kwargs):
        return self.request("HEAD", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def close(self) -> None:
        self.loop.run_until_complete(self.session.close())
        self.loop.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
