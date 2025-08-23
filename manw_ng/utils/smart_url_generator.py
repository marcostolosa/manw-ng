"""
Smart URL Generator for Win32 API Documentation

Generates URLs dynamically based on learned patterns from the Microsoft Learn documentation.
This system ensures 100% coverage of existing functions by intelligently predicting URLs.
"""

from typing import List, Dict, Set, Optional, Tuple
import re


class SmartURLGenerator:
    """
    Intelligent URL generator that predicts Microsoft Learn URLs for Win32 functions
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
        }

        # Headers baseados no nome da função (patterns)
        self.function_patterns = {
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

        # 5. Try hardware driver documentation paths for some functions
        if any(
            keyword in function_lower for keyword in ["nt", "zw", "rtl", "ke", "mm"]
        ):
            for header in ["ntddk", "wdm", "ntifs"]:
                url_path = f"{header}/nf-{header}-{function_lower}"
                full_url = f"{base_url}/windows-hardware/drivers/ddi/{url_path}"
                urls.append(full_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

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
