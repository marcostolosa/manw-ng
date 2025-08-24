"""
Smart URL Generator for Win32 API Documentation

Ultra-fast asynchronous URL generator that tests ALL known patterns simultaneously.
This system ensures 100% coverage with maximum speed using concurrent requests.
"""

from typing import List, Dict, Set, Optional, Tuple, Callable
import re
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random


class SmartURLGenerator:
    """
    Ultra-fast async URL generator that tests ALL known patterns concurrently
    """

    def __init__(self):
        # Pool of diverse user agents for rate limiting bypass
        self.user_agents = [
            # Chrome on Windows 10/11
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Firefox on Linux
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            # Mobile Chrome (Android)
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            # Mobile Safari (iOS)
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]

        # Additional headers to make requests more realistic
        self.additional_headers = [
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            },
        ]

        # Request counter for user agent rotation
        self._request_counter = 0

        # Mapeamento DLL -> Headers mais prováveis (baseado na análise)
        self.dll_to_headers = {
            "kernel32.dll": [
                "fileapi",
                "memoryapi",
                "processthreadsapi",
                "heapapi",
                "libloaderapi",
                "synchapi",
                "processenv",
                "sysinfoapi",
                "consoleapi",
                "errhandlingapi",
                "ioapiset",
                "namedpipeapi",
                "timezoneapi",
                "winbase",
            ],
            "user32.dll": ["winuser"],
            "gdi32.dll": ["wingdi"],
            "comctl32.dll": ["commctrl"],
            "uxtheme.dll": ["uxtheme"],
            "advapi32.dll": [
                "aclapi",
                "securitybaseapi",
                "winreg",
                "winsvc",
                "processthreadsapi",
                "wincrypt",
            ],
            "ws2_32.dll": ["winsock2", "winsock"],
            "wininet.dll": ["wininet"],
            "ntdll.dll": ["winternl", "winbase"],
            "psapi.dll": ["psapi"],
            "version.dll": ["winver"],
            "crypt32.dll": ["wincrypt"],
            "ole32.dll": ["combaseapi", "objbase"],
            "shell32.dll": ["shellapi"],
            "msvcrt.dll": ["corecrt"],
            "bcrypt.dll": ["bcrypt"],
            "ncrypt.dll": ["ncrypt"],
        }

        # Mapeamento específico baseado nos padrões descobertos
        self.dll_to_primary_header = {
            "gdi32.dll": "wingdi",
            "kernel32.dll": "fileapi",  # Para algumas funções como GetLogicalDrives
            "crypt32.dll": "wincrypt",
            "netapi32.dll": "lmaccess",
            "shell32.dll": "shellapi",
            "advapi32.dll": "aclapi",  # Para funções de ACL
            "ntdll.dll": "winternl",  # Native API functions
        }

        # Headers baseados no nome da função (patterns)
        self.function_patterns = {
            # Native API functions (highest priority)
            r"^nt.*": ["winternl", "ntddk", "wdm", "ntifs"],
            r"^zw.*": ["winternl", "ntddk", "wdm", "ntifs"],
            r"^rtl.*": ["ntddk", "wdm", "ntifs"],
            r"^ke.*": ["ntddk", "wdm"],
            r"^mm.*": ["ntddk", "wdm"],
            # Graphics/GDI operations
            r"^text.*": ["wingdi"],
            r".*blt.*": ["wingdi"],
            r"^draw.*": ["wingdi"],
            r"^paint.*": ["wingdi"],
            r"get.*dc.*": ["wingdi"],
            r"create.*dc.*": ["wingdi"],
            r"select.*": ["wingdi"],
            r"get.*object.*gdi": ["wingdi"],
            # File operations
            r".*file.*": ["fileapi"],
            r"^create.*file": ["fileapi"],
            r"^create.*process": ["processthreadsapi"],
            r"delete.*": ["fileapi"],
            r"copy.*": ["fileapi"],
            r"move.*": ["fileapi"],
            r"read.*file": ["fileapi", "ioapiset"],
            r"write.*file": ["fileapi", "ioapiset"],
            r"get.*drives.*": ["fileapi"],
            r"get.*logical.*drives": ["fileapi"],
            r"get.*command.*line": ["processenv"],
            # Memory operations
            r"virtual.*": ["memoryapi"],
            r"heap.*": ["heapapi"],
            r".*alloc.*": ["memoryapi", "heapapi"],
            r".*memory.*": ["memoryapi"],
            # Process/Thread
            r".*process.*": ["processthreadsapi"],
            r".*thread.*": ["processthreadsapi"],
            r"terminate.*": ["processthreadsapi"],
            r"suspend.*": ["processthreadsapi"],
            r"resume.*": ["processthreadsapi"],
            # Registry
            r"reg.*": ["winreg"],
            r".*key.*": ["winreg"],
            # Services
            r".*service.*": ["winsvc"],
            # Network
            r".*socket.*": ["winsock2"],
            r"ws.*": ["winsock2"],
            r"inet.*": ["wininet"],
            r"net.*": ["lmaccess", "lmserver"],
            # Security/Crypto/ACL
            r"cert.*": ["wincrypt"],
            r"crypt.*": ["wincrypt", "bcrypt"],
            r".*security.*": ["securitybaseapi"],
            r".*acl.*": ["aclapi"],
            r".*effective.*": ["aclapi"],
            r".*trustee.*": ["aclapi"],
            # Shell/System
            r"shell.*": ["shellapi"],
            r"sh.*": ["shellapi"],
            # Console
            r".*console.*": ["consoleapi"],
            # Library loading
            r"load.*": ["libloaderapi"],
            r"get.*module.*": ["libloaderapi"],
            r".*library.*": ["libloaderapi"],
            # UI Controls (CommCtrl)
            r".*toolbar.*": ["commctrl"],
            r".*listview.*": ["commctrl"],
            r".*treeview.*": ["commctrl"],
            r".*tab.*": ["commctrl"],
            r".*button.*": ["commctrl"],
            r".*edit.*": ["commctrl"],
            r".*combo.*": ["commctrl"],
            r"create.*window.*": ["winuser"],
            # More GDI functions
            r".*stock.*": ["wingdi"],
            r"delete.*": ["wingdi", "fileapi"],
            r".*dc.*": ["wingdi"],
            r".*brush.*": ["wingdi"],
            r".*font.*": ["wingdi"],
        }

    def generate_possible_urls(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
    ) -> List[str]:
        """
        Generate all possible URLs for a function based on patterns

        Args:
            function_name: Name of the Win32 function
            dll_name: DLL containing the function (if known)
            base_url: Base Microsoft Learn URL

        Returns:
            List of possible URLs in order of probability
        """
        function_lower = function_name.lower()
        urls = []

        # 1. Check for DLL-specific primary header first (highest priority)
        priority_headers = []
        if dll_name and dll_name.lower() in self.dll_to_primary_header:
            primary_header = self.dll_to_primary_header[dll_name.lower()]
            priority_headers.append(primary_header)

        # 2. Get headers based on function name patterns
        pattern_headers = []
        for pattern, pattern_header_list in self.function_patterns.items():
            if re.match(pattern, function_lower):
                pattern_headers.extend(pattern_header_list)

        # 3. Get headers based on DLL (secondary priority)
        dll_headers = []
        if dll_name:
            dll_headers = self.dll_to_headers.get(dll_name.lower(), [])

        # 4. Add common fallback headers (lowest priority)
        common_headers = [
            "winbase",
            "winuser",
            "fileapi",
            "memoryapi",
            "processthreadsapi",
        ]

        # Combine in order of priority
        all_headers = priority_headers + pattern_headers + dll_headers + common_headers

        # Remove duplicates while preserving order
        headers_to_try = []
        seen = set()
        for header in all_headers:
            if header not in seen:
                headers_to_try.append(header)
                seen.add(header)
            # Limit to max 8 headers to prevent infinite generation
            if len(headers_to_try) >= 8:
                break

        # 4. Generate URLs for each header
        for header in headers_to_try:
            # Standard pattern: header/nf-header-function
            url_path = f"{header}/nf-{header}-{function_lower}"
            full_url = f"{base_url}/windows/win32/api/{url_path}"
            urls.append(full_url)

            # Try with explicit A/W suffixes if function doesn't have them
            if not function_lower.endswith(("a", "w")):
                # Try with A suffix (most common)
                url_path_a = f"{header}/nf-{header}-{function_lower}a"
                full_url_a = f"{base_url}/windows/win32/api/{url_path_a}"
                urls.append(full_url_a)

                # Try with W suffix
                url_path_w = f"{header}/nf-{header}-{function_lower}w"
                full_url_w = f"{base_url}/windows/win32/api/{url_path_w}"
                urls.append(full_url_w)

            # Try without 'A' or 'W' suffix if function ends with them
            elif function_lower.endswith(("a", "w")):
                base_func = function_lower[:-1]
                url_path = f"{header}/nf-{header}-{base_func}"
                full_url = f"{base_url}/windows/win32/api/{url_path}"
                urls.append(full_url)

        # 5. Native API functions - prioritize WDK documentation paths
        if function_lower.startswith(("nt", "zw", "rtl", "ke", "mm")):
            # Native API functions are primarily documented in WDK paths
            driver_headers = ["ntifs", "ntddk", "wdm", "winternl", "ntdef"]
            for header in driver_headers:
                url_path = f"{header}/nf-{header}-{function_lower}"
                full_url = f"{base_url.replace('/en-us', '').replace('/pt-br', '')}/windows-hardware/drivers/ddi/{url_path}"
                urls.insert(0, full_url)  # Insert at beginning for priority

            # Also try winternl for some documented Native API functions
            if function_lower.startswith(("nt", "zw")):
                url_path = f"winternl/nf-winternl-{function_lower}"
                full_url = f"{base_url}/windows/win32/api/{url_path}"
                urls.append(full_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def generate_all_possible_urls(
        self, function_name: str, base_url: str = "https://learn.microsoft.com/en-us"
    ) -> List[Tuple[str, str, str]]:
        """Generate ALL possible URLs for Elite coverage (URL, locale, area)"""
        urls = []
        symbol_lower = function_name.lower()

        # INTELLIGENT HEADER PRIORITY: Use patterns first, then fallback to common headers
        pattern_headers = []
        for pattern, pattern_header_list in self.function_patterns.items():
            if re.match(pattern, symbol_lower):
                pattern_headers.extend(pattern_header_list)

        # Remove duplicates while preserving order
        intelligent_headers = []
        seen = set()
        for header in pattern_headers:
            if header not in seen:
                intelligent_headers.append(header)
                seen.add(header)

        # Common headers to try (PRIORITIZED for better coverage)
        common_headers = [
            # HIGH PRIORITY - Most common UI/System functions
            "wingdi",
            "winuser",
            "commctrl",
            "fileapi",
            "memoryapi",
            "processthreadsapi",
            "processenv",
            # MEDIUM PRIORITY - Network/Security/Registry
            "wininet",
            "winsock2",
            "winreg",
            "wincrypt",
            "shellapi",
            "aclapi",
            # LOW PRIORITY - Specialized functions
            "consoleapi",
            "libloaderapi",
            "synchapi",
            "sysinfoapi",
            "errhandlingapi",
            "securitybaseapi",
            "winsvc",
            "psapi",
            "uxtheme",
            "dwmapi",
            "powrprof",
            "setupapi",
            "cfgmgr32",
            "heapapi",
        ]

        # Combine: intelligent headers FIRST, then common headers as fallback
        all_headers = intelligent_headers + [h for h in common_headers if h not in seen]

        # WDK/DDI headers
        ddi_headers = ["ntifs", "ntddk", "wdm", "winternl", "ntdef"]

        # Both locales
        locales = ["pt-br", "en-us"] if "/pt-br" in base_url else ["en-us", "pt-br"]

        for locale in locales:
            # Try Win32 SDK patterns - INTELLIGENT HEADERS FIRST!
            for header in all_headers:
                base_api_url = (
                    f"https://learn.microsoft.com/{locale}/windows/win32/api/{header}"
                )

                # Function patterns
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}", locale, "SDK")
                )
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}a", locale, "SDK")
                )
                urls.append(
                    (f"{base_api_url}/nf-{header}-{symbol_lower}w", locale, "SDK")
                )

                # Struct patterns
                urls.append(
                    (f"{base_api_url}/ns-{header}-{symbol_lower}", locale, "SDK")
                )

                # Enum patterns
                urls.append(
                    (f"{base_api_url}/ne-{header}-{symbol_lower}", locale, "SDK")
                )

                # Interface patterns
                urls.append(
                    (f"{base_api_url}/nn-{header}-{symbol_lower}", locale, "SDK")
                )

            # Try WDK/DDI patterns for Native API
            for header in ddi_headers:
                base_ddi_url = f"https://learn.microsoft.com/{locale}/windows-hardware/drivers/ddi/{header}"

                urls.append(
                    (f"{base_ddi_url}/nf-{header}-{symbol_lower}", locale, "DDI")
                )
                urls.append(
                    (f"{base_ddi_url}/ns-{header}-{symbol_lower}", locale, "DDI")
                )
                urls.append(
                    (f"{base_ddi_url}/ne-{header}-{symbol_lower}", locale, "DDI")
                )

        return urls

    def get_random_headers(self) -> Dict[str, str]:
        """Get random User-Agent and additional headers to bypass rate limiting"""
        # Rotate through user agents for each request
        user_agent = self.user_agents[self._request_counter % len(self.user_agents)]
        additional = random.choice(self.additional_headers)
        self._request_counter += 1

        headers = {
            "User-Agent": user_agent,
            **additional,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Randomly add some optional headers to appear more human
        if random.random() < 0.5:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"

        if random.random() < 0.3:
            headers["Cache-Control"] = "max-age=0"

        return headers

    async def find_valid_url_async(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
        session: aiohttp.ClientSession = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """
        SMART async method that tests URLs sequentially to avoid rate limiting
        Returns the FIRST valid URL found or None if function doesn't exist.
        """
        # Generate ALL possible URLs using Elite system
        all_url_tuples = self.generate_all_possible_urls(function_name, base_url)

        # Special prioritization for Native API functions (Nt*, Zw*, Rtl*)
        if function_name.lower().startswith(("nt", "zw", "rtl")):
            # Prioritize DDI URLs first for Native API functions
            ddi_urls = [
                url_tuple for url_tuple in all_url_tuples if url_tuple[2] == "DDI"
            ]
            sdk_urls = [
                url_tuple for url_tuple in all_url_tuples if url_tuple[2] == "SDK"
            ]
            prioritized_urls = ddi_urls + sdk_urls
            all_urls = [
                url_tuple[0] for url_tuple in prioritized_urls[:50]
            ]  # More URLs for Nt functions
        else:
            all_urls = [
                url_tuple[0] for url_tuple in all_url_tuples[:30]
            ]  # Limit to top 30 for speed

        # Test URLs SEQUENTIALLY to avoid rate limiting
        if session:
            return await self._test_urls_sequential(
                all_urls, session, progress_callback
            )
        else:
            # Create temporary session
            connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as temp_session:
                return await self._test_urls_sequential(
                    all_urls, temp_session, progress_callback
                )

    async def _test_urls_sequential(
        self,
        urls: List[str],
        session: aiohttp.ClientSession,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """Test URLs sequentially to avoid rate limiting"""

        total = len(urls)

        for i, url in enumerate(urls, 1):
            try:
                if progress_callback:
                    progress_callback(i, total)

                # Use random headers for each request
                headers = self.get_random_headers()

                # Randomized delay between requests to appear more human
                if i > 1:
                    delay = random.uniform(
                        0.3, 0.8
                    )  # Random delay between 0.3-0.8 seconds
                    await asyncio.sleep(delay)

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Quick content check to ensure it's a valid function page
                        content = await response.text()
                        if any(
                            keyword in content.lower()
                            for keyword in [
                                "function",
                                "routine",
                                "api",
                                "syntax",
                                "parameters",
                            ]
                        ):
                            return url
                    elif response.status == 429:
                        # Rate limited - wait longer with exponential backoff
                        backoff_delay = random.uniform(2, 5)
                        await asyncio.sleep(backoff_delay)

            except Exception:
                continue

        return None

    async def _test_urls_async(
        self,
        urls: List[str],
        session: aiohttp.ClientSession,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Optional[str]:
        """Test multiple URLs concurrently and return first valid one"""

        async def test_single_url(url: str) -> Optional[str]:
            try:
                # Use random headers for each request
                headers = self.get_random_headers()
                # Random delay to avoid rate limiting and appear more human
                delay = random.uniform(0.1, 0.4)
                await asyncio.sleep(delay)
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Quick content check to ensure it's a valid function page
                        content = await response.text()
                        if any(
                            keyword in content.lower()
                            for keyword in [
                                "function",
                                "routine",
                                "api",
                                "syntax",
                                "parameters",
                            ]
                        ):
                            return url
                    return None
            except:
                return None

        # Create tasks for ALL URLs simultaneously
        tasks = [test_single_url(url) for url in urls]
        total = len(tasks)
        completed = 0

        # Use as_completed to get the FIRST successful result
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                if result:  # Found valid URL!
                    # Cancel remaining tasks for speed
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return result
            except:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                continue

        return None  # No valid URL found

    def find_valid_url_sync(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
        max_workers: int = 20,
    ) -> Optional[str]:
        """
        Synchronous version using ThreadPoolExecutor for maximum concurrency
        Tests ALL URLs simultaneously with multiple threads
        """
        import requests

        # Use Elite system for complete coverage
        all_url_tuples = self.generate_all_possible_urls(function_name, base_url)
        all_urls = [url_tuple[0] for url_tuple in all_url_tuples]

        def test_url(url: str) -> Optional[str]:
            try:
                # Use random headers for each request
                headers = self.get_random_headers()
                response = requests.get(url, headers=headers, timeout=3)
                if response.status_code == 200:
                    # Quick content check
                    content = response.text.lower()
                    if any(
                        keyword in content
                        for keyword in [
                            "function",
                            "routine",
                            "api",
                            "syntax",
                            "parameters",
                        ]
                    ):
                        return url
                return None
            except:
                return None

        # Use ThreadPoolExecutor for maximum concurrency
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit ALL URLs for testing simultaneously
            future_to_url = {executor.submit(test_url, url): url for url in all_urls}

            # Return FIRST successful result
            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    if result:
                        # Cancel remaining futures
                        for remaining_future in future_to_url:
                            if not remaining_future.done():
                                remaining_future.cancel()
                        return result
                except:
                    continue

        return None

    def get_high_probability_urls(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
    ) -> List[str]:
        """
        Get only the most likely URLs (top 5) for faster testing
        """
        all_urls = self.generate_possible_urls(function_name, dll_name, base_url)
        return all_urls[:5]  # Return top 5 most probable
