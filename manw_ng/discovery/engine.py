"""
Discovery Engine for MANW-NG

Intelligent URL discovery system based on reverse engineering techniques.
Multi-stage discovery pipeline to find any Win32 function.
"""

import re
import os
from typing import List, Dict, Set, Optional, Tuple
from bs4 import BeautifulSoup
from rich.console import Console
from rich.status import Status
from ..utils.url_verifier import SmartURLDiscovery, URLVerifier
from ..utils.catalog_integration import get_catalog
from ..utils.http_client import HTTPClient


class Win32DiscoveryEngine:
    """
    Intelligent discovery engine for Win32 API documentation
    """

    def __init__(
        self,
        base_url: str,
        http_client: HTTPClient,
        quiet: bool = False,
        user_agent: Optional[str] = None,
    ):
        self.base_url = base_url
        self.http = http_client
        self.quiet = quiet
        self.console = Console()

        # Extract locale from base_url
        if "pt-br" in base_url:
            self.locale = "pt-br"
        else:
            self.locale = "en-us"

        # Initialize new smart discovery system
        self.url_verifier = URLVerifier(user_agent=user_agent)
        self.smart_discovery = SmartURLDiscovery(self.url_verifier)
        self.catalog = get_catalog()

        # Get headers from catalog (more accurate and up-to-date)
        if self.catalog.is_catalog_available():
            self.all_headers = list(self.catalog.get_all_headers())
        else:
            # Fallback to essential headers
            self.all_headers = [
                "winuser",
                "winbase",
                "processthreadsapi",
                "memoryapi",
                "fileapi",
                "winreg",
                "synchapi",
                "libloaderapi",
            ]

    def discover_function_urls(self, function_name: str) -> List[str]:
        """
        Multi-stage discovery pipeline com cobertura completa usando padrões expandidos
        """
        discovered_urls = []

        # Sistema inteligente original
        url, method = self.smart_discovery.discover_function_url(
            function_name, self.locale
        )
        if url:
            discovered_urls.append(url)
            return discovered_urls

        # Descoberta específica por tipo de símbolo
        symbol_type = self._classify_symbol_type_safe(function_name)

        if symbol_type == "structure":
            discovered_urls.extend(self._structure_discovery(function_name))
        elif symbol_type == "native_function":
            discovered_urls.extend(self._native_api_discovery(function_name))
        elif symbol_type == "callback":
            discovered_urls.extend(self._callback_discovery(function_name))
        elif symbol_type == "com_interface":
            discovered_urls.extend(self._com_interface_discovery(function_name))

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

    def _native_api_discovery(self, function_name: str) -> List[str]:
        """Descoberta específica para Native API (Nt*/Zw*/Rtl*/Ldr*)"""
        urls = []
        function_lower = function_name.lower()

        # Headers específicos para Native API
        native_headers = ["winternl", "ntifs", "wdm", "ntddk", "fltkernel"]

        for header in native_headers:
            # Tentar em winternl primeiro
            url = f"{self.base_url}/windows/win32/api/{header}/nf-{header}-{function_lower}"
            urls.append(url)

            # Tentar em DDI drivers
            url = f"https://learn.microsoft.com/{self.locale}/windows-hardware/drivers/ddi/{header}/nf-{header}-{function_lower}"
            urls.append(url)

        return urls

    def _structure_discovery(self, function_name: str) -> List[str]:
        """Descoberta específica para estruturas"""
        urls = []
        function_lower = function_name.lower()

        # Headers comuns para estruturas
        struct_headers = ["winternl", "winnt", "winbase", "winuser"]

        for header in struct_headers:
            url = f"{self.base_url}/windows/win32/api/{header}/ns-{header}-{function_lower}"
            urls.append(url)

        return urls

    def _callback_discovery(self, function_name: str) -> List[str]:
        """Descoberta específica para callbacks"""
        urls = []
        function_lower = function_name.lower()

        # Headers comuns para callbacks
        callback_headers = ["winuser", "winbase", "winnt"]

        for header in callback_headers:
            url = f"{self.base_url}/windows/win32/api/{header}/nc-{header}-{function_lower}"
            urls.append(url)

        return urls

    def _com_interface_discovery(self, function_name: str) -> List[str]:
        """Descoberta específica para interfaces COM"""
        urls = []
        function_lower = function_name.lower()

        # Headers comuns para interfaces COM
        com_headers = ["unknwn", "objidl", "shobjidl", "comcat", "oleidl"]

        for header in com_headers:
            url = f"{self.base_url}/windows/win32/api/{header}/nn-{header}-{function_lower}"
            urls.append(url)

        return urls

    def _classify_symbol_type_safe(self, symbol_name: str) -> str:
        """Classificação de símbolo segura (sem imports circulares)"""
        symbol_lower = symbol_name.lower()

        if any(symbol_name.startswith(prefix) for prefix in ["Nt", "Zw", "Rtl", "Ldr"]):
            return "native_function"
        elif (symbol_name.isupper() and "_" in symbol_name) or symbol_lower in [
            "peb",
            "teb",
            "token_control",
        ]:
            return "structure"
        elif any(pattern in symbol_lower for pattern in ["proc", "callback", "hook"]):
            return "callback"
        elif (
            symbol_name.startswith("I")
            and len(symbol_name) > 1
            and symbol_name[1].isupper()
        ):
            return "com_interface"
        else:
            return "win32_function"

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

            # Timeout maior para CI/CD
            timeout = 30 if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else 15
            search_data = self.http.get(api_url, params=params, return_json=True)

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
            # Silenciar erros de busca - deixar o scraper gerenciar
            pass

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
            # Timeout maior para CI/CD
            timeout = 25 if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else 10
            html = self.http.get(search_url)
            soup = BeautifulSoup(html, "html.parser")

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
            # Silenciar erros de busca - deixar o scraper gerenciar
            pass

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

    def close(self):
        """Close resources used by the discovery engine."""
        self.url_verifier.close()
