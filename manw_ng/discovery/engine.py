"""
Discovery Engine for MANW-NG

Intelligent URL discovery system based on reverse engineering techniques.
Multi-stage discovery pipeline to find any Win32 function.
"""

import re
from typing import List, Dict, Set, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.status import Status
from ..utils.url_verifier import SmartURLDiscovery, URLVerifier
from ..utils.win32_url_patterns import Win32URLPatterns


class Win32DiscoveryEngine:
    """
    Intelligent discovery engine for Win32 API documentation
    """

    def __init__(self, base_url: str, session: requests.Session, quiet: bool = False):
        self.base_url = base_url
        self.session = session
        self.quiet = quiet
        self.console = Console()

        # Extract locale from base_url
        if "pt-br" in base_url:
            self.locale = "pt-br"
        else:
            self.locale = "en-us"

        # Initialize new smart discovery system
        self.url_verifier = URLVerifier()
        self.smart_discovery = SmartURLDiscovery(self.url_verifier)
        self.patterns = Win32URLPatterns()

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
            # RTL/Native API locations
            "winternl",
            "wdm",
            "ntddk",
            "ntifs",
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
        Multi-stage discovery pipeline to find any Win32 function using new smart system
        """
        discovered_urls = []

        # Nova estratégia principal: Sistema inteligente baseado em padrões
        url, method = self.smart_discovery.discover_function_url(
            function_name, self.locale
        )
        if url:
            if not self.quiet:
                self.console.print(f"[green]OK[/green] Found via {method}: {url}")
            discovered_urls.append(url)
            return (
                discovered_urls  # Se encontrou, não precisa tentar outras estratégias
            )

        # Fallback para sistema antigo se o novo não funcionar
        if not self.quiet:
            self.console.print(
                f"[yellow]INFO[/yellow] Smart discovery failed, trying legacy methods..."
            )

        # Special handling for RTL functions
        if function_name.lower().startswith("rtl"):
            discovered_urls.extend(self._rtl_function_discovery(function_name))

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

        # Special handling for NT functions - try multiple documentation locations
        if func_lower.startswith("nt") or func_lower.startswith("zw"):
            # NT functions can be in different documentation sections
            nt_patterns = [
                f"{self.base_url}/windows/win32/api/winternl/nf-winternl-{func_lower}",
                f"{self.base_url}/windows-hardware/drivers/ddi/ntddk/nf-ntddk-{func_lower}",
                f"{self.base_url}/windows-hardware/drivers/ddi/ntifs/nf-ntifs-{func_lower}",
                f"{self.base_url}/windows-hardware/drivers/ddi/wdm/nf-wdm-{func_lower}",
                f"{self.base_url}/windows-hardware/drivers/ddi/ntddk/nf-ntddk-zw{func_lower[2:]}",  # Nt->Zw mapping
            ]
            urls.extend(nt_patterns)

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

        return urls[:20]

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
        Busca oficial na documentação Microsoft usando múltiplas estratégias
        """
        results = []

        # Estratégia 1: API oficial de pesquisa do Microsoft Learn
        results.extend(self._search_microsoft_api(function_name))

        # Estratégia 2: Pesquisa por página HTML (fallback)
        results.extend(self._search_microsoft_html(function_name))

        return results[:10]  # Retorna top 10 resultados

    def _search_microsoft_api(self, function_name: str) -> List[str]:
        """
        Pesquisa usando a API oficial do Microsoft Learn
        """
        results = []

        try:
            # Detectar idioma baseado na base_url
            locale = "en-us" if "/en-us" in self.base_url else "pt-br"

            # API oficial do Microsoft Learn
            api_url = f"https://learn.microsoft.com/api/search"
            params = {
                "search": f"{function_name} win32 api",
                "locale": locale,
                "facet": "category",
                "$filter": "category eq 'Documentation'",
                "$top": 15,
                "expandScope": "true",
            }

            response = self.session.get(api_url, params=params, timeout=15)
            response.raise_for_status()

            search_data = response.json()

            if "results" in search_data:
                for result in search_data["results"]:
                    url = result.get("url", "")
                    title = result.get("title", "").lower()
                    description = result.get("description", "").lower()

                    # Verificar se é relevante para a função
                    if (
                        function_name.lower() in url.lower()
                        or function_name.lower() in title
                        or function_name.lower() in description
                    ):

                        # Priorizar URLs de API do Windows
                        if any(
                            pattern in url.lower()
                            for pattern in [
                                "/windows/win32/api/",
                                "/windows-hardware/drivers/ddi/",
                                "/windows/desktop/api/",
                            ]
                        ):
                            results.append(url)

        except Exception as e:
            if not self.quiet:
                self.console.print(f"[yellow]API search failed: {e}[/yellow]")

        return results

    def _search_microsoft_html(self, function_name: str) -> List[str]:
        """
        Pesquisa por página HTML (método tradicional como fallback)
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
                        any(
                            pattern in href.lower()
                            for pattern in [
                                "/windows/win32/api/",
                                "/windows-hardware/drivers/ddi/",
                                "/windows/desktop/api/",
                            ]
                        ),
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

        return results

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicatas mantendo ordem"""
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        return unique_urls

    def _rtl_function_discovery(self, function_name: str) -> List[str]:
        """Special discovery for RTL functions"""
        func_lower = function_name.lower()
        urls = []

        # RTL functions can be in multiple locations
        rtl_locations = [
            # Windows Driver Kit locations
            ("winternl", "winternl"),
            ("wdm", "wdm"),
            ("ntddk", "ntddk"),
            ("ntifs", "ntifs"),
            # Some RTL functions are documented as regular Win32
            ("winbase", "winbase"),
            ("kernel32", "kernel32"),
        ]

        for header, module in rtl_locations:
            # Try different URL patterns for RTL functions
            patterns = [
                f"{self.base_url}/windows-hardware/drivers/ddi/{header}/nf-{header}-{func_lower}",
                f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{func_lower}",
                f"{self.base_url}/windows-hardware/drivers/ddi/{module}/nf-{module}-{func_lower}",
            ]
            urls.extend(patterns)

        return urls

    def get_discovery_stats(self) -> Dict:
        """
        Retorna estatísticas completas do sistema de descoberta
        """
        stats = self.smart_discovery.get_discovery_stats()
        stats.update(
            {
                "legacy_headers_count": len(self.all_headers),
                "pattern_based_functions": len(self.patterns.FUNCTION_TO_MODULE),
                "supported_locales": ["en-us", "pt-br"],
            }
        )
        return stats

    def test_discovery_system(
        self, test_functions: List[str] = None
    ) -> Dict[str, bool]:
        """
        Testa o sistema de descoberta com funções conhecidas
        """
        if test_functions is None:
            test_functions = [
                "CreateProcessW",
                "OpenProcess",
                "VirtualAlloc",
                "HeapAlloc",
                "MessageBoxA",
                "RegOpenKeyExA",
                "socket",
                "LoadLibraryA",
                "RtlAllocateHeap",
                "CreateFileW",
                "ReadFile",
                "WriteFile",
            ]

        results = {}

        if not self.quiet:
            self.console.print("[bold blue]Testing discovery system...[/bold blue]")

        for func in test_functions:
            urls = self.discover_function_urls(func)
            results[func] = len(urls) > 0

            if not self.quiet:
                status = "[green]OK[/green]" if results[func] else "[red]FAIL[/red]"
                self.console.print(f"{status} {func}: {len(urls)} URLs found")

        success_rate = (sum(results.values()) / len(results)) * 100
        if not self.quiet:
            self.console.print(f"\n[bold]Success rate: {success_rate:.1f}%[/bold]")

        return results
