"""
Discovery Engine for MANW-NG

Intelligent URL discovery system based on reverse engineering techniques.
Multi-stage discovery pipeline to find any Win32 function.
"""

import re
from typing import List, Dict, Set, Optional
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.status import Status


class Win32DiscoveryEngine:
    """
    Intelligent discovery engine for Win32 API documentation
    """

    def __init__(self, base_url: str, session: requests.Session, quiet: bool = False):
        self.base_url = base_url
        self.session = session
        self.quiet = quiet
        self.console = Console()

        # Complete list of Win32 headers for intelligent fuzzing
        self.all_headers = [
            # Core System APIs
            "winbase",
            "winuser",
            "winreg",
            "winnt",
            "winnls",
            "wincon",
            "winerror",
            # Process/Thread
            "processthreadsapi",
            "synchapi",
            "handleapi",
            "namedpipeapi",
            # Memory
            "memoryapi",
            "heapapi",
            "virtualalloc",
            # File System
            "fileapi",
            "winioctl",
            "ioapiset",
            "wow64apiset",
            # Debugging
            "debugapi",
            "minidumpapiset",
            "imagehlp",
            "dbghelp",
            # Security
            "securitybaseapi",
            "authz",
            "sddl",
            "wincrypt",
            "ncrypt",
            "bcrypt",
            # Services
            "winsvc",
            "securityappcontainer",
            # Registry (extended)
            "winreg",
            "winperf",
            # Threading (extended)
            "threadpoollegacyapiset",
            "threadpoolapiset",
            # Libraries
            "libloaderapi",
            "errhandlingapi",
            # System Info
            "sysinfoapi",
            "systemtopologyapi",
            "processtopologyapi",
            # UI Extended
            "commctrl",
            "commdlg",
            "richedit",
            "shellapi",
            "shlobj_core",
            "shlwapi",
            # GDI
            "wingdi",
            # Network
            "winsock",
            "winsock2",
            "ws2tcpip",
            "wininet",
            "winhttp",
            "iphlpapi",
            "urlmon",
            # COM
            "objbase",
            "oleauto",
            "ole2",
            "olectl",
            # DirectX/Graphics
            "d3d11",
            "d3d12",
            "dxgi",
            "d2d1",
            # Crypto Extended
            "wintrust",
            "softpub",
            "mssip",
            # Tools/Debug Extended
            "tlhelp32",
            "psapi",
            "toolhelp",
            # Advanced
            "ntddscsi",
            "ntdddisk",
            "ntddser",
            "winternl",
        ]

    def discover_function_urls(self, function_name: str) -> List[str]:
        """
        Multi-stage discovery pipeline to find any Win32 function
        """
        discovered_urls = []

        # Pipeline de descoberta em ordem de eficiência

        # Estratégia 1: Fuzzing inteligente de patterns conhecidos (mais rápido)
        discovered_urls.extend(self._intelligent_fuzzing(function_name))

        # Estratégia 2: Busca oficial Microsoft (alta precisão)
        discovered_urls.extend(self._search_microsoft_docs(function_name))

        # Estratégia 3: Header-based discovery (cobertura ampla)
        discovered_urls.extend(self._header_based_discovery(function_name))

        # Estratégia 4: Pattern mining avançado (fallback)
        discovered_urls.extend(self._advanced_pattern_mining(function_name))

        # Remove duplicatas mantendo ordem de prioridade
        return self._deduplicate_urls(discovered_urls)[:20]

    def _intelligent_fuzzing(self, function_name: str) -> List[str]:
        """
        Fuzzing inteligente baseado em padrões algorítmicos de reverse engineering
        """
        func_lower = function_name.lower()
        urls = []

        # Gera URLs para cada header usando o padrão oficial Microsoft
        for header in self.all_headers:
            base_url = (
                f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{func_lower}"
            )
            urls.append(base_url)

            # Variações A/W automáticas
            if not func_lower.endswith("a") and not func_lower.endswith("w"):
                urls.append(f"{base_url}a")
                urls.append(f"{base_url}w")

        return urls[:15]

    def _header_based_discovery(self, function_name: str) -> List[str]:
        """
        Descoberta baseada em análise de headers - técnica avançada de RE
        """
        func_lower = function_name.lower()
        candidate_urls = []

        # Mapeamento semântico inteligente função -> headers prováveis
        semantic_mapping = {
            "process": ["processthreadsapi", "psapi", "toolhelp", "tlhelp32"],
            "thread": ["processthreadsapi", "synchapi", "threadpoollegacyapiset"],
            "create": ["processthreadsapi", "fileapi", "synchapi", "winbase"],
            "open": ["processthreadsapi", "fileapi", "winreg", "winsvc"],
            "close": ["handleapi", "winsvc", "winreg", "fileapi"],
            "virtual": ["memoryapi", "winbase"],
            "heap": ["heapapi", "winbase"],
            "memory": ["memoryapi", "heapapi", "winbase"],
            "file": ["fileapi", "winbase", "winioctl"],
            "reg": ["winreg", "winperf"],
            "window": ["winuser", "dwmapi"],
            "socket": ["winsock", "winsock2"],
            "crypt": ["wincrypt", "bcrypt", "ncrypt"],
            "debug": ["debugapi", "dbghelp"],
            "service": ["winsvc"],
            "library": ["libloaderapi"],
            "module": ["libloaderapi", "psapi"],
        }

        # Encontra headers relevantes
        relevant_headers = set()
        for pattern, headers in semantic_mapping.items():
            if pattern in func_lower:
                relevant_headers.update(headers)

        if not relevant_headers:
            relevant_headers = ["winbase", "winuser", "fileapi", "processthreadsapi"]

        # Gera URLs candidatas
        for header in relevant_headers:
            base_url = (
                f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{func_lower}"
            )
            candidate_urls.append(base_url)

            if not func_lower.endswith("a") and not func_lower.endswith("w"):
                candidate_urls.append(f"{base_url}a")
                candidate_urls.append(f"{base_url}w")

        return candidate_urls[:10]

    def _advanced_pattern_mining(self, function_name: str) -> List[str]:
        """
        Pattern mining avançado para casos complexos
        """
        func_lower = function_name.lower()
        mined_urls = []

        # Análise de prefixos e sufixos
        patterns = {
            "prefixes": {
                "nt": ["winternl", "ntdll"],
                "rtl": ["winternl", "ntdll"],
                "get": ["winbase", "winuser", "sysinfoapi"],
                "set": ["winbase", "winuser", "winreg"],
                "is": ["debugapi", "winbase"],
            },
            "suffixes": {
                "ex": ["winuser", "winreg", "fileapi"],
                "32": ["tlhelp32", "kernel32"],
                "w": ["winuser", "fileapi", "winbase"],
                "a": ["winuser", "fileapi", "winbase"],
            },
        }

        # Testa prefixos
        for prefix, headers in patterns["prefixes"].items():
            if func_lower.startswith(prefix):
                for header in headers:
                    base_url = f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{func_lower}"
                    mined_urls.append(base_url)

        # Testa sufixos
        for suffix, headers in patterns["suffixes"].items():
            if func_lower.endswith(suffix):
                for header in headers:
                    base_url = f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{func_lower}"
                    mined_urls.append(base_url)

        return mined_urls[:8]

    def _search_microsoft_docs(self, function_name: str) -> List[str]:
        """
        Busca oficial na documentação Microsoft
        """
        results = []
        search_url_base = self.base_url.replace(
            "/en-us", "/en-us/search/?scope=Windows&terms="
        )
        if "/pt-br" in self.base_url:
            search_url_base = self.base_url.replace(
                "/pt-br", "/pt-br/search/?scope=Windows&terms="
            )

        try:
            search_url = (
                f"{search_url_base}{function_name}+win32&category=Documentation"
            )
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text().lower()

                if all(
                    [
                        "/windows/win32/api/" in href.lower(),
                        function_name.lower() in href.lower(),
                        any(
                            keyword in text
                            for keyword in [function_name.lower(), "function", "api"]
                        ),
                    ]
                ):
                    if href.startswith("/"):
                        href = "https://learn.microsoft.com" + href
                    results.append(href)

        except Exception as e:
            if not self.quiet:
                self.console.print(f"[yellow]Busca Microsoft Docs falhou: {e}[/yellow]")

        return results[:5]

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicatas mantendo ordem"""
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        return unique_urls
