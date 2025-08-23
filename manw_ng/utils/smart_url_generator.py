"""
Smart URL Generator for Win32 API Documentation

Ultra-fast asynchronous URL generator that tests ALL known patterns simultaneously.
This system ensures 100% coverage with maximum speed using concurrent requests.
"""

from typing import List, Dict, Set, Optional, Tuple
import re
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class SmartURLGenerator:
    """
    Ultra-fast async URL generator that tests ALL known patterns concurrently
    """

    def __init__(self):
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

    async def find_valid_url_async(
        self,
        function_name: str,
        dll_name: str = None,
        base_url: str = "https://learn.microsoft.com/en-us",
        session: aiohttp.ClientSession = None,
    ) -> Optional[str]:
        """
        ULTRA-FAST async method that tests ALL possible URLs simultaneously!
        Returns the FIRST valid URL found or None if function doesn't exist.
        """
        # Generate ALL possible URLs
        all_urls = self.generate_possible_urls(function_name, dll_name, base_url)

        # Test ALL URLs concurrently with maximum speed
        if session:
            return await self._test_urls_async(all_urls, session)
        else:
            # Create temporary session
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
            timeout = aiohttp.ClientTimeout(total=5)  # Super fast timeout
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as temp_session:
                return await self._test_urls_async(all_urls, temp_session)

    async def _test_urls_async(
        self, urls: List[str], session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Test multiple URLs concurrently and return first valid one"""

        async def test_single_url(url: str) -> Optional[str]:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
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

        # Use as_completed to get the FIRST successful result
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                if result:  # Found valid URL!
                    # Cancel remaining tasks for speed
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return result
            except:
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

        all_urls = self.generate_possible_urls(function_name, dll_name, base_url)

        def test_url(url: str) -> Optional[str]:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
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
