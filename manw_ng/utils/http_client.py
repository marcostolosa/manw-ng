"""Asynchronous HTTP client with intelligent caching, proxy and user-agent rotation support."""

from __future__ import annotations

import aiohttp
import asyncio
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

from .smart_url_generator import SmartURLGenerator


class HTTPClient:
    """Advanced aiohttp wrapper with intelligent caching, ETag/Last-Modified support and stealth features."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        proxies: Optional[Iterable[str]] = None,
        rate_limit: int = 5,
        rotate_user_agent: bool = False,
        cache_ttl: int = 3600,  # 1 hour default TTL
    ) -> None:
        self.proxies = list(proxies) if proxies else []
        self.rotate_user_agent = rotate_user_agent
        self.cache_ttl = cache_ttl

        if user_agent is None:
            temp_generator = SmartURLGenerator()
            self.user_agent = temp_generator.user_agents_flat[0]
        else:
            self.user_agent = user_agent

        self.semaphore = asyncio.Semaphore(rate_limit)

        # Intelligent cache directory with persistent storage
        cache_home = os.path.expanduser("~/.cache/manw-ng")
        self.cache_dir = Path(cache_home)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache metadata for ETag/Last-Modified support
        self.cache_meta_file = self.cache_dir / "cache_metadata.json"
        self._load_cache_metadata()

        # Session reuse for better performance
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_created_at = 0

    def _load_cache_metadata(self) -> None:
        """Load cache metadata for ETag/Last-Modified tracking"""
        try:
            if self.cache_meta_file.exists():
                with open(self.cache_meta_file, "r", encoding="utf-8") as f:
                    self.cache_metadata = json.load(f)
            else:
                self.cache_metadata = {}
        except Exception:
            self.cache_metadata = {}

    def _save_cache_metadata(self) -> None:
        """Save cache metadata to disk"""
        try:
            with open(self.cache_meta_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_metadata, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Fail silently on cache metadata issues

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached content is still valid based on TTL"""
        if cache_key not in self.cache_metadata:
            return False

        cached_time = self.cache_metadata[cache_key].get("timestamp", 0)
        return (time.time() - cached_time) < self.cache_ttl

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create persistent session for better performance"""
        current_time = time.time()

        # Reuse session for 5 minutes, then recreate
        if (
            not self._session
            or self._session.closed
            or (current_time - self._session_created_at) > 300
        ):

            if self._session and not self._session.closed:
                await self._session.close()

            # Advanced connector settings for better performance
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)

            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Connection": "keep-alive"},
            )
            self._session_created_at = current_time

        return self._session

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        return_json: bool = False,
    ) -> Union[str, dict]:
        """Enhanced request method with intelligent caching and conditional requests"""

        # Only cache GET requests that return HTML/text
        if method.upper() != "GET" or return_json:
            return await self._make_request(
                method, url, params=params, return_json=return_json
            )

        cache_key = self._get_cache_key(url)
        cache_path = self.cache_dir / f"{cache_key}.html"

        # Check if we have valid cached content
        if cache_path.exists() and self._is_cache_valid(cache_key):
            try:
                return cache_path.read_text(encoding="utf-8")
            except Exception:
                pass  # If reading fails, continue with request

        # Prepare conditional request headers
        headers = self._get_request_headers()

        # Add conditional headers if we have cache metadata
        if cache_key in self.cache_metadata:
            metadata = self.cache_metadata[cache_key]
            if "etag" in metadata:
                headers["If-None-Match"] = metadata["etag"]
            if "last_modified" in metadata:
                headers["If-Modified-Since"] = metadata["last_modified"]

        session = await self._get_session()
        proxy = random.choice(self.proxies) if self.proxies else None

        async with self.semaphore:
            try:
                async with session.request(
                    method, url, params=params, proxy=proxy, headers=headers
                ) as resp:

                    # Handle 304 Not Modified - return cached content
                    if resp.status == 304 and cache_path.exists():
                        try:
                            return cache_path.read_text(encoding="utf-8")
                        except Exception:
                            pass  # Fall through to handle as error

                    resp.raise_for_status()
                    content = await resp.text()

                    # Cache the response with metadata
                    await self._cache_response(
                        cache_key, cache_path, content, resp.headers
                    )

                    return content

            except aiohttp.ClientError:
                # If request fails and we have cached content, return it
                if cache_path.exists():
                    try:
                        return cache_path.read_text(encoding="utf-8")
                    except Exception:
                        pass
                raise

    def _get_request_headers(self) -> Dict[str, str]:
        """Generate optimized request headers with user-agent rotation"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        if self.rotate_user_agent:
            temp_generator = SmartURLGenerator()
            headers["User-Agent"] = random.choice(temp_generator.user_agents_flat)

        return headers

    async def _cache_response(
        self, cache_key: str, cache_path: Path, content: str, response_headers: dict
    ) -> None:
        """Cache response content and metadata"""
        try:
            # Save content to file
            cache_path.write_text(content, encoding="utf-8")

            # Update cache metadata
            self.cache_metadata[cache_key] = {
                "timestamp": time.time(),
                "url": str(cache_path),  # For debugging
            }

            # Store ETag and Last-Modified for conditional requests
            if "ETag" in response_headers:
                self.cache_metadata[cache_key]["etag"] = response_headers["ETag"]
            if "Last-Modified" in response_headers:
                self.cache_metadata[cache_key]["last_modified"] = response_headers[
                    "Last-Modified"
                ]

            # Save metadata asynchronously
            self._save_cache_metadata()

        except Exception:
            pass  # Fail silently on cache errors

    async def _make_request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        return_json: bool = False,
    ) -> Union[str, dict]:
        """Make direct request without caching"""
        headers = self._get_request_headers()
        session = await self._get_session()
        proxy = random.choice(self.proxies) if self.proxies else None

        async with self.semaphore:
            async with session.request(
                method, url, params=params, proxy=proxy, headers=headers
            ) as resp:
                resp.raise_for_status()
                if return_json:
                    return await resp.json()
                return await resp.text()

    def get(self, url: str, **kwargs) -> Union[str, dict]:
        """Synchronous wrapper for GET requests."""
        return asyncio.run(self._request("GET", url, **kwargs))

    def post(self, url: str, **kwargs) -> Union[str, dict]:
        """Synchronous wrapper for POST requests."""
        return asyncio.run(self._request("POST", url, **kwargs))

    async def close(self) -> None:
        """Close the HTTP session and save cache metadata"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._save_cache_metadata()

    def cleanup_sync(self):
        """Synchronous cleanup method to be called explicitly"""
        if self._session and not self._session.closed:
            try:
                asyncio.run(self._session.close())
            except Exception:
                pass
        self._save_cache_metadata()

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self._save_cache_metadata()
        except Exception:
            pass

        # Don't try to close sessions in destructor - it causes issues
        # Sessions should be closed explicitly with cleanup_sync()
