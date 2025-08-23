"""
Win32 API Documentation Crawler

Scrapes the official Microsoft Learn documentation to build a comprehensive
catalog of all Win32 API entries (functions, structures, enums, macros,
interfaces, methods, data types).

Supports both Portuguese (pt-br) and English (en-us) documentation.
Part of MANW-NG utils package.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import csv
import json
from pathlib import Path
import time
from bs4 import BeautifulSoup
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class APIEntry:
    """Represents a Win32 API entry"""

    name: str
    type: str  # function, struct, enum, macro, interface, method, datatype
    header: str
    url: str
    language: str  # pt-br or en-us
    description: Optional[str] = None


class Win32APICrawler:
    """Advanced crawler for Win32 API documentation"""

    def __init__(self):
        self.base_urls = {
            "en-us": "https://learn.microsoft.com/en-us/windows/win32/",
            "pt-br": "https://learn.microsoft.com/pt-br/windows/win32/",
        }

        # URL patterns for different API types
        self.api_patterns = {
            "function": re.compile(r"/api/([^/]+)/nf-\1-([^/]+)/?$"),
            "struct": re.compile(r"/api/([^/]+)/ns-\1-([^/]+)/?$"),
            "enum": re.compile(r"/api/([^/]+)/ne-\1-([^/]+)/?$"),
            "interface": re.compile(r"/api/([^/]+)/nn-\1-([^/]+)/?$"),
            "method": re.compile(
                r"/api/([^/]+)/nf-\1-([^-]+)-([^/]+)/?$"
            ),  # interface-method
            "macro": re.compile(
                r"/api/([^/]+)/nf-\1-([^/]+)/?$"
            ),  # Same as function, distinguished by content
        }

        # Data types patterns (non-API specific)
        self.datatype_patterns = [
            re.compile(r"/winprog/windows-data-types"),
            re.compile(r"/gdi/colorref"),
            re.compile(r"/winmsg/"),
            re.compile(r"/secauthz/"),
        ]

        self.visited_urls: Set[str] = set()
        self.api_entries: List[APIEntry] = []
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self.request_delay = 0.2  # seconds between requests
        self.max_concurrent = 20
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[Tuple[str, str]]:
        """Fetch a single page with rate limiting and error handling"""
        if not self.session:
            raise RuntimeError("Session not initialized")

        async with self.semaphore:
            try:
                await asyncio.sleep(self.request_delay)

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        return url, content
                    elif response.status == 404:
                        logger.warning(f"Page not found: {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None

            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {url}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None

    def extract_api_info(
        self, url: str, content: str, language: str
    ) -> Optional[APIEntry]:
        """Extract API information from a page"""
        soup = BeautifulSoup(content, "html.parser")

        # Try to extract the API name from the title or main heading
        title_elem = soup.find("h1") or soup.find("title")
        if not title_elem:
            return None

        title = title_elem.get_text().strip()

        # Determine API type and extract name/header from URL
        for api_type, pattern in self.api_patterns.items():
            match = pattern.search(url)
            if match:
                if api_type == "method":
                    header, interface, method = match.groups()
                    name = f"{interface}::{method}"
                else:
                    header, name = match.groups()

                # Special handling for macros vs functions
                if api_type in ["function", "macro"]:
                    # Distinguish by checking content for macro indicators
                    content_lower = content.lower()
                    if any(
                        indicator in content_lower
                        for indicator in ["#define", "macro", "preprocessor"]
                    ):
                        api_type = "macro"
                    else:
                        api_type = "function"

                # Extract description
                description = self.extract_description(soup)

                return APIEntry(
                    name=name,
                    type=api_type,
                    header=header,
                    url=url,
                    language=language,
                    description=description,
                )

        # Check for data type patterns
        for pattern in self.datatype_patterns:
            if pattern.search(url):
                # Extract name from title or URL
                name = self.extract_datatype_name(title, url)
                return APIEntry(
                    name=name,
                    type="datatype",
                    header="",  # Data types don't always have specific headers
                    url=url,
                    language=language,
                    description=self.extract_description(soup),
                )

        return None

    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description/summary from the page"""
        # Look for common description patterns
        desc_selectors = [
            ".summary p",
            ".description p:first-of-type",
            'meta[name="description"]',
            ".content p:first-of-type",
        ]

        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == "meta":
                    return elem.get("content", "").strip()
                else:
                    return elem.get_text().strip()[:200] + "..."

        return None

    def extract_datatype_name(self, title: str, url: str) -> str:
        """Extract data type name from title or URL"""
        # Remove common prefixes/suffixes from title
        title = re.sub(
            r"\s*(structure|function|macro|data type|type).*",
            "",
            title,
            flags=re.IGNORECASE,
        )
        title = re.sub(r".*\s+", "", title)  # Take last word if multiple

        if title.strip():
            return title.strip()

        # Fallback to URL
        return urlparse(url).path.split("/")[-1]

    def extract_links(self, content: str, base_url: str) -> Set[str]:
        """Extract relevant links from a page"""
        soup = BeautifulSoup(content, "html.parser")
        links = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)

            # Only process Win32 API related URLs
            if self.is_api_url(full_url):
                links.add(full_url)

        return links

    def is_api_url(self, url: str) -> bool:
        """Check if URL is a Win32 API documentation URL"""
        # Must be Microsoft Learn
        if "learn.microsoft.com" not in url:
            return False

        # Must be Win32 related
        if "/windows/win32/" not in url:
            return False

        # Check against our patterns
        for pattern in self.api_patterns.values():
            if pattern.search(url):
                return True

        # Check data type patterns
        for pattern in self.datatype_patterns:
            if pattern.search(url):
                return True

        return False

    async def crawl_recursive(
        self, start_url: str, language: str, max_depth: int = 2, max_pages: int = 1000
    ):
        """Recursively crawl Win32 API documentation"""
        queue = [(start_url, 0)]
        processed = 0

        logger.info(f"Starting crawl for {language} from {start_url}")

        while queue and processed < max_pages:
            current_batch = []

            # Process in batches for better performance
            for _ in range(min(self.max_concurrent, len(queue))):
                if queue:
                    current_batch.append(queue.pop(0))

            # Fetch batch concurrently
            tasks = []
            for url, depth in current_batch:
                if url not in self.visited_urls and depth <= max_depth:
                    tasks.append(self.fetch_page(url))
                    self.visited_urls.add(url)

            if not tasks:
                continue

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    continue

                if result is None:
                    continue

                url, content = result
                processed += 1

                logger.info(f"Processed {processed}: {url}")

                # Extract API information
                api_entry = self.extract_api_info(url, content, language)
                if api_entry:
                    self.api_entries.append(api_entry)
                    logger.info(f"Found {api_entry.type}: {api_entry.name}")

                # Extract links for next level (if not at max depth)
                current_url, current_depth = current_batch[i]
                if current_depth < max_depth:
                    new_links = self.extract_links(content, url)
                    for link in new_links:
                        if link not in self.visited_urls:
                            queue.append((link, current_depth + 1))

        logger.info(
            f"Completed crawl for {language}. Processed {processed} pages, found {len([e for e in self.api_entries if e.language == language])} API entries"
        )

    async def crawl_all_languages(self):
        """Crawl both language versions"""
        for language, base_url in self.base_urls.items():
            # Start from main API index pages
            start_urls = [
                f"{base_url}api/",
                f"{base_url}desktop-programming/",
                f"{base_url}winmsg/",
                f"{base_url}secauthz/",
            ]

            for start_url in start_urls:
                try:
                    await self.crawl_recursive(start_url, language)
                except Exception as e:
                    logger.error(f"Error crawling {start_url}: {str(e)}")
                    continue

    def save_results(self):
        """Save results in multiple formats"""
        # Save as CSV
        csv_path = Path("win32_api_catalog.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Nome", "Tipo", "Header", "URL", "Idioma", "Descrição"])

            for entry in sorted(
                self.api_entries, key=lambda x: (x.name.lower(), x.language)
            ):
                writer.writerow(
                    [
                        entry.name,
                        entry.type,
                        entry.header,
                        entry.url,
                        entry.language,
                        entry.description or "",
                    ]
                )

        # Save as JSON for programmatic use
        json_path = Path("win32_api_catalog.json")
        with open(json_path, "w", encoding="utf-8") as jsonfile:
            data = [
                {
                    "name": entry.name,
                    "type": entry.type,
                    "header": entry.header,
                    "url": entry.url,
                    "language": entry.language,
                    "description": entry.description,
                }
                for entry in self.api_entries
            ]
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)

        # Print summary table
        self.print_summary()

        logger.info(f"Results saved to {csv_path} and {json_path}")

    def print_summary(self):
        """Print summary statistics and sample of results"""
        print("\n" + "=" * 80)
        print("WIN32 API CATALOG - SUMMARY")
        print("=" * 80)

        # Statistics by type
        type_counts = {}
        lang_counts = {"pt-br": 0, "en-us": 0}

        for entry in self.api_entries:
            type_counts[entry.type] = type_counts.get(entry.type, 0) + 1
            lang_counts[entry.language] = lang_counts.get(entry.language, 0) + 1

        print(f"\nTotal entries found: {len(self.api_entries)}")
        print(f"Portuguese (pt-br): {lang_counts['pt-br']}")
        print(f"English (en-us): {lang_counts['en-us']}")

        print("\nEntries by type:")
        for api_type, count in sorted(type_counts.items()):
            print(f"  {api_type}: {count}")

        # Sample entries
        print("\nSample entries (first 20):")
        print("| Nome | Tipo | Header | Idioma |")
        print("|------|------|--------|--------|")

        for entry in sorted(self.api_entries, key=lambda x: x.name.lower())[:20]:
            print(
                f"| {entry.name} | {entry.type} | {entry.header} | {entry.language} |"
            )

        print("\n" + "=" * 80)


async def main():
    """Main crawler execution"""
    print("Win32 API Documentation Crawler")
    print("=" * 50)

    async with Win32APICrawler() as crawler:
        start_time = time.time()

        try:
            await crawler.crawl_all_languages()
        except KeyboardInterrupt:
            print("\nCrawling interrupted by user")
        except Exception as e:
            logger.error(f"Crawler error: {str(e)}")
        finally:
            end_time = time.time()
            print(f"\nCrawling completed in {end_time - start_time:.2f} seconds")

            if crawler.api_entries:
                crawler.save_results()
            else:
                print("No API entries found")


if __name__ == "__main__":
    asyncio.run(main())
